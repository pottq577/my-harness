---
name: dba-knowledge
description: 데이터베이스 관련 질문(스키마, 인덱스, 쿼리, 트랜잭션, 락, 백업, 캐시, 메시지, ORM, 마이그레이션, DDL, 운영 환경 테이블 변경, 대용량 데이터, 장애 대응, DB 기술 선택, DB 면접과 이력서)이 오면 사용한다. 데이터베이스를 잘 모르고 답을 추측하기보다 이 스킬의 지식 문서를 먼저 조회해서 근거를 갖고 답한다. DB가 아닌 일반 개발 질문에는 사용하지 않는다.
---

# DBA Knowledge Base 스킬

DB 설계와 운영, DB 기술 선택과 직무 성장을 다루는 55개 지식 문서를 라우팅해 답변의 근거로 삼는 스킬이다. 12개 섹션에서 질문에 맞는 문서를 골라 읽고 `DBA-XXX` 출처를 달아 답한다.

## 패키지 구조

```text
dba-knowledge/
├── SKILL.md             # 이 파일 (진입점)
├── README.md            # 사람용 안내
├── knowledge-map.md     # 12개 섹션 라우팅 지도
├── retrieval-guide.md   # 조회 절차
├── metadata-schema.md   # frontmatter 규칙
├── document-index.md    # DBA-XXX ID 매핑표
├── raw/                 # 원문 7개 (계보 보존용)
└── annotated/           # 지식 문서 55개 (frontmatter 포함, 조회용)
```

## 조회 절차

1. 질문에서 도메인 단어, 기술 용어, 현재성 요구를 분리한다.
2. `knowledge-map.md`의 라우팅 우선순위에 따라 후보 섹션을 고른다.
3. 후보 문서의 `annotated/` frontmatter를 읽고 `triggers`, `code_signals`, `applies_to`를 확인한다.
4. 가장 많이 맞는 문서의 본문을 읽고 답한다. 한 문서로 결론이 안 나면 `read_also`로 이어 읽는다.
5. 버전, 가격, 기능 지원과 한도처럼 변하는 사실은 공식 문서로 다시 확인한다.
6. 답변 끝에 `참고: DBA-XXX` 출처를 붙인다.

## 원칙

- 답은 문서 본문에서 근거를 찾아 낸다. 추측으로 답하지 않는다.
- ID는 `document-index.md` 기준이고 절대 변경하지 않는다.
- 질문에 답할 때는 `annotated/`만 읽고 `raw/`는 근거로 사용하지 않는다.
- 문서 유지보수는 이 저장소의 `annotated/`, `document-index.md`, `knowledge-map.md`에 직접 반영한다.
- 같은 주제의 원문이 문장 축약, 줄바꿈, 코드 블록 언어, 목록 표현만 다른 경우 의미 중복으로 판단해 기준 문서 하나에 연결한다.
