---
id: DBA-049
title: "Aurora vs RDS: 비싸도 Aurora를 써야 하는 순간"
status: stable

topics:
  - aurora
  - rds
  - availability
  - replication
  - cost

triggers:
  - Aurora와 RDS 중 무엇을 선택하나
  - Aurora 비용을 정당화할 수 있나
  - 읽기 확장과 빠른 장애 전환이 필요하다

code_signals:
  - "Aurora Cluster"
  - "Reader Endpoint"
  - "Multi-AZ"
  - "Global Database"

applies_to:
  - application-architecture
  - backup-recovery
  - incident-response

risk_signals:
  - 가용성 요구 없이 Aurora를 기본 선택
  - 워크로드 측정 없이 고정 비용 배수로 판단

read_when:
  - AWS 관리형 관계형 DB를 선택할 때
  - 복제, 페일오버, DR 요구와 비용을 비교할 때

read_also:
  - DBA-042
  - DBA-029
  - DBA-030

source_sections:
  - "raw/6.md:222-422"

verified_at: 2026-09-09

references:
  - "https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Concepts.AuroraHighAvailability.html"
  - "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.Failover.html"
  - "https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/CHAP_AuroraOverview.html"
  - "https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.how-it-works.html"
  - "https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-global-database-disaster-recovery.html"
  - "https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/USER_PerfInsights.Enabling.html"

summary: >
  Aurora와 일반 RDS의 저장, 복제, 장애 전환, 확장 구조를 비교하고
  가용성과 운영 요구가 추가 비용을 정당화하는지 판단하는 기준을 제시한다.
---
# Aurora vs RDS: 비싸도 Aurora를 써야 하는 순간

"Aurora 쓰면 3배 비싸잖아요. 그냥 RDS 쓰면 안 돼요?"
이 질문을 정말 많이 받는다.
답은 "안 되는 건 아닌데, 경우에 따라 다르다"이다.
Aurora가 비싼 건 사실이다. 하지만 비싼 만큼 돌려주는 게 있다.
문제는 그 "돌려주는 것"이 모든 서비스에 필요한 건 아니라는 점이다.

## 스토리지 아키텍처가 근본적으로 다르다

RDS는 EBS에 데이터를 저장한다.
인스턴스 하나에 EBS 볼륨이 붙어 있다.
인스턴스가 쓰기를 하면 EBS에 기록한다.
복제본은 별도의 EBS를 가지고 비동기로 데이터를 받는다.
Aurora는 공유 스토리지(Aurora Storage)를 쓴다.
3개 AZ에 6개 복사본을 분산 저장한다.
Writer가 redo log만 스토리지 레이어에 보내면 스토리지가 알아서 페이지를 재구성한다.
이 차이가 모든 것을 바꾼다.
복제 방식, 페일오버 속도, 백업, 복구.

## 복제 차이

RDS 복제는 binlog 기반이다.
Writer가 데이터를 쓰고, binlog를 Reader에 전송하고, Reader가 그걸 재실행한다.
Write 부하가 높으면 복제 지연이 발생한다.
Reader에서 읽은 데이터가 Writer와 다를 수 있다.
Aurora 복제는 스토리지 레이어에서 일어난다.
Writer와 Reader가 같은 스토리지를 공유한다.
Reader는 redo log를 받아서 자기 버퍼 캐시만 갱신하면 된다.
복제 지연이 보통 20ms 이하다.
RDS에서 초 단위 지연이 발생하는 워크로드에서도 Aurora는 밀리초 단위를 유지한다.

## 페일오버 속도

이게 실무에서 체감되는 차이다.
RDS Multi-AZ 페일오버는 AWS 문서 기준으로 보통 60초에서 120초가 걸린다.
DNS 전파, EBS 재마운트, 크래시 리커버리.
그 사이에 서비스가 멈춘다.
Aurora 페일오버는 보통 60초 안에 완료되며, 서비스 상태와 워크로드에 따라 30초보다 짧을 수 있다.
Reader가 이미 같은 스토리지를 보고 있으므로 Writer로 승격할 때 스토리지를 옮길 필요가 없다.
크래시 리커버리도 redo log 기반이라 빠르다.
실제 순단은 DNS 캐시, 연결 재수립, 드라이버 재시도 설정과 승격 대상의 상태에도 좌우된다.
제품의 대표 수치만 비교하지 말고 애플리케이션이 복구되는 시점까지 장애 훈련으로 측정해야 한다.

## 백업과 복구

RDS 백업은 EBS 스냅샷이다. 전체 볼륨을 복사하는 방식.
복구 시 새 인스턴스를 만들고 스냅샷에서 볼륨을 복원한다.
특정 시점 복구(PITR)는 수십 분 걸릴 수 있다.
Aurora의 백업은 연속적이다.
스토리지 레이어가 자동으로 지속적인 백업을 수행한다.
PITR의 보존 기간과 복구 가능 시점은 현재 클러스터 설정에서 확인해야 한다.
Backtrack 기능을 쓰면 인스턴스를 되감기할 수도 있다.
새 인스턴스를 만들 필요 없이 특정 시점으로 되돌린다.
복구 시간은 데이터 크기와 구성에 따라 달라지므로 실제 복구 훈련으로 RTO를 측정해야 한다.

## 비용 차이

솔직한 비용 비교.

[인스턴스 비용]
같은 계열의 인스턴스라도 엔진, 리전, 구매 옵션에 따라 단가가 다르다.

[스토리지 비용]
RDS는 프로비저닝된 만큼 과금된다.
100GB를 할당하면 10GB만 써도 100GB 비용.
Aurora는 사용한 만큼 과금된다.
10GB 쓰면 10GB 비용.
대신 GB당 단가가 RDS보다 높다.

[I/O 비용]
Aurora는 I/O 요청마다 과금된다.
이게 예상치 못한 비용 폭탄이 될 수 있다.
Aurora I/O Optimized를 쓰면 I/O 과금 없이 스토리지 단가만 올라간다.

고정 배수로 결론 내리지 말고 인스턴스, 스토리지, I/O, 백업과 데이터 전송을 실제 워크로드로 계산해야 한다.

## Aurora를 안 써도 되는 경우

모든 서비스에 Aurora가 필요한 건 아니다.
오히려 RDS가 더 맞는 경우가 분명히 있다.

[개발/스테이징 환경]
짧은 페일오버가 중요하지 않고 비용이 더 중요한 환경이다.
RDS 싱글AZ면 충분하다.
하지만 Aurora의 특성을 운영과 동기화 시키기 위해서 그럴 땐 Aurora를 사용하는 것이 맞다.

[소규모 서비스]
일 트래픽이 수천 QPS 이하.
Reader가 필요 없거나 1대면 충분.
RDS 멀티AZ로도 가용성이 충분하다.

[배치/분석 전용 DB]
실시간 가용성이 중요하지 않다.
페일오버 2분이어도 아무도 모른다.

[비용이 절대적 제약]
스타트업 초기.
DB 비용에 2배를 쓸 여유가 없다.
RDS로 시작하고 나중에 Aurora로 마이그레이션해도 된다.

솔직한 내 생각으로는 EC2쓰다가 넘어가도 된다.

## Aurora를 써야 하는 순간

반대로 Aurora가 빛나는 순간이 있다.

[Reader가 많이 필요할 때]
RDS는 Reader를 추가할 때마다 별도 EBS 볼륨이 복제된다.
Aurora는 같은 스토리지를 공유하므로 Reader 추가가 빠르고 복제 지연이 적다.
최대 15대까지 가능하다.

[가용성이 생명인 서비스]
주문, 결제, 인증.
장애 전환 시간의 차이가 매출에 직결된다.
장애 시 빠른 복구가 보장돼야 하는 서비스.

[데이터 크기가 큰 서비스]
수 TB 이상의 데이터를 다루면 EBS 기반 RDS의 I/O 한계가 먼저 온다.
Aurora 스토리지는 자동으로 256TB까지 확장된다.

## Global Database

Aurora에만 있는 기능이다.
리전 간 복제를 스토리지 레이어에서 수행한다.
서울 리전의 Writer가 쓰면 오레곤 리전의 Reader가 1초 이내에 반영한다.
RDS에서 리전 간 복제를 하려면 binlog 기반 Cross-Region Read Replica를 써야 한다.
복제 지연이 수 초에서 수십 초.
리전 장애 전환 시간은 구성과 관리 방식에 따라 달라진다.
계획된 관리형 전환과 비계획 장애 복구를 구분해 공식 문서의 현재 조건을 확인해야 한다.
글로벌 서비스이거나 리전 단위 DR이 필수라면 Aurora를 선택하는 것이 꽤 좋은 편이다.
다만 실제로 특정 도메인(게임?)을 제외하고 DR로 인해서 Global Database까지는 사용하지 않는다.
DR은 멀티 AZ로도 법적으로 충분한 경우가 많다.

## Serverless v2

트래픽이 불규칙한 서비스에 답이 된다.
Aurora Serverless v2는 ACU 단위로 자동 스케일링한다.
설정 가능한 최소값과 최대값, 0 ACU 자동 일시 중지 지원은 엔진 버전과 리전에 따라 확인한다.
낮에는 트래픽이 많고 새벽에는 거의 없는 서비스.
프로비저닝 인스턴스로는 피크에 맞춰 과잉 프로비저닝하거나 새벽에 비용을 낭비한다.
Serverless v2는 부하에 따라 자동으로 줄어든다.
다만 스케일업 반응이 즉각적이진 않다.
급격한 스파이크에는 프로비저닝 인스턴스가 더 안정적이다.
혼합 구성(프로비저닝 Writer + Serverless Reader)도 가능하다.

## DBA가 실제로 느끼는 차이

스펙시트에 없는 것들이 있다.

[모니터링]
CloudWatch Database Insights에서 DB Load와 wait event를 분석할 수 있다.
기존 Performance Insights 콘솔 경험은 2026-07-31에 종료됐지만 Performance Insights API는 계속 제공된다.

[운영 편의]
스토리지 자동 확장.
Reader 추가/삭제가 빠름.
클론을 빠른시간 안에 만들 수 있다.
대략적으로 30분정도 걸리는 것 같다.

[예측 불가능한 비용]
I/O 과금은 월말에 청구서를 보기 전까지 정확한 비용을 모른다.
RDS는 프로비저닝 기반이라 비용이 예측 가능하다.

[마이그레이션]
RDS에서 Aurora로 마이그레이션은 비교적 쉽다.
스냅샷 복원으로 전환할 수 있고, 읽기 인스턴스를 Aurora로 생성해서 분리하는 방법도 있다.
역방향(Aurora에서 RDS)은 더 번거롭다.

## 선택 기준 정리

간단한 의사결정 트리다. 그냥 참고만 해두자.

- "서비스가 30초 이상 멈추면 안 되는가?"
  - 그렇다면 Aurora.
- "Reader가 3대 이상 필요한가?"
  - 그렇다면 Aurora.
- "데이터가 1TB를 넘어가는가?"
  - 그렇다면 Aurora.
- "개발/스테이징 환경인고 운영과 엔진 구조가 동일 할 필요가 없는가?"
  - 그렇다면 RDS.
- "월 DB 비용 100만 원 이하로 맞춰야 하는가?"
  - 그렇다면 RDS.

위 질문 중 Aurora 조건에 하나도 안 걸리면 RDS로 시작해도 늦지 않다.

## DBA 관점에서의 정리

Aurora는 비싸다. 하지만 비싼 이유가 있다.
스토리지 분리 아키텍처가 주는 복제 지연 감소, 빠른 페일오버, 자동 백업.
이것들이 필요한 서비스에는 가격 대비 값어치를 한다.
필요 없는 서비스에 Aurora를 쓰면 그냥 비싼 RDS다.
DBA의 역할은 "Aurora가 좋습니다"라고 말하는 게 아니라 "이 서비스에는 Aurora가 필요합니다" 또는 "이 서비스에는 RDS면 충분합니다"를 근거와 함께 말하는 것이다.
비싸도 써야 하는 순간이 있고, 비싸니까 안 써야 하는 순간이 있다.
그 경계를 아는 게 기술적 판단이다.
