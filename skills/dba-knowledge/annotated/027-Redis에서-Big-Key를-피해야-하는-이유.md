---
id: DBA-027
title: "Redis에서 Big Key를 피해야 하는 이유"
status: stable

topics:
  - redis
  - big-key
  - hot-key
  - memory
  - performance

triggers:
  - Redis에 큰 list나 hash를 저장해도 되나
  - 빅 키 때문에 성능이 느려질 때
  - hot key의 부하가 한 샤드에 몰림
  - Redis 메모리 절약 전략
  - 큰 키를 쪼개는 방법

code_signals:
  - "LPUSH"
  - "RPUSH"
  - "HSET"
  - "memory usage"
  - "redis-cli --bigkeys"
  - "GETRANGE"
  - "IDLE"

applies_to:
  - cache-design
  - performance-tuning

risk_signals:
  - 하나의 key에 거대한 list를 전부 저장
  - 빅 키가 동시 요청을 몰아 단일 스레드에서 블로킹
  - hot key가 샤드 하나로 트래픽 집중
  - 메모리 절약을 위해 비트나 바이트 연산 과다

read_when:
  - Redis에 저장할 값의 크기 스키마를 설계할 때
  - 특정 키에서만 느려지는 증상이 있을 때
  - 큰 값을 쪼개거나 분산 전략을 찾을 때

read_also:
  - DBA-026
  - DBA-025

summary: >
  빅 키 하나가 Redis 단일 스레드 아키텍처에서 모든 클라이언트를 블로킹하는
  지점이 되고, hot key가 샤드 하나에 부하를 몰아가는 문제를 다룬다.
  빅 키를 키-밸류 스플리팅, 해시로 저장, list 샤딩, 모듈 사용과 같은
  방식으로 피하는 방법을 제시한다.
---
# Redis에서 Big Key를 피해야 하는 이유

Redis는 빠르다. 싱글 스레드로 초당 수십만 건을 처리한다.
그런데 그 수십만 건 사이에 하나의 거대한 키가 끼어들면 전체가 멈춘다.
Big Key. Redis 운영에서 가장 흔하고 가장 치명적인 문제 중 하나다.

## Big Key란

말 그대로 크기가 큰 키다. 정확히는 값(Value)이 큰 키.
String이면 수 MB 이상. Hash, List, Set, Sorted Set이면 원소가 수만~수십만 개 이상.
명확한 기준이 공식적으로 정해져 있지는 않지만 실무에서 통용되는 기준은 이렇다.
String: 10KB 이상이면 주의, 100KB 이상이면 위험.
Collection: 원소 5,000개 이상이면 주의, 10,000개 이상이면 위험.
이건 절대적 기준이 아니라 "이 이상이면 문제가 생길 수 있다"는 개인적인 수치다.
실제로 Top-K + 평균 대비 비율로 상대적으로 판별하는 구조를 많이 사용한다.

## 왜 문제인가 --- 싱글 스레드

Redis의 핵심 아키텍처를 이해해야 한다.
Redis는 싱글 스레드다. 명령어를 하나씩, 순서대로 처리한다.
GET user:1이 1 마이크로초에 끝나고, GET user:2가 1 마이크로초에 끝나고, GET user:3이 1 마이크로초에 끝난다.
초당 수십만 건이 가능한 이유가 이거다. 하나하나가 빠르니까.
그런데 그 사이에 HGETALL giant-hash가 들어오면?
원소가 10만 개인 Hash를 전부 읽어서 직렬화하고 네트워크로 보내는 동안 뒤에 줄 서 있는 수만 건이 전부 기다린다.
앞에 한 명이 마트에서 카트 세 대 분량을 계산하는 동안 뒤에 음료수 하나 든 사람 100명이 꼼짝 못 하는 것과 같다.

## 문제 1 --- 지연 전파

Big Key 하나의 처리 시간이 50ms라고 하자. Redis가 그 50ms 동안 다른 걸 못 한다. 그 사이에 들어온 모든 요청이 50ms씩 밀린다.
평소 p99 응답 시간이 1ms였던 서비스가 갑자기 50ms, 100ms로 뛴다. 모니터링에서는 "Redis가 느려졌다"로 보인다.
하지만 Redis가 느린 게 아니라 Big Key 하나가 길을 막고 있는 것이다.
클라이언트 타임아웃이 짧으면 연쇄적으로 재시도가 발생하고, 재시도가 몰리면서 Redis가 진짜로 죽는다.
Big Key 하나가 전체 서비스 장애로 번지는 전형적인 시나리오다.

## 문제 2 --- 메모리 단편화

Redis는 메모리 할당자(jemalloc)를 쓴다.
작은 키들이 균일한 크기로 저장되면 메모리가 효율적으로 관리된다.
Big Key는 큰 연속 메모리 블록을 요구한다.
이 블록이 해제되면 빈 공간이 생기는데, 그 공간에 작은 키가 들어가기엔 크고 다른 Big Key가 들어가기엔 작다.
이게 반복되면 메모리 단편화가 심해진다.
`INFO memory`의 `mem_fragmentation_ratio`가 1.5를 넘기기 시작하면 실제 데이터보다 50% 이상 메모리를 더 쓰고 있다는 뜻이다.
물리 메모리 8GB인 노드에서 데이터는 4GB인데 RSS가 7GB를 찍는 게 이런 경우다.

## 문제 3 --- 네트워크 대역폭

Redis에서 클라이언트로 데이터를 보낼 때 직렬화 + 네트워크 전송이 발생한다.
1MB짜리 String을 GET 하면 1MB가 네트워크를 탄다.
초당 100번 호출되면 초당 100MB. 1Gbps NIC에서 800Mbps를 소모한다.
ElastiCache 같은 관리형 서비스에서는 네트워크 대역폭에 스펙별 상한이 있다.
cache.r7g.large 기준 최대 네트워크 대역폭 12.5Gbps이지만 baseline은 그보다 훨씬 낮다.
Big Key 몇 개가 대역폭을 독점하면 다른 정상적인 요청들이 네트워크에서 밀린다.
`INFO stats`의 `total_net_output_bytes`가 비정상적으로 높다면 Big Key를 의심해야 한다.

## 문제 4 --- DEL이 블로킹이다

Big Key를 삭제할 때가 가장 위험하다. DEL 명령은 동기적(synchronous)이다.
키를 삭제하는 동안 Redis가 멈춘다.
원소 100만 개짜리 Set을 DEL 하면?
100만 개를 하나씩 해제하는 동안 Redis 전체가 응답 불능이 된다.
실측 기준으로 100만 원소 Hash의 DEL은 수백 ms에서 수 초까지 걸릴 수 있다.
TTL이 걸려 있어도 마찬가지다. TTL 만료 시 내부적으로 DEL과 같은 동작이 일어난다.
Big Key에 TTL 1시간을 걸어두면 1시간 후에 시한폭탄이 터지는 것이다.

## 문제 5 --- 복제 지연

Redis 복제는 Primary가 쓴 데이터를 Replica에 전달하는 구조다.
Big Key가 수정되면 그 전체가 복제 버퍼를 통해 Replica로 전달된다.
1MB짜리 키가 초당 10번 수정되면 복제 트래픽만 초당 10MB.
Replica가 이걸 소화 못 하면 복제 지연(replication lag)이 발생한다.
복제 지연이 커지면 Read Replica에서 읽는 데이터가 Primary와 달라진다.
더 심하면 full resync가 발생한다.
Primary의 전체 RDB 스냅샷을 Replica에 다시 보내야 하는데, 이때 Primary의 메모리 사용량이 일시적으로 2배가 되고 복제 트래픽이 수 GB 단위로 발생한다.
Big Key 하나가 클러스터 전체를 흔드는 것이다.

## 문제 6 --- 클러스터 불균형

Redis Cluster는 16,384개 슬롯에 키를 해시해서 분산한다.
Big Key가 특정 슬롯에 들어가면 그 슬롯이 속한 노드만 메모리를 많이 쓴다.
노드 3대에 각각 4GB씩 분산되어야 하는데 Big Key가 몰린 노드만 7GB, 나머지는 2.5GB.
이 노드가 maxmemory에 먼저 도달하면 eviction이 이 노드에서만 발생한다.
정상적인 키가 Big Key 때문에 쫓겨나는 것이다.
리밸런싱으로 해결하려 해도 Big Key 자체가 이동 대상이 되면 migration 과정에서 또 블로킹이 발생한다.

## Big Key는 어떻게 생기나

의도적으로 만드는 경우는 드물다. 대부분 시간이 지나면서 커진다.

[점진적 축적]
장바구니, 알림 목록, 최근 본 상품. 쌓기만 하고 정리하지 않으면 시간이 지날수록 커진다.

[잘못된 데이터 모델링]
"사용자별 주문 내역"을 List 하나에 전부 넣으면 주문이 많은 사용자의 키가 수만 개가 된다.

[직렬화된 거대 객체]
애플리케이션에서 객체를 JSON이나 MessagePack으로 직렬화해서 String에 통째로 넣는 경우.
객체가 커지면 키도 따라서 커진다.

[캐시 설계 미스]
DB 쿼리 결과를 통째로 캐시.

```sql
SELECT * FROM products WHERE category = '식품'
```

결과가 1만 행이면 캐시 값도 수 MB.
처음에는 작았는데 서비스가 성장하면서 커지는 게 가장 찾기 어렵다.

## Big Key 찾는 법

문제를 고치려면 먼저 찾아야 한다.
[redis-cli --bigkeys] Redis가 제공하는 내장 기능.
각 자료구조 유형별로 가장 큰 키를 찾아준다.
프로덕션에서 실행해도 비교적 안전하다. SCAN 기반이라 블로킹이 적다.

```bash
redis-cli -h <host> -p 6379 --bigkeys
```

다만 유형별 TOP 1만 보여주기 때문에 전체적인 분포를 파악하기엔 부족하다.

[MEMORY USAGE]
특정 키의 메모리 사용량을 바이트 단위로 알려준다.
MEMORY USAGE mykey 의심되는 키가 있을 때 확인용.

[redis-cli --memkeys]
Redis 7.0부터 지원.
SCAN + MEMORY USAGE를 조합해서 전체 키를 크기순으로 보여준다.

[OBJECT ENCODING / DEBUG OBJECT]
키의 내부 인코딩과 직렬화 크기를 확인.
ziplist인지 hashtable인지에 따라 실제 메모리 사용이 크게 달라진다.

## 그럼에도 Big Key를 써야 한다면

현실에서는 "그럼 안 쓰면 되잖아"가 통하지 않는 경우가 있다.
실시간 랭킹보드에 10만 명이 올라가야 하고, 사용자의 피드 타임라인에 수만 건이 쌓이고, 세션 객체가 복잡해서 어쩔 수 없이 큰 경우.
피할 수 없다면 피해를 최소화하는 전략이 필요하다.

## 전략 1 --- 키 분할(Sharding within a Key)

하나의 큰 키를 여러 개의 작은 키로 쪼갠다.
사용자 피드가 10만 건이라면 하나의 List에 전부 넣지 말고 1,000건씩 100개 키로 나눈다.

```text
feed:user:1:page:0 → 최신 1~1000
feed:user:1:page:1 → 1001~2000
feed:user:1:page:2 → 2001~3000
```

조회할 때도 필요한 페이지만 읽으면 되니까 한 번에 10만 건을 꺼내는 일이 없다.
Hash가 크다면 논리적으로 분할한다.

```text
user:1:profile → {name, email, phone}
user:1:settings → {theme, lang, timezone}
user:1:stats → {login_count, last_seen}
```

하나의 거대한 user:1 Hash 대신 역할별로 나누면 필요한 부분만 읽고 쓸 수 있다.

## 전략 2 --- 부분 읽기

전체를 한 번에 읽지 않는다.

[Hash]
HGETALL 대신 HMGET으로 필요한 필드만 읽는다.
Bad: `HGETALL user:session:abc123`
Good: `HMGET user:session:abc123 user_id role permissions`

[List]
LRANGE 0 -1 대신 범위를 지정
Bad: `LRANGE notifications:user:1 0 -1`
Good: `LRANGE notifications:user:1 0 19`

[Set / Sorted Set]
SMEMBERS, ZRANGE 0 -1 대신 SSCAN, ZSCAN으로 커서 기반 순회. 또는 ZRANGEBYSCORE로 범위 지정.
Bad: `SMEMBERS large-set`
Good: `SSCAN large-set 0 COUNT 100`
전체를 읽는 명령은 Big Key에서 절대 쓰지 않는다.

## 전략 3 --- 안전한 삭제

DEL은 동기적이다. Big Key에 DEL을 쓰면 Redis가 멈춘다.
Redis 4.0부터 UNLINK가 있다.

```bash
# 나쁜 예 — 블로킹 삭제
DEL giant-hash
# 좋은 예 — 비동기 삭제
UNLINK giant-hash
```

UNLINK는 키를 keyspace에서 즉시 제거하고 실제 메모리 해제는 백그라운드 스레드에서 한다. 메인 스레드가 막히지 않는다.
TTL 만료 시에도 동일한 문제가 있다. Redis 4.0부터 `lazyfree-lazy-expire yes` 설정으로 TTL 만료 삭제도 비동기로 처리할 수 있다.

```text
lazyfree-lazy-expire yes # 4.0+
lazyfree-lazy-server-del yes # 4.0+
lazyfree-lazy-user-del yes # 6.0+
```

Big Key가 있는 환경이라면 이 설정은 기본으로 켜둬야 한다.

## 전략 4 --- 점진적 삭제

UNLINK도 쓸 수 없는 환경이거나 삭제 과정을 직접 제어하고 싶을 때.
Collection 타입이면 원소를 조금씩 지운다.

```bash
# Hash — 100개씩 삭제
HSCAN giant-hash 0 COUNT 100
# 반환된 필드들에 대해
HDEL giant-hash field1 field2 ... field100
# cursor가 0이 될 때까지 반복
# Set — 100개씩 삭제
SSCAN giant-set 0 COUNT 100
SREM giant-set member1 member2 ... member100
# Sorted Set — 범위 삭제
ZREMRANGEBYRANK giant-zset 0 99
# 100개씩 앞에서부터 제거
```

한 번에 100~500개씩, 사이사이에 짧은 sleep을 넣으면 Redis에 부담을 주지 않으면서 정리할 수 있다.
시간은 걸리지만 안전하다.

## 전략 5 --- 압축

String에 큰 데이터를 넣어야 한다면 애플리케이션에서 압축 후 저장한다.

```python
import zlib
import json
data = {"items": [...]} # 큰 객체
compressed = zlib.compress(json.dumps(data).encode())
redis.set("cache:big-result", compressed, ex=300)
# 읽을 때
raw = redis.get("cache:big-result")
data = json.loads(zlib.decompress(raw))
```

JSON 데이터는 압축률이 높다. 1MB가 200KB로 줄어드는 경우가 흔하다.
메모리 사용량이 줄고, 네트워크 대역폭도 줄고, 복제 트래픽도 줄어든다.
대신 CPU를 쓴다. 애플리케이션 서버의 CPU와 Redis의 블로킹 중 하나를 고르는 것인데, 대부분의 경우 애플리케이션 CPU가 여유롭다.

## 전략 6 --- 만료 정책 세분화

Big Key에 단일 TTL을 거는 건 위험하다.
만료되는 순간 삭제 비용이 한 번에 발생한다.
Collection이라면 키 자체의 TTL 대신 원소 단위로 만료를 관리한다.
Sorted Set을 예로 들면 score에 타임스탬프를 넣고 주기적으로 오래된 원소를 정리한다.

```bash
# score를 Unix timestamp로 사용
ZADD events:user:1 1720051200 "event_data_1"
ZADD events:user:1 1720054800 "event_data_2"
# 24시간 이전 데이터 정리 (점진적)
ZREMRANGEBYSCORE events:user:1 0 <24시간_전_timestamp>
```

키 자체는 TTL 없이 유지하되 내용물을 주기적으로 솎아내는 방식이다.
키 크기가 일정 수준 이상 커지지 않도록 상한을 두는 것이 핵심이다.

## 전략 7 --- 모니터링과 알림

Big Key는 예방이 최선이다. 커지기 전에 잡아야 한다.

[주기적 스캔]
크론잡으로 `redis-cli --bigkeys`를 주기적으로 돌린다.
결과를 파싱해서 임계치를 넘는 키가 있으면 알림.

[OBJECT FREQ / OBJECT IDLETIME]
키의 접근 빈도와 유휴 시간을 확인.
크면서 자주 접근되는 키가 가장 위험하다.
크지만 안 쓰이는 키는 그냥 지우면 된다.

[메모리 사용량 추이]
특정 키 패턴의 메모리 총합을 추적.
`notification:*`의 합이 지난주 대비 2배가 됐다면 어딘가에서 Big Key가 자라고 있다는 신호다.

[Collection 원소 수 임계치]
SCARD, HLEN, LLEN, ZCARD로 원소 수를 주기적으로 확인.
10,000개를 넘는 키가 발견되면 알림.
문제가 터진 후 찾는 것과 터지기 전에 잡는 것은 장애 1건의 차이다.

## 설계 시 원칙 --- Big Key를 만들지 않는 법

가장 좋은 전략은 애초에 Big Key가 생기지 않게 설계하는 것이다.

[원칙 1: 상한을 정한다]
List에 넣을 때 LTRIM으로 길이를 제한한다.

```bash
LPUSH recent:user:1 "item_new"
LTRIM recent:user:1 0 999
# 항상 최대 1,000개 유지
```

[원칙 2: 키를 나눈다]
시간 단위, 페이지 단위, 카테고리 단위.
하나의 키에 전부 넣지 않는다.

```text
orders:user:1:2026-07 → 이번 달 주문
orders:user:1:2026-06 → 지난 달 주문
```

[원칙 3: 전체 조회 명령을 금지한다]
`HGETALL, SMEMBERS, LRANGE 0 -1, KEYS *`.
코드 리뷰에서 이 명령이 보이면 막는다.

[원칙 4: 코드에 크기 체크를 넣는다]
캐시에 저장하기 전에 직렬화된 크기를 확인한다.

```python
serialized = json.dumps(data)
if len(serialized) > 10240: # 10KB
log.warning(
f"Large value: {len(serialized)}B"
f" for key {key}"
)
```

임계치를 넘으면 저장하지 않거나 분할 로직을 타게 한다.

## DBA 관점에서의 정리

Big Key는 Redis 장애의 단골 원인이다.
느려지고, 메모리가 비효율적으로 쓰이고, 삭제할 때 멈추고, 복제가 밀리고, 클러스터가 불균형해진다.
전부 하나의 원인에서 시작된다. "값이 크다."
Redis는 작고 빠른 연산을 위해 태어났다.
싱글 스레드라는 설계는 "모든 연산이 빠르다"는 전제 위에 서 있다. Big Key는 그 전제를 깨뜨린다.
그럼에도 쓸 수밖에 없다면 나누고, 부분만 읽고, 비동기로 지우고, 압축하고, 상한을 두고, 모니터링한다.
그리고 가장 중요한 건 코드 리뷰에서 잡는 것이다.
프로덕션에서 Big Key를 발견했다면 이미 늦었다.
설계 단계에서 "이 키가 얼마나 커질 수 있는가"를 한 번만 물어봤으면 막을 수 있었던 장애다.
