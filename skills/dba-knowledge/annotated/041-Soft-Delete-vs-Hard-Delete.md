---
id: DBA-041
title: "Soft Delete vs Hard Delete: 지우는 척하면 인덱스가 망가진다"
status: stable

topics:
  - soft-delete
  - hard-delete
  - index
  - retention
  - privacy

triggers:
  - 삭제 플래그를 모든 테이블에 둬야 하나
  - soft delete 때문에 조회가 느리다
  - 개인정보를 실제로 언제 삭제해야 하나

code_signals:
  - "is_deleted"
  - "deleted_at"
  - "WHERE is_deleted = 0"
  - "UNIQUE"

applies_to:
  - schema-design
  - indexing
  - migration

risk_signals:
  - 삭제 행이 계속 쌓이는데 보존 정책이 없음
  - 고유 제약이 삭제 행 때문에 재등록을 막음

read_when:
  - 논리 삭제 정책을 설계할 때
  - 삭제 데이터 때문에 인덱스와 조회가 비대해질 때

read_also:
  - DBA-006
  - DBA-024
  - DBA-034

source_sections:
  - "raw/4.md:1458-1594"

summary: >
  Soft Delete와 Hard Delete의 목적을 구분하고 인덱스, 고유 제약,
  보존 기간과 물리 삭제 배치를 함께 설계하는 방법을 설명한다.
---
# Soft Delete vs Hard Delete: 지우는 척하면 인덱스가 망가진다

"삭제"라는 단어가 DB에서는 두 가지 의미를 가진다. 진짜 지우는 것과, 지운 척하는 것.
대부분의 서비스는 지운 척한다.
is_deleted = 1로 플래그를 세우고 SELECT에서 `WHERE is_deleted = 0`을 붙인다. 편리하다.
복구가 쉽고, 감사 로그 대신 쓸 수 있고, 실수로 날린 데이터를 되살릴 수 있다.
편리함에는 비용이 따른다.
인덱스가 커지고, 풀스캔이 느려지고, 몇 년 뒤 테이블의 90%가 "삭제된 데이터"가 된다.

- 논리 삭제 컬럼에 부분 인덱스를 걸어라.
- 삭제된 row 비율이 50%를 넘으면 경고다.
- Hard Delete가 필요한 데이터와 아닌 데이터를 구분하라.
- GDPR 대상 데이터는 Soft Delete로 충분하지 않다.
- 삭제 정책 없는 Soft Delete는 방치다.

지우지 않는 건 안전이 아니다.
관리되지 않는 데이터는 쌓이는 것이 아니라 썩는 것이다.

## Soft Delete의 구조

가장 흔한 패턴이다.
테이블에 is_deleted 컬럼을 추가한다.
삭제 요청이 오면 DELETE 대신 UPDATE를 친다.

```sql
UPDATE users SET is_deleted = 1 WHERE user_id = 42;
```

모든 조회 쿼리에는 `WHERE is_deleted = 0`이 붙는다.
ORM을 쓰면 이 조건이 자동으로 붙기도 한다. Django의 SoftDeleteModel, JPA의 SQLRestriction 어노테이션.
개발자 입장에서는 간편하다.
DELETE 쿼리를 쓸 일이 없으니 참조 무결성 문제도 없고, 복구는 is_deleted = 0으로 되돌리면 된다.

## 인덱스가 망가지는 이유

문제는 시간이 지나면서 드러난다.
사용자 100만 명 중 90만 명이 탈퇴했다. is_deleted = 0인 row는 10만 개뿐이다.
하지만 인덱스에는 100만 건이 전부 들어 있다. B-Tree 인덱스는 삭제된 row를 모른다.
인덱스 키에 is_deleted가 포함되어 있지 않으면 활성 row 10만 건을 찾기 위해 100만 건짜리 인덱스를 탐색한다.
인덱스 선택도(selectivity)가 떨어진다.
옵티마이저가 인덱스를 타도 실제로 유효한 row는 10%뿐이다.
나머지 90%는 필터링에서 버려진다.

## 테이블 bloat

삭제되지 않은 row는 물리적으로 자리를 차지한다.
InnoDB에서 Soft Delete된 row는 페이지 안에 그대로 남는다.
페이지가 비효율적으로 채워지고, Buffer Pool에 불필요한 페이지가 올라온다.
PostgreSQL은 더 심하다.
UPDATE는 기존 row를 dead tuple로 남기고 새 row를 만든다.
VACUUM이 dead tuple을 회수하지만, is_deleted = 1로 바꾼 row는 dead tuple이 아니다. 살아 있는 row다. VACUUM 대상이 아니다.
테이블 크기는 계속 커진다.
데이터 파일이 커지면 백업 시간이 늘고, 복제 지연이 길어지고, 디스크 비용이 올라간다.

## Hard Delete의 위험

그렇다면 진짜 지우면 되지 않는가.

```sql
DELETE FROM users WHERE user_id = 42;
```

간단해 보이지만 위험이 크다.
외래 키가 걸려 있으면 CASCADE로 자식 테이블까지 연쇄 삭제된다. orders, payments, reviews가 한순간에 날아간다.
FK가 없어도 문제다. 다른 테이블이 user_id를 참조하고 있으면 데이터 정합성이 깨진다.
JOIN했을 때 NULL이 나오거나 존재하지 않는 ID를 가리키게 된다.
그리고 가장 근본적인 문제. 지운 데이터는 복구가 안 된다.
백업에서 복구하려면 PITR이 필요하고, 그 시간 동안 서비스는 기다려야 한다.

## 부분 인덱스라는 해법

PostgreSQL에는 부분 인덱스(Partial Index)가 있다.
조건을 만족하는 row만 인덱스에 넣는다.

```sql
CREATE INDEX idx_users_active
ON users (email)
WHERE is_deleted = false;
```

이 인덱스에는 활성 사용자만 들어간다.
100만 건 중 10만 건만 인덱스에 존재한다.
인덱스 크기가 1/10로 줄고, 조회가 빨라진다.
MySQL에는 부분 인덱스가 없다.
대신 복합 인덱스로 흉내 낼 수 있다.

```sql
ALTER TABLE users ADD INDEX idx_active_email (is_deleted, email);
```

`is_deleted = 0` 조건이 항상 포함되므로 인덱스의 앞부분에서 빠르게 좁혀진다.
부분 인덱스만큼 효율적이지는 않지만 전체 스캔보다는 훨씬 낫다.

## GDPR과 Soft Delete의 충돌

"삭제 요청을 받으면 지워야 한다."
Soft Delete는 지운 게 아니다.
`is_deleted = 1`은 "안 보여주겠다"는 뜻이지 "데이터를 파기했다"는 뜻이 아니다.
규제 기관이 DB 덤프를 뒤지면 `is_deleted = 1`인 row에서 개인정보가 고스란히 나온다.
해결 방법은 두 가지다.
Soft Delete 후 일정 기간이 지나면 Hard Delete하는 배치.
또는 Soft Delete 시점에 개인정보 컬럼을 NULL로 덮어쓰기.
어느 쪽이든 "삭제 정책"이 필요하다.
`is_deleted = 1`로 바꾸고 끝이 아니다. 그 이후에 무엇을 할 것인가를 정해야 한다.

## 아카이빙이라는 선택지

삭제도, 방치도 아닌 세 번째 길.
오래된 Soft Delete 데이터를 별도 테이블로 옮기는 것이다.

```sql
INSERT INTO users_archive
SELECT * FROM users
WHERE is_deleted = 1 AND deleted_at < '2025-01-01';
DELETE FROM users
WHERE is_deleted = 1 AND deleted_at < '2025-01-01';
```

원본 테이블은 가벼워진다. 인덱스가 작아지고, 풀스캔이 빨라진다.
아카이브 테이블은 별도 조회로만 접근한다.
배치로 주기적으로 돌리면 원본 테이블의 크기를 일정하게 유지할 수 있다.
복구가 필요하면 아카이브에서 꺼내면 된다.
Hard Delete보다 안전하고, Soft Delete 방치보다 깔끔하다.

## DBA 관점에서의 정리

논리 삭제 컬럼에 부분 인덱스를 걸어라.
삭제된 row 비율이 50%를 넘으면 경고다.
Hard Delete가 필요한 데이터와 아닌 데이터를 구분하라.
GDPR 대상 데이터는 Soft Delete로 충분하지 않다.
삭제 정책 없는 Soft Delete는 방치다.
Soft Delete는 "안 지우는 것"이 아니라 "나중에 지우기 위한 마킹"이어야 한다.
마킹만 하고 후속 조치가 없으면 테이블은 커지고, 인덱스는 느려지고, 개인정보는 남아 있게 된다.
is_deleted 컬럼을 추가하는 건 시작이다. 그 이후의 정책을 정하는 것이 끝이다.
지우지 않는 건 안전이 아니다.
관리되지 않는 데이터는 쌓이는 것이 아니라 썩는 것이다.
