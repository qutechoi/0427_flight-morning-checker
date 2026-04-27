# 0427_flight-morning-checker

청주(CJJ) → 제주(CJU) 노선에서 **특정 날짜 오전 12시 이전 출발편이 있는지** 확인하기 위한 전용 Python CLI 도구입니다.

## What changed in v2

2차 개발에서는 단일 소스만 보는 대신 다음을 함께 확인합니다.

- **KAYAK route page**의 구조화된 `Flight` 메타데이터
- **KAYAK meta description** 에서 보이는 항공사 힌트
- **청주공항 운항스케줄 페이지** 접근 가능 여부

즉, 단순 yes/no 대신:
- 오전편 실제 검출 여부
- 목표 날짜 편 검출 수
- 감지된 항공사
- 근거 수준(`high` / `medium` / `low`)
을 함께 돌려줍니다.

## Evidence levels

- `high`: 목표 날짜의 실제 flight instance가 검출됨
- `medium`: 목표 날짜 인스턴스는 없지만, 노선 항공사 힌트 + 공항 스케줄 페이지 접근이 확인됨
- `low`: 메타 힌트만 있는 잠정 상태

## Why this exists

필요한 건 “최저가”가 아니라:

> **2026-09-24 청주 → 제주 노선에 오전 출발편이 있는가?**

이 질문에 답하는 것입니다.

## Usage

```bash
python3 flight_morning_checker.py
```

### Custom arguments

```bash
python3 flight_morning_checker.py --from CJJ --to CJU --date 2026-09-24 --source multi
```

## Output fields

- `hasMorningFlight`: 오전 12시 전 출발편 탐지 여부
- `morningFlightCount`: 오전편 개수
- `morningFlights`: 오전편 상세 목록
- `targetDayFlightCount`: 목표 날짜로 검출된 전체 편 개수
- `detectedAirlines`: 메타/보조근거에서 감지된 항공사
- `evidenceLevel`: 근거 수준
- `notes`: 한계/보조 설명

## Current limitation

현재 가장 큰 한계는 여전합니다.

- 공개 페이지가 **목표 날짜의 실제 편 인스턴스**를 항상 노출하지 않음
- 항공사 사이트는 봇 차단/오류 페이지가 자주 발생함
- 공항 페이지는 일반 fetch만으로는 날짜별 상세 운항편 추출이 제한됨

그래서 이 도구는 지금도 **전용 로직으로서의 기반**은 갖췄지만,
정확도를 더 올리려면 다음이 필요할 수 있습니다.

## Recommended next steps

- 항공사별 예약 페이지 전용 파서 추가
- 브라우저 자동화 가능한 수집기 추가
- 다중 소스 교차검증 강화
- 날짜 파라미터를 실제 검색에 반영하는 쿼리 경로 확보
