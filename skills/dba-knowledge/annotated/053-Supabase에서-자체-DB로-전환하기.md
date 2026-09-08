---
id: DBA-053
title: "Supabase에서 자체 DB로 넘어가야 할 때는 언제인가?"
status: stable

topics:
  - supabase
  - postgresql
  - migration
  - vendor-lock-in
  - cutover

triggers:
  - Supabase에서 자체 PostgreSQL로 옮겨야 하나
  - Supabase 의존성을 어떻게 조사하나
  - 관리형 DB 이전의 컷오버와 롤백을 어떻게 하나

code_signals:
  - "supabase db dump"
  - "auth.users"
  - "storage.objects"
  - "pg_restore"
  - "Realtime"

applies_to:
  - migration
  - application-architecture
  - backup-recovery

risk_signals:
  - DB만 덤프하면 Auth와 Storage도 함께 옮겨진다고 가정
  - 연결 수와 가격을 고정값으로 판단

read_when:
  - Supabase 한계와 자체 운영 비용을 비교할 때
  - PostgreSQL 이전 계획과 롤백 기준을 만들 때

read_also:
  - DBA-023
  - DBA-030
  - DBA-047

source_sections:
  - "raw/6.md:1432-1655"

verified_at: 2026-09-09

references:
  - "https://supabase.com/docs/guides/self-hosting/restore-from-platform"
  - "https://supabase.com/docs/guides/database/connection-management"
  - "https://supabase.com/pricing"

summary: >
  Supabase의 속도와 관리 편의성을 자체 PostgreSQL의 통제력과 비교하고,
  Auth, Storage, Realtime 의존성 조사부터 단계적 전환과 롤백까지 설명한다.
---
# Supabase에서 자체 DB로 넘어가야 할 때는 언제인가?

Supabase는 빠르다.
회원가입 하고 테이블 만들고 API 키 받으면 바로 CRUD가 된다.
인증, 스토리지, 실시간 구독까지 백엔드 없이 프론트만으로 서비스가 돌아간다.
그런데 서비스가 커지면 어느 순간 벽을 만난다.
그 벽이 보이기 시작하면 자체 DB로 넘어갈 때다.

## Supabase란

PostgreSQL 위에 얹은 BaaS(Backend as a Service)다.
PostgREST로 테이블을 자동으로 REST API로 노출하고, GoTrue로 인증을 처리하고, Realtime으로 CDC 기반 구독을 제공한다.
DB를 직접 만질 수 있다는 게 Firebase와의 가장 큰 차이다.
PostgreSQL이니까 SQL도 치고, 인덱스도 걸고, 함수도 만들 수 있다.
"관리형 PostgreSQL + 자동 API + 인증"
한 문장으로 요약하면 이거다.

## Supabase의 장점 1 - 속도

가장 큰 장점. 프로토타입에서 MVP까지의 속도가 압도적이다.
테이블 만들면 API가 자동으로 생긴다.
인증 붙이는 데 하루면 된다.
Row Level Security로 권한 제어까지 된다.
백엔드 서버를 따로 만들 필요가 없다.
DevOps 엔지니어가 없어도 된다.
스타트업 초기, 해커톤, 사이드 프로젝트.
"일단 돌아가는 것"이 중요한 시점에서 Supabase는 최선의 선택이다.

## 장점 2 - PostgreSQL 그 자체

Firebase는 NoSQL(Firestore)이라 복잡한 쿼리, JOIN, 트랜잭션이 어렵다.
Supabase는 PostgreSQL이다.
ACID 트랜잭션이 된다.
복잡한 JOIN이 된다.
윈도우 함수, CTE, 서브쿼리 다 된다.
나중에 자체 DB로 옮길 때도 PostgreSQL → PostgreSQL이면 마이그레이션 난이도가 확 낮아진다.
데이터 모델 자체를 바꿀 필요가 없다.

## 장점 3 - 관리 부담 제로

DB 서버 프로비저닝, 백업 설정, 모니터링 구성, 보안 패치, 버전 업그레이드.
이걸 다 Supabase가 해준다.
팀에 DBA가 없고 인프라 엔지니어도 없는 초기 팀에게 이건 결정적인 장점이다.
DB가 죽어도 새벽 3시에 일어날 사람이 없는 팀이라면 관리형 서비스가 맞다.

## 장점 4 - 내장 기능 생태계

- 인증(Auth) - 이메일, OAuth, 매직링크
- 스토리지(Storage) - S3 호환 파일 저장
- 엣지 펑션(Edge Functions) - Deno 기반 서버리스
- 실시간(Realtime) - WebSocket 기반 변경 구독
- 벡터(pgvector) - AI 임베딩 검색

이걸 각각 구축하면 Auth0 + S3 + Lambda + Pusher + Pinecone.
5개 서비스를 붙여야 한다.
Supabase 하나면 대시보드 하나에서 전부 관리된다.

## 장점 5 - 비용 구조 (초기)

초기에는 DB, 인증, 스토리지, API 운영 비용을 한 서비스에서 시작할 수 있다.
플랜 가격과 포함량은 자주 바뀌므로 이 문서의 고정 수치가 아니라 공식 가격표와 프로젝트 사용량을 기준으로 비교한다.
비교할 때는 인프라 비용뿐 아니라 운영 인력과 장애 대응 비용도 포함한다.

## 그런데 왜 넘어가야 하나

Supabase가 이렇게 좋은데 왜 자체 DB로 옮기는 팀이 생기나.
서비스가 커지면서 "편리함의 대가"가 보이기 시작하기 때문이다.
처음에는 느끼지 못한다. 트래픽이 적고, 데이터가 적고, 요구사항이 단순할 때는.
문제는 성장하면서 드러난다.

## 단점 1 - 성능 제어권 부재

Supabase의 컴퓨트 자원과 한도는 프로젝트의 컴퓨트 크기에 따라 달라진다.
슬로우 쿼리가 터졌을 때 pg_stat_statements를 볼 수는 있지만, postgresql.conf를 직접 튜닝할 수 없다.
shared_buffers, work_mem, effective_cache_size, max_connections.
이 파라미터들을 워크로드에 맞게 조정할 수 없다는 건 일정 규모 이상에서는 치명적이다.
"왜 느린지는 아는데 고칠 수가 없다."
이 상황이 반복되면 옮겨야 할 때다.

## 단점 2 - 연결 수 제한

직접 연결과 Supavisor 풀의 연결 한도는 컴퓨트 크기와 풀 설정에 따라 달라진다.
서버리스 아키텍처에서는 함수 하나 실행될 때마다 커넥션을 연다.
동시 요청이 몰리면 순식간에 풀이 소진된다.
자체 DB라면 PgBouncer를 앞에 두고 transaction 모드로 수천 개를 처리할 수 있다.
max_connections도 인스턴스 스펙에 맞게 자유롭게 올릴 수 있다.

## 단점 3 - PostgREST의 한계

PostgREST가 자동으로 만들어주는 API는 CRUD에는 충분하다.
하지만 비즈니스 로직이 복잡해지면 한계가 온다.
여러 테이블을 하나의 트랜잭션으로 묶는 작업, 조건부 업데이트,
복잡한 집계 + 페이지네이션.
결국 DB Function(PL/pgSQL)을 만들어서 RPC로 호출하게 된다.
DB에 비즈니스 로직이 쌓이기 시작하면 그건 더 이상 "간편한 BaaS"가 아니다.
복잡한 PL/pgSQL을 관리하느니 백엔드 서버를 두는 게 낫다.

## 단점 4 - Row Level Security의 복잡성

RLS는 강력하지만 정책이 복잡해지면 관리가 어렵다.
"이 사용자는 자기 팀의 데이터만 볼 수 있고, 매니저는 하위 팀까지 볼 수 있고, 어드민은 전체를 볼 수 있되 삭제는 못 하고..."
이런 정책이 테이블마다 붙으면 RLS 함수만 수십 개가 된다. 디버깅이 어렵다.
"이 사용자가 왜 이 데이터를 못 보죠?" 에 대한 답을 찾으려면 RLS 정책 체인을 하나하나 따라가야 한다.
성능 문제도 있다.
RLS 정책이 복잡할수록 매 쿼리마다 추가 비용이 든다.

## 단점 5 - 비용 역전 (성장 후)

초기에는 통합 관리 비용이 작지만 데이터, 컴퓨트, 네트워크 사용량이 늘면 비용 구조가 달라진다.
현재 가격표로 Supabase 총비용과 자체 PostgreSQL의 인프라, 운영 인력, 백업, 관측 비용을 같은 조건에서 비교한다.

## 단점 6 - 벤더 종속

Supabase Auth, Storage, Realtime, Edge Functions.
이걸 다 쓰고 있으면 탈출 비용이 높다.
DB 자체는 PostgreSQL이니까 옮기기 쉽다.
하지만 인증 시스템을 Auth0이나 자체 구축으로 바꾸고, 파일 스토리지를 S3로 옮기고, 실시간 구독을 다시 만들고, Edge Functions를 Lambda나 CloudFlare Workers로 바꾸는 건 각각이 프로젝트급 작업이다.
"PostgreSQL이니까 쉽게 옮기겠지"는 DB만 보면 맞고, 전체 스택으로 보면 틀리다.

## 단점 7 - 멀티 리전 / 고가용성

가용성, 읽기 복제본, 리전 구성은 플랜과 제공 기능에 따라 달라진다.
필요한 RTO, RPO, 데이터 위치, 장애 전환 통제권을 현재 공식 기능과 비교해 부족하면 이전을 검토한다.

## 단점 8 - 확장(Extension) 제약

관리형 환경에서는 설치할 수 있는 Extension과 설정 권한이 제한될 수 있다.
필요한 Extension과 버전을 현재 지원 목록에서 확인하고, 지원되지 않거나 서버 수준 권한이 필요하면 자체 운영을 검토한다.

## 넘어가야 할 신호 - 체크리스트

아래 중 3개 이상 해당되면 마이그레이션을 진지하게 검토할 때다.

- 슬로우 쿼리가 반복되는데 튜닝할 수단이 없다
- 커넥션 풀이 자주 소진된다
- RLS 정책이 10개를 넘어 관리가 안 된다
- PL/pgSQL 함수가 비즈니스 로직의 핵심이 됐다
- 현재 사용량에서 자체 운영을 포함한 총비용이 지속적으로 더 낮다
- 멀티 리전이나 자동 페일오버가 필요하다
- 지원하지 않는 Extension이 필요하다
- 규제 요건으로 데이터가 특정 인프라에 있어야 한다
- 팀에 DB를 운영할 수 있는 사람이 생겼다

마지막 항목이 핵심이다.
자체 DB는 자유를 주지만 그 자유를 감당할 역량이 필요하다.

## 아직 넘어가지 말아야 할 신호

반대로, 아래에 해당되면 Supabase에 남는 게 낫다.

- 팀이 5명 이하이고 백엔드 전담이 없다.
- 트래픽이 예측 가능하고 급격한 성장이 없다.
- 데이터와 트래픽이 현재 플랜 한도 안에서 충분히 여유롭다.
- 인프라 운영 경험이 팀에 없다.
- 제품-시장 적합성(PMF)을 아직 못 찾았다.

PMF 전에 인프라에 투자하는 건 집 지을 땅도 안 샀는데 인테리어 업체를 부르는 것과 같다.

## 넘어간다면 - 단계별 전략

한 번에 다 옮기면 사고 난다. 단계적으로 간다.

1. 1단계: 백엔드 서버 도입
   1. PostgREST 직접 호출을 걷어내고 백엔드 API 서버를 사이에 둔다.
   2. DB는 아직 Supabase 그대로.
2. 2단계: DB 마이그레이션
   1. 공식 절차의 `supabase db dump`로 roles, schema, data를 분리 덤프해 대상 PostgreSQL에 복원한다.
   2. 소스와 대상 PostgreSQL 버전, 확장, 소유자와 권한 차이를 먼저 검증한다.
   3. 백엔드의 연결 문자열을 전환하고 즉시 되돌릴 수 있게 이전 값을 보존한다.
3. 3단계: 부가 서비스 전환
   1. Auth → 자체 구축 또는 Auth0/Clerk
   2. Storage → S3 + CloudFront
   3. Realtime → 필요 시 별도 구현

1단계와 2단계 사이에는 변경 데이터 동기화 방식과 쓰기 소유자를 명확히 정한다.
무계획한 이중 쓰기는 피하고, 동결 또는 CDC 방식 중 하나를 선택해 행 수와 핵심 집계를 대조한 뒤 전환한다.
오류율, 지연, 정합성 임계치를 넘으면 연결을 원본으로 되돌리는 롤백 기준을 미리 둔다.

## 마이그레이션 시 주의할 것들

Supabase가 자동으로 만들어주는 것들이 있다.
이걸 놓치면 마이그레이션 후 장애가 난다.

[auth.users 테이블]
Supabase Auth가 관리하는 사용자 테이블.
자체 인증으로 바꾸면 이 데이터를 새 시스템으로 옮겨야 한다.
비밀번호 해시 호환성을 확인해야 한다.

[storage.objects 테이블]
파일 메타데이터와 실제 객체는 DB 덤프만으로 이전되지 않는다.
공식 복원 가이드의 별도 Storage 마이그레이션 절차가 필요하다.

[RLS 정책]
정규 컬럼의 제약조건이 아니라 정책(Policy)으로 걸려 있다.
자체 DB로 옮기면 애플리케이션 레벨에서 권한 체크를 다시 구현해야 한다.

[pg_net, pg_cron 등 Supabase 전용 설정]
프로젝트에서 사용 중인 Supabase 특화 기능을 먼저 목록화한다.

[Edge Functions와 프로젝트 설정]
Edge Functions, JWT 비밀, 인증 제공자, SMTP와 사용자 지정 도메인은 DB 덤프에 포함되지 않는다.
대상 환경에서 별도로 재구성하고 전환 전에 기능별 검증을 끝낸다.

## DBA 관점에서의 정리

Supabase는 "DB를 몰라도 되는 세계"를 만들어줬다. 그리고 그 세계는 놀라울 정도로 잘 작동한다. 일정 규모까지는.
넘어가야 할 때의 핵심 판단 기준은 결국 두 가지다.
"제어권이 필요한가?"
"그 제어권을 행사할 역량이 있는가?"
둘 다 Yes면 넘어간다. 하나라도 No면 남는다.
Supabase에서 시작해서 자체 DB로 졸업하는 건 부끄러운 게 아니다.
서비스가 그만큼 성장했다는 뜻이다.
다만 졸업 시점을 너무 늦추면 기술 부채가 이자처럼 쌓이고, 너무 당기면 아직 필요 없는 복잡성을 떠안는다. 타이밍이 전부다.
그걸 알기 위해서 DB공부를 해야하는 이유다.
