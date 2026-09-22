---
id: DBA-061
title: "B-Tree vs LSM-Tree: 읽기를 위한 구조와 쓰기를 위한 구조"
status: stable

topics:
  - b-tree
  - lsm-tree
  - storage-engine
  - compaction
  - rocksdb
  - cassandra

triggers:
  - B-Tree와 LSM-Tree의 차이가 뭔가
  - RocksDB나 Cassandra가 쓰기에 강한 이유
  - Write Amplification과 Read Amplification이 뭔가
  - 로그성 데이터 저장 엔진을 어떻게 고르나

code_signals:
  - "MemTable"
  - "SST"
  - "compaction"
  - "Bloom Filter"
  - "write amplification"
  - "read amplification"

applies_to:
  - domain-modeling
  - performance-tuning
  - application-architecture
  - technical-interview

risk_signals:
  - 로그성 데이터를 B-Tree 엔진에 그대로 저장
  - 쓰기 헤비 워크로드에서 compaction 지연이 흔들림
  - 엔진 선택 없이 워크로드와 무관하게 DB 결정

read_when:
  - 스토리지 엔진이나 DB를 선택할 때
  - 쓰기 헤비 워크로드의 지연 문제를 분석할 때
  - Cassandra/RocksDB 계열의 동작 원리를 이해하고 싶을 때

read_also:
  - DBA-005
  - DBA-047
  - DBA-051
  - DBA-052

source_sections:
  - "raw/7.md:1683-1863"

summary: >
  B-Tree와 LSM-Tree의 원리와 트레이드오프를 다룬다. in-place update 대비
  순차 쓰기, compaction의 대가, Write/Read/Space Amplification, compaction
  전략과 실제 DB 진영(OLTP vs 쓰기 헤비) 선택 기준을 설명한다.
---
# B-Tree vs LSM-Tree: 읽기를 위한 구조와 쓰기를 위한 구조

데이터베이스에 데이터를 넣으면 어딘가에 저장된다.
그 "어딘가"의 구조가 읽기와 쓰기의 성능을 결정한다.
B-Tree는 읽기를 위해 설계됐다.
LSM-Tree는 쓰기를 위해 설계됐다.
MySQL과 PostgreSQL은 B-Tree를 선택했다.
RocksDB와 Cassandra는 LSM-Tree를 선택했다.
같은 데이터를 저장하는데 왜 구조가 달라야 할까.

## B-Tree의 원리

B-Tree는 1972년에 등장한 자료구조다.
50년이 넘었지만 여전히 대부분의 RDBMS가 이걸 쓴다.
정렬된 트리 구조다.
루트에서 시작해서 중간 노드를 거쳐 리프 노드에 도달한다.
리프 노드에 실제 데이터(또는 포인터)가 있다.
높이가 보통 3~4다.
수억 건의 데이터에서도 3~4번의 디스크 읽기면 원하는 값을 찾는다.
읽기에 강한 이유가 여기 있다.
데이터가 정렬된 상태로 제자리에 있으니 찾아가는 경로가 짧다.

## B-Tree의 쓰기 방식

B-Tree는 in-place update다.
데이터가 바뀌면 해당 위치를 찾아가서 그 자리에서 직접 수정한다.
INSERT가 들어오면 정렬 순서에 맞는 리프 노드를 찾는다.
공간이 있으면 끼워 넣는다.
없으면 노드를 분할(split)한다.
UPDATE도 마찬가지.
해당 행이 있는 페이지를 찾아가서 그 자리에서 값을 고친다.
문제는 이게 랜덤 I/O라는 것이다.
데이터가 디스크 여기저기에 흩어져 있으니 매번 다른 위치를 찾아가야 한다.

## LSM-Tree의 원리

LSM-Tree는 1996년 O'Neil의 논문에서 시작됐다.
Log-Structured Merge-Tree.
이름에 핵심이 다 들어 있다.
쓰기가 들어오면 디스크에 바로 쓰지 않는다.
메모리의 MemTable에 먼저 쌓는다.
MemTable이 가득 차면 정렬된 파일(SST)로 디스크에 flush한다.
이건 순차 쓰기다.
파일을 처음부터 끝까지 쭉 쓴다. 랜덤 I/O가 아니다.
랜덤 쓰기를 순차 쓰기로 바꾼다.
이게 LSM-Tree가 쓰기에 강한 이유다.

## Compaction이라는 대가

LSM-Tree에는 공짜가 없다. SST 파일이 계속 쌓인다.
같은 키가 여러 파일에 흩어진다.
user_id=1의 값이 레벨 0에도 있고 레벨 2에도 있고 레벨 3에도 있다.
읽을 때 여러 파일을 뒤져야 한다.
최신 값을 찾으려면 최악의 경우 모든 레벨을 전부 탐색해야 한다.
이걸 해결하는 게 compaction이다.
여러 파일을 합치고 중복을 제거한다.
하지만 compaction 자체가 I/O를 소모한다.
데이터를 읽고, 합치고, 다시 쓴다.
쓰기 속도를 얻는 대신 뒤에서 compaction 비용을 치르는 것이다.

## Write Amplification

같은 데이터를 디스크에 몇 번 쓰는가. 이걸 Write Amplification이라 부른다.
B-Tree의 Write Amplification.
데이터를 한 번 쓰면 페이지 단위로 기록된다.
8KB 중 1바이트만 바꿔도 8KB를 다시 쓴다.
WAL에도 기록하니 최소 2배다.
LSM-Tree의 Write Amplification.
MemTable flush가 1회.
레벨 0에서 1로 compaction이 1회.
레벨 1에서 2로 또 1회.
레벨이 깊어질수록 같은 데이터가 반복 기록된다.
10~30배까지 올라갈 수 있다.
그런데 왜 LSM-Tree가 쓰기에 빠른가.
순차 쓰기이기 때문이다.
횟수가 많아도 순차가 랜덤보다 빠르다.

## Read Amplification

하나의 값을 읽기 위해 몇 번 디스크를 읽는가.

[B-Tree]
트리 높이만큼 읽으면 된다.
3~4회. 예측 가능하다.
인덱스가 정렬돼 있으니 경로가 명확하다.

[LSM-Tree]
최악의 경우 모든 레벨을 탐색한다.
Bloom Filter가 없으면 실용성이 떨어진다.
Bloom Filter는 "이 파일에 이 키가 없다"를 높은 확률로 알려준다.
없는 파일을 건너뛰어서 탐색 횟수를 줄인다.
Point lookup은 Bloom Filter로 완화된다.
하지만 Range scan은 여전히 비싸다.
여러 파일에서 정렬된 결과를 합쳐야 하기 때문이다.

## Space Amplification

같은 데이터를 저장하는 데 얼마나 공간을 쓰는가.
B-Tree는 페이지 단위 할당이다.
페이지가 반만 차 있어도 한 페이지를 점유한다.
삭제 후에도 공간이 바로 회수되지 않는다.
fragmentation이 쌓인다.
LSM-Tree는 compaction 전까지 같은 키의 여러 버전이 공존한다.
하지만 compaction이 끝나면 깔끔해진다.
압축도 잘 먹는다. 정렬된 데이터는 압축 효율이 높기 때문이다.
Meta가 InnoDB를 MyRocks로 교체했을 때 스토리지가 절반으로 줄어든 이유가 여기에 있다.

## Compaction 전략

LSM-Tree의 성격은 compaction 전략이 결정한다.

[Leveled Compaction]
각 레벨의 크기가 10배씩 커진다.
레벨 간 겹침이 없다.
읽기 증폭이 낮다. 쓰기 증폭이 높다.
RocksDB의 기본값이다.

[Size-Tiered Compaction]
비슷한 크기의 파일끼리 합친다.
쓰기 증폭이 낮다. 공간 증폭이 높다.
Cassandra의 기본값이었다.

[Universal Compaction]
RocksDB가 제공하는 또 다른 전략.
쓰기가 극단적으로 많은 워크로드에 적합하다.
전략 선택이 곧 트레이드오프 선택이다.

## 실제로 누가 무엇을 쓰는가

[B-Tree 진영]
MySQL(InnoDB), PostgreSQL, Oracle, SQL Server.
전통적인 OLTP 데이터베이스는 전부 B-Tree다.
읽기 비중이 높고 트랜잭션 정합성이 중요한 영역.

[LSM-Tree 진영]
RocksDB, LevelDB, Cassandra, HBase, ScyllaDB.
쓰기 비중이 높거나 대규모 분산이 필요한 영역.
로그, 시계열, 메시지, IoT 데이터.

[혼합 진영]
CockroachDB는 SQL 인터페이스에 LSM-Tree 스토리지.
TiDB도 마찬가지다.
"읽기 친화적 인터페이스 + 쓰기 친화적 엔진"이라는 조합이 분산 SQL의 트렌드다.

## OLTP에서 B-Tree가 이기는 이유

OLTP 워크로드를 생각해보자.
주문을 넣고, 결제하고, 상태를 조회한다. 읽기 비중이 70~90%다.
쓰기보다 읽기가 압도적으로 많다.
한 건의 주문을 조회하는 point lookup이 핵심이다.
B-Tree는 이 패턴에 최적이다.
정렬된 인덱스에서 PK로 바로 찾는다. 3번 읽으면 끝이다.
예측 가능한 지연 시간.
LSM-Tree로 이걸 하면 Bloom Filter가 도와주긴 하지만 compaction 상태에 따라 지연이 흔들린다.
p99 latency의 안정성이 B-Tree보다 떨어진다.

## 쓰기 헤비에서 LSM-Tree가 이기는 이유

로그 수집 시스템을 생각해보자.
초당 수십만 건의 이벤트가 쏟아진다. 한번 쓰면 거의 수정하지 않는다.
조회는 시간 범위 기반이다.
B-Tree로 이걸 받으면 매 INSERT마다 정렬 위치를 찾아 페이지를 읽고, 쓰고, 분할한다.
랜덤 I/O의 폭풍이다.
LSM-Tree는 메모리에 쌓고 순차로 내린다.
쓰기 throughput이 B-Tree의 수배에서 수십 배다.
Cassandra가 시계열 데이터에 강한 이유다.
ScyllaDB가 Discord의 메시지를 감당하는 이유다.

## DBA 관점에서의 정리

어떤 엔진을 쓸지는 결국 워크로드가 결정한다.
읽기 80% 이상의 OLTP라면 B-Tree다.
MySQL, PostgreSQL이 정답인 이유가 있다.
안정적인 읽기 지연, 예측 가능한 성능.
쓰기 헤비, 로그, 시계열, 이벤트 스트림이라면 LSM-Tree를 고려해야 한다.
RocksDB, Cassandra, ScyllaDB.
분산 SQL이 필요하면 CockroachDB나 TiDB처럼 LSM-Tree 위에 SQL을 얹은 시스템이 후보다.
만능은 없다.
B-Tree와 LSM-Tree는 읽기와 쓰기 사이의 트레이드오프를 각각 다른 방향으로 최적화한 결과다.
"이 시스템의 워크로드는 무엇인가."
이 질문에 답할 수 있으면 엔진 선택은 자연스럽게 따라온다.