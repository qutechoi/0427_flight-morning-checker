# 0427_flight-morning-checker

청주(CJJ) → 제주(CJU) 노선에서 **특정 날짜 오전 12시 이전 출발편이 있는지** 확인하기 위한 전용 Python CLI 도구입니다.

지금 버전은 항공권 사이트를 무작정 cron으로 긁는 대신, 목적에 맞는 로직을 코드로 분리해서:
- 목표 날짜 필터링
- 오전편 필터링
- JSON 결과 정규화
를 수행합니다.

## Why this exists

필요한 건 “최저가”가 아니라:

> **2026-09-24 청주 → 제주 노선에 오전 출발편이 있는가?**

이 질문에 답하는 것입니다.

그래서 이 프로젝트는 가격 추적이 아니라 **오전편 존재 여부 탐지**에 초점을 맞춥니다.

## Current source

현재 구현 소스:
- **KAYAK route page**

이 소스는 공개 HTML 안에 일부 구조화된 `Flight` 메타데이터를 포함하기 때문에, 일반 fetch 기반 자동화가 어느 정도 가능합니다.

## Limitation

아주 중요한 한계가 있습니다.

현재 사용한 KAYAK route URL은:
- 노선 정보는 잘 노출하지만
- 목표 날짜(`2026-09-24`)의 실제 편 인스턴스를 항상 바로 노출하지는 않습니다.

즉 현재 출력은 다음 중 하나입니다:
1. 목표 날짜 실제 편 데이터가 보이면 오전편을 정확히 탐지
2. 목표 날짜 데이터가 안 보이면 `targetDayFlightCount = 0` 으로 반환하고, 잠정 결과라고 표시

그래서 이 도구는 **전용 로직의 뼈대**로는 맞지만,
정확도를 더 끌어올리려면 나중에 추가 소스나 브라우저 자동화가 붙을 수 있습니다.

## Usage

```bash
python3 flight_morning_checker.py
```

기본값:
- from: `CJJ`
- to: `CJU`
- date: `2026-09-24`
- source: `kayak`

### Custom arguments

```bash
python3 flight_morning_checker.py --from CJJ --to CJU --date 2026-09-24 --source kayak
```

## Output example

```json
{
  "routeFrom": "CJJ",
  "routeTo": "CJU",
  "date": "2026-09-24",
  "source": "KAYAK",
  "hasMorningFlight": false,
  "morningFlightCount": 0,
  "morningFlights": [],
  "targetDayFlightCount": 0,
  "notes": [
    "현재 소스가 목표 날짜의 정확한 편 데이터를 노출하지 않아 잠정 결과입니다."
  ],
  "fetchedAt": "2026-04-27T12:00:00Z"
}
```

## Recommended next steps

정확도를 더 올리려면:
- 항공사별 예약 페이지 파서 추가
- 공항/메타서치 소스 추가
- 브라우저 자동화 가능한 환경에서 날짜 지정 검색 구현
- 다중 소스 교차검증

## Cron philosophy

cron은 이 도구를 **실행만** 하도록 두는 게 좋습니다.

핵심 로직은 이 저장소의 코드에 있어야:
- 테스트 가능
- 수정 가능
- 목적 지향적
- 다른 날짜/노선으로 확장 가능
