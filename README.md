# 0427_flight-morning-checker

청주(CJJ) → 제주(CJU) 노선에서 **특정 날짜 오전 12시 이전 출발편이 있는지** 확인하기 위한 전용 Python CLI 도구입니다.

## What changed in v3

3차 개발에서는 항공사 힌트 수집 범위를 더 넓혔습니다.

이제 다음 항공사를 감지 대상으로 둡니다.
- 대한항공
- 아시아나항공
- 제주항공
- 진에어
- 이스타 항공
- 티웨이항공
- 에어로케이항공 / Aero K

그리고 KAYAK의:
- 구조화된 flight 메타데이터
- meta description
- 본문 텍스트 일부
를 함께 스캔해서 `detectedAirlines`를 넓게 채웁니다.

## Important note

이 항공사 목록은 **실제 예약 가능 확정 목록**이 아니라,
현재 공개 소스에서 **노선 관련 근거로 감지된 항공사 힌트**입니다.

즉:
- `detectedAirlines`는 노선 후보/근거
- `morningFlights`는 실제 목표 날짜 인스턴스를 잡았을 때의 직접 근거

라고 이해하면 됩니다.

## Evidence levels

- `high`: 목표 날짜의 실제 flight instance가 검출됨
- `medium`: 목표 날짜 인스턴스는 없지만, 여러 항공사 힌트 + 공항 스케줄 페이지 접근이 확인됨
- `low`: 제한된 힌트만 있는 잠정 상태

## Usage

```bash
python3 flight_morning_checker.py
```

## Output fields

- `hasMorningFlight`
- `morningFlightCount`
- `morningFlights`
- `targetDayFlightCount`
- `detectedAirlines`
- `evidenceLevel`
- `notes`

## Current limitation

여전히 핵심 한계는 남아 있습니다.

- 공개 페이지가 목표 날짜 실제 편 데이터를 항상 노출하지 않음
- 항공사 사이트는 봇 차단/오류 페이지가 잦음
- 그래서 일부 항공사는 텍스트 근거로만 감지될 수 있음

하지만 현재 버전은 이전보다:
- 항공사 범위가 넓고
- 근거가 더 많고
- cron 보고용으로 더 실용적입니다.
