---
id: DBA-068
title: "당신의 Upsert는 진짜로 쓰고 있는가"
status: stable

topics:
  - upsert
  - on-duplicate-key
  - batch
  - performance-schema
  - write-amplification

triggers:
  - INSERT ON DUPLICATE KEY UPDATE를 배치에서 매번 쓰고 있다
  - 피드 동기화가 5분마다 전건 upsert를 보낸다
  - 쓰기가 유난히 많은데 원인을 모르겠다
  - 같은 값을 반복 덮어쓰는 배치를 줄이고 싶다

code_signals:
  - "ON DUPLICATE KEY UPDATE"
  - "INSERT ... ON DUPLICATE"
  - "VALUES()"
  - "affected_rows"
  - "count_insert"
  - "count_update"

applies_to:
  - sql-review
  - performance-tuning
  - monitoring
  - incident-response

risk_signals:
  - INSERT:UPDATE 비율이 1:1
  - row 수 대비 upsert 횟수가 100배 이상
  - 값이 안 바뀌어도 매번 전건 덮어쓰기
  - affected_rows가 0인데도 lock과 binlog가 계속 발생

read_when:
  - 배치/동기화 파이프라인의 쓰기 부하를 줄일 때
  - Performance Schema로 쓰기 패턴을 진단할 때
  - upsert 안티패턴을 개발팀에 숫자로 설명할 때

read_also:
  - DBA-009
  - DBA-010
  - DBA-024

source_sections:
  - "raw/8.md:964-1136"

summary: >
  무조건 upsert가 쓰기 부하의 안티패턴이 되는 과정을 다룬다. 같은 값
  덮어쓰기가 lock, binlog, 복제를 계속 태우는 구조, 실제 사례(row 414만에
  upsert 32억), 순수 UPDATE와의 차이, "보내지 않는 것"이 최선인 해법을
  Performance Schema 기준과 함께 설명한다.
---
# 당신의 Upsert는 진짜로 쓰고 있는가

```sql
INSERT ... ON DUPLICATE KEY UPDATE
```

MySQL에서 가장 편리한 구문 중 하나다.
있으면 수정하고, 없으면 넣는다.
한 줄이면 끝이니까 누구나 고민 없이 쓴다.
문제는 "고민 없이"라는 부분이다.
값이 바뀌었든 안 바뀌었든 매번 전건 upsert를 보내는 배치가 있다면, 그 DB는 아무 의미 없는 쓰기를 반복하고 있다.

- 변하지 않는 값을 매번 덮어쓰지 마라.
- INSERT:UPDATE 비율이 1:1이면 의심하라.
- row 수 대비 upsert 횟수가 100배를 넘으면 경고다.

DB는 "같은 값이면 무시"해주지 않는다.
affected_rows가 0인 건수를 세라.
쉽다고 생각한 순간부터 한 줄짜리 upsert가 사고가 된다.

## Upsert는 뭘 하는가

MySQL에서 `ON DUPLICATE KEY UPDATE`는 INSERT를 먼저 시도한다.
Primary Key나 Unique Key에 충돌이 없으면 그냥 INSERT. 충돌이 있으면 UPDATE로 전환한다.
한 줄로 "있으면 수정, 없으면 삽입"을 해결하니까 배치, 스케줄러, 동기화 파이프라인에서 습관처럼 쓰인다.

```sql
INSERT INTO feed (feed_id, content, updated_at)
VALUES (?, ?, NOW())
ON DUPLICATE KEY UPDATE
content = VALUES(content),
updated_at = VALUES(updated_at);
```

간결하다. 그래서 위험하다.

## 어디서 문제가 시작되는가

값이 바뀌었든 아니든 매번 전건 upsert를 날리는 배치.
피드를 5분마다 동기화한다고 하자.
테이블에 row가 400만 개 있다.
5분마다 400만 건 upsert. 하루 288번. 하루 11.5억 건. 한 달이면 345억 건.
이 중에서 실제로 값이 바뀐 건 몇 퍼센트나 될까?
피드 내용이 5분마다 바뀌는 row는 전체의 1%도 안 될 수 있다.
나머지 99%는 똑같은 값을 똑같은 자리에 덮어쓰고 있을 뿐이다.

## DB는 "같은 값"을 알아서 무시해주지 않는다

흔한 오해가 있다.
"값이 같으면 MySQL이 알아서 skip 하지 않나?"
반은 맞고 반은 틀리다.
MySQL은 값이 동일하면 `affected_rows = 0`을 반환한다.
실제로 디스크에 쓰지 않는다.
하지만 그 이전 단계에서 이미 비용이 발생한다.

- row lock을 획득한다.
- binlog에 이벤트를 기록한다.
- Reader에 복제한다.

값이 같아도 lock과 binlog와 replication은 돌아간다.
DB가 "같은 값"을 무시해주는 건 디스크 쓰기뿐이다.

## 눈에 보이지 않는 비용들

upsert 한 건이 내부에서 하는 일을 따라가 보자.

1. INSERT를 시도한다.
2. PK/Unique 인덱스에서 기존 row를 검색한다.
3. 충돌을 발견한다.
4. INSERT intention lock을 잡는다.
5. S lock에서 X lock으로 전환한다.
6. row를 갱신한다.
7. binlog에 기록한다.
8. redo log에 기록한다.
9. Reader로 복제한다.

값이 바뀌든 안 바뀌든 이 과정을 전부 탄다.
400만 건을 매번 이렇게 처리하면 Buffer Pool에는 이 row들의 페이지가 올라오고 정작 서비스 쿼리가 쓸 hot 페이지를 밀어낸다.

- Buffer Pool 오염.
- 복제 지연.
- I/O 비용.
- lock 경합.

전부 "같은 값 덮어쓰기"에서 나온다.

## 실제 사례 --- row 400만에 upsert 32억

실제 프로덕션 클러스터에서 Performance Schema를 조회했다.
`schedule_feed_32` 테이블.
실제 row 수는 414만. 누적 upsert 횟수는 32억.
row 하나당 평균 770번 덮어쓴 셈이다.
InnoDB 전체 쓰기의 83%가 upsert에서 UPDATE로 전환된 것이었다.
digest를 확인하니 99.99%가 `ON DUPLICATE KEY UPDATE`.
순수 INSERT는 1,792건.
32억 건 중 진짜 새로운 row는 0.000056%.
나머지 99.999%는 있는 row에 같은 값을 덮어쓰고 있었다.

## ON DUPLICATE KEY UPDATE vs 순수 UPDATE

"그러면 UPDATE로 바꾸면 해결되는 거 아닌가?"
row를 찾아서 갱신하는 건 어차피 UPDATE나 upsert나 같다.
차이는 upsert의 INSERT 시도 과정이다.

[ON DUPLICATE KEY UPDATE]

1. INSERT intention lock 획득
2. PK 충돌 발견
3. S lock → X lock 전환
4. UPDATE 수행

[순수 UPDATE]

1. X lock 획득
2. UPDATE 수행

lock 전환 과정에서 동시성이 높으면 deadlock 확률이 올라간다.
하지만 핵심은 거기가 아니다.
UPDATE로 바꿔도 "같은 값 덮어쓰기"는 남는다.
진짜 해결은 **값이 안 바뀌었으면 아예 안 보내는 것**이다.

## 해결 --- 보내지 않는 것이 최선이다

쿼리를 바꾸는 게 아니다.
쿼리를 보낼지 말지를 판단하는 것이다.
앱에서 이전 값과 새 값을 비교한다.
4개 컬럼이 전부 같으면 skip. 하나라도 다르면 기존처럼 upsert.
비교는 DB에 SELECT를 추가로 날리는 게 아니다.
앱이 이미 갖고 있는 캐시에서 한다.
DB 부하는 오히려 줄기만 한다.
skip하면 INSERT 시도도 안 하고 UPDATE도 안 한다.
binlog도 안 쓰고 Reader에 복제도 안 한다.
32억 건 중 90%가 동일 값이라면 28.8억 건의 쓰기가 사라진다.

## 그런데 upsert가 다 나쁜 건 아니다

`ON DUPLICATE KEY UPDATE`를 쓴다고 무조건 안티패턴인 것은 아니다.
워크플로우 엔진에서 이벤트 소싱의 idempotency를 보장하기 위해 upsert를 쓰는 경우가 있다.
이때는 INSERT가 대부분이고 UPDATE는 거의 발생하지 않는다.
실제로 다른 클러스터를 조회하니 INSERT 7.79억에 UPDATE 4.8만. UPDATE 비율 0.006%.
이건 "같은 row를 반복 덮어쓰는 것"이 아니라 "중복 방지 안전장치"로 쓰는 것이다.
구분 기준은 간단하다.

- INSERT:UPDATE가 1:1이면 안티패턴.
- INSERT가 압도적이면 정상.

## DBA는 어떻게 찾는가

Performance Schema에서 두 가지를 본다.
`table_io_waits_summary_by_table`에서 `count_insert`와 `count_update`가 1:1인 테이블.
`events_statements_summary_by_digest`에서 ON DUPLICATE KEY UPDATE가 있는 digest.
그리고 `information_schema.tables`에서 `table_rows`와 upsert 횟수를 비교한다.
row 414만에 upsert 32억이면 770배 덮어쓰기.
이 세 가지가 모이면 개발팀에 숫자를 보여줄 수 있다.
"이 테이블, row당 770번 같은 값 덮어쓰고 있습니다."
숫자가 있으면 설득이 된다.
감으로는 안 된다.

## DBA 관점에서의 정리

- 변하지 않는 값을 매번 덮어쓰지 마라.
- INSERT:UPDATE 비율이 1:1이면 의심하라.
- row 수 대비 upsert 횟수가 100배를 넘으면 경고다.
- DB는 "같은 값이면 무시"해주지 않는다.
- affected_rows가 0인 건수를 세라.

OFFSET/LIMIT이 읽기의 대표적 안티패턴이라면 무조건 upsert는 쓰기의 대표적 안티패턴이다.
둘 다 "일단 동작하니까" 전건 처리하는 습관에서 온다.
둘 다 규모가 커지면서 비용이 폭발한다.
둘 다 DB 단에서 발견할 수 있고, 둘 다 고치는 건 앱 쪽의 몫이다.
DBA가 할 수 있는 건 문제를 숫자로 보여주는 것이다.
"row 414만에 upsert 32억"이라는 한 줄이 개발팀을 움직이게 한다.
쉽다고 생각한 순간부터 한 줄짜리 upsert가 사고가 된다.