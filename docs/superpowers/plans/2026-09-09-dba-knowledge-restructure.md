# DBA 지식 베이스 재구성 실행 계획

설계 문서: `docs/superpowers/specs/2026-09-09-dba-knowledge-restructure-design.md`

- [x] 1. `raw/` 체크섬과 기존 문서 집합을 기록한다.
  - 검증: 작업 전 SHA-256과 Git 상태를 보관한다.
- [x] 2. 중복 원문을 기존 기준 문서에 연결하고 부분 중복의 고유 내용을 병합한다.
  - 대상: `DBA-018`, `DBA-019`, `DBA-023`, `DBA-027`, `DBA-029`, `DBA-036`, `DBA-038`
  - 검증: 중복 항목마다 기준 문서가 하나뿐인지 확인한다.
- [x] 3. 운영과 설계 주제를 `DBA-039`부터 `DBA-054`까지 구조화한다.
  - 검증: YAML 파싱, ID 고유성, 출처 범위를 확인한다.
- [x] 4. 학습, 면접, 이력서 주제를 `DBA-999`로 통합한다.
  - 검증: 세 원문의 고유 목적이 문서 안에서 모두 검색되는지 확인한다.
- [x] 5. `document-index.md`, `knowledge-map.md`, `metadata-schema.md`, `retrieval-guide.md`, `SKILL.md`, `README.md`를 최신화한다.
  - 검증: 모든 annotated 문서가 색인과 지도에 정확히 한 번 나타나며 링크가 유효한지 확인한다.
- [x] 6. 공식 문서가 필요한 최신성 항목을 교정한다.
  - 검증: DynamoDB, Aurora와 RDS, Redis, Supabase, PostgreSQL, Jakarta Persistence 관련 문구와 링크를 확인한다.
- [x] 7. 독립 검색 평가와 전체 정합성 검증을 실행한다.
  - 검증: RED 평가의 공백이 해소되고 raw 체크섬이 유지되며 스킬 검증이 통과한다.
- [x] 8. 변경을 추적 가능한 범위로 나누어 커밋한다.
  - 검증: 각 커밋의 경로와 목적이 분리되어 있고 최종 작업 트리가 깨끗하다.
