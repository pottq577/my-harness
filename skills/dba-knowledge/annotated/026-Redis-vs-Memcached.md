---
id: DBA-026
title: Redis vs Memcached: 캐시만 할 거면 Memcached가 맞다
status: stable

topics:
  - redis
  - memcached
  - cache
  - cache-server

triggers:
  - Redis와 Memcached 중 무엇을 쓸까
  - 캐시 서버를 직접 띄워야 하나 관리형을 쓰나
  - Memcached 최대 키 크기 제한
  - 대규모 인증 세션을 빠르게 저장하는 법
  - 메모리 초과 발생 시 Memcached가 제거하는 워크셋

code_signals:
  - "redis-client"
  - "memcached"
  - "세션"
  - "캐시"
  - "s3"
  - "쿠키"

applies_to:
  - cache-design
  - application-architecture

risk_signals:
  - 캐시 용량을 초과해 Memcached가 LRU로 데이터를 쫓아냄
  - Redis의 복잡성 감수 조건을 놓침
  - 캐시가 메모리 제한을 넘겨 비정상 동작

read_when:
  - 캐시 전용 서버를 고를 때
  - 세션 저장소를 Redis로 했을 때 운영 난이도 검토할 때
  - 캐시 워크셋이 메모리를 초과할 때의 동작을 확인할 때

read_also:
  - DBA-025
  - DBA-027

summary: >
  캐시만 하는 용도에서는 진입비용이 낮고 단순한 Memcached가 맞을 수 있다는
  입장에서 Redis와 Memcached를 비교한다. 관리형 서비스까지 포함한 선택
  프레임워크와, Redis가 필요한 조건(세션 저장, 순차 처리, 복잡 자료구조
  등)을 명확히 한다.
---
# Redis vs Memcached: 캐시만 할 거면 Memcached가 맞다

"캐시 쓸 건데 Redis 올려주세요."
이 요청을 받으면 하나 물어본다.
"혹시 캐시만 할 건가요?"
캐시만 할 거라면 Memcached가 더 나은 선택일 수 있다.
"Redis가 Memcached 상위호환 아닌가요?"
아니다. 그 오해를 풀어보자.

## 태생이 다르다

Memcached는 2003년에 나왔다. LiveJournal의 브래드 피츠패트릭이 만들었다.
목적이 명확했다. "DB 앞에 메모리 캐시를 두자."
Redis는 2009년에 나왔다. 살바토레 산필리포가 만들었다.
처음부터 "데이터 구조 서버"를 지향했다.
캐시는 Redis가 할 수 있는 일 중 하나일 뿐이다.
Memcached는 캐시를 위해 태어났다. Redis는 캐시도 할 수 있게 태어났다.
이 차이가 설계 전체에 반영돼 있다.

## 데이터 구조 차이

Memcached의 데이터 모델은 단순하다. key-value.
value는 바이트 배열이다.
문자열이든 직렬화된 객체든 Memcached는 신경 안 쓴다. 그냥 저장하고 돌려줄 뿐이다.
Redis는 다르다.
String, Hash, List, Set, Sorted Set, Stream, HyperLogLog, Bitmap, Geospatial.
서버 사이드에서 데이터 구조를 조작할 수 있다.
Sorted Set에서 랭킹을 계산하고, List에서 큐를 구현하고, Hash에서 필드 단위로 읽고 쓴다.
캐시만 할 거면 이 기능이 전부 필요 없다.
GET, SET, DELETE. Memcached로 충분하다.

## 스레딩 모델

이게 가장 과소평가되는 차이다.
Redis는 싱글 스레드다. 명령어를 하나씩 순서대로 처리한다.
이 설계 덕분에 락 없이 원자적 연산이 가능하다. 하지만 CPU 코어 하나만 쓴다.
Memcached는 멀티스레드다. 여러 코어를 동시에 활용한다.
단순 GET/SET 연산을 여러 스레드가 병렬로 처리한다.
vCPU 4코어 인스턴스에서 단순 캐시 룩업만 한다면 Memcached가 Redis보다 처리량이 높다.
Redis 7.0부터 I/O 스레딩이 추가됐지만 명령어 처리 자체는 여전히 싱글 스레드다.

## 메모리 효율

Memcached는 slab allocator를 쓴다.
메모리를 미리 slab 단위로 나눠놓고 비슷한 크기의 아이템을 같은 slab에 넣는다.
메모리 단편화가 적다. 예측 가능한 메모리 사용.
Redis는 jemalloc을 쓴다.
다양한 데이터 구조를 지원하다 보니 오버헤드가 더 크다.
같은 key-value 1,000만 건을 저장하면 Memcached가 Redis보다 메모리를 적게 쓴다. 각 키에 붙는 메타데이터가 더 작기 때문이다.
순수 캐시 워크로드에서 같은 메모리로 더 많은 데이터를 넣을 수 있다는 건 노드 수를 줄일 수 있다는 뜻이다.
비용 차이가 생긴다.

## 영속성

Redis는 RDB 스냅샷과 AOF 로그를 지원한다. 재시작해도 데이터가 살아 있다.
이 기능 덕분에 Redis를 1차 저장소처럼 쓰는 서비스도 있다.
Memcached는 영속성이 없다. 재시작하면 전부 사라진다. 캐시니까 사라져도 된다는 전제.
영속성은 공짜가 아니다.
Redis의 AOF는 디스크 I/O를 유발한다.
fsync 정책에 따라 쓰기 성능에 영향을 준다.
RDB 포크는 메모리를 일시적으로 2배 쓸 수 있다.
캐시 용도로만 쓴다면 이 오버헤드가 전부 불필요하다.
Memcached는 이 비용을 처음부터 지지 않는다.

## 클러스터링

[Memcached]
클라이언트 사이드 샤딩.
클라이언트가 키를 해시해서 적절한 노드를 직접 선택한다.
서버끼리는 서로를 모른다.
단순하고 예측 가능하다.

[Redis Cluster]
서버 사이드 샤딩.
16,384개 해시 슬롯을 노드에 분배한다.
노드 간 gossip 프로토콜로 상태를 공유한다.
자동 페일오버, 리샤딩이 가능하다.
Redis Cluster는 강력하지만 복잡하다.
MULTI/EXEC가 같은 슬롯 안에서만 동작하고, 클라이언트가 MOVED/ASK 리다이렉션을 처리해야 한다.
ElastiCache Memcached는 Auto Discovery로 노드 추가/제거를 클라이언트가 자동 감지한다.
구성이 단순하다.

## "Redis가 무조건 상위호환"이라는 오해

이 오해가 널리 퍼져 있다.
Redis가 Memcached의 기능을 전부 포함하니까 Redis만 쓰면 된다는 논리.
틀렸다. Memcached가 Redis보다 나은 지점이 있다.

- 멀티스레드로 코어를 전부 활용한다.
- 메모리 오버헤드가 작다.
- 영속성 비용이 없다.
- 구조가 단순해서 예측 가능하다.

"캐시만 할 거면 Memcached"는 성능과 효율의 관점에서 합리적인 선택이다.
Redis는 캐시 이상의 일을 할 때 빛난다. 캐시만 할 때는 불필요한 복잡성이 딸려온다.

## Redis가 빛나는 순간

캐시를 넘어서는 요구사항이 있을 때.

[세션 스토어]
사용자 세션을 Hash로 저장하고 TTL로 자동 만료.
필드 단위 읽기/쓰기가 가능하다.

[실시간 랭킹]
Sorted Set 하나로 수백만 명의 실시간 순위를 관리한다.
ZADD, ZRANK, ZRANGE.

[메시지 큐]
List의 LPUSH/BRPOP으로 간단한 큐.
Stream으로 본격적인 이벤트 스트리밍.

[분산 락]
SET NX EX 로 분산 환경 락을 구현한다.
Redlock 알고리즘까지 지원.

[Pub/Sub]
실시간 알림, 이벤트 브로드캐스트.

이 중 하나라도 필요하면 Redis다. Memcached로는 할 수 없다.

## Memcached가 더 나은 경우

구체적으로 이런 상황이다.

[순수 캐시]
DB 쿼리 결과를 key-value로 캐시.
GET으로 읽고, 없으면 DB에서 가져와서 SET.
이 패턴만 반복하는 서비스.

[높은 처리량 요구]
초당 수십만 건의 단순 GET/SET.
멀티스레드의 이점이 극대화된다.

[메모리 효율이 중요]
같은 예산으로 더 많은 데이터를 캐시해야 할 때.
노드당 캐시 용량이 Memcached가 더 크다.

[운영 단순성]
캐시 노드가 죽으면 다시 워밍업하면 된다.
페일오버 복잡성이 필요 없다.
상태가 없으니 교체가 쉽다.

Facebook이 Memcached를 선택한 이유가 정확히 이것이다.
수십억 건의 단순 캐시 룩업.

## ElastiCache에서의 선택

AWS 관리형 서비스 기준으로 보면.

[ElastiCache for Redis]
클러스터 모드, 자동 페일오버, 백업/복원.
기능이 풍부하고 관리 포인트가 많다.

[ElastiCache for Memcached]
Auto Discovery, 멀티스레드.
백업 없음, 페일오버 없음.

노드가 죽으면 새 노드가 빈 상태로 올라온다. 비용도 다르다.
같은 인스턴스 타입이라도 Redis가 Memcached보다 비싸다.
Redis의 복제, 백업, 클러스터 관리 비용이 반영돼 있다.
캐시 미스 시 원본 DB로 가면 되는 구조라면 Memcached의 "상태 없음"이 오히려 장점이다. 복구가 단순해진다.

## 실무 판단 기준

팀에서 "캐시 도입하겠습니다"라고 할 때 DBA가 물어야 하는 질문이 있다.
"캐시 외에 Redis의 데이터 구조를 쓸 건가요?"
쓴다면 Redis. 안 쓴다면 Memcached를 먼저 고려.
"캐시 데이터가 유실되면 서비스에 영향이 있나요?"
있다면 Redis(영속성). 없다면 Memcached.
"단일 키 조회가 대부분인가요, 서버 사이드 연산이 필요한가요?"
전자면 Memcached. 후자면 Redis.
세 질문 모두 첫 번째 답이면 Memcached가 맞는 선택이다.

## DBA 관점에서의 정리

Redis는 만능이 아니다.
만능에 가깝지만 만능에는 비용이 따른다.

- 싱글 스레드의 처리량 한계.
- 다양한 데이터 구조에 따른 메모리 오버헤드.
- 영속성 유지 비용.
- 클러스터 운영의 복잡성.

캐시만 할 거면 이 비용을 다 치를 필요가 없다.
Memcached는 캐시라는 한 가지 일을 30년 가까이 해온 도구다.
Redis를 써야 하는 이유가 명확할 때 Redis를 쓰고, "그냥 Redis가 좋다더라"로 선택하지 않는 것.
도구는 용도에 맞게 쓸 때 빛난다.
Redis는 데이터 구조 서버로 빛나고,
Memcached는 캐시로 빛난다.
