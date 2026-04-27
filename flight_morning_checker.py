#!/usr/bin/env python3
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from html import unescape
from typing import List

DEFAULT_ROUTE_FROM = 'CJJ'
DEFAULT_ROUTE_TO = 'CJU'
DEFAULT_DATE = '2026-09-24'
DEFAULT_SOURCE = 'kayak'

KAYAK_ROUTE_URL = 'https://www.kayak.co.kr/%ED%95%AD%EA%B3%B5%EA%B6%8C/%EC%B2%AD%EC%A3%BC%EA%B5%AD%EC%A0%9C%EA%B3%B5%ED%95%AD-CJJ/%EC%A0%9C%EC%A3%BC%EA%B5%AD%EC%A0%9C%EA%B3%B5%ED%95%AD-CJU'
USER_AGENT = 'Mozilla/5.0 (OpenClaw FlightMorningChecker)'


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
    notes: List[str]
    fetchedAt: str


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode('utf-8', errors='ignore')


def clean(text: str) -> str:
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


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
                source='KAYAK',
            )
        )
    return flights


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


def check_kayak(route_from: str, route_to: str, date_str: str) -> Result:
    notes = []
    if route_from != 'CJJ' or route_to != 'CJU':
        notes.append('현재 버전은 KAYAK 청주(CJJ) → 제주(CJU) 전용 경로에 맞춰져 있어 다른 노선은 추가 구현이 필요합니다.')
    if date_str != DEFAULT_DATE:
        notes.append('현재 소스 URL은 날짜 파라미터를 직접 반영하지 않아, 목표 날짜 편 데이터가 실제로 노출될 때만 정확 검출됩니다.')

    html = fetch(KAYAK_ROUTE_URL)
    flights = extract_kayak_flights(html)
    target_day = filter_target_day(flights, date_str)
    morning = filter_morning(target_day)

    if not target_day:
        notes.append('현재 소스가 목표 날짜의 정확한 편 데이터를 노출하지 않아 잠정 결과입니다.')

    return Result(
        routeFrom=route_from,
        routeTo=route_to,
        date=date_str,
        source='KAYAK',
        hasMorningFlight=bool(morning),
        morningFlightCount=len(morning),
        morningFlights=[asdict(flight) for flight in morning],
        targetDayFlightCount=len(target_day),
        notes=notes,
        fetchedAt=datetime.utcnow().isoformat() + 'Z',
    )


def parse_args():
    parser = argparse.ArgumentParser(description='Check whether morning flights exist for a target route/date.')
    parser.add_argument('--from', dest='route_from', default=DEFAULT_ROUTE_FROM, help='Origin airport IATA code')
    parser.add_argument('--to', dest='route_to', default=DEFAULT_ROUTE_TO, help='Destination airport IATA code')
    parser.add_argument('--date', dest='date_str', default=DEFAULT_DATE, help='Target date in YYYY-MM-DD')
    parser.add_argument('--source', dest='source', default=DEFAULT_SOURCE, choices=['kayak'], help='Source backend')
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        if args.source == 'kayak':
            result = check_kayak(args.route_from, args.route_to, args.date_str)
        else:
            raise ValueError('Unsupported source')
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
