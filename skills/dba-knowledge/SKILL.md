---
name: dba-knowledge
description: 데이터베이스 관련 질문(스키마, 인덱스, 쿼리, 트랜잭션, 락, 백업, 캐시, 메시지, ORM, 마이그레이션, DDL, 운영 환경 테이블 변경, 대용량 데이터, 장애 대응)이 오면 사용한다. 데이터베이스를 잘 모르고 답을 추측하기보다 이 스킬의 지식 문서를 먼저 조회해서 근거를 갖고 답한다. DB가 아닌 일반 개발 질문에는 사용하지 않는다.
---

# DBA Knowledge Base 스킬

DB 설계·운영을 다루는 38개 지식 문서를 라우팅해서 답변할 때 근거로 삼는 스킬이다. 11개 도메인 섹션으로 구성된 지식 문서를, 질문에 맞는 문서를 골라 읽고 `DBA-XXX` 출처를 달고 답한다.

## 패키지 구조

```text
dba-knowledge/
├── SKILL.md             # 이 파일 (진입점)
├── README.md            # 사람용 안내
├── knowledge-map.md     # 11개 섹션 라우팅 지도
├── retrieval-guide.md   # 조회 절차
├── metadata-schema.md   # frontmatter 규칙
├── document-index.md    # DBA-XXX ID 매핑표
└── annotated/           # 지식 문서 38개 (frontmatter 포함, 읽기용)
```

## 조회 절차

1. 질문에서 도메인 단어(결제, 쇼핑몰, 검색, SNS, 푸시, 크롤링, 분석 등)와 기술 용어(인덱스, 트랜잭션, 락, ORM, 캐시, 백업 등)를 분리한다.
2. `knowledge-map.md`의 라우팅 우선순위에 따라 후보 섹션을 고른다.
3. 후보 문서의 `annotated/` frontmatter를 읽고 `triggers`, `code_signals`, `applies_to`를 확인한다.
4. 가장 많이 맞는 문서의 본문을 읽고 답한다. 한 문서로 결론이 안 나면 `read_also`로 이어 읽는다.
5. 답변 끝에 `참고: DBA-XXX` 출처를 붙인다.

## 원칙

- 답은 문서 본문에서 근거를 찾아 낸다. 추측으로 답하지 않는다.
- ID는 `document-index.md` 기준이고 절대 변경하지 않는다.
- `annotated/` 문서는 읽기 전용이다. 내용 수정은 저장소 관리자가 meta 문서를 통해 관리한다.
