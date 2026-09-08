---
id: DBA-047
title: "MySQL vs PostgreSQL: 뭘 고르든 후회하는 이유"
status: stable

topics:
  - mysql
  - postgresql
  - database-selection
  - operations
  - sql

triggers:
  - MySQL과 PostgreSQL 중 무엇을 고르나
  - 두 DB의 운영 차이가 무엇인가
  - JSON과 복잡한 쿼리에 어떤 DB가 맞나

code_signals:
  - "InnoDB"
  - "MVCC"
  - "VACUUM"
  - "JSONB"
  - "utf8mb4"

applies_to:
  - domain-modeling
  - application-architecture
  - schema-design

risk_signals:
  - 기능 표만 보고 팀의 운영 경험을 무시
  - 버전과 관리형 서비스 차이를 확인하지 않고 일반화

read_when:
  - 신규 서비스의 관계형 DB를 선택할 때
  - MySQL과 PostgreSQL 마이그레이션 비용을 비교할 때

read_also:
  - DBA-005
  - DBA-039
  - DBA-049

source_sections:
  - "raw/5.md:1154-1324"

verified_at: 2026-09-09

references:
  - "https://www.postgresql.org/docs/current/release-18.html"
  - "https://dev.mysql.com/blog-archive/introducing-mysql-innovation-and-long-term-support-lts-versions/"
  - "https://dev.mysql.com/doc/refman/8.4/en/upgrade-best-practices.html"

summary: >
  MySQL과 PostgreSQL의 쿼리, 운영, 복제, DDL 특성을 비교하고
  도메인 복잡도와 팀 경험을 포함한 선택 기준을 제시한다.
---
# MySQL vs PostgreSQL: 뭘 고르든 후회하는 이유

"MySQL이 좋아요, PostgreSQL이 좋아요?"
DBA한테 가장 많이 들어오는 질문이다.
솔직하게 답하면 "둘 다 좋고, 둘 다 불편하다."
뭘 고르든 어느 시점에 후회한다.
MySQL을 쓰면 PostgreSQL의 기능이 부럽고, PostgreSQL을 쓰면 MySQL의 생태계가 그립다.
이 글은 "뭐가 더 좋냐"가 아니라 "뭐가 다르냐"를 정리한다.
2026-09 기준 PostgreSQL 현재 문서는 18을 다루고, MySQL은 LTS와 Innovation 릴리스 모델을 운영한다.
실제 선택에서는 제품 이름만 비교하지 말고 조직이 지원할 메이저 버전과 관리형 서비스의 기능을 함께 고정한다.

## 철학부터 다르다

MySQL은 "빠르고 쉽게"에서 출발했다.
웹 서비스 백엔드로 태어났다. 읽기가 많고 스키마가 단순한 서비스에 최적화.
PostgreSQL은 "정확하고 확장 가능하게"에서 출발했다.
학술 프로젝트(POSTGRES)에서 시작했다.
SQL 표준 준수, 타입 확장, 복잡한 쿼리 처리.
이 철학 차이가 30년 뒤에도 남아 있다.
MySQL은 단순한 것을 빠르게 한다.
PostgreSQL은 복잡한 것을 정확하게 한다.

## MVCC 구현이 완전히 다르다

둘 다 MVCC를 쓰지만 방식이 정반대다.

[MySQL InnoDB]
행을 수정하면 원본을 undo log에 복사한다.
현재 데이터 페이지에는 최신 버전만 남는다.
읽기가 이전 버전을 원하면 undo log에서 재구성한다.

[PostgreSQL]
행을 수정하면 새 버전을 힙에 직접 추가한다.
이전 버전도 같은 테이블 안에 남아 있다.
죽은 튜플이 쌓이고, VACUUM이 정리한다.

MySQL은 오래된 트랜잭션이 undo를 잡으면 history list length가 폭증한다.
PostgreSQL은 VACUUM이 못 돌면 dead tuple이 쌓여 테이블이 부풀어 오른다.
최악에는 XID wraparound가 터진다.
어느 쪽이든 오래된 트랜잭션이 적이다.

## 기본 격리 수준이 다르다

MySQL InnoDB의 기본은 Repeatable Read.
트랜잭션 시작 시점의 스냅샷을 끝까지 유지한다.
Gap Lock으로 Phantom Read까지 막는다.
PostgreSQL의 기본은 Read Committed.
매 쿼리마다 새로운 스냅샷을 찍는다.
같은 트랜잭션 안에서 같은 SELECT가 다른 결과를 줄 수 있다.
MySQL DBA는 Gap Lock 데드락에 익숙하다.
PostgreSQL DBA는 Non-Repeatable Read를 감수한다.
두 DB를 넘나드는 개발자가 가장 헷갈리는 지점이다.
"같은 코드인데 왜 동작이 다르지?"
격리 수준이 다르기 때문이다.

## 복제 방식이 다르다

[MySQL]
binlog 기반 복제.
Statement, Row, Mixed 세 가지 포맷.
비동기 복제가 기본이고 Semi-sync로 한 단계 올릴 수 있다.
Group Replication으로 멀티마스터도 가능하다.

[PostgreSQL]
WAL(Write-Ahead Log) 기반 스트리밍 복제.
물리 복제가 기본이고 논리 복제(Logical Replication)도 지원한다.
논리 복제는 테이블 단위 선택이 가능해서 부분 복제가 자유롭다.

MySQL의 binlog는 생태계가 풍부하다. Debezium, Maxwell, Canal.
CDC 파이프라인 구축이 훨씬 쉽다.
PostgreSQL의 논리 복제는 유연하지만 도구 생태계가 아직 MySQL에 못 미친다.

## DDL 차이가 실무에서 크다

MySQL의 ALTER TABLE은 오래 전부터 악명이 높았다.
테이블 전체를 복사하는 Online DDL.
pt-online-schema-change, gh-ost 같은 외부 도구 없이는 대규모 테이블 변경이 무섭다.
PostgreSQL은 대부분의 ALTER TABLE이 즉시 완료된다.
컬럼 추가는 메타데이터만 바꾸면 된다.
NOT NULL 제약도 빠르게 붙는다.
대신 PostgreSQL의 컬럼 타입 변경은 테이블 전체를 다시 쓰는 경우가 있다.
그리고 ALTER TABLE에 ACCESS EXCLUSIVE LOCK이 걸리면 그 순간 모든 읽기/쓰기가 멈춘다.
어느 쪽이든 DBA는 DDL 앞에서 긴장한다.
방식이 다를 뿐 위험은 같다.

## MySQL이 한국에서 압도적인 이유

솔직히 기술적 이유보다 역사적 이유가 크다.
한국 IT 성장기에 LAMP 스택이 들어왔다.
PHP + MySQL 조합이 웹 서비스의 표준이었다.
네이버, 다음, 초기 커머스 서비스 전부 MySQL이었다.
MySQL 경험자가 많다. 채용이 쉽다. 문서가 많다. 커뮤니티가 크다.
AWS Aurora MySQL이 킬러 서비스가 됐다.
관리형 서비스에서의 편의성이 MySQL 선택을 더 굳혔다.
기술 선택은 진공 상태에서 이뤄지지 않는다.
"사람을 구할 수 있는가"가 종종 아키텍처보다 중요하다.

## PostgreSQL이 빠르게 치고 올라오는 이유

2020년 이후 분위기가 확실히 바뀌었다.

[클라우드 네이티브]
Aurora PostgreSQL이 안정화됐다.
Supabase가 PostgreSQL 위에서 BaaS를 만들었다.
Neon이 서버리스 PostgreSQL을 내놓았다.

[기능 확장]
JSON 지원이 MySQL보다 강력하다.
JSONB 타입, GIN 인덱스, JSON 경로 쿼리.
파티셔닝도 선언적이라 쉽다.

[분석 워크로드]
Window Function, CTE, 재귀 쿼리.
OLTP와 가벼운 OLAP을 하나의 DB로 커버한다.
신규 서비스에서 PostgreSQL을 선택하는 사례가 늘었지만 산업과 팀에 따라 분포가 다르므로 보편적 비율로 일반화하지 않는다.

## MySQL이 여전히 강한 영역

대규모 웹 서비스 백엔드.
읽기 비율이 높고 스키마가 단순한 서비스.
MySQL은 이 영역에서 30년 검증됐다.
Facebook이 MySQL 포크(MyRocks)를 쓰고, Slack이 Vitess 위에 MySQL을 올렸다.
InnoDB의 클러스터 인덱스 구조는 PK 기반 포인트 룩업이 빠르다.
Buffer Pool의 메모리 효율이 좋다.
그리고 무엇보다 운영 도구와 모니터링 생태계가 성숙하다.
Percona Toolkit, orchestrator, ProxySQL.

## PostgreSQL이 더 나은 영역

복잡한 도메인 모델링.
JSON, 배열, 사용자 정의 타입. GIS 데이터(PostGIS).
분석과 트랜잭션이 공존하는 서비스.
물류, 결제, ERP처럼 복잡한 쿼리와 정합성이 둘 다 필요한 곳.
확장 생태계도 다르다.
pg_stat_statements로 쿼리 통계를 꺼내고, Foreign Data Wrapper로 외부 DB를 조인하고, Extension으로 기능을 확장한다.
PostgreSQL은 "DB 안에서 다 하겠다"는 사상이다.
MySQL은 "DB는 저장소, 나머지는 밖에서"라는 사상이다.

## 실무에서 겪는 차이들

DBA가 두 DB를 운영하면 사소한 차이에서 자꾸 발이 걸린다.
MySQL의 utf8은 3바이트다. 이모지를 넣으려면 utf8mb4를 써야 한다.
PostgreSQL은 처음부터 UTF-8이 UTF-8이다.
MySQL은 빈 문자열과 NULL을 구분하지만 INSERT 시 NOT NULL 컬럼에 빈 문자열을 허용한다.
PostgreSQL은 NOT NULL이면 빈 문자열도 NOT NULL이다.
MySQL의 GROUP BY는 관대하다. SELECT에 집계되지 않은 컬럼이 있어도 돌아간다.
PostgreSQL은 칼같이 에러를 뱉는다.
이런 차이가 마이그레이션 때 수백 건의 쿼리 수정으로 돌아온다.

## 뭘 고를 것인가

"새 프로젝트인데 뭘 쓸까요?"
팀에 MySQL 경험이 많으면 MySQL.
팀에 PostgreSQL 경험이 많으면 PostgreSQL.
둘 다 비슷하면 서비스 특성으로 판단.

- 읽기 위주 + 단순 스키마 + CDC 필요 = MySQL.
- 복잡한 도메인 + JSON + 분석 쿼리 = PostgreSQL.

"팀에 아무도 경험이 없는데요?"
그러면 MySQL.
채용 풀이 넓고 장애 시 도움받을 곳이 많다.

## DBA 관점에서의 정리

MySQL과 PostgreSQL은 같은 문제를 다른 방향에서 푼다.
MVCC 구현이 다르고, 기본 격리 수준이 다르고, 복제 방식이 다르고, DDL 처리가 다르다.
"뭐가 더 좋냐"는 질문에는 답이 없다. "어떤 상황에 맞느냐"에는 답이 있다.
둘 다 써본 DBA로서 말하자면 뭘 골라도 어느 시점엔 후회한다.
MySQL을 쓰면 PostgreSQL의 DDL이 부럽고, PostgreSQL을 쓰면 MySQL의 도구들이 그립다.
완벽한 DB는 없다. 자기 서비스에 맞는 DB가 있을 뿐이다.
그 판단을 내리는 게 DBA의 일이다.
