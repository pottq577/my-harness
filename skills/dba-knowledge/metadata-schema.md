# DBA 문서 메타데이터 스키마

이 파일은 이 스킬 패키지의 `annotated/` 아래 문서들에 붙이는 YAML frontmatter의 작성 규칙을 정의한다. 규칙이 바뀌면 이 파일이 기준이고, `annotated/` 문서들은 이 규칙을 따라야 한다.

## 원칙

- frontmatter는 문서 최상단에 `---`로 감싼 YAML 블록으로 둔다.
- 각 문서는 `document-index.md`에 고정된 ID를 가진다. ID는 절대 변경하지 않는다.
- `annotated/`의 문서는 지식 문서 최종본이며, 각자가 frontmatter를 갖는다. `raw/`는 원문 계보 보존용이며 라우팅 대상이 아니다.
- ID, title, topics, applies_to 등 AI가 라우팅을 결정하는 데 쓰는 필드는 규칙을 통일해서 쓴다.

## 필수 필드

```yaml
id:
title:
status:
topics:
triggers:
applies_to:
summary:
```

## 권장 필드

```yaml
code_signals:
risk_signals:
read_when:
read_also:
```

## 필드별 작성 기준

| 필드           | 작성 방식                                               |
| -------------- | ------------------------------------------------------- |
| `id`           | `DBA-001` 형식. `document-index.md`와 1:1. 변경 금지    |
| `title`        | 본문 H1과 동일. 반드시 일치시킨다                       |
| `status`       | `draft`, `stable`, `needs-review`, `deprecated` 중 하나 |
| `topics`       | 짧은 영문 태그. 소문자, 하이픈 구분                     |
| `triggers`     | 사람이 질문할 법한 실제 표현이나 상황                   |
| `code_signals` | 코드, SQL, 설정 파일에서 보이는 문자열 패턴             |
| `applies_to`   | 아래 고정 어휘 목록에서만 선택                          |
| `risk_signals` | 장애/성능/정합성 위험 신호                              |
| `read_when`    | 이 문서를 읽어야 하는 조건                              |
| `read_also`    | 함께 읽을 문서 ID 목록. `DBA-XXX` 형식                  |
| `summary`      | 2~4문장 요약. 한 번에 요점을 건지도록 작성              |

## 작성 규칙

- `topics`: 소문자 영문, 3~6개. 예: `null`, `three-valued-logic`, `data-modeling`.
- `triggers`: 구체적일수록 좋다. "NULL을 허용해도 되는가", "결제 상태를 어떻게 저장하나" 같은 실제 대화 표현.
- `code_signals`: 그대로 옮겨 쓰거나 앞뒤를 자른 문자열. 예: `"IS NULL"`, `"ON DELETE CASCADE"`, `"maximumPoolSize"`.
- `applies_to`: 아래 어휘 중 해당하는 것만. 상황에 따라 겹치게 선택할 수 있다.
- `risk_signals`: 나쁜 판단이자 코드에서 보면 위험한 신호를 서술한다.
- `summary`: markdown의 `>` 블록 스칼라로 2~4문장. 마침표로 끝나고 첫 필드명과 들여쓰기를 지킨다.

## applies_to 어휘

문서와 메타데이터, knowledge-map 라우팅에 공통으로 쓰는 고정 어휘다.

| 값                         | 의미                                     |
| -------------------------- | ---------------------------------------- |
| `domain-modeling`          | 도메인 분석, 엔티티/데이터 모델링        |
| `schema-design`            | 테이블/컬럼/제약 조건 설계               |
| `sql-review`               | SQL 작성과 리뷰                          |
| `query-review`             | 느린 쿼리 원인 분석                      |
| `indexing`                 | 인덱스 설계                              |
| `performance-tuning`       | 성능 튜닝                                |
| `transaction-design`       | 트랜잭션 경계와 격리 설계                |
| `concurrency-safety`       | 동시성 안전성                            |
| `orm-review`               | ORM 코드 리뷰                            |
| `application-architecture` | 커넥션 풀, 캐시, 메시지, 이벤트 아키텍처 |
| `production-ddl`           | 운영 환경 DDL 실행                       |
| `migration`                | 마이그레이션, 대용량 데이터 변경         |
| `backup-recovery`          | 백업과 복구                              |
| `incident-response`        | 장애 대응                                |
| `monitoring`               | 모니터링, 진단                           |
| `cache-design`             | 캐시 설계                                |
| `event-design`             | 이벤트/메시지 아키텍처                   |
| `analytics`                | 분석 쿼리, 데이터 웨어하우스             |

## 작성 예시

```markdown
---
id: DBA-001
title: NULL을 이해한다는 것: WHERE a != 1 이 NULL을 빠뜨리는 이유
status: stable

topics:
  - null
  - three-valued-logic
  - data-modeling

triggers:
  - WHERE status != 1 인데 NULL 행이 빠진다
  - NULL과 빈 문자열을 어떻게 구분하나
  - nullable 컬럼을 허용해도 되나

code_signals:
  - "IS NULL"
  - "IS NOT NULL"
  - "COALESCE"
  - "@Column(nullable = true)"

applies_to:
  - schema-design
  - query-review
  - domain-modeling

risk_signals:
  - NULL이 비즈니스 상태를 의미함
  - NULL과 빈 문자열을 혼용함
  - nullable 컬럼이 조건 분기를 복잡하게 만듦

read_when:
  - 컬럼을 nullable로 둘지 결정해야 할 때
  - NULL 때문에 조회 결과가 예상과 다를 때
  - 도메인 상태를 NULL로 표현하려고 할 때

read_also:
  - DBA-002
  - DBA-003

summary: >
  NULL의 의미, SQL 조건식에서의 동작, 데이터 모델링에서 nullable 컬럼을
  허용할 때의 판단 기준과 위험을 다룬다.
---
```
