---
id: DBA-050
title: "JSON을 잘 쓴다는 것: 구조, 네이밍, 흔한 실수"
status: stable

topics:
  - json
  - api-contract
  - naming
  - schema
  - serialization

triggers:
  - 좋은 JSON 구조를 어떻게 설계하나
  - API 필드 이름과 null을 어떻게 다루나
  - JSON 응답이 커지고 중첩이 복잡하다

code_signals:
  - "application/json"
  - "snake_case"
  - "camelCase"
  - "null"
  - "items"

applies_to:
  - application-architecture
  - domain-modeling

risk_signals:
  - 필드 이름을 축약해 의미가 불명확
  - 깊은 중첩과 거대한 배열을 한 응답에 포함

read_when:
  - API나 이벤트의 JSON 계약을 설계할 때
  - JSON 구조와 DB JSON 저장을 구분할 때

read_also:
  - DBA-003
  - DBA-017
  - DBA-028

source_sections:
  - "raw/6.md:423-784"

summary: >
  JSON 데이터 계약의 네이밍, 타입, null, 중첩, 배열 설계 원칙을
  다룬다. DB의 JSON 컬럼 선택을 다루는 DBA-003과 목적을 분리한다.
---
# JSON을 잘 쓴다는 것: 구조, 네이밍, 흔한 실수

JSON은 어디에나 있다. API 응답, 설정 파일, 로그, 메시지 큐, DB 컬럼.
누구나 읽을 수 있고, 누구나 쓸 수 있다.
그런데 "잘" 쓰는 사람은 생각보다 적다.
같은 데이터를 담아도 어떤 JSON은 읽기 좋고, 파싱하기 쉽고, 확장이 된다.
어떤 JSON은 읽을 때마다 코드가 꼬이고, 6개월 후에 본인도 못 알아본다.
잘 쓴 JSON은 스키마 없이도 의도가 보인다.
못 쓴 JSON은 스키마가 있어도 혼란스럽다.

## JSON은 왜 이겼나

2000년대 초반, 표준은 XML이었다.

```xml
<order>
<id>12345</id>
<items>
<item><name>치킨</name></item>
</items>
</order>
```

태그가 두 번씩 나오고, 파싱에 라이브러리가 필요하다.
JSON은 단순했다.

```json
{ "id": 12345, "items": [{ "name": "치킨" }] }
```

사람이 읽을 수 있고, 대부분의 언어에서 네이티브 객체로 바로 변환된다.
단순함이 이긴 것이다.
그리고 그 단순함 때문에 규칙 없이 쓰게 되는 것이기도 하다.

## 키 네이밍: snake_case로 통일하라

JSON 키 네이밍은 종교 전쟁이다.

```json
{"userName": "bear"}
{"user_name": "bear"}
{"UserName": "bear"}
```

셋 다 유효하다. 하지만 한 시스템 안에서 섞이면 재앙이다.
추천은 snake_case다.
DB 컬럼이 snake_case고, AWS API, Stripe API가 snake_case다.
camelCase 진영도 강력하다.
JavaScript 생태계, Google Cloud API.
어떤 걸 고르든 상관없다. 한 시스템 안에서 절대 섞지 않는다.
`user_name`과 `orderDate`가 공존하는 순간 파싱하는 사람은 매번 확인해야 한다.
그게 100개 필드면 버그가 된다.

## 타입을 지켜라: 숫자는 숫자로, 불린은 불린으로

문제는 전부 string으로 때려넣는 습관이다.

```json
{ "price": "15000", "is_paid": "true" }
```

`"15000" + "2"`는 `"150002"`다.
`"false"`도 truthy다.
`"null"`은 null이 아니라 4글자짜리 문자열이다.

```json
{ "price": 15000, "is_paid": true }
```

숫자는 따옴표 없이. 불린은 true/false. 없는 값은 null.
당연한 것 같지만 외부 시스템에서 받은 JSON을 보면 절반 이상이 이 규칙을 어긴다.

## 날짜는 ISO 8601, 예외 없다

날짜 포맷은 합의가 끝난 주제다.
ISO 8601. 이것만 쓰면 된다.

```json
{ "created_at": "2026-07-14T15:30:00+09:00" }
```

현실에서 보게 되는 것들.

```json
{"created_at": "20260714"}
{"expired_at": "2026/07/21 00:00:00"}
{"updated_at": 1752476400}
```

셋 다 날짜인데 셋 다 포맷이 다르다.
파싱하는 쪽에서 파서를 세 개 만들어야 한다.
Unix timestamp는 비교가 빠르지만 사람이 읽을 수 없다.
내부 통신이면 timestamp도 괜찮다.
사람이 읽을 가능성이 있으면 ISO 8601.
타임존은 반드시 명시한다.
타임존 없는 날짜는 시한폭탄이다.

## null을 두려워하지 마라, 다만 규칙을 정해라

값이 없을 때, 선택지가 세 가지다.

```json
{"middle_name": null}
{"middle_name": ""}
{}
```

null, 빈 문자열, 키 생략.
셋 다 "없다"를 뜻하지만 읽는 쪽 코드가 다르다.
정답은 하나만 골라서 일관되게 쓰는 것이다.
값이 없다 → null.
스키마에 명시된 키는 항상 포함, null 허용.
빈 문자열은 "빈 문자열"이라는 값이다. "없음"과 다르다.
`""`과 `null`을 구분 못 하는 시스템은 반드시 버그를 만든다.

## 배열 안에는 같은 타입만

```json
{ "data": [1, "two", true, null] }
```

유효한 JSON이다. 하지만 파싱하는 사람은 미친다.
배열은 같은 타입을 나열하기 위한 구조다.
타입이 섞이면 반복 처리가 불가능하다.

```json
{ "tags": ["배달", "포장", "예약"] }
```

문자열이면 전부 문자열. 숫자면 전부 숫자. 객체면 같은 구조의 객체.
null과 빈 배열은 다르다.
`"items": null`은 "정보가 없다." `"items": []`은 "0개다."
구분해서 써야 한다.

## 깊이를 제한하라: 최대 3단계

JSON은 얼마든지 깊어질 수 있다.

```json
{ "order": { "customer": { "address": { "city": { "detail": "3층" } } } } }
```

이걸 안전하게 접근하려면 null 체크가 5번이다.
실용적인 상한은 3단계다.

```json
{
  "order_id": 12345,
  "address": { "city": "서울", "detail": "강남구 테헤란로" }
}
```

깊이가 3을 넘어가면 구조를 분해하거나 ID 참조로 바꾸는 게 맞다.
깊은 JSON은 읽기 어렵고, 파싱하기 어렵고, 변경하기 어렵다.
셋 다 어려우면 설계를 의심해야 한다.

## 열거형은 문자열 상수로

```json
{"status": 1}
{"status": "DELIVERED"}
```

숫자로 된 상태 코드는 매번 매핑 표를 찾아야 한다.
1이 뭔지, 99는 뭔지.

```json
{ "status": "DELIVERED", "payment_method": "CARD" }
```

대문자 상수 문자열. 코드를 안 봐도 의미를 안다.
로그에 찍혀도 바로 읽힌다.
DB에 정수로 저장하더라도 JSON에서는 문자열로 변환하라.
DB는 저장 효율, JSON은 가독성.
둘의 최적화 방향이 다르다.

## 빈 객체와 기본값

```json
{ "name": "bear", "preferences": {} }
```

`preferences`가 빈 객체다.
"설정이 없다"는 뜻인가, "기본값을 쓴다"는 뜻인가.
빈 객체 `{}`는 null과 다르고, 키 생략과도 다르다.
하지만 의미가 모호하다.
설정 안 함 → null.
기본값 → 명시적으로 채운다.

```json
{ "preferences": { "theme": "light", "lang": "ko" } }
```

읽는 쪽에서 "없으면 기본값" 로직을 짜는 것보다 보내는 쪽에서 기본값을 채워 보내는 게 낫다.
빈 객체는 가능하면 피한다.

## 응답 봉투 패턴: data, error, meta

```json
[
  { "id": 1, "name": "치킨" },
  { "id": 2, "name": "피자" }
]
```

배열을 최상위에 두면 메타데이터를 넣을 곳이 없다.
봉투(envelope) 패턴을 쓴다.

```json
{
  "data": [{ "id": 1 }, { "id": 2 }],
  "meta": { "total": 128, "page": 1 }
}
```

에러 시.

```json
{ "data": null, "error": { "code": "NOT_FOUND" } }
```

최상위는 항상 객체. `data`에 페이로드, `error`에 에러, `meta`에 부가 정보.
구조가 일정하면 공통 파서 하나로 모든 API를 처리할 수 있다.

## 흔한 실수 1: 키에 데이터를 넣는다

```json
{ "2026-07-14": { "orders": 150 }, "2026-07-13": { "orders": 132 } }
```

날짜가 키다.
정렬은 보장되지 않고, 타입 정의가 불가능하다.

```json
{
  "daily_stats": [
    { "date": "2026-07-14", "orders": 150 },
    { "date": "2026-07-13", "orders": 132 }
  ]
}
```

데이터를 값으로 내리면 순회가 되고, 정렬이 되고, 필터링이 된다.
키는 구조를 정의하는 것이지 데이터를 담는 것이 아니다.
키가 동적으로 바뀐다면 설계가 잘못된 것이다.

## 흔한 실수 2: 하나의 필드에 여러 의미

```json
{"result": "SUCCESS"}
{"result": "주문번호: 12345"}
```

성공이면 주문번호, 실패면 에러 메시지.
같은 필드가 상황에 따라 다른 의미를 갖는다.

```json
{"success": true, "order_id": 12345}
{"success": false, "error_message": "재고 부족"}
```

한 필드에 한 의미.
필드 이름만 보고 뭐가 들어있는지 알 수 있어야 한다.
`result`인데 타입이 매번 다르면 그건 설계가 아니라 주머니에 아무거나 넣은 것이다.

## 흔한 실수 3: 불필요한 래핑

```json
{ "response": { "data": { "result": { "user": { "name": "bear" } } } } }
```

다섯 단계를 거쳐야 이름 하나를 꺼낸다.
`response`, `data`, `result`는 아무 정보도 없다.

```json
{ "user": { "name": "bear" } }
```

한 단계 더 감쌀 때마다 인지 비용이 올라가고, 접근 코드가 길어지고, null 체크가 하나 더 필요해진다.
래핑은 의미가 있을 때만 한다. 의미 없는 래핑은 벗겨라.

## 흔한 실수 4: 약어와 모호한 키 이름

```json
{ "crt_dt": "2026-07-14", "tp": "DLV", "st": 1, "amt": 15000 }
```

DB 컬럼 네이밍을 그대로 가져온 패턴이다.
VARCHAR(30) 시절의 습관이 JSON까지 따라왔다.
JSON 키에는 길이 제한이 없다.
네트워크 비용이 걱정이면 gzip이 해결한다.

```json
{ "created_at": "2026-07-14", "type": "DELIVERY", "amount": 15000 }
```

6개월 후에 `tp`가 type인지 transport인지 모른다.
`st`가 status인지 state인지 stock인지 모른다.
키 이름을 아끼면 읽는 사람의 시간을 쓰게 된다.

## JSON Schema: 구조에 계약을 걸어라

JSON에는 스키마가 없다.
그래서 자유롭고, 그래서 위험하다.
JSON Schema는 그 위험에 계약을 거는 도구다.

```json
{
  "required": ["order_id", "status"],
  "properties": {
    "order_id": { "type": "integer" },
    "status": { "enum": ["PENDING", "DELIVERED"] }
  }
}
```

필수 필드, 타입, 허용 값. DB의 NOT NULL, CHECK 제약조건과 같은 역할이다.
프로듀서가 스키마를 검증하고 보내면 컨슈머가 방어 코드를 줄일 수 있다.
계약이 명확할수록 양쪽 코드가 깨끗해진다.

## 큰 JSON을 다루는 법

1MB를 넘기면 메모리가 문제다. 10MB를 넘기면 파싱 시간이 문제다.
대부분의 파서는 전체를 메모리에 올린다.
대안은 스트리밍 파서다. Python의 `ijson`, Java의 Jackson Streaming.
그보다 나은 건 크게 만들지 않는 것이다.
데이터가 크면 JSON Lines(JSONL)를 쓴다.

```jsonl
{"id": 1, "name": "치킨", "price": 18000}
{"id": 2, "name": "피자", "price": 22000}
```

줄 단위로 읽으니 스트리밍, 병렬 처리가 된다.
BigQuery, Athena도 JSONL을 지원한다.

## DBA가 보는 JSON

DB에 들어오는 JSON의 품질은 애플리케이션에서 결정된다.
키가 일관되지 않으면 쿼리 조건이 안 먹고, 타입이 뒤섞이면 인덱스가 무의미해진다.

```sql
SELECT JSON_EXTRACT(payload, '$.order.status')
FROM events
WHERE JSON_EXTRACT(payload, '$.order.status') = 'DELIVERED';
```

어떤 행은 `order.status`, 어떤 행은 `order.st`, 어떤 행은 `orderStatus`이면 이 쿼리는 1/3만 건진다.
JSON을 잘 쓰는 건 프런트엔드만의 일이 아니다.
결국 그 데이터는 DB에 쌓이고, DBA가 꺼내야 한다.

## 마무리

JSON을 잘 쓴다는 건 대단한 기술을 익히는 게 아니다.
키를 일관되게 짓고, 타입을 정직하게 쓰고, 깊이를 얕게 유지하고, 배열에는 같은 것만 넣고, 날짜는 표준을 따르고, 의미 없는 래핑을 하지 않는 것.
전부 "하지 않는 것"에 가깝다.
JSON의 매력은 단순함이다.
단순한 포맷에 복잡한 구조를 쑤셔넣으면 단순함이 사라지고 복잡함만 남는다.
좋은 JSON은 열었을 때 설명이 필요 없다.
키 이름이 문서이고, 구조가 스키마이고, 값의 타입이 계약이다.
그 정도면 충분하다.
