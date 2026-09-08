---
id: DBA-003
title: "DB에서 JSON을 쓴다는 것: 장점, 단점, 가이드라인"
status: stable

topics:
  - json
  - jsonb
  - schema-flexibility
  - denormalization
  - audit-log

triggers:
  - 외부 API 응답을 JSONB로 저장해도 되나
  - 자주 바뀌는 필드를 JSON 컬럼으로 빼도 되나
  - JSON 컬럼에 인덱스를 걸 수 있나
  - PG 원본 응답을 그대로 보관하고 싶다
  - 테이블 대신 JSON으로 스키마를 유연하게 가져가고 싶다

code_signals:
  - "json"
  - "jsonb"
  - "->>"
  - "@>"
  - "CAST(... AS JSON)"
  - "JSON_EXTRACT"
  - "JSON_CONTAINS"
  - "USING GIN"

applies_to:
  - schema-design
  - domain-modeling
  - sql-review
  - query-review

risk_signals:
  - JSONB를 스키마 회피 수단으로만 사용
  - 핵심 비즈니스 값을 JSON 내부에만 저장
  - 인덱스나 제약 조건이 필요한 값을 JSON에만 저장
  - 결제 상태 같은 정합성 판단을 JSON 내부 값에 의존

read_when:
  - 외부 시스템 원본 응답 보존이 필요할 때
  - 자주 바뀌는 속성을 어디에 저장할지 고민할 때
  - JSON 컬럼 도입 전 위험을 확인하고 싶을 때

read_also:
  - DBA-001
  - DBA-002
  - DBA-018
  - DBA-034

summary: >
  JSON 컬럼의 장점인 스키마 유연성, 반정규화 조회 성능, 외부 응답 저장과,
  단점인 무결성 부재, 쿼리 성능, JOIN과 집계의 어려움을 비교한다. 언제
  쓰고 언제 피해야 하는지 가이드라인과 하이브리드 패턴, 인덱싱 전략을
  제시한다.
---
# DB에서 JSON을 쓴다는 것: 장점, 단점, 가이드라인

관계형 데이터베이스는 행과 열로 데이터를 정리한다.
그런데 어느 순간부터 JSON 컬럼을 쓰는 팀이 많아졌다.
스키마를 안 바꿔도 되니까 편하다. 근데 그 편함에는 대가가 있다.
언제 쓰면 좋고, 언제 피해야 하는지.
DBA 관점에서 정리해본다.

## 왜 JSON 컬럼이 등장했나

서비스가 커지면 테이블 구조가 자주 바뀐다.
배달 주문에 "포장 옵션"이 추가되고, 다음 달에는 "친환경 포장 여부"가 붙고, 그다음 달에는 "배달 메모 카테고리"가 생긴다.
매번 `ALTER TABLE`을 치면 대형 테이블은 수 분~수십 분 락이 걸린다.
`pt-online-schema-change`를 써도 운영 부담은 남는다.
"자주 바뀌는 부분만 JSON으로 넣으면 안 되나?"
이 질문에서 시작됐다.

## 장점 1 — 스키마 유연성

가장 큰 장점으론 DDL 없이 필드를 추가할 수 있다.
상품 속성이 카테고리마다 다를 때,

```json
의류: {color, size, material}
식품: {expiry, allergen, storage_temp}
전자기기: {voltage, warranty_months}
```

정규화하면 속성 테이블이 끝없이 늘어난다.
JSON이면 하나의 컬럼에 각자 다른 구조를 담을 수 있다.
`ALTER TABLE` 없이, 배포 없이.

## 장점 2 — 반정규화 조회 성능

API 응답을 조립할 때 여러 테이블을 JOIN하는 대신 미리 조립된 JSON을 한 번에 읽을 수 있다.
주문 상세 조회에서 배달지 주소 + 가게 정보 + 메뉴 옵션을 매번 4~5개 테이블 JOIN하는 것과,
주문 테이블에 snapshot JSON을 박아두고 SELECT 한 방으로 끝내는 것.
읽기 비율이 압도적일 때 이 전략이 효과적이다.

## 장점 3 — 외부 시스템 연동 데이터 저장

외부 API 응답을 그대로 저장해야 할 때.
PG 결과 JSON, 택배사 API 응답, 소셜 로그인 프로필 데이터.
이런 건 우리가 스키마를 통제할 수 없다.
외부에서 필드가 추가되거나 바뀌면 매번 ALTER TABLE을 칠 수도 없다.
원본을 JSON으로 보관하고, 자주 쓰는 필드만 별도 컬럼으로 꺼내 쓰는 하이브리드 패턴이 실용적이다.

## 장점 4 — 이벤트/로그성 데이터

감사 로그, 사용자 활동 로그, 설정 변경 이력 같은 데이터.
이벤트 종류마다 payload 구조가 다르다.

```json
로그인: {ip, device, browser}
설정변경: {key, old_value, new_value}
결제: {amount, method, pg_tid}
```

이걸 각각 테이블로 만들면 테이블이 수십 개가 된다.
JSON payload 컬럼 하나면 충분하다.

## 장점 5 — 프로토타이핑 속도

신규 기능을 빠르게 검증할 때.
아직 스키마가 확정되지 않은 초기 단계에서 JSON으로 먼저 만들고, 패턴이 안정되면 정규 컬럼으로 승격시킨다.
"일단 JSON으로 시작해서 나중에 컬럼으로 빼자"
이 전략 자체는 나쁘지 않다.
다만 "나중에"가 안 오는 게 문제다.

## 단점 1 — 데이터 무결성 부재

가장 치명적인 단점.
정규 컬럼은 NOT NULL, UNIQUE, FK, CHECK 제약조건으로 잘못된 데이터를 막는다.
JSON에는 이게 없다.
price가 문자열로 들어와도, 필수 필드가 빠져도, DB는 아무 말 없이 저장한다.
MySQL의 JSON 스키마 검증은 CHECK 제약조건으로 가능하지만 성능 비용이 있고, 대부분의 팀이 안 쓴다.
결과적으로 데이터 품질은 애플리케이션 코드에 100% 의존하게 된다.

## 단점 2 — 쿼리 성능

JSON 내부 키를 조건으로 검색하면 느리다.

```sql
-- MySQL
SELECT * FROM orders
WHERE JSON_EXTRACT(options, '$.delivery_type') = 'express';
-- PostgreSQL
SELECT * FROM orders
WHERE options->>'delivery_type' = 'express';
```

정규 컬럼이면 B-Tree 인덱스를 타지만 JSON 필드는 기본적으로 풀스캔이다.
MySQL은 가상 컬럼 + 인덱스로 우회 가능하다. PostgreSQL은 GIN 인덱스를 걸 수 있다.
하지만 이걸 매번 챙기는 팀은 드물다.
"JSON에 넣었는데 왜 느려요?" DBA가 가장 많이 듣는 질문 중 하나다.

## 단점 3 — JOIN과 집계의 어려움

JSON 안의 값으로 다른 테이블과 JOIN하거나 GROUP BY, SUM 같은 집계를 하려면 매번 JSON 함수로 값을 꺼내야 한다.

```sql
SELECT JSON_EXTRACT(payload, '$.category') AS cat,
COUNT(*)
FROM events
GROUP BY cat;
```

쿼리가 복잡해지고, 옵티마이저가 최적화하기 어렵다.
데이터 분석 팀이 "이 데이터 좀 뽑아주세요" 할 때 JSON 컬럼이면 뽑는 사람이 괴롭다.

## 단점 4 — 스키마 파악 불가

테이블 DDL을 보면 어떤 데이터가 들어있는지 바로 안다.
JSON은 안 보인다. DESC 테이블 쳐도 "json" 타입만 보인다.
실제로 어떤 키가 들어있는지, 어떤 구조인지 알려면 데이터를 직접 까봐야 한다.
시간이 지나면 같은 컬럼인데 들어있는 구조가 시기별로 달라지는 일도 생긴다.

```json
v1: {address: "서울시 강남구"}
v2: {address: {city: "서울", district: "강남구"}}
```

마이그레이션 없이 구조가 바뀌니까 읽는 쪽 코드가 양쪽 다 처리해야 한다.

## 단점 5 — 저장 공간과 복제 부하

JSON은 키 이름을 매 행마다 반복 저장한다.
100만 행이 있으면 "delivery_type"이라는 문자열이 100만 번 저장된다.
정규 컬럼이면 컬럼 이름은 메타데이터에 한 번만 저장된다.
row 기반 복제에서는 JSON 컬럼 전체가 before/after 이미지로 들어간다.
JSON 안의 값 하나만 바꿔도 전체 JSON이 binlog에 기록된다.
대형 JSON이면 복제 지연의 원인이 된다.

## 단점 6 — 부분 업데이트의 비용

JSON 안의 값 하나를 바꾸려면 MySQL은 JSON_SET으로 부분 업데이트가 가능하긴 하다.
하지만 내부적으로는 전체 JSON을 다시 쓰는 경우가 많다.
PostgreSQL jsonb도 마찬가지.
불변(immutable) 구조라 값 하나 바꿔도 전체를 새로 쓴다.
정규 컬럼이면 해당 필드만 in-place 업데이트되는 것과 근본적으로 다르다.
업데이트가 잦은 필드를 JSON에 넣으면 I/O가 뻥튀기된다.

## 가이드라인 1 — JSON을 써도 되는 경우

다음 조건을 대부분 만족할 때 쓴다:

1. 읽기 위주다.
2. 자주 업데이트하지 않는다.
3. WHERE 조건으로 거의 검색하지 않는다.
4. JOIN이나 집계에 사용하지 않는다.
5. 구조가 가변적이거나 사전에 확정하기 어렵다.

예시:
상품 속성 (카테고리별 다른 스펙)
외부 API 원본 응답 보관
UI 설정/사용자 환경설정
이벤트 payload

## 가이드라인 2 — JSON을 쓰면 안 되는 경우

이 중 하나라도 해당되면 정규 컬럼으로 빼라:

1. WHERE 절에서 자주 필터링한다.
2. 다른 테이블과 JOIN 키로 쓴다.
3. NOT NULL이 반드시 보장돼야 한다.
4. UNIQUE 제약이 필요하다.
5. 집계(SUM, COUNT, AVG)의 대상이다.
6. 값이 자주 업데이트된다.
7. 핵심 비즈니스 식별자

(주문번호, 사용자ID, 결제금액)를 JSON에 넣는 건 사고를 예약하는 것이다.

## 가이드라인 3 — 하이브리드 패턴

가장 실용적인 접근.
자주 조회하는 필드는 정규 컬럼으로, 나머지는 JSON으로.

```sql
CREATE TABLE products (
id BIGINT PRIMARY KEY,
name VARCHAR(200) NOT NULL,
price DECIMAL(10,2) NOT NULL,
category VARCHAR(50) NOT NULL,
-- 핵심 필드는 정규 컬럼
attributes JSON
-- 카테고리별 가변 속성은 JSON
);
```

검색은 정규 컬럼으로, 상세 조회 시에만 JSON을 읽는다.
두 세계의 장점을 모두 가져가는 방식이다.

## 가이드라인 4 — JSON에도 규칙을 정하라

스키마가 없다고 무법지대로 두면 안 된다.
팀 차원에서 지켜야 할 것들:

1. JSON 스키마 문서를 별도로 관리한다.
2. 키 네이밍 컨벤션을 정한다 (snake_case 등).
3. 버전 필드를 넣는다 (schema_version: 2).
4. 최대 깊이를 제한한다 (2~3단계).
5. 최대 크기를 제한한다.

```json
{
  "_schema_version": 2,
  "delivery_type": "express",
  "packaging": {
    "eco_friendly": true,
    "material": "paper"
  }
}
```

구조가 바뀔 때 버전 필드가 있으면 읽는 쪽에서 분기 처리가 가능하다.

## 가이드라인 5 — 인덱싱 전략

JSON을 WHERE에 쓸 수밖에 없다면 반드시 인덱스를 챙긴다.
MySQL은 가상 컬럼 + 인덱스로 우회한다.
PostgreSQL은 GIN 인덱스를 건다.

```sql
-- MySQL: 가상 컬럼
ALTER TABLE orders
ADD dt VARCHAR(20) GENERATED ALWAYS AS
(JSON_UNQUOTE(JSON_EXTRACT(
options,'$.delivery_type'))) VIRTUAL,
ADD INDEX idx_dt (dt);
-- PostgreSQL: GIN
CREATE INDEX idx_opts
ON orders USING GIN (options);
```

인덱스 없이 JSON 검색을 허용하면 장애로 이어진다.

## 가이드라인 6 — 크기 제한

JSON 컬럼에 크기 제한을 걸어라.
MySQL JSON 타입은 이론상 4GB까지 담긴다.
하지만 1MB짜리 JSON이 100만 행이면 그것만 1TB다.
업데이트할 때마다 전체를 다시 쓰고, binlog에도 전체가 기록된다.
실무 권장:

- 일반 속성 데이터: 10KB 이하
- 이벤트 payload: 64KB 이하
- 원본 보관용: 별도 테이블 분리, 1MB 상한

```sql
-- MySQL CHECK 제약
ALTER TABLE products
ADD CONSTRAINT chk_attr_size
CHECK (JSON_LENGTH(attributes) < 100
AND LENGTH(attributes) < 10240);
```

## 가이드라인 7 — 마이그레이션 계획

"나중에 컬럼으로 빼자"를 실제로 실행하는 시점을 정하라.
JSON 필드가 다음 조건을 충족하면 정규 컬럼 승격 시점이다:

1. 그 키로 검색하는 쿼리가 생겼다.
2. 그 키에 NOT NULL이 필요해졌다.
3. 그 키로 리포팅/집계를 한다.
4. 그 키의 값을 자주 업데이트한다.

승격 절차:

1. 정규 컬럼 추가 (NULL 허용)
2. 백필: JSON에서 값을 꺼내 정규 컬럼에 채움
3. 애플리케이션에서 정규 컬럼으로 읽기/쓰기 전환
4. JSON에서 해당 키 제거 (선택)

한 번에 다 바꾸지 말고 읽기 전환 → 쓰기 전환 → 정리 순서로 단계적으로 한다.

## DBA 관점에서의 정리

JSON 컬럼은 도구다.
좋은 도구도 잘못 쓰면 사고가 난다.
편한 것들:

- 스키마 변경 없이 필드 추가
- 가변 구조 데이터 저장
- 프로토타이핑 속도

불편한 것들:

- 데이터 무결성을 DB가 보장 못함
- 인덱싱을 별도로 챙겨야 함
- 복제 부하 증가
- 스키마 파악 불가

핵심은 한 가지다.
"이 데이터가 비즈니스의 핵심인가, 아니면 부가 정보인가?"
핵심이면 정규 컬럼, 부가 정보면 JSON.
이 판단 하나만 맞추면 대부분의 문제는 피할 수 있다.

## 마무리

관계형 데이터베이스에 JSON을 넣는다는 건 정규화의 엄격함 위에 유연함을 한 겹 얹는 것이다.
Document DB로 가면 유연함은 극대화되지만 JOIN과 트랜잭션을 포기해야 한다.
RDBMS의 JSON 컬럼은 그 중간 지점이다.
구조화된 세계와 비구조화된 세계를 한 테이블 안에서 공존시키는 것.
다만 그 공존에는 규칙이 필요하다.
규칙 없는 JSON 컬럼은 시한폭탄이다.
규칙 있는 JSON 컬럼은 강력한 도구다.
차이는 설계 시점의 판단에 있다.
