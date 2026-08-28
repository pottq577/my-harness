# DBA Knowledge Map

38개 문서를 11개 지식 섹션으로 묶은 지도다. 사용자가 질문하거나 요청한 주제가 어느 문서 그룹에 닿는지 빠르게 찾기 위한 용도로 쓴다. 각 문서의 상세 메타데이터는 `annotated/`의 frontmatter를 본다.

## 섹션 1. Data Modeling & Constraints

데이터 모델링 기초와 제약 조건, 저장 유형 선택에 관한 문서다.

- [DBA-001](annotated/001-NULL을-이해한다는-것.md) NULL을 이해한다는 것
- [DBA-002](annotated/002-FK-없이-사는-법.md) FK 없이 사는 법
- [DBA-003](annotated/003-DB에서-JSON을-쓴다는-것.md) DB에서 JSON을 쓴다는 것
- [DBA-004](annotated/004-Collation의-실체.md) Collation의 실체
- [DBA-005](annotated/005-도메인이-다르면-DB도-달라야-한다.md) 도메인이 다르면 DB도 달라야 한다

**라우팅 키워드**: 데이터 모델링, ERD, nullable, NOT NULL, NULL, FK, 외래키, 데이터 타입, JSON, JSONB, collation, charset, 정렬, 도메인 분석, DBMS 선택, 정합성, 일관성.

## 섹션 2. Index & Query Performance

인덱스 동작 원리와 옵티마이저 관점의 쿼리 성능 분석 문서다.

- [DBA-006](annotated/006-인덱스의-진짜-동작-원리.md) 인덱스의 진짜 동작 원리
- [DBA-007](annotated/007-인덱스의-해부학.md) 인덱스의 해부학
- [DBA-008](annotated/008-옵티마이저가-보는-세상.md) 옵티마이저가 보는 세상

**라우팅 키워드**: 인덱스, B-tree, 복합 인덱스, 커버링, EXPLAIN, 실행 계획, 옵티마이저, 통계, 히스토그램, 카디널리티, GIN, GiST, 클러스터형 인덱스.

## 섹션 3. Large Query & Pagination

대용량 조회와 페이지네이션 최적화 문서다.

- [DBA-009](annotated/009-대용량-SELECT의-기술.md) 대용량 SELECT의 기술
- [DBA-010](annotated/010-'다음-페이지'가-점점-느려지는-이유.md) '다음 페이지'가 점점 느려지는 이유
- [DBA-011](annotated/011-느린-쿼리를-쪼개는-기술.md) 느린 쿼리를 쪼개는 기술

**라우팅 키워드**: 대용량 조회, 페이지네이션, OFFSET, 커서, keyset, LIMIT, 배치 조회, 쿼리 분리, 집계 쿼리, 파티션 프루닝.

## 섹션 4. Transactions & Concurrency

트랜잭션 격리와 락, 동시성 설계 문서다.

- [DBA-013](annotated/013-트랜잭션-격리-수준의-실체.md) 트랜잭션 격리 수준의 실체
- [DBA-014](annotated/014-락의-지형도.md) 락의 지형도

**라우팅 키워드**: 트랜잭션, 격리 수준, REPEATABLE READ, READ COMMITTED, MVCC, 스냅샷, Phantom Read, 락, 데드락, FOR UPDATE, 낙관적 잠금, 비관적 잠금, Advisory Lock.

## 섹션 5. Application / ORM / Connection

애플리케이션 개발자가 매일 만나는 ORM, 커넥션, DB 로직 배치 문서다.

- [DBA-019](annotated/019-ORM이-만드는-쿼리의-실체.md) ORM이 만드는 쿼리의 실체
- [DBA-020](annotated/020-바이브코더들을-위한-ORM-생존리스트.md) 바이브코더들을 위한 ORM 생존리스트
- [DBA-021](annotated/021-프로시저는-아직도-쓸-만한가.md) 프로시저는 아직도 쓸 만한가
- [DBA-022](annotated/022-커넥션-풀의-안쪽.md) 커넥션 풀의 안쪽

**라우팅 키워드**: JPA, ORM, 하이버네이트, N+1, Lazy Loading, fetch join, 엔티티, 프로시저, 트리거, 커넥션 풀, HikariCP, 스레드 풀, 연결 부족, 타임아웃.

## 섹션 6. Schema Change & Bulk Operation

운영 중 스키마 변경과 대용량 DML 문서다.

- [DBA-023](annotated/023-바이브코딩을-하더라도-DB-구조-변경을-안전하게-하는-방법.md) DB 구조 변경을 안전하게 하는 방법
- [DBA-024](annotated/024-대용량-DML의-기술-.md) 대용량 DML의 기술

**라우팅 키워드**: ALTER TABLE, 스키마 변경, 마이그레이션, DDL, Online DDL, gh-ost, pt-osc, 대량 DELETE, TRUNCATE, 데이터 정리, 레플리카 지연, 배치 크기.

## 섹션 7. Logging / Replication / CDC

DB 로그와 복제, CDC에 관한 문서다.

- [DBA-015](annotated/015-Undo-Log-vs-Redo-Log.md) Undo Log vs Redo Log
- [DBA-016](annotated/016-트랜잭션-로그의-세계.md) 트랜잭션 로그의 세계

**라우팅 키워드**: UNDO, REDO, WAL, Binlog, Archive Log, 로그, 복제, 리플리케이션 지연, CDC, replication slot, MVCC.

## 섹션 8. Cache & Messaging

Redis, Memcached를 중심으로 캐시 선택과 메시지 큐 문서다.

- [DBA-025](annotated/025-캐시는-언제부터-쓰면-될까.md) 캐시는 언제부터 쓰면 될까
- [DBA-026](annotated/026-Redis-vs-Memcached.md) Redis vs Memcached
- [DBA-027](annotated/027-Redis에서-Big-Key를-피해야-하는-이유.md) Redis에서 Big Key를 피해야 하는 이유
- [DBA-028](annotated/028-Kafka-vs-RabbitMQ.md) Kafka vs RabbitMQ

**라우팅 키워드**: 캐시, Redis, Memcached, 적중률, TTL, 캐시 스탬피드, hot key, big key, 팬아웃 부하, Kafka, RabbitMQ, 메시지 큐, 파티션, 컨슈머 그룹.

## 섹션 9. Event Architecture

커밋과 메시지 발행의 정합성, 이벤트 기반 설계 문서다.

- [DBA-017](annotated/017-DB가-이벤트를-발행해야-할-때.md) DB가 이벤트를 발행해야 할 때

**라우팅 키워드**: 이벤트, 이벤트 발행, Outbox, Transactional Outbox, CDC, 사가, 이벤트 소싱, 메시지 정합성, 분산 트랜잭션.

## 섹션 10. Backup / Recovery / Incident

백업, 복구, 장애 대응 문서다.

- [DBA-029](annotated/029-Wait-Event로-읽는-Aurora-MySQL.md) Wait Event로 읽는 Aurora MySQL
- [DBA-030](annotated/030-백업과-복구의-실체.md) 백업과 복구의 실체
- [DBA-031](annotated/031-Physical-vs-Logical-Backup.md) Physical vs Logical Backup
- [DBA-032](annotated/032-DB-장애-대응의-기술.md) DB 장애 대응의 기술

**라우팅 키워드**: 백업, 복구, PITR, RPO, RTO, 물리 백업, 논리 백업, 장애, 장애 대응, runbook, 알림, wait event, Aurora, 오탐, 회고.

## 섹션 11. Real Service Cases

실서비스 유형별 DB 설계와 장애 사례 문서다.

- [DBA-012](annotated/012-검색-서비스와-DB.md) 검색 서비스와 DB
- [DBA-018](annotated/018-결제와-DB.md) 결제와 DB
- [DBA-033](annotated/033-홈페이지와-DB.md) 홈페이지와 DB
- [DBA-034](annotated/034-쇼핑몰과-DB.md) 쇼핑몰과 DB
- [DBA-035](annotated/035-게시판에서-SNS로.md) 게시판에서 SNS로
- [DBA-036](annotated/036-푸시-알림이-DB에-주는-영향.md) 푸시 알림이 DB에 주는 영향
- [DBA-037](annotated/037-크롤링이-DB에-주는-영향.md) 크롤링이 DB에 주는 영향
- [DBA-038](annotated/038-왜-분석-쿼리는-RDBMS에서-느린가.md) 왜 분석 쿼리는 RDBMS에서 느린가

**라우팅 키워드**: 검색, Elasticsearch, 결제, 금액, 정산, 통화, 홈페이지, 마케팅 사이트, 쇼핑몰, 장바구니, 재고, SNS, 피드, 타임라인, 팬아웃, 푸시, 크롤링, 봇, 분석, OLAP, 웨어하우스, Snowflake, BigQuery, Athena.

## 라우팅 우선순위

1. 질문에 도메인 단어(결제, 쇼핑몰, 검색, 푸시 등)가 보이면 섹션 11을 먼저 본다.
2. 기술 동사(인덱스, 락, 조회, 마이그레이션 등)가 보이면 해당 기술 섹션을 본다.
3. 한 질문이 두 섹션에 걸치면 겹치는 문서를 우선 읽는다.
4. 문서 안에서도 `triggers`와 `code_signals`가 가장 많이 맞는 문서를 최종 선택한다.
