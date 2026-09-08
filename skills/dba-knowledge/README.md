# dba-knowledge

DB 설계, 스키마, 인덱스, 쿼리, 트랜잭션, 락, 백업, 캐시, 메시지, ORM, 마이그레이션, 운영 DDL, 대용량 데이터, 장애 대응, 기술 선택과 DB 직무 성장을 다루는 지식 베이스 스킬이다. 55개 문서가 12개 섹션으로 구성되어 있고 질문에 맞는 문서를 라우팅해 출처(`DBA-XXX`)와 함께 답하게 한다.

## 구성

```text
dba-knowledge/
├── SKILL.md             # 에이전트 진입점
├── knowledge-map.md     # 12개 섹션 라우팅 지도
├── metadata-schema.md   # frontmatter 규칙
├── document-index.md    # DBA-XXX ID 매핑표 (55개)
├── raw/                 # 원문 7개, 변경하지 않는 계보 자료
└── annotated/           # 스킬용 지식 문서 55개
```

문서 ID는 `DBA-001`부터 `DBA-054`, 그리고 직무 성장 문서 `DBA-999`이며 `document-index.md`와 1:1이다.
`raw/`는 원문 계보를 보존하는 경로이며 실제 질문 라우팅에는 사용하지 않는다.

## 에이전트별 설치

스킬 폴더(`skills/dba-knowledge/`)를 에이전트가 스킬을 읽는 위치에 놓는다.

- **Claude Code**: `~/.claude/skills/dba-knowledge/` 로 복사하거나 심링크
- **Codex**: 자체 스킬 디렉토리(`~/.codex/skills/` 등)에 복사
- **opencode**: `~/.agents/skills/` 또는 전역 스킬 경로, 또는 설정의 skills 경로에 등록

복사가 아니라 레포를 클론하고 여기에서 스킬 폴더로 심링크하면 업데이트 추적이 쉽다. 설치 후 스킬이 로드되도록 에이전트를 재시작한다.

## 에이전트 사용 예시

```text
작업: PostgreSQL에서 재고 동시 주문 로직을 구현한다.
조회: DBA-034, DBA-014를 읽고 현재 스키마와 트랜잭션 경계를 확인한다.
적용: PostgreSQL에 맞는 락을 선택하고 구현 설명에 사용한 문서 ID를 적는다.
```

## 유지보수

- `skills/dba-knowledge/`가 DBA 지식 베이스의 단일 원본이다. PEOPLO의 기존 사본과 동기화하지 않는다.
- 질문에 답할 때는 `annotated/`를 읽기 전용으로 사용하고 `raw/`를 근거로 사용하지 않는다.
- 스킬 문서를 추가하거나 갱신할 때는 `annotated/`에 직접 반영한다.
- 새 문서 추가는 `metadata-schema.md`의 frontmatter 규칙을 따르고, `document-index.md`에 ID를 고정해 등록한다.
- 버전, 가격, 제한과 지원 기능은 `verified_at`과 공식 `references`를 기록하고 답변 시점에 다시 확인한다.
