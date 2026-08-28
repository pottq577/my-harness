# my-harness 에이전트 지침 (AGENTS)

이 레포는 에이전트 스킬과 플러그인 저장소다. 이 파일은 AGENTS 규격을 읽는 에이전트(Codex, opencode 등)의 진입점이다.

## 처음 이 레포를 열면

1. `README.md`를 읽는다. 스킬 목록, 설치 경로, 구조를 여기서 파악한다.
2. 질문이 데이터베이스 관련이면 `skills/dba-knowledge/`의 스킬을 사용한다.
3. 그 밖의 스킬이 필요하면 `skills/` 아래를 찾아 `SKILL.md`를 읽는다.

## 스킬 사용 규칙

- 스킬은 `skills/<name>/SKILL.md`가 진입점이다. `description`을 보고 트리거 여부를 판단한다.
- `dba-knowledge`는 DB 지식 베이스로, 지식 문서(`annotated/`)를 라우팅해 답하고 출처(`DBA-XXX`)를 단다.
- 스킬 폴더 안의 문서는 읽기 전용이다. 수정은 저장소에 변경을 제안하는 방식으로 한다.
