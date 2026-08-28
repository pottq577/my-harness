---
id: DBA-001
title: NULL을 이해한다는 것: WHERE a != 1 이 NULL을 빠뜨리는 이유
status: stable

topics:
  - null
  - three-valued-logic
  - sql-condition
  - data-modeling

triggers:
  - WHERE status != 1 인데 NULL 행이 빠진다
  - NULL과 빈 문자열을 어떻게 구분하나
  - nullable 컬럼을 허용해도 되나
  - NOT IN에 NULL이 섞이면 왜 결과가 비나
  - COUNT(*)와 COUNT(column)이 다른 이유

code_signals:
  - "IS NULL"
  - "IS NOT NULL"
  - "COALESCE"
  - "IFNULL"
  - "NOT IN"
  - "status != 1"
  - "@Column(nullable = true)"

applies_to:
  - sql-review
  - schema-design
  - domain-modeling

risk_signals:
  - NULL이 비즈니스 상태를 의미함
  - NULL과 빈 문자열을 혼용함
  - nullable 컬럼이 조건 분기를 복잡하게 만듦
  - NOT IN이나 NOT EXISTS에 NULL이 섞임

read_when:
  - 컬럼을 nullable로 둘지 결정해야 할 때
  - WHERE 비교에서 NULL 행이 사라질 때
  - COUNT나 SUM 집계가 예상과 다를 때
  - 도메인 상태를 NULL로 표현하려고 할 때

read_also:
  - DBA-002
  - DBA-003

summary: >
  NULL은 값이 아니라 '알 수 없음'이며 SQL의 삼값 논리에서 UNKNOWN으로
  동작한다. 비교 연산, 집계 함수, NOT IN, 인덱스, UNIQUE 제약에서 NULL이
  어떻게 다뤄지는지와, 모델링에서 nullable 컬럼을 허용할 때의 판단 기준과
  위험을 다룬다.
---
# NULL을 이해한다는 것: WHERE a != 1 이 NULL을 빠뜨리는 이유

`WHERE status != 1`.
이 쿼리는 status가 NULL인 행을 빠뜨린다.
"NULL도 1은 아닌 거 아닌가?"
맞는 말이지만 DB는 그렇게 생각하지 않는다.
NULL은 값이 아니라 "모른다"는 뜻이기 때문이다.

1. NULL은 비교 대상이 아니다. IS NULL을 쓰라.
2. 조건절에서 NULL이 사라지는 구조를 이해하라.
3. NOT IN에 NULL이 섞이면 공집합이 된다.
4. 집계 함수에서 NULL이 무시된다는 사실을 잊지 마라.
5. NULL 허용 여부를 의도적으로 결정하라.

NULL을 모르면 쿼리를 모르는 것이다.

## NULL은 값이 아니다

NULL은 0이 아니다. 빈 문자열도 아니다. FALSE도 아니다.
NULL은 "알 수 없음"이다.
값의 부재, 상태의 미정, 정보의 공백.
배송일이 NULL이면 배송이 안 된 게 아니다. 아직 모른다는 뜻이다.
이 구분이 흐려지는 순간, 쿼리에 구멍이 뚫린다.
NULL을 0으로 취급하는 코드는 언젠가 장애를 만든다.
NULL은 존재하지 않는 값이 아니다. 존재 여부 자체를 모르는 상태다.

## 비교의 함정

```sql
SELECT * FROM orders
WHERE status != 1;
```

이 쿼리는 status가 NULL인 행을 반환하지 않는다.
`NULL != 1`의 결과는 FALSE가 아니다. UNKNOWN이다.
WHERE절은 TRUE인 행만 통과시킨다. UNKNOWN은 통과하지 못한다.
같은 이유로 = NULL도 동작하지 않는다.

```sql
WHERE status = NULL -- 항상 UNKNOWN
WHERE status IS NULL -- 올바른 문법
```

`=`는 두 값을 비교하는 연산자다.
NULL은 값이 아니므로 비교 자체가 성립하지 않는다.

## Three-Valued Logic

SQL은 이진 논리가 아니다.
TRUE, FALSE, 그리고 UNKNOWN. 삼값 논리다.

[AND]
TRUE AND UNKNOWN = UNKNOWN
FALSE AND UNKNOWN = FALSE

[OR]
TRUE OR UNKNOWN = TRUE
FALSE OR UNKNOWN = UNKNOWN

[NOT]
NOT UNKNOWN = UNKNOWN
UNKNOWN은 전파된다.

하나라도 UNKNOWN이 끼면 전체 결과가 흔들린다.

```sql
WHERE status != 1 AND category = 'A'
```

status가 NULL이면 좌변이 UNKNOWN이다. AND의 결과도 UNKNOWN이다.
행은 사라진다.

## NULL과 집계 함수

```sql
SELECT COUNT(*) FROM orders;
SELECT COUNT(status) FROM orders;
```

`COUNT(*)`는 행을 센다. `COUNT(column)`은 값을 센다.
NULL은 값이 아니므로 세지 않는다. SUM과 AVG도 NULL을 무시한다.
값이 1, 2, NULL인 세 행이 있다면 SUM은 3이고, AVG는 1.5다.
NULL을 0으로 치면 AVG는 1이 된다. 전혀 다른 결과다.
의도에 따라 COALESCE로 0을 채울지, NULL 그대로 둘지 판단해야 한다.

## NULL과 인덱스

흔한 오해가 있다.
"NULL이면 인덱스를 못 타지 않나?"
MySQL InnoDB에서는 NULL도 인덱스에 포함된다.
IS NULL 조건도 인덱스를 탈 수 있다.

```sql
ALTER TABLE orders
ADD INDEX idx_deleted (deleted_at);
SELECT * FROM orders
WHERE deleted_at IS NULL;
```

이 쿼리는 인덱스를 사용한다. soft delete 패턴에서 자주 쓰이는 구조다.
다만 NULL 비율이 높으면 옵티마이저가 풀스캔을 택할 수 있다.
카디널리티와 분포를 함께 봐야 한다.

## NULL과 UNIQUE 제약

```sql
CREATE TABLE users (
user_id BIGINT PRIMARY KEY,
email VARCHAR(255) UNIQUE
);
```

email에 UNIQUE가 걸려 있어도 NULL은 여러 건 들어간다.
MySQL에서 NULL은 어떤 값과도 같지 않다. NULL끼리도 같지 않다.
그래서 UNIQUE 위반이 발생하지 않는다.
"email이 없는 사용자"가 여러 명 있어도 DB는 이들을 서로 다른 것으로 본다.
이것이 의도인지 아닌지는 설계자가 판단해야 한다.
DBMS마다 이 동작이 다르다는 점도 기억하라. 같은 스키마가 다른 DB에서 다르게 작동할 수 있다.

## NULL과 JOIN

```sql
SELECT o.order_id, c.coupon_code
FROM orders o
LEFT JOIN coupons c
ON o.coupon_id = c.coupon_id;
```

쿠폰 없이 주문한 행은 coupon_id가 NULL이다.
LEFT JOIN이므로 행은 남지만, 우측 컬럼은 전부 NULL로 채워진다.
INNER JOIN이었다면? NULL끼리는 `=`로 매칭되지 않으므로 해당 행은 사라진다.
OUTER JOIN에서 생기는 NULL과 원래 컬럼에 있던 NULL을 구분하지 못하면 결과 해석을 틀린다.
어떤 NULL이 "원래 없던 값"이고 어떤 NULL이 "JOIN에서 만들어진 빈 자리"인지.
이걸 구분하는 것이 JOIN을 읽는 힘이다.

## COALESCE와 IFNULL

NULL을 다루는 가장 직접적인 방법이다.

```sql
SELECT COALESCE(nickname, username, 'unknown')
FROM users;
```

COALESCE는 왼쪽부터 읽어서 첫 번째 NOT NULL 값을 반환한다.
IFNULL은 MySQL 전용이고 인자가 둘뿐이다.

```sql
SELECT IFNULL(discount, 0) FROM orders;
```

기본값 패턴으로 자주 쓰인다. 하지만 남용하면 안 된다.
NULL을 숨기는 것과 다루는 것은 다르다.
NULL이 왜 생기는지를 먼저 확인하라.
원인을 무시하고 COALESCE로 덮으면, 데이터의 의미가 왜곡된다.

## NOT IN의 함정

실무에서 가장 위험한 패턴이다.

```sql
SELECT * FROM orders
WHERE status NOT IN (
SELECT status FROM cancelled_orders);
```

서브쿼리에 NULL이 하나라도 있으면 전체 결과가 공집합이 된다.
NOT IN (1, 2, NULL)은 마지막 항이 UNKNOWN이므로 전체가 UNKNOWN이다.
대안은 NOT EXISTS다.

```sql
SELECT * FROM orders o
WHERE NOT EXISTS (
SELECT 1 FROM cancelled_orders c
WHERE c.status = o.status);
```

## NULL을 피하는 설계

대부분의 컬럼은 NOT NULL이 맞다.

```sql
CREATE TABLE orders (
order_id BIGINT NOT NULL,
status TINYINT NOT NULL DEFAULT 0,
created_at DATETIME NOT NULL
);
```

상태값에 "미정"이 필요하면 NULL 대신 명시적인 값을 쓰라.
0은 미정, 1은 진행, 2는 완료. 코드로 구분되는 상태가 NULL보다 안전하다.
NOT NULL DEFAULT는 습관이 되어야 한다.
NULL 허용 여부는 반드시 의도적인 결정이어야 한다.
"그냥 비워둬도 되겠지"는 설계가 아니다.

## NULL을 허용하는 설계

그럼에도 NULL이 필요한 순간이 있다.
탈퇴일. 아직 탈퇴하지 않은 회원은?
값이 없는 게 맞다. 0도 아니고 기본값도 아니다.
"아직 일어나지 않은 사건"은 NULL로 표현하는 것이 정직하다.

```sql
withdrawn_at DATETIME NULL
```

soft delete의 deleted_at도 같은 맥락이다.
결제 취소일, 환불 완료일, 해지일. 모두 "발생하지 않은 시점"이다.
이런 컬럼에 NOT NULL DEFAULT '1970-01-01'을 넣으면 의미가 오염된다.
NULL은 무지가 아니라, 정직한 표현이다.

## Oracle의 NULL: 빈 문자열이 NULL이다

DB 간 NULL 차이 중 가장 충격적인 것.
Oracle에서 빈 문자열(`''`)은 NULL이다.

```sql
-- Oracle
SELECT * FROM users
WHERE nickname = ''; -- 결과 없음. '' 자체가 NULL이니까.
```

VARCHAR2에 `''`을 INSERT하면 NULL로 저장된다.
MySQL이나 PostgreSQL에서는 `''`과 NULL이 완전히 다른 값이다.
MySQL에서 Oracle로, Oracle에서 PostgreSQL로 마이그레이션할 때 이걸 모르면 데이터가 깨진다.
`WHERE nickname = ''` 이 한쪽에서는 결과가 나오고 다른 쪽에서는 공집합이다.
같은 SQL인데 DB에 따라 결과가 다르다.

## DB마다 다른 NULL

NULL은 SQL 표준이지만, 세부 동작은 DB마다 다르다.

[정렬]
MySQL은 NULL이 가장 작다. ASC에서 맨 앞.
PostgreSQL, Oracle은 가장 크다. ASC에서 맨 뒤.

[UNIQUE]
MySQL, PostgreSQL은 NULL 여러 건 허용.
SQL Server는 하나만 허용.

[NULL-safe 비교]
MySQL: <=> 연산자.
PostgreSQL: IS DISTINCT FROM.
SQL Server: ANSI_NULLS 설정으로 변경 가능.
DB를 옮기면 NULL 때문에 결과가 달라진다.

## DBA 관점에서의 정리

NULL로 인한 장애를 여러 번 봐왔다. 대부분은 NULL을 값으로 취급한 데서 시작됐다.

1. NULL은 비교 대상이 아니다. IS NULL을 쓰라.
2. 조건절에서 NULL이 사라지는 구조를 이해하라.
3. NOT IN에 NULL이 섞이면 공집합이 된다. 기억하라.
4. 집계 함수에서 NULL이 무시된다는 사실을 잊지 마라.
5. 스키마 설계 시 NULL의 허용 여부를 의도적으로 결정하라.
6. 이 다섯 가지만 알아도 NULL로 인한 사고는 대부분 막을 수 있다.

## 마무리

NULL은 어렵지 않다. 다만 대부분이 정면으로 마주하지 않을 뿐이다.
값이 없는 것을 값처럼 다루는 순간, 쿼리는 조용히 거짓말을 시작한다.
에러도 없이, 경고도 없이, 결과만 틀린다.
NULL을 안다는 것은 "모른다"는 상태를 인정하는 것이다.
데이터베이스가 "모른다"고 말할 때, 우리도 "모른다"고 받아들여야 한다.
NULL을 모르면 쿼리를 모르는 것이다.
