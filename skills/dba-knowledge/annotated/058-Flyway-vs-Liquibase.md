---
id: DBA-058
title: "Flyway vs Liquibase: DB 마이그레이션, 단순함이 답인가"
status: stable

topics:
  - flyway
  - liquibase
  - migration
  - ddl
  - schema-versioning

triggers:
  - 마이그레이션 도구를 뭘 써야 하나
  - Flyway와 Liquibase의 차이가 뭔가
  - DDL을 버전 관리하고 싶다
  - 마이그레이션 롤백 전략은 어떻게 하나

code_signals:
  - "flyway_schema_history"
  - "DATABASECHANGELOG"
  - "V1__"
  - "changeSet"
  - "flyway migrate"
  - "liquibase update"
  - "flyway repair"

applies_to:
  - migration
  - production-ddl
  - schema-design
  - technical-interview

risk_signals:
  - 적용된 마이그레이션 파일을 수정해서 체크섬 불일치가 남
  - FK 순서가 틀린 채 마이그레이션을 실행
  - DDL이 MDL을 잡아 서비스가 멈추는 걸 도구에 위임
  - 환경별 분기가 필요한데 도구가 단순해서 커스텀 폭주

read_when:
  - 마이그레이션 도구를 도입하거나 선택할 때
  - DDL 배포 파이프라인을 설계할 때
  - 팀 규모와 DB 개수에 맞는 도구를 고를 때

read_also:
  - DBA-023
  - DBA-066

source_sections:
  - "raw/7.md:1256-1422"

summary: >
  Flyway와 Liquibase의 철학 차이(SQL 그대로 vs 추상화)와 롤백 전략, 멀티 DB
  지원, CI/CD 통합을 비교한다. DBA 관점에서 도구 안에 담긴 DDL의 락 영향과
  순서 문제가 더 중요하다는 판단 기준을 제시한다.
---
# Flyway vs Liquibase: DB 마이그레이션, 단순함이 답인가

스키마를 바꿔야 한다.
ALTER TABLE 한 줄이면 될 일인데, 그 한 줄을 누가, 언제, 어떤 순서로 실행했는지 아무도 모른다.
DB 마이그레이션 도구는 이 문제를 풀기 위해 존재한다.
Flyway와 Liquibase. 둘 다 같은 문제를 푸는데 철학이 다르다.

## 마이그레이션 도구가 필요한 이유

운영 DB에 DDL을 수동으로 친다.
Slack에 "orders 테이블에 컬럼 추가했습니다" 남긴다.
한 달 뒤 beta 환경과 prod 스키마가 다르다.
누가 언제 뭘 바꿨는지 추적할 수 없다.
마이그레이션 도구는 이 혼란을 버전으로 정리한다.
V1, V2, V3 순서대로 적용. 어떤 환경이든 같은 순서로 같은 결과.
코드처럼 Git에 넣고 리뷰하고 배포한다.

## Flyway의 철학: SQL 그대로

Flyway는 SQL 파일 자체가 마이그레이션이다.
`V1__create_orders.sql` 파일을 만들면 끝이다.

```sql
-- V1__create_orders.sql
CREATE TABLE orders (
order_id BIGINT PRIMARY KEY,
user_name VARCHAR(100),
created_at DATETIME
);
```

파일명이 버전이고, DB에 `flyway_schema_history` 테이블이 생겨서 어디까지 실행했는지 기록한다.
배울 게 거의 없다. SQL 쓸 줄 알면 쓸 수 있다.
이 단순함이 Flyway의 가장 큰 강점이다.

## Liquibase의 철학: 추상화

Liquibase는 SQL 위에 한 겹을 덮는다.
XML, YAML, JSON으로 변경을 선언한다.

```yaml
- changeSet:
changes:
- createTable:
tableName: orders
columns:
- column:
name: order_id
type: BIGINT
```

왜 이런 번거로운 일을 하는가. DB 엔진에 독립적이기 위해서다.
같은 changelog로 MySQL에도 PostgreSQL에도 적용된다.
SQL로 직접 써도 되지만 그러면 Liquibase를 쓰는 이유가 반감된다.

## 롤백 전략의 차이

Flyway는 롤백에 솔직하다. Community 버전에는 롤백이 없다.
"DDL은 롤백하지 마라. 새 마이그레이션으로 고쳐라." 이게 Flyway의 입장이다.
Liquibase는 롤백을 일급 시민으로 다룬다.
각 changeSet에 rollback 블록을 선언할 수 있다.
`liquibase rollbackCount 1`이면 직전 변경을 되돌린다.
현실은 어떤가?
DBA 관점에서 DDL 롤백은 대부분 환상이다.
컬럼을 추가하고 데이터가 들어간 뒤에 롤백한다고 컬럼을 삭제하면 데이터가 날아간다.
도구의 롤백보다 "앞으로 가며 고치는" 전략이 안전하다.

## 멀티 DB 지원

서비스가 하나의 DB 엔진만 쓰면 이 항목은 의미 없다.
MySQL만 쓰면 Flyway든 Liquibase든 상관없다.
그런데 서비스가 커지면 상황이 달라진다.
결제는 PostgreSQL, 주문은 MySQL, 분석은 Redshift.
Liquibase의 추상화 레이어가 빛을 발하는 순간이다.
Flyway도 여러 DB를 지원하지만 결국 DB별 SQL 파일을 따로 관리해야 한다.
`V1__create_orders_mysql.sql`과 `V1__create_orders_postgresql.sql`이 공존한다.
엔진이 하나면 Flyway, 여럿이면 Liquibase.
판단은 단순하다.

## CI/CD 통합

둘 다 CI/CD에 잘 붙는다.
Maven, Gradle 플러그인이 있고 CLI로도 실행할 수 있다.

[Flyway]
`flyway migrate` 한 줄이면 된다.
설정 파일에 DB 접속 정보 넣고 실행.
Jenkins든 GitHub Actions든 스텝 하나 추가면 끝.

[Liquibase]
`liquibase update` 한 줄이면 된다. 여기까지는 같다.
다만 Liquibase는 diff, snapshot, generateChangeLog 같은 부가 기능이 많아서 파이프라인이 복잡해질 수 있다.

- 단순한 파이프라인을 원하면 Flyway.
- 승인 게이트, diff 검증, 환경별 분기까지 원하면 Liquibase.

## 소규모 팀에서 Flyway가 유리한 이유

개발자가 5명인 팀이 있다. 마이크로서비스 하나에 MySQL 하나.
이 팀에 Liquibase의 추상화가 필요한가? 필요 없다.
SQL 파일 하나 만들고 PR 올리고 merge하면 끝이다.
새 팀원이 와도 10분이면 이해한다.
"V번호 붙여서 SQL 파일 만들면 됩니다."
Liquibase는 changelog 문법을 배워야 하고, XML이든 YAML이든 구조를 이해해야 한다.
학습 곡선이 도구 선택의 가장 큰 비용이다.

## 엔터프라이즈에서 Liquibase가 유리한 이유

개발자가 200명이고 DB가 15종류다.
DBA 팀이 모든 DDL을 리뷰한다.
환경이 dev, staging, qa, prod 네 개다.
Liquibase는 이 복잡성에 맞는 도구를 제공한다.
context 태그로 환경별 분기, precondition으로 "이 테이블 있을 때만 실행", label로 릴리스 단위 묶기.
Flyway의 단순함은 이 규모에서 한계가 온다.
환경별 SQL 파일 분기, 조건부 실행, 감사 로그.
전부 커스텀으로 만들어야 한다.

## 실행 이력과 감사

Flyway는 `flyway_schema_history`에 파일명, 체크섬, 실행 시각을 기록한다.
단순하지만 필요한 정보는 다 있다.
Liquibase는 `DATABASECHANGELOG`에 changeSet별로 author, context, label까지 기록한다.
누가 어떤 맥락에서 어떤 변경을 넣었는지 테이블 하나로 추적할 수 있다.
DBA가 "이 컬럼 언제 추가됐어요?" 물어보면 두 도구 모두 이력 테이블에서 답을 찾을 수 있다.
Liquibase가 좀 더 상세할 뿐이다.

## DBA가 마이그레이션 도구를 볼 때

DBA는 마이그레이션 도구 자체보다 그 안에 담긴 DDL을 본다.

[DDL 순서]
FK가 있는 테이블을 먼저 만들면 실패한다.
참조 대상이 먼저 존재해야 한다.
도구가 순서를 보장하는가?
Flyway는 파일명 순서, Liquibase는 changelog 순서.
둘 다 개발자가 순서를 틀리면 막아주지 못한다.

[락 영향]
ALTER TABLE이 MDL을 잡으면 서비스가 멈춘다.
마이그레이션 도구는 이걸 모른다.
`pt-online-schema-change`나 `gh-ost`로 우회해야 하는데 그건 도구 밖의 영역이다.

## Flyway의 치명적 약점

한번 적용한 마이그레이션은 수정할 수 없다.
체크섬이 바뀌면 Flyway가 에러를 뱉는다.
"V3 파일에 오타가 있어서 고쳤어요."
prod에는 이미 적용됐다.
체크섬 불일치.
`flyway repair`로 강제 맞추거나 새 마이그레이션으로 패치해야 한다.
개발 초기에는 스키마가 자주 바뀐다.
매번 새 파일을 만들면 V1부터 V47까지 쌓인다.
Liquibase는 changeSet 단위 관리라 유연하다.

## DBA 관점에서의 정리

마이그레이션 도구는 DDL의 버전 관리다.
어떤 도구를 쓰든 핵심은 같다.
변경을 추적하고 순서를 보장하고 반복 가능하게 만드는 것.
Flyway는 단순하다. SQL만 쓰면 된다.
Liquibase는 유연하다. 복잡한 환경에 맞는 기능이 있다.
DBA의 본질적 관심사는 도구 선택이 아니다.
그 안에 담긴 DDL이 락을 얼마나 잡는지, 순서가 맞는지, 롤백이 필요할 때 어떻게 할 건지.
도구는 결국 수단이다.
팀이 작고 DB가 하나면 Flyway.
조직이 크고 환경이 복잡하면 Liquibase.
판단 기준은 기능이 아니라 맥락이다.