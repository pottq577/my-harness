# DBA Knowledge Base 문서 인덱스

`annotated/` 아래 72개 문서의 파일 번호와 문서 ID를 1:1로 고정한 매핑표다.
ID는 이후 절대 변경하지 않는다.

| id      | file                                                                     | title                                                                                        |
| ------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| DBA-001 | annotated/001-NULL을-이해한다는-것.md                                    | NULL을 이해한다는 것: WHERE a != 1 이 NULL을 빠뜨리는 이유                                   |
| DBA-002 | annotated/002-FK-없이-사는-법.md                                         | FK 없이 사는 법: 외래키를 안 쓰는 팀이 많아진 이유                                           |
| DBA-003 | annotated/003-DB에서-JSON을-쓴다는-것.md                                 | DB에서 JSON을 쓴다는 것: 장점, 단점, 가이드라인                                              |
| DBA-004 | annotated/004-Collation의-실체.md                                        | Collation의 실체: 같은 글자가 다르게 정렬되는 이유                                           |
| DBA-005 | annotated/005-도메인이-다르면-DB도-달라야-한다.md                        | 도메인이 다르면 DB도 달라야 한다 --- 1초의 복구와 1원의 정합성                                |
| DBA-006 | annotated/006-인덱스의-진짜-동작-원리.md                                 | 인덱스의 진짜 동작 원리: B-tree, 순서, 커버링의 실체                                         |
| DBA-007 | annotated/007-인덱스의-해부학.md                                         | 인덱스의 해부학: B-Tree에서 GIN까지, 그리고 안 타는 이유                                     |
| DBA-008 | annotated/008-옵티마이저가-보는-세상.md                                  | 옵티마이저가 보는 세상: 쿼리가 느린 건 DB가 다르게 생각하기 때문이다                         |
| DBA-009 | annotated/009-대용량-SELECT의-기술.md                                    | 대용량 SELECT의 기술: 1억 건에서 원하는 데이터를 꺼내는 법                                   |
| DBA-010 | annotated/010-'다음-페이지'가-점점-느려지는-이유.md                      | '다음 페이지'가 점점 느려지는 이유: OFFSET 없이 페이지 번호를 만드는 법                      |
| DBA-011 | annotated/011-느린-쿼리를-쪼개는-기술.md                                 | 느린 쿼리를 쪼개는 기술: 하나보다 둘이 빠른 이유                                             |
| DBA-012 | annotated/012-검색-서비스와-DB.md                                        | 검색 서비스와 DB: 검색은 DB의 일이 아니다                                                    |
| DBA-013 | annotated/013-트랜잭션-격리-수준의-실체.md                               | 트랜잭션 격리 수준의 실체: Read Committed에서 Serializable까지                               |
| DBA-014 | annotated/014-락의-지형도.md                                             | 락의 지형도: Row Lock, Gap Lock, Advisory Lock                                               |
| DBA-015 | annotated/015-Undo-Log-vs-Redo-Log.md                                    | Undo Log vs Redo Log: 되돌리는 기록과 다시 쓰는 기록                                         |
| DBA-016 | annotated/016-트랜잭션-로그의-세계.md                                    | 트랜잭션 로그의 세계: Binlog, WAL, Archive Log                                               |
| DBA-017 | annotated/017-DB가-이벤트를-발행해야-할-때.md                            | DB가 이벤트를 발행해야 할 때: 트랜잭션과 메시지 사이의 설계                                  |
| DBA-018 | annotated/018-결제와-DB.md                                               | 결제와 DB: 1원이 틀리면 안 되는 세계                                                         |
| DBA-019 | annotated/019-ORM이-만드는-쿼리의-실체.md                                | ORM이 만드는 쿼리의 실체: JPA가 보내는 SQL을 본 적 있는가                                    |
| DBA-020 | annotated/020-바이브코더들을-위한-ORM-생존리스트.md                      | 바이브코더들을 위한 ORM 생존리스트                                                           |
| DBA-021 | annotated/021-프로시저는-아직도-쓸-만한가.md                             | 프로시저는 아직도 쓸 만한가: DB에 로직을 넣는다는 것                                         |
| DBA-022 | annotated/022-커넥션-풀의-안쪽.md                                        | 커넥션 풀의 안쪽: 왜 DB가 멀쩡한데 연결이 안 되는가                                          |
| DBA-023 | annotated/023-바이브코딩을-하더라도-DB-구조-변경을-안전하게-하는-방법.md | 바이브코딩을 하더라도 DB 구조 변경을 안전하게 하는 방법: ALTER TABLE 앞뒤로 확인해야 할 것들 |
| DBA-024 | annotated/024-대용량-DML의-기술-.md                                      | 대용량 DML의 기술: 1억 건을 지우는 세 가지 방법                                              |
| DBA-025 | annotated/025-캐시는-언제부터-쓰면-될까.md                               | 캐시는 언제부터 쓰면 될까: RDBMS에서 Redis로 가는 시점                                       |
| DBA-026 | annotated/026-Redis-vs-Memcached.md                                      | Redis vs Memcached: 캐시만 할 거면 Memcached가 맞다                                          |
| DBA-027 | annotated/027-Redis에서-Big-Key를-피해야-하는-이유.md                    | Redis에서 Big Key를 피해야 하는 이유                                                         |
| DBA-028 | annotated/028-Kafka-vs-RabbitMQ.md                                       | Kafka vs RabbitMQ: 메시지를 보내는 것과 로그를 남기는 것의 차이                              |
| DBA-029 | annotated/029-Wait-Event로-읽는-Aurora-MySQL.md                          | Wait Event로 읽는 Aurora MySQL: 느릴 때 진짜 원인을 찾는 법                                  |
| DBA-030 | annotated/030-백업과-복구의-실체.md                                      | 백업과 복구의 실체: 풀백업은 쉬운데 복구는 왜 어려운가                                       |
| DBA-031 | annotated/031-Physical-vs-Logical-Backup.md                              | Physical vs Logical Backup: 백업이 빠르면 복구는 느리다                                      |
| DBA-032 | annotated/032-DB-장애-대응의-기술.md                                     | DB 장애 대응의 기술: 탐지에서 회고까지, DBA는 무엇을 하는가                                  |
| DBA-033 | annotated/033-홈페이지와-DB.md                                           | 홈페이지와 DB: 간단해 보이는 것이 복잡해지는 순간                                            |
| DBA-034 | annotated/034-쇼핑몰과-DB.md                                             | 쇼핑몰과 DB: 장바구니 하나가 이렇게 어려운 이유                                              |
| DBA-035 | annotated/035-게시판에서-SNS로.md                                        | 게시판에서 SNS로: 피드가 DB를 바꾸는 순간                                                    |
| DBA-036 | annotated/036-푸시-알림이-DB에-주는-영향.md                              | 푸시 알림이 DB에 주는 영향: 1000만 명에게 쿠폰을 보내면 생기는 일                            |
| DBA-037 | annotated/037-크롤링이-DB에-주는-영향.md                                 | 크롤링이 DB에 주는 영향: 검색엔진이 서비스를 죽이는 순간                                     |
| DBA-038 | annotated/038-왜-분석-쿼리는-RDBMS에서-느린가.md                         | 왜 분석 쿼리는 RDBMS에서 느린가: Athena, Snowflake, BigQuery의 구조                          |
| DBA-039 | annotated/039-인조키를-알고-써야-한다.md                                 | 인조키를 알고 써야 한다: DB의 특성에 따라 달라지는 키 전략                                  |
| DBA-040 | annotated/040-데이터베이스-OOM의-실체.md                                 | 데이터베이스 OOM의 실체: t4g.medium이 자꾸 재부팅되는 이유                                  |
| DBA-041 | annotated/041-Soft-Delete-vs-Hard-Delete.md                              | Soft Delete vs Hard Delete: 지우는 척하면 인덱스가 망가진다                                 |
| DBA-042 | annotated/042-레플리케이션과-페일오버.md                                 | 레플리케이션과 페일오버: 복제는 쉬운데 전환은 왜 어려운가                                   |
| DBA-043 | annotated/043-Load-Average와-AAS.md                                      | Load Average와 AAS: DB 부하를 읽는 두 개의 눈금                                             |
| DBA-044 | annotated/044-주문-테이블-설계.md                                        | 주문 테이블 설계: orders 하나로 시작하면 첫 환불에서 깨진다                                 |
| DBA-045 | annotated/045-로그인이-DB에-주는-영향.md                                 | 로그인이 DB에 주는 영향: 출근 시간에 서버가 느려지는 이유                                   |
| DBA-046 | annotated/046-SQL과-NoSQL-선택-기준.md                                   | SQL과 NoSQL: 정답 대신 요구사항으로 선택하는 법                                             |
| DBA-047 | annotated/047-MySQL-vs-PostgreSQL.md                                     | MySQL vs PostgreSQL: 뭘 고르든 후회하는 이유                                                |
| DBA-048 | annotated/048-JPA와-MyBatis.md                                           | JPA와 MyBatis: 프레임워크가 아니라 철학의 차이다                                            |
| DBA-049 | annotated/049-Aurora-vs-RDS.md                                           | Aurora vs RDS: 비싸도 Aurora를 써야 하는 순간                                               |
| DBA-050 | annotated/050-JSON을-잘-쓴다는-것.md                                     | JSON을 잘 쓴다는 것: 구조, 네이밍, 흔한 실수                                                |
| DBA-051 | annotated/051-Netflix가-Cassandra를-선택한-이유.md                        | Netflix: 초당 백만 쓰기가 Cassandra를 선택한 이유                                           |
| DBA-052 | annotated/052-RocksDB.md                                                  | RocksDB: DB를 만드는 사람들이 선택한 엔진                                                   |
| DBA-053 | annotated/053-Supabase에서-자체-DB로-전환하기.md                          | Supabase에서 자체 DB로 넘어가야 할 때는 언제인가?                                           |
| DBA-054 | annotated/054-MongoDB-설계-패턴.md                                       | MongoDB 설계 패턴: 도메인이 구조를 결정한다                                                 |
| DBA-055 | annotated/055-GC가-데이터베이스를-멈추는-순간.md                          | GC가 데이터베이스를 멈추는 순간: Stop the World의 실체                                     |
| DBA-056 | annotated/056-락을-이해한다는-것.md                                       | 락을 이해한다는 것: 데드락, 락 대기, 그리고 면접에서의 깊이                               |
| DBA-057 | annotated/057-DocumentDB-쿼리-플래너.md                                   | DocumentDB 쿼리 플래너: v1과 v2는 왜 이렇게 다른가                                         |
| DBA-058 | annotated/058-Flyway-vs-Liquibase.md                                      | Flyway vs Liquibase: DB 마이그레이션, 단순함이 답인가                                     |
| DBA-059 | annotated/059-빅오-표기법.md                                              | 빅오 표기법: 코드의 속도를 말하는 언어                                                     |
| DBA-060 | annotated/060-마이크로서비스-전환이-DB에-주는-영향.md                      | 마이크로서비스 전환이 DB에 주는 영향: 모놀리스를 쪼개면 JOIN이 사라진다                   |
| DBA-061 | annotated/061-B-Tree-vs-LSM-Tree.md                                       | B-Tree vs LSM-Tree: 읽기를 위한 구조와 쓰기를 위한 구조                                   |
| DBA-062 | annotated/062-쿼리-플래너의-머릿속.md                                     | 쿼리 플래너의 머릿속: 데이터베이스는 어떻게 길을 고르는가                                 |
| DBA-063 | annotated/063-알림-시스템과-DB.md                                         | 알림 시스템과 DB: 보내는 건 쉬운데 안 보내는 게 어렵다                                    |
| DBA-064 | annotated/064-낙관적-락-vs-비관적-락.md                                   | Optimistic Lock vs Pessimistic Lock: 충돌을 막느냐, 충돌을 받아들이느냐                  |
| DBA-065 | annotated/065-커넥션-풀이-필요한-진짜-이유.md                              | 커넥션 풀이 필요한 진짜 이유: HikariCP, pgBouncer, 그리고 적정 사이즈                     |
| DBA-066 | annotated/066-무중단-스키마-변경.md                                       | 무중단 스키마 변경: ALTER TABLE이 서비스를 멈추는 이유                                    |
| DBA-067 | annotated/067-Aurora-MySQL-failover.md                                    | Aurora MySQL failover 62초의 비밀: JDBC URL 한 줄이 만드는 차이                           |
| DBA-068 | annotated/068-Upsert.md                                                   | 당신의 Upsert는 진짜로 쓰고 있는가                                                         |
| DBA-069 | annotated/069-채팅과-DB.md                                                | 채팅과 DB: 읽었는지 안 읽었는지, 그게 이렇게 어려운 일                                     |
| DBA-070 | annotated/070-예약-시스템과-DB.md                                         | 예약 시스템과 DB: 같은 시간에 두 명이 예약하면 생기는 일                                  |
| DBA-071 | annotated/071-ID를-만든다는-것.md                                         | ID를 만든다는 것: AUTO_INCREMENT가 1, 2, 3이 아닌 이유                                    |
| DBA-999 | annotated/999-DB-전문가의-성장과-커뮤니케이션.md                          | DB 전문가의 성장과 커뮤니케이션: 학습, 면접, 이력서                                         |

## 안내

- 72개 문서는 모두 `annotated/` 아래에 있고 frontmatter를 갖는다.
- AI가 문서를 읽을 때는 frontmatter가 있는 `annotated/`의 파일을 우선 읽는다.
- 문서를 검색할 때는 `knowledge-map.md`의 라우팅을 먼저 따른다.
