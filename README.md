# my-harness

개인 개발 환경의 에이전트(Claude Code, Codex, opencode 등)가 공용으로 쓰는 스킬과 플러그인 저장소다. 이 레포를 클론하면 어떤 프로젝트에서든 아래 스킬을 설치해서 쓸 수 있다.

루트의 `AGENTS.md`, `CLAUDE.md`는 에이전트가 이 레포를 열었을 때 읽는 진입점이다. `skills/` 아래에 스킬이 있고, 앞으로 `plugins/`가 추가될 예정이다.

## 구성

```text
my-harness/
├── README.md       # 이 파일 (카탈로그)
├── AGENTS.md       # AGENTS 규격 에이전트(Codex, opencode) 진입점
├── CLAUDE.md       # Claude Code 진입점
└── skills/
    └── dba-knowledge/    # DBA 지식 베이스 스킬 (38개 문서)
```

## 스킬 목록

| 스킬                    | 설명                            | 설치 경로                                   |
| ----------------------- | ------------------------------- | ------------------------------------------- |
| `skills/dba-knowledge/` | DB 설계·운영 지식 베이스 라우팅 | `~/.claude/skills/`, `~/.agents/skills/` 등 |

## 설치 방법

각 스킬의 `README.md`에 에이전트별 설치 경로가 있다. 스킬 폴더를 해당 위치에 복사하거나 아래처럼 심링크하면 업데이트가 바로 반영된다.

```bash
ln -s "$PWD/skills/dba-knowledge" ~/.claude/skills/dba-knowledge
```

## 새 스킬 추가 규칙

- `skills/<name>/` 폴더에 `SKILL.md`를 두고 frontmatter(`name`, `description`)를 채운다. `description`에 트리거 키워드를 명확히 한다.
- 스킬 폴더 안에는 `SKILL.md`와 필요 문서만 둔다. 에이전트 자동 로드 진입점은 루트의 `AGENTS.md`/`CLAUDE.md`이며 여기서 스킬을 안내한다.
- 스킬을 추가하면 이 카탈로그를 함께 갱신한다.
