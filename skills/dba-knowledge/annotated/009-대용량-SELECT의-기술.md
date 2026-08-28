---
id: DBA-009
title: 대용량 SELECT의 기술: 1억 건에서 원하는 데이터를 꺼내는 법
status: stable

topics:
  - large-query
  - pagination
  - cursor-pagination
  - keyset
  - covering-index
  - streaming

triggers:
  - 대용량 조회를 최적화하고 싶다
  - OFFSET 페이지네이션을 없애는 법
  - keyset 페이지네이션을 쓰는 법
  - 커버링 인덱스로 대용량 쿼리를 줄이는 법
  - Read Replica 라우팅 기준

code_signals:
  - "LIMIT"
  - "OFFSET"
  - "ORDER BY"
  - "WHERE id >"
  - "Using index"
  - "FETCH FIRST"

applies_to:
  - query-review
  - performance-tuning
  - indexing

risk_signals:
  - OFFSET 기반 무한 페이지네이션
  - SELECT * 남발
  - buffer pool 오염을 일으키는 대용량 스캔
  - 스트리밍 없이 전체 결과를 메모리에 적재

read_when:
  - 천만 건 이상 테이블 조회를 설계할 때
  - 페이지네이션이 점점 느려질 때
  - 대용량 추출이나 배치 조회를 만들 때

read_also:
  - DBA-006
  - DBA-010
  - DBA-011

summary: >
  대용량 SELECT가 버퍼 풀 오염과 undo 유지 같은 부하를 만드는 이유를
  설명하고, OFFSET 페이지네이션의 함정, 커서와 키셋 페이지네이션, 커버링
  인덱스, Read Replica 라우팅, 파티셔닝, 스트리밍 조회를 다룬다.
---
# 대용량 SELECT의 기술: 1억 건에서 원하는 데이터를 꺼내는 법

"조회 쿼리인데 왜 이렇게 느려요?"
서비스 초기에는 나오지 않던 질문이다.
테이블이 100만 행일 때는 어떤 쿼리를 날려도 빨랐다.
1천만을 넘기면서 느려지기 시작하고, 1억을 넘기면 단순한 SELECT도 무기가 된다.
읽기는 쓰기보다 안전하다고 믿지만, 대용량 SELECT는 DB를 죽일 수 있다.

## 왜 대용량 조회가 어려운가

SELECT는 락을 안 잡는다고 생각하지만 MVCC 스냅샷을 유지하는 동안 undo log를 정리하지 못한다.
수백만 행을 읽으면 그만큼의 메모리를 소비하고, 네트워크로 전송하고, buffer pool을 오염시킨다.
자주 쓰이는 핫 데이터가 밀려나고 한 번 쓸 콜드 데이터가 버퍼를 채운다. 이걸 buffer pool pollution이라 부른다.
대용량 SELECT는 자기만 느린 게 아니라 다른 쿼리까지 느리게 만든다.

## OFFSET 페이지네이션의 함정

가장 흔한 페이지네이션이다.

```sql
SELECT * FROM orders
ORDER BY id
LIMIT 20 OFFSET 1000000;
```

이 쿼리는 100만 행을 읽고 99만 9,980행을 버린다.
20행을 보여주기 위해 100만 행을 스캔하는 것이다.
페이지가 뒤로 갈수록 읽어야 하는 행이 선형으로 늘어난다.
1페이지는 0.001초, 50000페이지는 3초.
OFFSET은 건너뛰는 게 아니라 읽고 버리는 것이다.

## 커서 기반 페이지네이션

OFFSET의 대안이다.
마지막으로 본 행의 키를 기준으로 다음 페이지를 가져온다.

```sql
SELECT * FROM orders
WHERE id > 1000000
ORDER BY id
LIMIT 20;
```

id에 인덱스가 있으면 1000000번째 행으로 바로 점프한다.
앞의 100만 행을 읽지 않는다.
1페이지든 50000페이지든 실행 시간이 일정하다.
단점은 "3페이지로 바로 이동"이 안 된다는 것.
하지만 무한 스크롤, API 페이지네이션에는 이 방식이 압도적으로 유리하다.

## 복합 키 커서 페이지네이션

시간 순서로 정렬된 데이터는 id만으로 커서를 만들 수 없다.

```sql
SELECT * FROM events
WHERE (created_at, id) > ('2026-07-01', 99999)
ORDER BY created_at, id
LIMIT 100;
```

created_at이 같은 행이 여러 개일 때 id로 순서를 보장한다. 이걸 keyset pagination이라 부른다.
인덱스는 (created_at, id)로 잡는다.
정렬 순서와 인덱스 순서가 일치해야 filesort 없이 인덱스만으로 처리된다.
WHERE 절의 튜플 비교가 핵심이다. MySQL 8.0, PostgreSQL 모두 지원한다.

## 커버링 인덱스

쿼리가 필요로 하는 모든 컬럼이 인덱스에 포함돼 있으면 테이블 본체를 읽지 않는다.

```sql
-- 인덱스: (status, created_at, amount)
SELECT status, created_at, amount
FROM orders
WHERE status = 'done'
AND created_at > '2026-07-01';
```

EXPLAIN에 "Using index"가 뜨면 성공이다. 테이블 랜덤 I/O가 사라진다.
대용량 조회에서 가장 효과적인 최적화 중 하나다.
인덱스가 커지는 대신 조회가 극적으로 빨라진다.

## `SELECT *`는 비싸다

필요한 컬럼이 3개인데 테이블에 50개 컬럼이 있다.
`SELECT *`는 47개의 쓸모없는 컬럼을 함께 읽는다.
행 하나가 4KB면 100만 행은 4GB다.
필요한 3개 컬럼만 읽으면 200MB로 줄 수 있다.

[buffer pool 관점]
넓은 행은 버퍼 페이지를 많이 차지한다.
좁은 행은 같은 페이지에 더 많이 들어간다.
캐시 효율이 달라진다.

[네트워크 관점]
DB와 애플리케이션 사이 전송량이 20배 차이 날 수 있다.
`SELECT *`는 편하지만 대가가 크다.

## Read Replica 라우팅

무거운 조회를 Writer에서 돌리면 쓰기 트래픽에 영향을 준다.
Reader로 보내는 것이 원칙이다.

```text
Writer: INSERT, UPDATE, DELETE
Reader: SELECT (특히 대용량)
```

하지만 복제 지연(replication lag)이 있다.
Aurora는 보통 20ms 이내지만 부하가 높으면 수 초까지 벌어진다.

[주의할 쿼리]
방금 INSERT한 데이터를 바로 SELECT하는 패턴.
Writer에 쓰고 Reader에서 읽으면 아직 복제가 안 됐을 수 있다.
이런 read-after-write는 Writer에서 읽거나 복제 지연을 확인한 뒤 읽어야 한다.

## 파티셔닝으로 스캔 범위 줄이기

1억 행 테이블에서 최근 한 달 데이터만 조회한다면 나머지 11개월은 볼 필요가 없다.

```sql
CREATE TABLE logs (
id BIGINT,
created_at DATE,
message TEXT
) PARTITION BY RANGE (created_at);
```

`WHERE created_at >= '2026-07-01'`이면 7월 파티션만 스캔한다. 파티션 프루닝이다.
파티션 키가 WHERE 절에 없으면 모든 파티션을 뒤지므로 오히려 느려진다.
대용량 SELECT와 파티셔닝은 쿼리 패턴이 맞아떨어질 때만 궁합이 좋다.

## 비정규화와 사전 집계

주문 1억 행에서 매장별 월매출을 구한다고 하자.

```sql
SELECT store_id, SUM(amount) FROM orders
WHERE created_at BETWEEN '2026-06-01' AND '2026-07-01'
GROUP BY store_id;
```

매번 수천만 행을 집계하면 DB가 못 버틴다.
사전 집계 테이블을 만든다.

```sql
SELECT store_id, SUM(amount)
FROM daily_store_sales
WHERE sale_date BETWEEN '2026-06-01' AND '2026-07-01'
GROUP BY store_id;
```

1억 행 스캔이 3만 행 스캔으로 바뀐다.
실시간성을 약간 포기하고 속도를 얻는다.

## 스트리밍 조회

100만 행을 SELECT하면 애플리케이션은 메모리에 100만 행을 올릴까?
기본 JDBC는 그렇다. 전체 결과를 메모리에 올린 뒤 반환한다.
서버 사이드 커서를 쓰면 다르다.

```java
statement.setFetchSize(1000);
```

1000행씩 가져와서 처리한다.
메모리는 1000행분만 쓴다.

[MySQL 주의점]
MySQL JDBC는 fetchSize=Integer.MIN_VALUE로 설정해야 스트리밍 모드가 된다.
일반 숫자로는 동작하지 않는다.
대용량 데이터를 처리할 때 OOM의 원인은 쿼리가 아니라 결과를 한꺼번에 받는 클라이언트다.

## 대량 추출 패턴

1억 행을 파일로 내보내야 한다면 애플리케이션을 거치지 않는다.

```sql
-- MySQL
SELECT * INTO OUTFILE '/tmp/orders.csv'
FIELDS TERMINATED BY ','
FROM orders WHERE created_at > '2026-01-01';
-- PostgreSQL
COPY (SELECT * FROM orders
WHERE created_at > '2026-01-01')
TO '/tmp/orders.csv' WITH CSV;
```

DB가 직접 파일을 쓴다. 네트워크 전송도 행 변환 오버헤드도 없다.
애플리케이션에서 row-by-row로 처리하면 10~100배 느리다.
대량 추출은 DB 네이티브 도구가 답이다.

## 캐싱 전략

같은 쿼리가 초당 1000번 실행된다면 DB에 보내지 말고 캐시에서 꺼낸다.

```text
요청 → Redis 확인 → 있으면 반환
→ 없으면 DB 조회 → Redis 저장
```

[캐시 무효화]
데이터가 변경되면 캐시도 갱신해야 한다.
이게 가장 어려운 부분이다.
TTL 기반: 일정 시간 후 자동 만료.
이벤트 기반: 데이터 변경 시 캐시 삭제.
완벽한 정합성이 필요하면 캐시를 쓰지 않는다. "약간의 지연은 괜찮다"가 전제여야 한다.
핫 쿼리를 캐시로 빼면 DB의 대용량 조회 부담이 극적으로 줄어든다.

## 분석 DB로 넘어가야 할 때

"전체 사용자의 월별 구매 패턴을 뽑아주세요."
이런 쿼리를 운영 DB에서 돌리면 서비스가 멈출 수 있다.
OLTP DB는 행 단위 트랜잭션에 최적화돼 있다. 컬럼 단위 집계는 구조적으로 불리하다.

[언제 분석 DB로 가는가]
집계 대상이 수천만 행 이상.
쿼리에 GROUP BY, 윈도우 함수가 복잡하게 걸림.
실시간이 아니라 일/주/월 단위 분석.
Athena, BigQuery, ClickHouse 같은 컬럼 스토어 엔진은 같은 쿼리를 10~100배 빠르게 처리한다.
운영 DB와 분석 DB의 역할 분리. 이것이 대규모 서비스의 기본 구조다.

## DBA 관점에서의 정리

1000개 넘는 클러스터를 운영하면서 대용량 조회 문제를 수없이 봤다.
패턴은 대부분 같다.

[가장 흔한 실수]
`SELECT *`에 OFFSET 페이지네이션.
이 조합만 고쳐도 절반은 해결된다.

[가장 효과적인 최적화]
커버링 인덱스 + 커서 기반 페이지네이션.
인덱스 설계만으로 100배 차이가 난다.

[가장 자주 하는 조언]
"그 쿼리, 운영 DB에서 돌리지 마세요."
분석은 분석 DB에서.
대량 추출은 Reader에서.
실시간 조회는 캐시에서.
DB를 잘 쓴다는 건 DB에 보내지 않아도 될 쿼리를 보내지 않는 것이다.

## 마무리

1억 행은 특별한 숫자가 아니다.
조금만 성장한 서비스면 어디서든 마주치는 규모다.
문제는 데이터 양이 아니라 꺼내는 방식이다.
OFFSET 대신 커서를 쓰고, `SELECT *` 대신 필요한 컬럼만 고르고, Writer 대신 Reader로 보내고, DB 대신 캐시에서 응답하고, OLTP 대신 분석 DB에서 집계한다.
도구는 이미 다 있다. 대용량을 다루는 기술은 새로운 것을 배우는 게 아니라 기본을 정확히 지키는 것이다.
