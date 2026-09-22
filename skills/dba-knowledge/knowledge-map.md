# DBA Knowledge Map

72개 문서를 12개 지식 섹션으로 묶은 지도다. 각 문서는 주 라우팅 섹션에 한 번만 둔다. 교차 주제는 문서 frontmatter의 `read_also`로 연결한다.

## 섹션 1. Data Modeling & Constraints

- [DBA-001](annotated/001-NULL을-이해한다는-것.md) NULL을 이해한다는 것
- [DBA-002](annotated/002-FK-없이-사는-법.md) FK 없이 사는 법
- [DBA-003](annotated/003-DB에서-JSON을-쓴다는-것.md) DB에서 JSON을 쓴다는 것
- [DBA-004](annotated/004-Collation의-실체.md) Collation의 실체
- [DBA-039](annotated/039-인조키를-알고-써야-한다.md) 인조키를 알고 써야 한다
- [DBA-071](annotated/071-ID를-만든다는-것.md) ID를 만든다는 것

라우팅 키워드: NULL, FK, JSON 컬럼, collation, charset, 기본키, 자연키, 인조키, UUID, ULID, ID 설계, AUTO_INCREMENT.

## 섹션 2. Database Selection & Storage Engines

- [DBA-005](annotated/005-도메인이-다르면-DB도-달라야-한다.md) 도메인이 다르면 DB도 달라야 한다
- [DBA-046](annotated/046-SQL과-NoSQL-선택-기준.md) SQL과 NoSQL 선택 기준
- [DBA-047](annotated/047-MySQL-vs-PostgreSQL.md) MySQL vs PostgreSQL
- [DBA-051](annotated/051-Netflix가-Cassandra를-선택한-이유.md) Netflix와 Cassandra
- [DBA-052](annotated/052-RocksDB.md) RocksDB
- [DBA-053](annotated/053-Supabase에서-자체-DB로-전환하기.md) Supabase에서 자체 DB로 전환하기
- [DBA-054](annotated/054-MongoDB-설계-패턴.md) MongoDB 설계 패턴
- [DBA-061](annotated/061-B-Tree-vs-LSM-Tree.md) B-Tree vs LSM-Tree

라우팅 키워드: DBMS 선택, SQL, NoSQL, MySQL, PostgreSQL, Cassandra, RocksDB, Supabase, MongoDB, 문서 모델, B-Tree, LSM Tree.

## 섹션 3. Index & Query Performance

- [DBA-006](annotated/006-인덱스의-진짜-동작-원리.md) 인덱스의 진짜 동작 원리
- [DBA-007](annotated/007-인덱스의-해부학.md) 인덱스의 해부학
- [DBA-008](annotated/008-옵티마이저가-보는-세상.md) 옵티마이저가 보는 세상
- [DBA-009](annotated/009-대용량-SELECT의-기술.md) 대용량 SELECT의 기술
- [DBA-010](annotated/010-'다음-페이지'가-점점-느려지는-이유.md) OFFSET 없는 페이지네이션
- [DBA-011](annotated/011-느린-쿼리를-쪼개는-기술.md) 느린 쿼리를 쪼개는 기술
- [DBA-057](annotated/057-DocumentDB-쿼리-플래너.md) DocumentDB 쿼리 플래너
- [DBA-059](annotated/059-빅오-표기법.md) 빅오 표기법
- [DBA-062](annotated/062-쿼리-플래너의-머릿속.md) 쿼리 플래너의 머릿속

라우팅 키워드: 인덱스, B-tree, 커버링, EXPLAIN, 옵티마이저, 통계, 대용량 조회, OFFSET, keyset, 쿼리 분리, 실행 계획, 비용 모델, 빅오, DocumentDB.

## 섹션 4. Large Data & Analytics

- [DBA-024](annotated/024-대용량-DML의-기술-.md) 대용량 DML의 기술
- [DBA-038](annotated/038-왜-분석-쿼리는-RDBMS에서-느린가.md) 왜 분석 쿼리는 RDBMS에서 느린가
- [DBA-068](annotated/068-Upsert.md) Upsert

라우팅 키워드: 대량 DELETE, 백필, 파티셔닝, OLAP, 웨어하우스, Athena, Snowflake, BigQuery, 컬럼형 저장, Upsert, ON CONFLICT, MERGE.

## 섹션 5. Transactions & Concurrency

- [DBA-013](annotated/013-트랜잭션-격리-수준의-실체.md) 트랜잭션 격리 수준의 실체
- [DBA-014](annotated/014-락의-지형도.md) 락의 지형도
- [DBA-056](annotated/056-락을-이해한다는-것.md) 락을 이해한다는 것
- [DBA-064](annotated/064-낙관적-락-vs-비관적-락.md) 낙관적 락 vs 비관적 락

라우팅 키워드: 트랜잭션, 격리 수준, MVCC, 스냅샷, Phantom Read, 락, 데드락, FOR UPDATE, Advisory Lock, 낙관적 락, 비관적 락, 락 대기.

## 섹션 6. Application, ORM & Connections

- [DBA-019](annotated/019-ORM이-만드는-쿼리의-실체.md) ORM이 만드는 쿼리의 실체
- [DBA-020](annotated/020-바이브코더들을-위한-ORM-생존리스트.md) ORM 생존리스트
- [DBA-021](annotated/021-프로시저는-아직도-쓸-만한가.md) 프로시저는 아직도 쓸 만한가
- [DBA-022](annotated/022-커넥션-풀의-안쪽.md) 커넥션 풀의 안쪽
- [DBA-048](annotated/048-JPA와-MyBatis.md) JPA와 MyBatis
- [DBA-050](annotated/050-JSON을-잘-쓴다는-것.md) JSON 데이터 계약
- [DBA-060](annotated/060-마이크로서비스-전환이-DB에-주는-영향.md) 마이크로서비스 전환이 DB에 주는 영향
- [DBA-065](annotated/065-커넥션-풀이-필요한-진짜-이유.md) 커넥션 풀이 필요한 진짜 이유

라우팅 키워드: JPA, MyBatis, ORM, N+1, Lazy Loading, SQL 매퍼, 프로시저, 커넥션 풀, HikariCP, pgBouncer, JSON 계약, MSA, 마이크로서비스.

## 섹션 7. Schema Change & Data Lifecycle

- [DBA-023](annotated/023-바이브코딩을-하더라도-DB-구조-변경을-안전하게-하는-방법.md) DB 구조 변경을 안전하게 하는 방법
- [DBA-041](annotated/041-Soft-Delete-vs-Hard-Delete.md) Soft Delete vs Hard Delete
- [DBA-058](annotated/058-Flyway-vs-Liquibase.md) Flyway vs Liquibase
- [DBA-066](annotated/066-무중단-스키마-변경.md) 무중단 스키마 변경

라우팅 키워드: ALTER TABLE, 마이그레이션, Rolling Update, Online DDL, gh-ost, pt-osc, soft delete, hard delete, 보존 정책, Flyway, Liquibase, 무중단 배포.

## 섹션 8. Logs, Replication & Availability

- [DBA-015](annotated/015-Undo-Log-vs-Redo-Log.md) Undo Log vs Redo Log
- [DBA-016](annotated/016-트랜잭션-로그의-세계.md) 트랜잭션 로그의 세계
- [DBA-042](annotated/042-레플리케이션과-페일오버.md) 레플리케이션과 페일오버
- [DBA-049](annotated/049-Aurora-vs-RDS.md) Aurora vs RDS
- [DBA-067](annotated/067-Aurora-MySQL-failover.md) Aurora MySQL failover

라우팅 키워드: UNDO, REDO, WAL, Binlog, CDC, 복제, 페일오버, split brain, quorum, fencing, Multi-AZ, Aurora, 읽기/쓰기 엔드포인트.

## 섹션 9. Cache, Messaging & Events

- [DBA-017](annotated/017-DB가-이벤트를-발행해야-할-때.md) DB가 이벤트를 발행해야 할 때
- [DBA-025](annotated/025-캐시는-언제부터-쓰면-될까.md) 캐시는 언제부터 쓰면 될까
- [DBA-026](annotated/026-Redis-vs-Memcached.md) Redis vs Memcached
- [DBA-027](annotated/027-Redis에서-Big-Key를-피해야-하는-이유.md) Redis Big Key
- [DBA-028](annotated/028-Kafka-vs-RabbitMQ.md) Kafka vs RabbitMQ

라우팅 키워드: 캐시, Redis, Memcached, TTL, hot key, big key, Kafka, RabbitMQ, Outbox, CDC, 이벤트 정합성.

## 섹션 10. Backup, Monitoring & Incident

- [DBA-029](annotated/029-Wait-Event로-읽는-Aurora-MySQL.md) Wait Event로 읽는 Aurora MySQL
- [DBA-030](annotated/030-백업과-복구의-실체.md) 백업과 복구의 실체
- [DBA-031](annotated/031-Physical-vs-Logical-Backup.md) Physical vs Logical Backup
- [DBA-032](annotated/032-DB-장애-대응의-기술.md) DB 장애 대응의 기술
- [DBA-040](annotated/040-데이터베이스-OOM의-실체.md) 데이터베이스 OOM
- [DBA-043](annotated/043-Load-Average와-AAS.md) Load Average와 AAS
- [DBA-055](annotated/055-GC가-데이터베이스를-멈추는-순간.md) GC가 데이터베이스를 멈추는 순간

라우팅 키워드: 백업, 복구, PITR, RPO, RTO, 장애, runbook, wait event, OOM, 메모리, Load Average, AAS, Database Insights, GC, Stop the World, JVM.

## 섹션 11. Service Domain Cases

- [DBA-012](annotated/012-검색-서비스와-DB.md) 검색 서비스와 DB
- [DBA-018](annotated/018-결제와-DB.md) 결제와 정산
- [DBA-033](annotated/033-홈페이지와-DB.md) 홈페이지와 DB
- [DBA-034](annotated/034-쇼핑몰과-DB.md) 쇼핑몰과 DB
- [DBA-035](annotated/035-게시판에서-SNS로.md) 게시판에서 SNS로
- [DBA-036](annotated/036-푸시-알림이-DB에-주는-영향.md) 푸시 알림과 배치
- [DBA-037](annotated/037-크롤링이-DB에-주는-영향.md) 크롤링과 DB
- [DBA-044](annotated/044-주문-테이블-설계.md) 주문 테이블 설계
- [DBA-045](annotated/045-로그인이-DB에-주는-영향.md) 로그인과 DB
- [DBA-063](annotated/063-알림-시스템과-DB.md) 알림 시스템과 DB
- [DBA-069](annotated/069-채팅과-DB.md) 채팅과 DB
- [DBA-070](annotated/070-예약-시스템과-DB.md) 예약 시스템과 DB

라우팅 키워드: 검색, 결제, 정산, 홈페이지, 쇼핑몰, 주문, 환불, 재고, SNS, 피드, 푸시, 배치, 크롤링, 로그인, 세션, 알림, 채팅, 읽음 처리, 예약, 좌석.

## 섹션 12. DB Professional Growth & Communication

- [DBA-999](annotated/999-DB-전문가의-성장과-커뮤니케이션.md) DB 전문가의 성장과 커뮤니케이션

라우팅 키워드: DB 학습, 기술 면접, 트레이드오프 설명, 이력서, 성과 수치, 커리어.

## 라우팅 우선순위

1. 질문의 도메인 단어와 기술 용어를 함께 찾는다.
2. 가장 구체적인 섹션에서 후보 문서의 `triggers`와 `code_signals`를 확인한다.
3. 선택한 문서의 `read_also`만 따라가 교차 주제를 보완한다.
4. 버전, 가격, 기능 지원과 한도처럼 변하는 사실은 `verified_at`과 공식 `references`를 확인한다.
