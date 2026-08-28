# dba-knowledge

DB 설계, 스키마, 인덱스, 쿼리, 트랜잭션, 락, 백업, 캐시, 메시지, ORM, 마이그레이션, 운영 DDL, 대용량 데이터, 장애 대응을 다루는 지식 베이스 스킬이다. 38개 문서가 11개 도메인 섹션으로 구성되어 있고, 질문에 맞는 문서를 라우팅해 출처(`DBA-XXX`)와 함께 답하게 한다.

## 구성

```text
dba-knowledge/
├── SKILL.md             # 에이전트 진입점
├── knowledge-map.md     # 11개 섹션 라우팅 지도
├── retrieval-guide.md   # 조회 절차
├── metadata-schema.md   # frontmatter 규칙
├── document-index.md    # DBA-XXX ID 매핑표 (38개)
└── annotated/           # 지식 문서 38개
```

문서 ID는 `DBA-001`부터 `DBA-038`, `document-index.md`와 1:1이다.

## 에이전트별 설치

스킬 폴더(`skills/dba-knowledge/`)를 에이전트가 스킬을 읽는 위치에 놓는다.

- **Claude Code**: `~/.claude/skills/dba-knowledge/` 로 복사하거나 심링크
- **Codex**: 자체 스킬 디렉토리(`~/.codex/skills/` 등)에 복사
- **opencode**: `~/.agents/skills/` 또는 전역 스킬 경로, 또는 설정의 skills 경로에 등록

복사가 아니라 레포를 클론하고 여기에서 스킬 폴더로 심링크하면 업데이트 추적이 쉽다. 설치 후 스킬이 로드되도록 에이전트를 재시작한다.

## 사용 예시

```text
질문: 재고를 동시에 주문하면 중복으로 팔리는 문제를 막으려면?
답변: (DBA-034, DBA-014 라우팅) 락/트랜잭션 근거로 답하고 출처를 붙인다.
```

## 유지보수

- 지식 문서(`annotated/`)는 읽기 전용이다.
- 새 문서 추가는 `metadata-schema.md`의 frontmatter 규칙을 따르고, `document-index.md`에 ID를 고정해 등록한다.
- 문서를 수정하면 두 곳(PEOPLO repo의 학습 KB, 이 스킬 패키지)을 함께 갱신해야 한다.
