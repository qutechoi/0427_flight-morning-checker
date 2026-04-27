#!/usr/bin/env python3
import argparse
import json
import re
import sys
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from html import unescape
from typing import List

DEFAULT_ROUTE_FROM = 'CJJ'
DEFAULT_ROUTE_TO = 'CJU'
DEFAULT_DATE = '2026-09-24'
DEFAULT_SOURCE = 'multi'

KAYAK_ROUTE_URL = 'https://www.kayak.co.kr/%ED%95%AD%EA%B3%B5%EA%B6%8C/%EC%B2%AD%EC%A3%BC%EA%B5%AD%EC%A0%9C%EA%B3%B5%ED%95%AD-CJJ/%EC%A0%9C%EC%A3%BC%EA%B5%AD%EC%A0%9C%EA%B3%B5%ED%95%AD-CJU'
CHEONGJU_AIRPORT_SCHEDULE_URL = 'https://www.airport.co.kr/cheongju/cms/frCon/index.do?MENU_ID=110'
USER_AGENT = 'Mozilla/5.0 (OpenClaw FlightMorningChecker)'
KNOWN_AIRLINES = ['대한항공', '아시아나항공', '제주항공', '진에어', '이스타 항공', '이스타항공', '티웨이항공', '에어로케이항공', 'Aero K']


@dataclass
class Flight:
    airline: str
    departureTime: str
    arrivalTime: str
    source: str


@dataclass
class Result:
    routeFrom: str
    routeTo: str
    date: str
    source: str
    hasMorningFlight: bool
    morningFlightCount: int
    morningFlights: List[dict]
    targetDayFlightCount: int
    detectedAirlines: List[str]
    evidenceLevel: str
    notes: List[str]
    fetchedAt: str


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode('utf-8', errors='ignore')


def clean(text: str) -> str:
    text = unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_meta(html: str):
    title_match = re.search(r'<title>(.*?)</title>', html, re.I | re.S)
    desc_match = re.search(r'<meta\s+name="description"\s+content="(.*?)"', html, re.I | re.S)
    title = clean(title_match.group(1)) if title_match else ''
    desc = clean(desc_match.group(1)) if desc_match else ''
    return title, desc


def extract_kayak_flights(html: str) -> List[Flight]:
    pattern = re.compile(
        r'"provider":\{"@type":"Airline","name":"([^"]+)"\}.*?'
        r'"departureTime":"([^"]+)".*?'
        r'"arrivalTime":"([^"]+)"',
        re.S,
    )
    flights = []
    for airline, departure, arrival in pattern.findall(html):
        flights.append(
            Flight(
                airline=clean(airline),
                departureTime=departure,
                arrivalTime=arrival,
                source='KAYAK-structured',
            )
        )
    return flights


def detect_airlines(text: str) -> List[str]:
    found = []
    for airline in KNOWN_AIRLINES:
        if airline in text and airline not in found:
            found.append(airline)
    return found


def filter_target_day(flights: List[Flight], date_str: str) -> List[Flight]:
    return [flight for flight in flights if flight.departureTime.startswith(date_str)]


def filter_morning(flights: List[Flight]) -> List[Flight]:
    morning = []
    for flight in flights:
        try:
            dt = datetime.fromisoformat(flight.departureTime)
            if dt.hour < 12:
                morning.append(flight)
        except ValueError:
            continue
    return morning


def check_multi(route_from: str, route_to: str, date_str: str) -> Result:
    notes = []
    if route_from != 'CJJ' or route_to != 'CJU':
        notes.append('현재 버전은 청주(CJJ) → 제주(CJU) 중심으로 튜닝되어 있어 다른 노선은 추가 구현이 필요합니다.')

    kayak_html = fetch(KAYAK_ROUTE_URL)
    kayak_title, kayak_desc = extract_meta(kayak_html)
    kayak_text = clean(kayak_html)
    kayak_flights = extract_kayak_flights(kayak_html)
    target_day = filter_target_day(kayak_flights, date_str)
    morning = filter_morning(target_day)

    airline_sources = [kayak_title, kayak_desc, kayak_text[:12000]]
    airlines = []
    for chunk in airline_sources:
        for airline in detect_airlines(chunk):
            if airline not in airlines:
                airlines.append(airline)

    airport_available = False
    try:
        airport_html = fetch(CHEONGJU_AIRPORT_SCHEDULE_URL)
        airport_available = '운항스케줄' in airport_html or '꼭 확인해 주세요' in airport_html
    except Exception as exc:
        notes.append(f'청주공항 운항스케줄 페이지 확인 실패: {exc}')

    evidence_level = 'low'
    if target_day:
        evidence_level = 'high'
    elif len(airlines) >= 3 and airport_available:
        evidence_level = 'medium'
    elif airlines:
        evidence_level = 'low'

    if not target_day:
        notes.append('현재 KAYAK route 페이지가 목표 날짜의 실제 편 데이터를 직접 노출하지 않아, 오전편 판정은 아직 잠정적입니다.')
    if airlines:
        notes.append('메타 설명과 본문 텍스트 기준으로 현재 노선 관련 항공사 힌트를 넓게 수집했습니다.')
    if airport_available:
        notes.append('청주공항 운항스케줄 페이지 접근은 가능하지만, 현재 일반 fetch만으로는 목표 날짜별 상세 편명/시간이 직접 추출되지는 않습니다.')
    if '아시아나항공' not in airlines:
        notes.append('현재 공개 소스 텍스트에서는 아시아나항공이 직접 감지되지 않았습니다. 나중에 노출되면 자동으로 포함됩니다.')

    return Result(
        routeFrom=route_from,
        routeTo=route_to,
        date=date_str,
        source='KAYAK+CheongjuAirport',
        hasMorningFlight=bool(morning),
        morningFlightCount=len(morning),
        morningFlights=[asdict(flight) for flight in morning],
        targetDayFlightCount=len(target_day),
        detectedAirlines=airlines,
        evidenceLevel=evidence_level,
        notes=notes,
        fetchedAt=datetime.utcnow().isoformat() + 'Z',
    )


def parse_args():
    parser = argparse.ArgumentParser(description='Check whether morning flights exist for a target route/date.')
    parser.add_argument('--from', dest='route_from', default=DEFAULT_ROUTE_FROM, help='Origin airport IATA code')
    parser.add_argument('--to', dest='route_to', default=DEFAULT_ROUTE_TO, help='Destination airport IATA code')
    parser.add_argument('--date', dest='date_str', default=DEFAULT_DATE, help='Target date in YYYY-MM-DD')
    parser.add_argument('--source', dest='source', default=DEFAULT_SOURCE, choices=['multi', 'kayak'], help='Source backend')
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        result = check_multi(args.route_from, args.route_to, args.date_str)
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({
            'ok': False,
            'error': str(exc),
            'routeFrom': args.route_from,
            'routeTo': args.route_to,
            'date': args.date_str,
            'source': args.source,
        }, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()
