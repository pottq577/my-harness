---
id: DBA-057
title: "DocumentDB 쿼리 플래너: v1과 v2는 왜 이렇게 다른가"
status: stable

topics:
  - documentdb
  - query-planner
  - index
  - mongodb
  - collscan

triggers:
  - DocumentDB에 인덱스를 걸었는데도 풀스캔이 나온다
  - DocumentDB 쿼리 플래너 버전이 뭔가
  - $nin이나 $ne 쿼리가 계속 COLLSCAN이다
  - DocumentDB 5.0에서 plannerVersion을 바꿔야 하나

code_signals:
  - "plannerVersion"
  - "$nin"
  - "$ne"
  - "COLLSCAN"
  - "IXSCAN"
  - "planCacheSetFilter"

applies_to:
  - query-review
  - performance-tuning
  - indexing
  - monitoring

risk_signals:
  - 부정 연산자 쿼리가 인덱스 없이 풀스캔
  - plannerVersion이 1인데 인덱스가 안 타는 쿼리가 존재
  - Plan Cache Filter가 없는 상태에서 쿼리 회귀 방치

read_when:
  - DocumentDB 5.0 이상을 운영할 때
  - 인덱스를 걸었는데도 쿼리가 느릴 때
  - v2나 v3로의 플래너 전환을 검토할 때

read_also:
  - DBA-006
  - DBA-007
  - DBA-008
  - DBA-062

source_sections:
  - "raw/7.md:1050-1254"

verified_at: 2026-09-22

references:
  - "https://docs.aws.amazon.com/documentdb/latest/developerguide/query-planner.html"

summary: >
  DocumentDB 쿼리 플래너 v1과 v2의 차이를 다룬다. 부정 연산자, partial index,
  $in compound index 최적화, $regex, 8KB 이상 도큐먼트, Plan Cache Filter,
  v3로의 전환 경로를 플래너 버전 관점에서 설명한다.
---
# DocumentDB 쿼리 플래너: v1과 v2는 왜 이렇게 다른가

Amazon DocumentDB에는 쿼리 플래너 버전이 있다. v1과 v2.
같은 쿼리를 던져도 v1은 컬렉션 풀스캔을 하고 v2는 인덱스를 탄다.
최대 10배 성능 차이.
인덱스를 걸어놨는데 안 타는 경험이 있다면 플래너 버전을 의심해봐야 한다.
DocumentDB 5.0에서 v2가 도입됐지만 기본값은 여전히 v1이다.
명시적으로 켜야 한다.
뭐가 달라졌는지, 왜 바꿔야 하는지 정리한다.

## v1의 치명적 약점: 부정 연산자

v1에서 가장 큰 문제는 부정 연산자가 인덱스를 못 타는 것이다.
`$nin`, `$ne`, `$not` 같은 연산자가 쿼리에 포함되면 인덱스가 있어도 COLLSCAN이 발생한다.

```javascript
db.foo.createIndex({ x: 1 });
db.foo.find({ x: { $nin: [20, 30] } }).explain();
```

v1의 실행 계획:

```json
{ "winningPlan": { "stage": "COLLSCAN" } }
```

인덱스를 만들어놨는데 풀스캔이다.
100만 건이면 100만 건을 다 읽는다.

## v2는 부정 연산자에 인덱스를 쓴다

같은 쿼리를 v2에서 실행하면 결과가 완전히 다르다.

```json
{
  "winningPlan": {
    "stage": "FETCH",
    "inputStage": {
      "stage": "IXSCAN",
      "indexName": "x_1"
    }
  }
}
```

COLLSCAN이 IXSCAN으로 바뀌었다. `$nin`, `$ne`, `$not {$eq}`, `$not {$in}` 전부.
`$type`과 중첩 `$elemMatch`도 인덱스를 탄다.
이게 "최대 10배" 성능 개선의 핵심이다.
부정 연산자를 안 쓰는 서비스는 드물다.

## Partial Index가 유연해졌다

v1에서 partial 인덱스를 타려면 쿼리에 `$exists`를 명시해야 했다.

```javascript
db.foo.createIndex(
  { email: 1 },
  { partialFilterExpression: { email: { $exists: true } } },
);
db.foo.find({ email: "a@b.com" }); // COLLSCAN
db.foo.find({ email: "a@b.com", email: { $exists: true } }); // IXSCAN
```

v2는 `$exists` 없이도 인덱스를 탄다.
필터 표현식의 부분집합이면 자동 매칭한다.

## `$in` + Compound Index 최적화

`$in`과 compound index를 함께 쓸 때 v1은 불필요한 정렬 단계를 추가한다.

```javascript
db.foo.createIndex({ x: 1, y: 1 });
db.foo.find({ x: 2, y: { $in: [1, 2, 3, 4] } }).sort({ x: 1, y: 1 });
```

- v1: COLLSCAN → SORT → 결과 반환.
- v2: compound index를 활용해 정렬 단계를 제거한다.

```json
{ "stage": "IXSCAN", "indexName": "x_1_y_1" }
```

`$in` 요소가 100개 이상일 때 차이가 극적이다.

## `$regex` 인덱스 지원

v1에서 정규식 검색에 인덱스를 태우려면 `$hint`를 명시적으로 줘야 했다.
v2는 prefix 패턴이면 자동으로 인덱스를 탄다.

```javascript
db.foo.createIndex({ y: 1 });
// 앞쪽 매칭 → IXSCAN
db.foo.find({ y: { $regex: "^apple" } });
// 뒤쪽 매칭 → COLLSCAN (prefix가 아니므로)
db.foo.find({ y: { $regex: "apple$" } });
```

prefix 검색만 인덱스를 탄다는 제약이 있지만 v1에서는 아예 불가능했다.

## 8KB 이상 도큐먼트와 다중 필터

v1은 도큐먼트 크기가 8KB를 넘으면 다중 필터 쿼리에서 성능이 급격히 떨어진다.

```javascript
db.foo.find({
  $and: [
    { x: { $gt: 1 } },
    { y: { $gt: 3 } },
    { z: { $lt: 10 } },
    { t: { $lt: 100 } },
  ],
});
```

v2는 비용 추정 알고리즘을 개선해서 여러 필터가 걸린 쿼리에서 최적 인덱스를 더 정확하게 골라낸다.
이벤트 로그나 주문 데이터처럼 도큐먼트가 큰 컬렉션에서 체감이 크다.

## Plan Cache Filter: 서버 사이드 힌트

v2에서 추가된 기능.
애플리케이션 코드 변경 없이 서버 측에서 특정 쿼리가 쓸 인덱스를 지정할 수 있다.

```javascript
db.runCommand({
  planCacheSetFilter: "orders",
  query: { status: "ACTIVE", region: "KR" },
  indexes: ["status_1_region_1"],
});
```

쿼리 회귀가 발생했을 때 배포 없이 즉시 대응할 수 있다.
MongoDB는 필터가 메모리에만 있어서 재시작하면 사라진다.
DocumentDB v2는 재시작과 패치를 거쳐도 유지된다.

## explain 출력이 달라졌다

v1의 explain은 stage와 indexName만 보여준다.
v2는 여기에 두 필드가 추가된다.

```json
"indexCond": { "$and": [{ "price": { "$eq": 300 } }] },
"filter": { "$and": [{ "item": { "$eq": "apples" } }] }
```

`indexCond`는 인덱스를 탄 조건.
`filter`는 인덱스 이후 필터로 처리된 조건.
어떤 조건이 인덱스를 탔고 어떤 조건이 걸러졌는지 한눈에 알 수 있다.

## v2 활성화 방법

v2는 기본 꺼져 있다. 명시적으로 켜야 한다.

- 조건:
  - DocumentDB 5.0, 엔진 패치 3.0.15902 이상.
  - 클러스터 파라미터 그룹에서 `plannerVersion` 값을 `2.0`으로 변경한다.
  - Apply immediately를 선택해야 즉시 반영된다.
- 주의사항:
  - 글로벌 클러스터는 양쪽 리전 모두 같은 버전을 써야 한다.
  - 트래픽이 적은 시간대에 변경하는 게 안전하다.
  - 변경 중 일시적으로 에러율이 오를 수 있다.

## v2의 제약사항

만능이 아니다. 알고 써야 한다.
aggregation과 distinct 명령은 v2가 처리 못 한다. 자동으로 v1로 폴백된다.
Elastic Cluster에서는 v2를 쓸 수 없다. 역시 v1 폴백.
`$regex` 인덱스 스캔은 prefix 패턴만 지원한다.
MongoDB는 전체 regex에 인덱스를 쓸 수 있지만 DocumentDB v2는 `^`로 시작하는 패턴만.
Plan Cache Filter에서 `regex`, `text search`, `geospatial`, `$expr`은지원하지 않는다.

## v3: DocumentDB 8.0의 다음 단계

DocumentDB 8.0에서는 v3가 기본이다.
v2 대비 최대 2배, aggregation은 7배 빠르다.
v2에서 못 했던 aggregation 최적화가 핵심이다.
`$match`스테이지를 파이프라인 앞쪽으로 끌어올린다.
`$lookup`과 `$unwind`를 합쳐서 처리한다.
distinct 명령을 네이티브 지원한다.
21개 aggregation 스테이지를 지원하며 `$vectorSearch`, `$merge` 같은 신규 스테이지도 포함된다.
5.0에서 v2를 쓰고 있다면 8.0 업그레이드 시 v3로 자연스럽게 넘어간다.

## DBA 관점에서의 정리

DocumentDB 5.0을 운영 중이라면 v2를 안 켜놓을 이유가 없다.
부정 연산자에 인덱스가 안 타서 COLLSCAN이 나는 쿼리가 클러스터 어딘가에 반드시 있다.
확인 방법:

```javascript
db.collection.find({ field: { $nin: [...] } }).explain()
```

`plannerVersion: 1`이 보이고 `COLLSCAN`이면 v2로 바꿀 때다.
Plan Cache Filter도 강력하다.
프로파일러에서 슬로우 쿼리가 잡히면 배포 없이 인덱스 필터를 걸어서 즉시 대응할 수 있다.
v1에서 v2로의 전환은 인덱스를 새로 만드는 것이 아니라 이미 있는 인덱스를 제대로 쓰게 하는 것이다.

## 마무리

DocumentDB의 쿼리 플래너는 조용히 바뀌었다.
v1은 부정 연산자 앞에서 무력했다. 인덱스가 있어도 풀스캔을 했다.
v2는 그 틈을 메웠다.
인덱스를 더 잘 고르고, 더 많은 연산자를 지원하고, 서버 사이드 힌트까지 추가했다.
파라미터 하나 바꾸는 것으로 최대 10배 성능이 달라진다.
`plannerVersion: 2.0`
이 한 줄이 아직 적용 안 됐다면 오늘 확인해볼 가치가 있다.