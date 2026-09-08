---
id: DBA-054
title: "MongoDB 설계 패턴: 도메인이 구조를 결정한다"
status: stable

topics:
  - mongodb
  - document-model
  - schema-pattern
  - embedding
  - denormalization

triggers:
  - MongoDB 문서를 어떻게 나누고 합치나
  - 임베딩과 참조 중 무엇을 선택하나
  - MongoDB 설계 패턴을 도메인에 적용하고 싶다

code_signals:
  - "schema_version"
  - "bucket"
  - "outlier"
  - "computed"
  - "extended reference"

applies_to:
  - domain-modeling
  - schema-design
  - application-architecture

risk_signals:
  - 관계형 정규화를 문서 DB에 그대로 적용
  - 무한히 커지는 배열을 한 문서에 임베딩

read_when:
  - MongoDB 컬렉션과 문서 경계를 설계할 때
  - 조회 패턴에 맞는 문서 모델 패턴을 고를 때

read_also:
  - DBA-003
  - DBA-005
  - DBA-046

source_sections:
  - "raw/7.md:3-462"

verified_at: 2026-09-09

references:
  - "https://www.mongodb.com/docs/manual/data-modeling/design-patterns/"
  - "https://www.mongodb.com/docs/manual/data-modeling/best-practices/"

summary: >
  MongoDB의 문서 경계를 조회 패턴과 변경 빈도에 맞춰 정하고
  다형성, 속성, 버킷, 이상치, 스키마 버전 패턴을 적용하는 기준을 설명한다.
---
# MongoDB 설계 패턴: 도메인이 구조를 결정한다

MongoDB에는 스키마가 없다고 한다. 틀렸다.
스키마가 없는 게 아니라 강제하지 않을 뿐이다.
자유도가 높다는 건 실수할 여지도 크다는 뜻이다.
그래서 패턴이 필요하다.
반복되는 문제에 대한 검증된 구조.
MongoDB 공식 매뉴얼과 Building with Patterns 시리즈에는 반복되는 문서 모델 문제를 푸는 여러 설계 패턴이 정리돼 있다.
모든 걸 외울 필요는 없다.
도메인을 이해하면 어떤 패턴이 필요한지 보인다.

- 읽기 패턴이 구조를 결정하게 하라.
- 배열의 성장을 항상 경계하라.
- 자주 읽히는 것과 자주 바뀌는 것을 분리하라.
- 도메인의 핫 데이터와 콜드 데이터를 구분하라.
- 패턴은 조합이다. 하나만 쓰는 경우는 드물다.

같은 MongoDB를 써도 구조가 다르면 성능이 10배 차이 난다.

## 패턴이 왜 필요한가

RDB에서는 정규화가 기본 설계 원칙이다.
3NF를 따르면 대부분의 구조가 결정된다.
선택의 여지가 적다. 대신 실수도 적다.
MongoDB는 다르다.
같은 데이터를 표현하는 방법이 열 가지다.
주문-아이템을 Embed할 수도 있고 Reference할 수도 있고 Bucket으로 묶을 수도 있다.
자유도가 높으면 경험이 없는 사람은 헤맨다.
패턴은 이 자유도를 줄여주는 가이드라인이다.
"이런 상황에서는 이렇게 하면 된다"는 선배의 답.
현재 공식 매뉴얼의 Design Patterns 분류와 Building with Patterns 시리즈를 함께 참고한다.
전부 다루지는 않는다. 실무에서 자주 마주치는 것만 깊게 간다.

## Bucket Pattern

시계열 데이터의 표준 패턴이다.
IoT 센서가 1초마다 값을 보낸다.
하루 86,400건. 센서 100개면 864만 건.
Document 하나가 하나의 측정값이면 Collection이 폭발한다.
Bucket Pattern은 시간 단위로 묶는다.

```json
{
  "sensor": "temp-01",
  "hour": 14,
  "readings": [
    { "sec": 0, "val": 23.1 },
    { "sec": 1, "val": 23.2 }
  ],
  "stats": { "count": 3600, "avg": 23.15 }
}
```

한 시간 = 하나의 Document. 3,600건이 1건으로 줄어든다.

## Bucket Pattern: 왜 이렇게 효과적인가

Document 수가 줄면 세 가지가 동시에 좋아진다.

[인덱스 크기]
Document 수가 1/3600이면 인덱스 엔트리도 1/3600이다.
인덱스가 메모리에 올라갈 확률이 높아진다.

[쿼리 효율]
"14시의 평균 온도"를 구할 때 3,600건을 scan하는 게 아니라 1건의 stats.avg_temp를 읽으면 된다.
사전 계산된 집계값(pre-aggregated)의 위력이다.

[쓰기 효율]
매초 insert 대신 $push로 배열에 추가한다.
기존 Document에 append하는 게 새 Document를 만드는 것보다 가볍다.
주의: Bucket 크기를 잘 정해야 한다.
너무 크면 16MB에 근접하고 너무 작으면 Bucket의 의미가 줄어든다.
데이터 크기를 계산해서 정한다.

## Subset Pattern

"전부 읽지 않아도 되는데 전부 읽고 있다."
이 낭비를 해결하는 패턴이다.
영화 상세 페이지를 생각하자. 리뷰가 5,000개다.
페이지를 열 때마다 5,000개를 다 읽는가?
아니다. 최신 5개만 보여준다.

```json
{
  "title": "인셉션",
  "recent_reviews": [
    { "user": "A", "score": 9, "text": "꿈속의 꿈" },
    { "user": "B", "score": 10, "text": "다시 봐도 새롭다" }
  ],
  "review_count": 5000
}
```

전체 리뷰는 별도 reviews Collection에 둔다. "더보기"를 누를 때만 조회한다.
읽기의 90%가 recent_reviews만 필요하다면 90%의 읽기에서 불필요한 I/O를 제거하는 것이다.

## Extended Reference Pattern

Reference의 약점을 보완하는 패턴이다.
주문에 사용자를 Reference로 연결했다.
주문 목록에 사용자 이름을 보여주려면 매번 users Collection을 $lookup해야 한다.
Extended Reference는 자주 필요한 필드만 복사해 둔다.

```json
{
    "order_iid": "ORD-001",
    "user": {
        "_id": ObjectId("64a..."),
        "name": "김철수",
        "tier": "VIP"
    },
    "items": [...]
}
```

전체 사용자 정보가 아니라 name과 tier만 복사했다.
주문 목록을 보여줄 때 $lookup이 필요 없다.
대가는 데이터 중복이다.
사용자 이름이 바뀌면 주문의 복사본도 고쳐야 한다.
자주 안 바뀌는 필드만 복사하는 게 핵심이다.
이름은 거의 안 바뀐다. 주소는 자주 바뀐다.

## Computed Pattern

미리 계산해 두는 패턴이다.
읽을 때마다 계산하는 비용을 쓸 때 한 번으로 옮긴다.
상품 페이지에 "총 리뷰 수"와 "평균 별점"이 있다.
매번 리뷰 전체를 aggregate하면 비용이 크다.

```json
{
  "product": "치킨",
  "review_stats": {
    "count": 1247,
    "avg_score": 4.3,
    "score_dist": { "5": 512, "4": 389, "3": 201 }
  }
}
```

리뷰가 추가될 때 $inc로 count를 올리고 avg_score를 갱신한다.
읽기 시점에 계산하지 않는다.

[적합한 경우]
읽기가 쓰기보다 훨씬 많을 때.
대시보드, 리더보드, 통계 페이지.

[부적합한 경우]
쓰기가 빈번하고 정확도가 중요할 때.
실시간 정산처럼 정합성이 필수인 경우.

## Attribute Pattern

필드의 종류가 예측 불가능할 때 쓴다.
전자제품 카탈로그를 생각하자.
노트북은 CPU, RAM, 화면크기. 냉장고는 용량, 에너지등급, 도어수.
카테고리마다 속성이 다르다.
RDB라면 모든 속성을 컬럼으로 만들거나 EAV 테이블을 쓴다. 둘 다 고통스럽다.

```json
{
  "name": "맥북 프로 16",
  "attributes": [
    { "k": "cpu", "v": "M3 Max" },
    { "k": "ram", "v": 36, "unit": "GB" },
    { "k": "screen", "v": 16.2, "unit": "inch" }
  ]
}
```

인덱스는 `{ "attributes.k": 1, "attributes.v": 1 }`.
Multikey Index가 배열 안의 모든 k-v를 인덱싱한다.

## Outlier Pattern

대부분은 정상인데 극소수가 비정상인 경우.
SNS에서 일반 사용자의 팔로워는 수백 명이다.
연예인의 팔로워는 수백만 명이다. 같은 구조로 둘 다 담을 수 없다.
일반 사용자는 followers 배열을 Embed한다.

```json
{
  "user": "일반유저",
  "followers": ["A", "B", "C"],
  "has_overflow": false
}
```

팔로워가 임계값(예: 1000)을 넘으면 overflow 플래그를 켠다.

```json
{
  "user": "연예인",
  "followers": ["A", "B", "...처음 1000명"],
  "has_overflow": true
}
```

나머지 팔로워는 별도 Collection에 저장한다.
읽을 때 has_overflow를 확인해서 분기한다.
99%의 사용자는 빠른 Embed로 처리하고 1%의 예외만 Reference로 처리하는 전략이다.

## Tree Pattern

계층 구조를 표현하는 패턴이다. 카테고리, 조직도, 댓글 트리.
여러 변형이 있고 읽기/쓰기 빈도에 따라 선택한다.

[Parent Reference]
각 노드가 부모의 \_id를 가진다.
가장 단순하지만 하위 트리 조회가 재귀적이다.

[Child Reference]
각 노드가 자식 목록을 가진다.
바로 아래 자식 조회가 빠르다.

[Materialized Path]
경로를 문자열로 저장한다.
`{ "path": "/전자제품/컴퓨터/노트북" }`
정규식으로 하위 트리 전체를 조회할 수 있다.

[Ancestors Array]
조상 전체를 배열로 저장한다.
특정 조상의 모든 하위를 빠르게 찾을 수 있다.

## Schema Versioning Pattern

스키마는 바뀐다.
v1에서는 address가 문자열이었는데 v2에서는 객체(city, street, zip)로 바뀌었다.
RDB에서는 ALTER TABLE로 한 번에 바꾼다.
수억 건의 테이블이면 몇 시간 락이 걸린다.
MongoDB에서는 기존 Document를 안 바꿔도 된다.
새 Document만 새 구조로 넣으면 된다.

```json
{"_id": 1, "schema_v": 1, "address": "서울시 강남구 ..."}
{"_id": 2, "schema_v": 2, "address": {"city": "서울", "district": "강남", "detail": "..."}}
```

애플리케이션이 schema_v를 보고 분기한다. 점진적 마이그레이션이 가능하다.
읽을 때 v1이면 변환하고 다시 쓸 때 v2로 저장하면 된다.
다운타임 없이 스키마를 진화시키는 패턴이다.
장기 운영 서비스에서 반드시 필요하다.

## Approximation Pattern

정확하지 않아도 되는 숫자를 싸게 관리하는 패턴이다.
페이지 조회수를 생각하자. 조회 한 번마다 $inc를 날린다.
초당 1만 조회면 초당 1만 번 쓰기다. 정확한 숫자가 필요한가?
"조회수 1,247,382"와 "약 125만"의 차이가 의미 있는가?
Approximation Pattern은 확률적으로 갱신한다.
10번 중 1번만 $inc: 10으로 업데이트한다.
쓰기가 1/10로 줄어든다.

```python
import random
if random.random() < 0.1:
    db.pages.update_one(
        {"_id": page_iid},
        {"$inc": {"views": 10}}
)
```

좋아요 수, 조회수, 다운로드 수. "대략적인 크기"만 중요한 카운터에 적합하다.
정산, 재고처럼 1 단위가 중요한 곳에는 절대 쓰면 안 된다.

## 도메인별 패턴 맵: 이커머스

주문, 상품, 리뷰, 장바구니. 이커머스는 MongoDB 설계 패턴의 종합 선물세트다.

[주문]
주문-아이템은 Embed (항상 함께 읽힌다).
사용자 정보는 Extended Reference (이름, 등급만 복사).
주문 상태 변경은 단일 Document 원자성으로 충분.

[상품 카탈로그]
카테고리마다 속성이 다르다 → Attribute Pattern.
리뷰 요약은 Computed Pattern (평균 별점, 건수 사전 계산).
상세 리뷰는 Subset Pattern (최신 5개만 Embed).

[장바구니]
아이템 수가 제한적 → Embed.
유효기간이 있다 → TTL Index.

[검색/필터]
다양한 속성 필터 → Attribute Pattern + Multikey Index.
전문 검색 → Atlas Search.

## 도메인별 패턴 맵: 소셜/콘텐츠

게시글, 댓글, 좋아요, 팔로우, 피드. 읽기가 압도적으로 많고 핫 데이터가 극단적으로 편중된다.

[게시글]
본문은 Embed. 좋아요 수는 Computed Pattern.
조회수는 Approximation Pattern (정확할 필요 없다).

[댓글]
댓글이 적으면 Subset Pattern (최신 N개 Embed).
많으면 별도 Collection + Reference.
대댓글(트리) → Tree Pattern.

[팔로우/팔로워]
일반 사용자 → Embed (수백 명 수준).
인플루언서 → Outlier Pattern (별도 Collection 분리).

[피드]
Fan-out on write: 게시 시 팔로워 피드에 미리 복사.
Fan-out on read: 읽을 때 팔로워의 게시글을 aggregate.

팔로워 수에 따라 전략이 달라진다.

## 도메인별 패턴 맵: IoT / 시계열

센서, 로그, 메트릭, 이벤트. 시계열은 "쓰기가 많고 최근 데이터만 자주 읽힌다"가 특징이다.

[센서 데이터]
Bucket Pattern이 핵심이다.
시간 단위로 묶고 사전 집계값을 함께 저장한다.
stats 필드에 min, max, avg, count를 넣는다.

[로그]
TTL Index로 보존 기간을 자동 관리한다.
30일 지난 로그는 자동 삭제.
Schema Versioning으로 로그 포맷 변경에 대응한다.

[실시간 대시보드]
Computed Pattern으로 분/시간/일 단위 집계를 사전 계산.
읽을 때 aggregate하면 너무 느리다. Bucket의 stats와 조합하면 대시보드 쿼리가 단순해진다.
MongoDB 5.0부터 Time Series Collection이 있다.
Bucket Pattern을 DB 레벨에서 자동으로 처리한다.
직접 Bucket을 구현할 필요가 줄어들었다.

## 도메인별 패턴 맵: 게임

플레이어, 인벤토리, 랭킹, 매치 기록. 게임은 읽기와 쓰기가 동시에 폭발하는 도메인이다.

[플레이어 프로필]
장비, 스킬, 퀘스트 진행도를 하나의 Document에 Embed.
게임 세션에서 프로필을 통째로 읽고 통째로 쓴다.
Document 단위 원자성이 게임 상태 관리에 딱 맞는다.

[인벤토리]
아이템 수가 제한적이면 Embed.
아이템이 수천 개로 늘어나는 게임이면 Bucket Pattern으로 카테고리별 묶기.

[랭킹/리더보드]
Computed Pattern.
점수가 바뀔 때마다 랭킹 Document를 갱신한다.
상위 100명은 별도 Document에 캐시.

[매치/전투 기록]
시계열 성격 → Bucket Pattern.
한 매치의 상세 로그는 Embed.
매치 요약만 플레이어 Document에 Subset으로 둔다.

## 도메인별 패턴 맵: 물류/배달

주문, 배송 추적, 라이더 위치, 경로. 실시간 위치 데이터와 상태 전이가 핵심이다.

[배송 추적]
상태 변경 이력을 배열로 Embed.
["접수", "픽업", "배달중", "완료"]는 고정된 단계다.
단계가 유한하니까 배열이 무한히 자라지 않는다.

[라이더 위치]
Bucket Pattern으로 시간 단위 위치 묶기.
GeoJSON + 2dsphere Index로 "근처 라이더" 검색.
실시간성이 중요하면 TTL로 오래된 위치 자동 삭제.

[경로 최적화]
하나의 배송 건에 경유지 목록을 Embed.
경유지 순서 변경은 단일 Document 원자성으로 처리.
Polymorphic Pattern으로 도보/자전거/오토바이 경유지를 같은 구조에.

## 도메인별 패턴 맵: 금융/결제

잔액, 거래 내역, 정산.
금융은 정합성이 최우선이다. 1원이 틀리면 안 된다.

[계좌/잔액]
단일 Document에 잔액. findOneAndUpdate로 원자적 처리.
동시 접근이 많으면 WriteConflict retry가 빈번해진다.

[거래 내역]
시계열 성격이지만 Bucket을 쓰면 안 된다.
건별 감사(audit)가 필요하기 때문이다.
한 건 = 한 Document. 수정 불가(immutable).

[이체]
Multi-document Transaction이 반드시 필요한 영역.
A 차감 + B 증가가 원자적이어야 한다.

[정산]
Approximation Pattern은 절대 금지. 정확한 $sum 필수.
Computed Pattern도 사전 계산 후 검증이 필수다.

MongoDB가 금융에 적합한가는 논쟁적이다.
가능은 하지만, 더 많은 주의가 필요하다.

## 도메인별 패턴 맵: CMS / 콘텐츠 관리

페이지, 블록, 미디어, 다국어. CMS는 구조가 유동적이고 콘텐츠 타입이 다양한 도메인이다.

[페이지/블록]
Polymorphic Pattern이 핵심이다.
텍스트 블록, 이미지 블록, 비디오 블록, 테이블 블록.
type 필드로 구분하고 각 타입마다 구조가 다르다.
하나의 Collection에 전부 담을 수 있다.

[다국어]
하나의 Document에 언어별 필드를 둔다.
`{ "title": {"ko": "제목", "en": "Title", "ja": "タイトル"} }`
Attribute Pattern의 변형이다.

[버전 관리]
Schema Versioning Pattern의 확장.
Document를 수정하면 이전 버전을 versions 배열에 push.
최신은 항상 Document 본체.
이전 버전은 Subset Pattern으로 최근 N개만 유지.

## 패턴 조합 치트시트

실전에서는 패턴을 하나만 쓰지 않는다. 도메인 하나에 3~4개 패턴이 겹친다.

[이커머스 주문]
Embed + Extended Reference + Computed

[소셜 피드]
Subset + Computed + Outlier

[IoT 대시보드]
Bucket + Computed + TTL Index

[게임 플레이어]
Embed + Subset + Computed

[CMS 페이지]
Polymorphic + Schema Versioning + Tree

[물류 배송]
Embed + Bucket + GeoJSON

패턴을 외우는 것보다 중요한 건 "이 도메인에서 읽기는 어떻게 일어나는가"를 먼저 묻는 것이다.
읽기가 구조를 결정하고 구조가 패턴을 결정한다.

## DBA 관점에서의 정리

- 읽기 패턴이 구조를 결정하게 하라.
- 배열의 성장을 항상 경계하라.
- 자주 읽히는 것과 자주 바뀌는 것을 분리하라.
- 도메인의 핫 데이터와 콜드 데이터를 구분하라.

패턴은 조합이다. 하나만 쓰는 경우는 드물다.
RDB에서는 정규화를 먼저 하고 성능이 필요하면 비정규화한다.
MongoDB에서는 비정규화가 기본이고 문제가 생기면 정규화한다.
방향이 반대다. 그래서 패턴이 더 중요하다.
정규화에는 1NF, 2NF, 3NF라는 단계가 있지만 비정규화에는 단계가 없다.
패턴이 그 단계를 대신한다.
도메인을 모르면 패턴을 고를 수 없고 패턴 없이 설계하면 MongoDB는 느린 JSON 저장소가 된다.
같은 MongoDB를 써도 구조가 다르면 성능이 10배 차이 난다.
