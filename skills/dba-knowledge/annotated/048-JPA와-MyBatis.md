---
id: DBA-048
title: "JPA와 MyBatis: 프레임워크가 아니라 철학의 차이다"
status: stable

topics:
  - jpa
  - mybatis
  - orm
  - sql-mapper
  - java

triggers:
  - JPA와 MyBatis 중 무엇을 선택하나
  - 복잡한 조회는 JPA로 어떻게 처리하나
  - ORM 생산성과 SQL 통제를 함께 가져가고 싶다

code_signals:
  - "jakarta.persistence"
  - "@Entity"
  - "SqlSession"
  - "QueryDSL"

applies_to:
  - orm-review
  - application-architecture
  - sql-review

risk_signals:
  - JPA가 만든 SQL을 확인하지 않음
  - MyBatis SQL을 복사해 중복 관리

read_when:
  - 자바 데이터 접근 기술을 선택할 때
  - CRUD와 복잡한 조회의 경계를 정할 때

read_also:
  - DBA-019
  - DBA-020
  - DBA-011

source_sections:
  - "raw/5.md:1325-1599"

verified_at: 2026-09-09

references:
  - "https://jakarta.ee/specifications/persistence/3.2/jakarta-persistence-spec-3.2.html"
  - "https://mybatis.org/mybatis-3/"

summary: >
  객체 그래프와 생산성에 강한 JPA, SQL 통제에 강한 MyBatis의
  차이를 설명하고 CRUD, 복잡한 조회, 팀 역량에 따른 선택 기준을 제시한다.
---
# JPA와 MyBatis: 프레임워크가 아니라 철학의 차이다

자바 진영에서 DB를 다루는 방법은 크게 둘이다. JPA와 MyBatis.
현재 표준 명칭은 Jakarta Persistence이며 안정 버전 3.2의 패키지는 `jakarta.persistence`다.
프레임워크와 런타임 버전의 호환 범위는 도입 시 공식 문서로 확인한다.
면접에서도 자주 나오고 팀마다 종교 전쟁 수준으로 갈린다.
"JPA가 표준이니까 JPA 써야죠" "MyBatis가 쿼리를 직접 제어하니까 낫죠"
둘 다 틀렸다.
이건 좋고 나쁨의 문제가 아니라 철학의 차이다.
객체 중심으로 생각하느냐, 쿼리 중심으로 생각하느냐.
그 차이가 아키텍처 전체를 바꾼다.

## JPA란 무엇인가

자바 표준 ORM 스펙이다. 구현체는 Hibernate가 사실상 독점.
핵심 사상은 하나다.
"개발자는 객체를 다루고, SQL은 프레임워크가 만든다."

```java
@entity
public class Order {
    Id @GeneratedValue
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    private User user;

    private String status;
}
```

엔티티를 정의하면 테이블 매핑, SQL 생성, 변경 감지까지 JPA가 알아서 한다.
개발자는 SQL을 몰라도 된다. 이게 장점이자 함정이다.

## MyBatis란 무엇인가

SQL Mapper. 개발자가 SQL을 직접 쓴다.
MyBatis는 그 SQL과 자바 객체를 연결해준다.

```xml
<select id="findOrderById" resultType="Order">
    SELECT o.id, o.status, u.name as userName
    FROM orders o
    JOIN users u ON o.user_id = u.id
    WHERE o.id = #{orderId}
</select>
```

SQL이 그대로 보인다.
무슨 쿼리가 나가는지 개발자가 이미 알고 있다.
ORM이 아니다. 객체-관계 매핑을 자동으로 해주지 않는다.
SQL의 결과를 객체에 담아줄 뿐이다.

## 철학의 차이: 객체냐 쿼리냐

JPA는 객체 중심이다.
"데이터베이스를 잊어라. 객체의 관계를 설계하라."
MyBatis는 쿼리 중심이다.
"SQL이 곧 인터페이스다. DB가 어떻게 동작하는지 알고 써라."
도메인 주도 설계를 하는 팀은 JPA가 자연스럽다.
엔티티가 곧 도메인 모델이 된다.
데이터 중심 설계를 하는 팀은 MyBatis가 자연스럽다.
테이블 구조가 곧 모델이다.
어느 쪽이 낫냐가 아니라 팀이 어떤 방식으로 생각하느냐의 문제다.

## JPA의 강점: 생산성

CRUD는 코드를 안 써도 된다.

```java
public interface OrderRepository extends JpaRepository<Order, Long> {
    List<Order> findByStatus(String status);
}
```

메서드 이름만으로 쿼리가 만들어진다.
인터페이스 하나로 기본 CRUD가 끝난다.
변경 감지도 강하다.
엔티티의 필드를 바꾸면 트랜잭션 커밋 시점에 UPDATE가 자동 실행된다.

```java
order.setStatus("COMPLETED");
// save를 안 불러도 UPDATE가 나간다
```

단순 서비스에서의 개발 속도는 MyBatis와 비교가 안 된다.

## JPA의 강점: 영속성 컨텍스트

JPA의 핵심 메커니즘. 1차 캐시, 변경 감지, 쓰기 지연.
같은 트랜잭션 안에서 같은 엔티티를 두 번 조회하면 두 번째는 DB에 안 간다.
1차 캐시에서 꺼낸다.
변경된 필드만 감지해서 UPDATE한다.
INSERT도 모아서 한 번에 보낸다.
JDBC Batch가 자동으로 동작한다.
이 메커니즘을 이해하면 JPA는 강력한 도구다.
이해하지 못하면 예측 불가능한 블랙박스다.

## JPA가 DBA를 힘들게 하는 순간

DBA한테 날아오는 슬로우 쿼리.
JPA가 만든 쿼리에서 자주 보이는 패턴이 있다.

[N+1]
주문 100건을 조회하면서 각 주문의 사용자 정보를 하나씩 쿼리. 101번.

[SELECT *]
이름만 필요한데 엔티티 전체를 가져온다.
커버링 인덱스를 탈 수 있었던 쿼리가 테이블 풀 액세스로 바뀐다.

[무분별한 Eager Loading]
FetchType.EAGER가 걸린 연관 엔티티가 어디서든 항상 JOIN된다.

[대량 UPDATE]
1만 건을 수정하는데 건건이 SELECT + UPDATE.
SQL 한 줄이면 끝나는 일이 2만 번의 쿼리가 된다.

## MyBatis의 강점: SQL 제어

MyBatis의 최대 장점. SQL을 개발자가 직접 쓴다.
필요한 컬럼만 SELECT.
인덱스를 타도록 WHERE절 설계.
EXPLAIN으로 확인하고 튜닝.

```xml
<select id="getOrderSummary">
    SELECT o.id, o.status, o.created_at
    FROM orders o
    WHERE o.user_id = #{userId}
    AND o.status = #{status}
    ORDER BY o.created_at DESC
    LIMIT 20
</select>
```

DBA가 이 쿼리를 보면 인덱스 전략을 바로 세울 수 있다.
실행 계획이 눈에 보인다.
JPA가 만든 쿼리에서는 이게 쉽지 않다.

## MyBatis의 강점: 복잡한 쿼리

JPA가 어려워하는 영역에서 MyBatis가 빛난다.

[다중 테이블 집계]

```sql
SELECT dept_name, COUNT(order_id), SUM(amount)
FROM departments
JOIN users ON departments.dept_id = users.dept_id
JOIN orders ON users.user_id = orders.user_id
WHERE orders.created_at >= #{startDate}
GROUP BY dept_name
HAVING SUM(amount) > 1000000
```

JPQL이나 Criteria API로 이걸 표현하면 코드가 세 배는 길어진다.

[동적 쿼리]
MyBatis의 `<if>`, `<choose>`, `<foreach>`는 조건에 따라 SQL을 유연하게 조립한다.
검색 조건이 열 개인 화면에서 깔끔하게 대응할 수 있다.

## MyBatis의 약점

SQL을 직접 쓰는 대가가 있다.

[보일러플레이트]
테이블이 50개면 INSERT, UPDATE, SELECT, DELETE를 50번 반복해서 써야 한다.
JPA는 인터페이스 하나로 끝난다.

[DB 종속성]
MySQL 문법으로 쓴 SQL은 PostgreSQL에서 안 돌아갈 수 있다.
LIMIT과 FETCH FIRST, IFNULL과 COALESCE.
JPA는 방언이 알아서 변환해준다.

[매핑 노동]
ResultMap을 직접 작성해야 한다.
엔티티 구조가 바뀌면 XML도 같이 고쳐야 한다.
이게 싫어서 JPA로 가는 팀이 많다. 이해한다.

## JPA의 약점

ORM의 추상화에는 비용이 있다.

[학습 곡선]
영속성 컨텍스트, 프록시, 페치 전략, 1차 캐시, 2차 캐시, OSIV, Cascade, orphanRemoval.
제대로 쓰려면 배울 게 많다.

[디버깅 난이도]
문제가 생겼을 때 "어떤 SQL이 나갔는지"부터 파악해야 한다.
Hibernate가 만든 SQL은 사람이 쓴 것과 구조가 다르다.

[성능 튜닝 한계]
옵티마이저 힌트를 주기 어렵다.
네이티브 쿼리로 내려가면 JPA를 쓰는 의미가 줄어든다.
MyBatis는 처음부터 SQL이 보이니까 이런 문제가 없다.

## 한국 시장의 현실

한국 SI, 금융, 대기업에서는 MyBatis가 아직도 압도적이다. 이유가 있다.
금융 시스템은 SQL을 직접 제어해야 한다.
DBA가 쿼리를 리뷰하고 승인한다.
JPA가 만든 쿼리를 DBA가 검증하기란 현실적으로 어렵다.
오라클 기반 레거시가 많다.
프로시저, 힌트, 다이나믹 SQL.
MyBatis가 이걸 자연스럽게 감싼다.
"JPA가 표준이니까 써야 한다"는 기술의 표준이지 산업의 표준이 아니다.
스타트업과 커머스에서는 JPA에 QueryDSL이나 직접 SQL을 보완해 쓰는 팀도 많다.
환경이 다르면 선택도 다르다.

## QueryDSL이라는 제3의 선택지

JPA의 약점을 보완하는 도구.

```java
List<OrderDto> result = queryFactory
    .select(Projections.constructor(
        OrderDto.class,
        qOrder.orderId, qOrder.status, qUser.userName))
    .from(qOrder)
    .join(qOrder.user, qUser)
    .where(qOrder.status.eq("PENDING"))
    .orderBy(qOrder.createdAt.desc())
    .limit(20)
    .fetch();
```

SQL에 가까운 구조. 타입 안전성. 필요한 컬럼만 프로젝션.
JPA 진영에서 "복잡한 쿼리는 QueryDSL로"가 사실상 공식 답이 됐다.
MyBatis의 SQL 제어력과 JPA의 타입 안전성 사이.
그 적당한 지점에 있다.

## 실무에서의 선택 기준

[JPA가 맞는 경우]
CRUD 중심의 서비스.
도메인 모델이 복잡한 DDD 프로젝트.
빠른 개발 속도가 필요한 초기 스타트업.
단순한 조회가 대부분인 서비스.

[MyBatis가 맞는 경우]
복잡한 조회와 집계가 많은 서비스.
DBA와 협업이 긴밀한 환경.
대량 배치 처리가 핵심인 시스템.
SQL 튜닝이 서비스 품질에 직결되는 곳.

[둘 다 쓰는 경우]
JPA로 기본 CRUD를 처리하고 복잡한 조회는 MyBatis나 QueryDSL.
현실에서 가장 많이 보이는 패턴이다.

## 면접에서 이 질문이 나오면

"JPA와 MyBatis 중 어떤 걸 선호하세요?"

[감점 답변]
"JPA요. 표준이니까요."
왜 표준인지, 한계가 뭔지 모르는 것으로 보인다.
"MyBatis요. 쿼리를 직접 쓸 수 있으니까요."
ORM의 장점을 모르는 것으로 보인다.

[득점 답변]
"CRUD 중심이면 JPA로 생산성을 높이고, 복잡한 조회는 QueryDSL이나 네이티브 SQL로 풉니다.
N+1이나 `SELECT *` 같은 패턴은 쿼리 로그를 켜서 개발 단계에서 잡고, 대량 배치는 JDBC Template을 직접 씁니다."
도구의 장단을 알고 상황에 맞게 조합한다는 걸 보여줘라.

## DBA 관점에서의 정리

JPA든 MyBatis든 DBA한테 중요한 건 하나다.
프로덕션에 나가는 쿼리가 뭔지 아느냐.
JPA를 쓰면서 show-sql도 안 켜본 개발자가 "갑자기 느려졌어요"라고 한다.
MyBatis를 쓰면서 EXPLAIN 한 번 안 찍어본 개발자가 "인덱스 추가해주세요"라고 한다.
프레임워크는 도구다.
도구가 만드는 결과를 이해하지 못하면 어떤 도구를 쓰든 같은 장애를 만든다.
JPA가 맞느냐 MyBatis가 맞느냐. 그건 팀과 서비스가 결정한다.
다만 어떤 걸 쓰든 쿼리를 읽을 줄 알고, 실행 계획을 이해하고, 느릴 때 왜 느린지 설명할 수 있어야 한다.
프레임워크는 바뀐다.
SQL을 이해하는 능력은 남는다.
