---
id: DBA-052
title: "RocksDB: DB를 만드는 사람들이 선택한 엔진"
status: stable

topics:
  - rocksdb
  - lsm-tree
  - storage-engine
  - compaction
  - write-amplification

triggers:
  - RocksDB는 일반 DB와 무엇이 다른가
  - LSM Tree가 쓰기에 왜 유리한가
  - 스토리지 엔진을 내장해야 하나

code_signals:
  - "LSM Tree"
  - "SSTable"
  - "memtable"
  - "compaction"
  - "WAL"

applies_to:
  - application-architecture
  - performance-tuning

risk_signals:
  - RocksDB를 서버형 DB처럼 직접 운영
  - 컴팩션과 쓰기 증폭을 고려하지 않음

read_when:
  - 쓰기 중심 임베디드 저장 엔진을 검토할 때
  - LSM Tree와 B-Tree의 트레이드오프를 비교할 때

read_also:
  - DBA-006
  - DBA-015
  - DBA-051

source_sections:
  - "raw/6.md:889-1045"

verified_at: 2026-09-09

references:
  - "https://rocksdb.org/"
  - "https://www.cockroachlabs.com/blog/value-separation-pebble-optimization/"

summary: >
  RocksDB의 memtable, SSTable, WAL, compaction 구조를 설명하고
  LSM Tree의 빠른 쓰기와 읽기 증폭, 운영 책임 사이의 트레이드오프를 다룬다.
---
# RocksDB: DB를 만드는 사람들이 선택한 엔진

Threads는 어떤 DB로 만들어졌을까? 2023년 7월, Meta가 출시했다.
5일 만에 1억 명이 가입했다. 역대 가장 빠른 앱 성장.
1억 명이 동시에 가입하고, 프로필을 만들고, 첫 게시글을 올렸다.
전부 쓰기 연산이다.
이 쓰기 폭풍을 받아낸 핵심 중 하나가 ZippyDB --- Meta의 분산 Key-Value 스토어다.
스토리지 엔진이 RocksDB다.
그런데 이건 Threads만의 이야기가 아니다.
CockroachDB, TiDB, YugabyteDB.
분산 데이터베이스를 만드는 사람들이 전부 RocksDB를 가져다 쓴다.
Meta가 2012년에 만든 이 작은 임베디드 엔진이 왜 이렇게 많은 곳에서 선택됐을까.
답은 간단하다. 쓰기가 빠르기 때문이다.

## 태생 --- LevelDB에서 시작

RocksDB는 Google의 LevelDB를 포크해서 만들어졌다.
2013년, Meta(당시 Facebook)가 오픈소스로 공개했다.
Engineering at Meta 블로그에서 "Under the Hood: Building and open-sourcing RocksDB"라는 제목으로 공개 배경을 설명한다.
LevelDB는 단순하고 우아했지만 Meta 규모의 워크로드를 감당하기엔 부족했다.
멀티스레드 지원이 약하고, compaction 제어가 제한적이었다.
Meta는 LevelDB의 핵심 설계를 유지하면서 대규모 서비스에 필요한 기능을 추가했다.
그게 RocksDB다.

## LSM-Tree --- 쓰기를 위해 태어난 구조

RocksDB를 이해하려면 LSM-Tree를 이해해야 한다.
Log-Structured Merge-Tree.
1996년 Patrick O'Neil의 논문에서 시작된 자료구조다.
기존 B-Tree와 비교하면 명확하다.
B-Tree는 읽기에 유리하다.
데이터가 정렬된 상태로 디스크에 저장되니 원하는 값을 빠르게 찾을 수 있다.
하지만 쓰기가 들어올 때마다 트리의 특정 위치를 찾아가서 수정해야 한다. 랜덤 I/O가 발생한다.
LSM-Tree는 반대다.
쓰기가 들어오면 디스크에 바로 쓰지 않는다.
먼저 메모리의 MemTable에 쌓는다.
MemTable이 가득 차면 디스크에 SST(Sorted String Table) 파일로 flush한다.
이건 순차 쓰기다.
랜덤 쓰기를 순차 쓰기로 바꾸는 것. 이게 LSM-Tree의 핵심이다.

## 왜 순차 쓰기가 중요한가

HDD 시절에는 당연한 이야기였다.
디스크 헤드가 물리적으로 이동해야 하니까 랜덤 쓰기가 순차 쓰기보다 100배 이상 느렸다.
SSD는 물리적 헤드가 없다. 그러면 랜덤이든 순차든 상관없지 않을까?
아니다.
SSD에서도 순차 쓰기가 빠르다.
내부적으로 페이지 단위 쓰기와 블록 단위 삭제 구조 때문에 랜덤 쓰기는 쓰기 증폭(Write Amplification)을 유발한다.
실제로 쓰려는 데이터보다 디스크에 실제로 쓰이는 데이터가 훨씬 많아진다.
쓰기 증폭이 높으면 SSD의 수명이 줄어든다.
Meta 규모에서 SSD 교체 비용은 수백만 달러 단위다.
"쓰기 패턴을 바꾸는 것"이 인프라 비용을 바꾸는 것이다.

## Compaction --- LSM-Tree의 숙제

LSM-Tree에는 대가가 있다.
쓰기는 빠르지만 시간이 지나면 SST 파일이 계속 쌓인다.
같은 키에 대한 여러 버전이 여러 파일에 흩어져 있을 수 있다.
읽기를 할 때 여러 파일을 뒤져야 하는 상황이 생긴다.
쓰기를 위해 읽기를 희생한 셈이다.
이걸 해결하는 게 compaction이다.
여러 SST 파일을 합치고, 중복을 제거하고, 정렬된 새 파일을 만든다.
RocksDB가 LevelDB를 넘어선 지점이 여기다.
Level Compaction, Universal Compaction, FIFO Compaction 등 다양한 전략을 제공한다.
워크로드에 따라 compaction 전략을 바꿀 수 있다.
쓰기가 많으면 Universal.
읽기가 중요하면 Level.
시계열 데이터면 FIFO.
"한 가지 방법으로 모든 걸 풀지 않겠다"는 설계 철학이다.

## MyRocks --- MySQL 안에 들어간 RocksDB

RocksDB는 임베디드 엔진이다.
단독으로 쓰는 데이터베이스가 아니라 다른 시스템 안에 들어가는 부품이다.
Meta는 이 부품을 MySQL의 스토리지 엔진으로 통합했다. MyRocks다.
Meta의 주력 DB는 MySQL이다.
수천 개의 MySQL 샤드가 소셜 그래프, 메시지, 타임라인을 저장한다.
기본 엔진인 InnoDB는 B-Tree 기반이다.
읽기에 강하지만 쓰기 증폭이 크고, 공간 효율이 떨어진다.
Meta 규모에서 이 비효율은 거대한 비용이다.
InnoDB를 MyRocks로 교체했을 때 스토리지 사용량이 절반으로 줄었다.
같은 데이터, 같은 MySQL, 같은 쿼리.
엔진만 바꿨을 뿐인데 저장 공간이 반으로 줄어든다.
LSM-Tree의 압축 친화적 구조와 Zstandard 압축 알고리즘의 조합이다.

## Messenger --- HBase에서 MyRocks로

Meta의 Messenger는 원래 HBase를 썼다.
HBase도 LSM-Tree 기반이지만 Hadoop 위에서 돌아가는 무거운 시스템이다.
HBase에서 MyRocks로 옮기면서 스토리지 소비를 90% 줄였다. 데이터 유실 없이.
90%가 나온 이유는 세 가지다.

1. 스키마 단순화. HBase의 복잡한 row-key 구조를 MySQL의 단순한 테이블로 재설계했다.
2. Zstandard 압축. 높은 압축률과 빠른 속도를 동시에 달성한다.
3. 복제 팩터 축소. HBase의 복제 팩터 6에서 MyRocks의 3으로.

아키텍처가 다르면 같은 데이터도 필요한 공간이 달라진다.

## RocksDB를 품은 분산 데이터베이스들

RocksDB가 Meta 안에서만 쓰이면 그저 "Facebook의 사내 도구"로 남았을 것이다.
오픈소스로 풀린 뒤 전혀 다른 궤도를 탔다.

[CockroachDB]
분산 SQL. PostgreSQL 호환.
내부 스토리지는 RocksDB(현재는 포크한 Pebble).

[TiDB]
분산 HTAP. MySQL 호환.
스토리지 레이어 TiKV가 RocksDB 위에서 동작한다.

[YugabyteDB]
분산 DB. PostgreSQL 호환.
자체 스토리지 엔진 DocDB가 RocksDB 포크다.

패턴이 보인다.
스토리지 엔진을 처음부터 만들기보다 RocksDB를 가져다 쓰는 게 합리적이다.
검증된 쓰기 성능, 압축 효율, 안정성.
10년 넘게 Meta 규모에서 수조 건의 데이터를 처리해 온 엔진이다.

## B-Tree vs LSM-Tree --- 영원한 트레이드오프

RocksDB가 모든 곳에 적합한 건 아니다.
LSM-Tree의 태생적 한계가 있다.

- 읽기 증폭(Read Amplification).
  - 여러 레벨의 SST 파일을 뒤져야 한다.
  - Bloom Filter로 완화하지만 없앨 수는 없다.
- 쓰기 증폭(Write Amplification).
  - compaction이 데이터를 읽고 합치고 다시 쓴다.
  - 쓰기를 위해 쓰기를 희생하는 아이러니.
- 공간 증폭(Space Amplification).
  - 같은 키의 여러 버전이 동시에 존재한다.
  - 두 개를 줄이면 나머지가 커진다.
  - RUM conjecture다.

B-Tree(InnoDB)는 읽기 증폭을 최소화한다.
LSM-Tree(RocksDB)는 쓰기 증폭을 최소화한다.
어느 쪽이 낫다는 게 아니다. 워크로드에 따라 답이 달라진다.
읽기가 많으면 InnoDB. 쓰기가 많으면 MyRocks.
DBA는 이 판단을 내려야 하는 사람이다.

## DBA 관점에서의 정리

RocksDB를 직접 운영할 DBA는 많지 않다.
임베디드 엔진이니까 대부분은 CockroachDB나 TiDB를 통해 간접적으로 만나게 된다.
하지만 그 안에서 무슨 일이 일어나는지 이해하고 있어야 한다.
compaction이 밀리면 왜 읽기가 느려지는지.
write stall이 왜 발생하는지.
Bloom Filter의 false positive가 쿼리 성능에 어떤 영향을 주는지.
MyRocks를 쓰는 환경이라면 더 직접적이다.
InnoDB와 MyRocks의 특성 차이를 모르면 인덱스 설계부터 쿼리 패턴까지 전부 빗나간다.
Meta는 폭발적 쓰기와 페타바이트 규모에 맞는 엔진이 없어서 직접 만들었다.
그 엔진이 분산 데이터베이스 생태계 전체의 기반이 됐다.
도메인이 도구를 만들고, 도구가 생태계를 만들고, 생태계가 다시 새로운 도메인을 가능하게 한다.
RocksDB는 그 순환의 한가운데에 있다.
