---
id: DBA-051
title: "Netflix: 초당 백만 쓰기가 Cassandra를 선택한 이유"
status: stable

topics:
  - cassandra
  - netflix
  - write-throughput
  - denormalization
  - case-study

triggers:
  - 초대형 쓰기 워크로드에 Cassandra가 맞나
  - Netflix가 관계형 DB를 벗어난 이유가 무엇인가
  - 쿼리별 테이블을 왜 설계하나

code_signals:
  - "partition key"
  - "replication factor"
  - "eventual consistency"
  - "denormalization"

applies_to:
  - application-architecture
  - domain-modeling
  - analytics

risk_signals:
  - 관계형 모델을 그대로 Cassandra에 이식
  - 조회 패턴 없이 파티션 키를 선택

read_when:
  - 대규모 쓰기 중심 분산 저장소를 검토할 때
  - Cassandra 사례의 전제와 비용을 이해할 때

read_also:
  - DBA-005
  - DBA-046
  - DBA-038

source_sections:
  - "raw/6.md:785-888"

verified_at: 2026-09-09

references:
  - "https://medium.com/netflixtechblog/dynamically-splitting-wide-partitions-in-cassandra-for-time-series-workloads-0eded064f456"
  - "https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html"
  - "https://cassandra.apache.org/doc/stable/cassandra/developing/data-modeling/intro.html"

summary: >
  Netflix 사례를 통해 쓰기 처리량과 가용성이 중요한 워크로드에서
  Cassandra의 파티션, 비정규화, 일관성 선택이 어떤 역할을 하는지 설명한다.
---
# Netflix: 초당 백만 쓰기가 Cassandra를 선택한 이유

Netflix에서 재생 버튼을 누르면 기록이 남는다.
몇 시 몇 분에 재생했는지, 어디까지 봤는지, 어떤 디바이스에서 봤는지.
전 세계 2억 명이 매일 이걸 한다. 쓰기가 쏟아진다.
이 데이터를 저장하는 DB는 RDBMS가 아니다. Cassandra다.

## 시청 기록의 특성

Netflix TechBlog에서 시청 기록 데이터의 특성을 공개했다.
쓰기와 읽기의 비율이 9:1.
사용자가 재생을 시작하면 쓰기.
일시 정지하면 쓰기.
10분마다 진행 위치를 업데이트하면 쓰기.
에피소드가 끝나면 쓰기.
디바이스를 바꾸면 쓰기.
반면, 시청 기록을 "조회"하는 빈도는 상대적으로 낮다.
앱을 열 때 "이어 보기" 목록을 한 번 읽고, 가끔 "내가 봤던 콘텐츠" 페이지를 열 때 읽는다.
9번 쓰고 1번 읽는 워크로드.
이 비율이 DB 선택의 핵심이었다.

## 왜 RDBMS가 아닌가

RDBMS의 쓰기는 비싸다.
MySQL이든 PostgreSQL이든 쓰기가 들어오면 B-Tree 인덱스를 업데이트하고, WAL에 기록하고, 트랜잭션 로그를 동기화한다.
이건 정합성을 위한 비용이다.
데이터가 정확하게 저장되려면 이 단계를 건너뛸 수 없다.
하지만 시청 기록에 이 수준의 정합성이 필요한가?
"어디까지 봤는지"가 1분 정도 어긋나면 어떻게 되는가?
사용자가 되감기를 몇 번 하면 된다.
"최근 본 목록"의 순서가 몇 초간 불일치하면 어떻게 되는가?
새로고침하면 맞춰진다.
이 데이터는 "정확성"보다 "속도"가 중요하다.
ACID의 비용을 감수할 이유가 없다.

## Cassandra의 쓰기 구조

Cassandra가 쓰기에 강한 이유는 구조적이다.
쓰기가 들어오면

1. Commit Log(WAL)에 순차 기록
2. MemTable(메모리)에 적재
3. 클라이언트에 응답 반환

디스크에 정렬된 구조로 쓰는 건 나중에 MemTable이 flush될 때 한다.
SSTable(Sorted String Table)로 순차적으로 쓴다. LSM-Tree 구조다. RocksDB와 같은 원리.
B-Tree처럼 "제자리에 끼워 넣기"가 아니라 "일단 메모리에 쌓고 나중에 정리하기"다.
랜덤 I/O가 아니라 순차 I/O. 여기에 분산까지 더해진다.
데이터가 여러 노드에 동시에 복제되므로 쓰기 부하가 클러스터 전체에 분산된다.
노드를 추가하면 쓰기 처리량이 선형으로 늘어난다.

## 초당 백만 쓰기

Netflix TechBlog에서 "Benchmarking Cassandra Scalability on AWS"라는 제목으로 벤치마크 결과를 공개했다.
288대 노드 클러스터에서 클라이언트 쓰기 초당 110만 건.
3중 복제를 포함하면 초당 330만 건의 쓰기.
이후 "Revisiting 1 Million Writes per Second"에서 이 벤치마크를 재검증했다.
이 수치는 실험실이 아니라 AWS 위에서 달성한 것이다. Netflix의 실제 인프라 환경에서.
RDBMS 단일 인스턴스에서는 초당 수만 건의 쓰기도 쉽지 않다.
100만 건은 아키텍처 자체가 달라야 가능한 수치다.

## 시청 기록의 데이터 모델

초기 Netflix의 시청 기록은 단순했다.
Netflix TechBlog에 따르면 CustomerId를 row key로 쓰고, 한 사용자의 모든 시청 기록을 하나의 행에 저장했다.
단순하고 직관적인 설계.
사용자의 전체 시청 기록을 한 번의 읽기로 가져올 수 있다.
하지만 문제가 생겼다.
사용자 수가 늘고, 각 사용자가 더 많은 콘텐츠를 보면서 행 하나의 크기가 계속 커졌다.
거대한 행을 읽을 때 성능이 떨어지고, compaction 비용이 증가했다.
시간이 지나면서 Netflix는 이 데이터 모델을 재설계했다.
시계열 형태로 데이터를 분할하고, 저장과 조회를 분리하는 구조로 진화했다.

## Eventual Consistency를 받아들이는 법

Cassandra는 최종적 일관성(Eventual Consistency)을 기본으로 한다.
모든 노드가 항상 같은 데이터를 보지 않는다.
잠깐 동안 불일치가 있을 수 있다. 하지만 "결국에는" 일치한다.
Netflix는 이걸 의도적으로 받아들였다.
시청 기록에서 "결국에는"의 시간은 보통 수백 밀리초에서 수 초다.
사용자 A가 노트북에서 드라마를 보다 멈추고, 곧바로 폰에서 이어 보기를 누르면 극히 드물게 진행 위치가 안 맞을 수 있다.
하지만 이건 "재생 위치가 1분 뒤로 간다" 수준이지 "결제가 두 번 된다" 수준이 아니다.
실패의 비용이 낮은 도메인에서는 정합성을 느슨하게 가져가는 게 합리적이다.
그래서 얻는 것:

- 초당 백만 건의 쓰기.
- 밀리초 단위의 응답.
- 글로벌 분산.

트레이드오프를 이해하고 의도적으로 선택한 것이다.

## DBA 관점에서의 정리

Netflix의 사례에서 배울 점은 "Cassandra가 좋다"가 아니다.
데이터의 성격을 먼저 보라는 것이다.
쓰기와 읽기의 비율이 얼마인가. 불일치의 비용이 얼마인가. 한 건의 유실이 만드는 피해가 얼마인가.

- 시청 기록: 9:1 쓰기, 불일치 비용 낮음 → Cassandra.
- 결제 내역: 1:9 읽기, 불일치 비용 무한 → RDBMS.

같은 Netflix 안에서도 결제 시스템은 Cassandra를 쓰지 않을 것이다.
DB 선택의 단위는 "회사"가 아니라 "데이터"다.
"Netflix가 Cassandra를 쓴다"가 아니라 "Netflix의 시청 기록이 Cassandra에 맞았다"가 정확한 문장이다.
