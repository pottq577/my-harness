---
id: DBA-038
title: "왜 분석 쿼리는 RDBMS에서 느린가: Athena, Snowflake, BigQuery의 구조"
status: stable

topics:
  - analytic-query
  - data-warehouse
  - snowflake
  - bigquery
  - athena
  - olap

triggers:
  - 분석 쿼리를 RDBMS에서 돌리려다 느릴 때
  - 대용량 데이터를 OLAP으로 옮겨야 하는 이유
  - 웨어하우스의 컬럼형 저장 구조
  - 파티셔닝과 프루닝이 오는 과정
  - Snowflake/BigQuery/Athena 선택 기준

code_signals:
  - "COUNT(*)"
  - "GROUP BY"
  - "PARQUET"
  - "STREAMING"
  - "PARTITION"
  - "S3"
  - "two-phase commit"

applies_to:
  - analytics
  - performance-tuning
  - schema-design

risk_signals:
  - 행 단위 RDBMS에서 분석 쿼리 강행
  - 대용량 조인과 집계가 운영 트랜잭션과 섞임
  - 파티션키로 프루닝 되지 않는 쿼리 구조

read_when:
  - 분석 쿼리 성능이 나오지 않을 때
  - 데이터 웨어하우스 도입 타당성을 검토할 때
  - 파티셔닝과 프루닝 전략을 설계할 때

read_also:
  - DBA-009
  - DBA-011
  - DBA-005

source_sections:
  - "raw/3.md:1624-끝"
  - "raw/6.md:3-221 (표현 차이가 있는 중복)"

summary: >
  OLTP와 OLAP의 저장 구조 차이를 통해 행 단위 RDBMS가 분석 쿼리에
  취약한 이유를 설명한다. 컬럼형 저장과 파티셔닝 프루닝, 수직/수평 확장의
  구조로 Athena, Snowflake, BigQuery를 비교해 분석 워크로드의 선택 기준을
  제시한다.
---
# 왜 분석 쿼리는 RDBMS에서 느린가: Athena, Snowflake, BigQuery의 구조

10억 행 테이블에서

```sql
SELECT AVG(amount) FROM orders WHERE created_at >= '2026-01-01'
```

을 실행한다.
MySQL에서 돌리면 수십 분이 걸린다.
BigQuery에서 돌리면 수 초에 끝난다. 같은 SQL인데 왜 이렇게 다를까.
답은 "DB가 좋아서"가 아니다. 데이터를 저장하는 방식이 근본적으로 다르기 때문이다.

## 행 저장이라는 기본값

모든 건 저장 방식에서 시작한다.
MySQL, PostgreSQL 같은 RDBMS는 행 단위(row-oriented)로 데이터를 저장한다.
하나의 행이 디스크에 연속으로 놓인다.

```text
[id=1, name="김철수", amount=50000, created_at="2026-01-15"]
[id=2, name="이영희", amount=30000, created_at="2026-02-20"]
[id=3, name="박민수", amount=70000, created_at="2026-01-08"]
```

한 사람의 정보를 전부 읽으려면 한 번의 디스크 읽기로 충분하다.

```sql
SELECT * FROM users WHERE id = 1
```

에 최적화된 구조다.

## 열 저장이라는 발상의 전환

BigQuery, Snowflake, Athena는 열 단위(column-oriented)로 저장한다.

```text
[id]: 1, 2, 3, ...
[name]: "김철수", "이영희", "박민수", ...
[amount]: 50000, 30000, 70000, ...
[created_at]: "2026-01-15", "2026-02-20", "2026-01-08", ...
```

같은 컬럼의 값들이 디스크에 연속으로 놓인다.
100개 컬럼 중 2개만 필요한 분석 쿼리라면 98개 컬럼은 아예 읽지 않는다.
이 차이가 모든 성능 격차의 출발점이다.

## 왜 열 저장이 분석에 유리한가

분석 쿼리의 특성을 보자.

```sql
SELECT AVG(amount) FROM orders WHERE created_at >= '2026-01-01'
```

이 쿼리가 필요한 컬럼은 딱 두 개다. amount와 created_at.
100개 컬럼이 있는 테이블이라도 98개 컬럼은 읽을 필요가 없다.
행 저장에서는?
amount를 읽으려면 그 행의 모든 컬럼을 디스크에서 읽어야 한다.
`id, name, email, address, phone...` 필요 없는 98개 컬럼까지 전부.
10억 행이면 10억 행의 모든 컬럼을 읽는다.
열 저장에서는?
amount 컬럼만 읽는다. created_at 컬럼만 읽는다. 나머지 98개 컬럼은 아예 디스크에서 읽지 않는다.
I/O 양이 50분의 1로 줄어든다. 100개 컬럼 중 2개만 읽으니까.
이게 "10배 빠르다"가 아니라 "100배 빠르다"가 가능한 이유다.

## 압축이라는 두 번째 무기

열 저장의 두 번째 장점은 압축이다.
같은 컬럼의 값은 같은 타입이다. amount에는 숫자만, created_at에는 날짜만, status에는 몇 가지 값만 반복된다.
같은 타입의 데이터가 연속으로 놓여 있으면 압축률이 극적으로 올라간다.

[Run-Length Encoding]
status에 'active'가 100만 번 반복되면 ('active', 1000000)으로 저장한다.
100만 개를 하나로 줄이는 셈이다.

[Dictionary Encoding]
값이 'active', 'inactive', 'pending' 세 가지면 사전을 만든다. 0, 1, 2.
문자열을 숫자로 바꾸는 것만으로 공간이 줄어든다.

## Delta Encoding과 Capacitor

[Delta Encoding]
created_at이 시간 순서로 정렬돼 있으면 값 자체 대신 이전 값과의 차이만 저장한다.
차이값은 원래 값보다 훨씬 작다.
BigQuery의 Capacitor 포맷은 이런 인코딩 기법들을 조합하고, 행의 순서까지 재배치(record reordering)해서 압축률을 극대화한다.
압축된 데이터는 디스크에서 더 적게 읽힌다. 네트워크를 덜 탄다. 메모리에 더 많이 올라간다.
모든 단계에서 빨라진다.

## BigQuery --- Google의 10년

BigQuery의 뿌리는 Dremel이다.
2010년 Google이 발표한 논문에서 시작된, 수십 페타바이트를 대화형으로 분석하기 위한 시스템이다.
Dremel 쿼리 엔진이 쿼리를 실행 트리로 분해한다.
리프 노드(slot)가 데이터를 읽고, 브랜치 노드(mixer)가 결과를 집계한다.
수천 대의 머신이 동시에 읽고, 집계하고, 합친다.
스토리지는 Colossus, 네트워크는 Jupiter, 컴퓨팅은 Borg. 이 세 인프라가 분리돼 있다.
스토리지와 컴퓨팅의 분리. 쿼리를 보내면 컴퓨팅 리소스가 동적으로 할당되고, 끝나면 반납된다.
서버를 프로비저닝할 필요가 없다. Serverless.

## Snowflake --- 3층 아키텍처

Snowflake는 스토리지와 컴퓨팅의 분리를 상용 제품으로 구현한 첫 클라우드 데이터 웨어하우스다.

[Storage Layer]
데이터는 Micro-Partition(50MB~500MB) 단위로 열 저장된다.
파티셔닝은 자동이다. 스키마 정의가 필요 없다.

[Compute Layer]
가상 웨어하우스가 쿼리를 실행한다. 웨어하우스는 독립적이다.
분석팀과 대시보드 서비스가 같은 데이터를 읽지만 서로의 성능에 영향을 주지 않는다.

[Cloud Services Layer]
인증, 메타데이터 관리, 쿼리 최적화, 접근 제어.
컴퓨팅과 분리된 독립 레이어에서 동작한다.

## Athena --- S3 위의 쿼리 엔진

Athena는 자체 스토리지가 없다. S3에 있는 데이터를 직접 쿼리하는 서비스다.
데이터를 "로드"하지 않는다.
S3에 Parquet 파일을 올려놓고, 스키마를 정의하고, SQL을 던진다.
쿼리 엔진은 Trino 기반이다.
코디네이터가 계획을 세우고, 워커 노드가 S3에서 데이터를 읽어 처리한다.
모든 처리가 인메모리 파이프라인이다.
강점은 "있는 데이터를 그대로 쿼리한다"는 것이다.
로그, 이벤트, JSON, CSV, Parquet. ETL 없이 바로 분석할 수 있다.
단, 성능은 포맷에 좌우된다. CSV 10TB는 느리고, Parquet로 변환하면 열 단위 접근 + 압축의 이점을 그대로 얻는다.

## 자원 경합과 수평 확장의 벽

RDBMS가 분석에 약한 진짜 이유는 단순히 "행 저장이니까"가 전부가 아니다.

[자원 경합]
RDBMS는 OLTP를 위해 설계됐다.
INSERT, UPDATE, DELETE가 초당 수천 건 들어오는 환경.
분석 쿼리가 10억 행을 풀스캔하면 Buffer Pool과 I/O 대역폭을 독점하고, 서비스 쿼리가 밀린다.
BigQuery, Snowflake, Athena는 분석 전용이다.
서비스 DB와 물리적으로 분리돼 있어서 아무리 무거운 쿼리를 돌려도 서비스에 영향이 없다.

[수평 확장]
RDBMS의 분석 쿼리는 하나의 인스턴스에서 실행된다.
그 서버의 물리적 한계가 쿼리의 한계다.
분석 엔진은 분산 실행한다.
10억 행을 1대가 읽으면 10분.
1000대가 나눠 읽으면 0.6초.

## 비용 모델의 전환

RDBMS는 서버가 항상 켜져 있다. 분석을 안 해도 비용이 나간다.
BigQuery는 스캔한 데이터 양에 비례해서 과금된다. 쿼리를 안 돌리면 스토리지 비용만 나간다.
Snowflake는 웨어하우스 실행 시간당 과금이다. 안 쓸 때는 자동으로 꺼진다.
Athena도 스캔한 데이터 양에 비례한다.
Parquet로 저장하면 스캔량이 줄어서 비용도 줄어든다.
"쓴 만큼만 낸다"는 모델이 대용량 분석에 훨씬 합리적이다.

## 세 서비스의 차이

같은 "분석용 DB"지만 세 서비스의 포지션은 다르다.

[BigQuery]
Google 인프라 위의 완전 서버리스.
Capacitor 포맷 + Dremel 엔진으로 자동 분산 실행.
적합: 페타바이트 스케일 분석, ML 파이프라인.

[Snowflake]
멀티 클라우드(AWS, GCP, Azure).
워크로드 격리와 데이터 거버넌스가 강점.
적합: 여러 팀이 같은 데이터를 다른 용도로 쓰는 환경.

[Athena]
자체 스토리지 없이 S3 직접 쿼리. Trino 기반.
적합: 이미 S3에 데이터가 있는 AWS 환경, 애드혹 분석.

## Parquet이라는 공통 언어

세 서비스 모두 Apache Parquet을 지원한다.
BigQuery는 자체 Capacitor 포맷이 기본이지만 Parquet 읽기를 지원한다.
Parquet은 열 단위 저장 포맷의 사실상 표준이다.
Parquet으로 데이터를 저장하면:

- 열 단위 접근 → 필요한 컬럼만 읽기
- 내장 압축 → Snappy, Zstd 등
- 중첩 구조 지원 → JSON 같은 데이터도 가능
- Row Group 단위 → 병렬 읽기에 적합

CSV 10TB를 Parquet으로 변환하면 1~2TB로 줄어드는 경우가 흔하다.
Athena에서 CSV를 쿼리하면 10TB를 스캔해서 비용이 50달러.
같은 데이터를 Parquet으로 바꾸면 200GB만 스캔해서 비용이 1달러.
포맷을 바꾸는 것만으로 성능과 비용이 동시에 개선된다.

## DBA 관점에서의 정리

"분석 쿼리가 느려요." 이 말을 들었을 때 RDBMS에서 인덱스를 추가하거나 쿼리를 튜닝하는 건 근본적 해결이 아닐 수 있다.
10억 행에서 GROUP BY + AVG를 하는 건 행 저장 기반 DB가 구조적으로 느린 작업이다.
아무리 튜닝해도 열 저장 + 분산 실행을 이길 수 없다.
올바른 질문은 이것이다. "이 쿼리는 OLTP인가, OLAP인가?"
OLTP면 RDBMS.
`WHERE id = 1`로 한 행을 빠르게 찾는 일.
INSERT, UPDATE가 초당 수천 건 들어오는 일.
OLAP면 분석 엔진.
수억 행에서 집계하는 일.
여러 차원으로 그룹핑하고 비교하는 일.

여기서는 BigQuery, Snowflake, Athena가 맞다.
"MySQL이 느린 게 아니다. MySQL에게 시킬 일이 아닌 걸 시킨 것이다."
망치에게 나사를 박으라고 하면 못 박는 게 아니라 나사가 부러진다.
도구를 탓하기 전에 쓰임새를 먼저 확인해야 한다.
