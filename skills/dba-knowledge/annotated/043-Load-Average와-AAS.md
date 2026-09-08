---
id: DBA-043
title: "Load Average와 AAS: DB 부하를 읽는 두 개의 눈금"
status: stable

topics:
  - load-average
  - aas
  - wait-event
  - cpu
  - monitoring

triggers:
  - Load Average가 높은데 CPU는 낮다
  - AAS가 vCPU보다 높으면 무엇을 뜻하나
  - DB 병목이 CPU인지 대기인지 구분하고 싶다

code_signals:
  - "Load Average"
  - "Average Active Sessions"
  - "DBLoad"
  - "vCPU"

applies_to:
  - monitoring
  - incident-response
  - performance-tuning

risk_signals:
  - CPU 사용률만 보고 DB 부하를 판단
  - AAS 총량만 보고 wait event 구성을 무시

read_when:
  - 서버와 DB 지표가 서로 다르게 보일 때
  - CloudWatch Database Insights에서 DB Load를 해석할 때

read_also:
  - DBA-029
  - DBA-032
  - DBA-040

source_sections:
  - "raw/4.md:1944-끝"

verified_at: 2026-09-09

references:
  - "https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/USER_PerfInsights.Enabling.html"

summary: >
  운영체제 Load Average와 DB의 Average Active Sessions를 비교해
  CPU 실행과 I/O, 락 대기를 구분하고 병목 지점을 찾는 방법을 설명한다.
---
# Load Average와 AAS: DB 부하를 읽는 두 개의 눈금

CPU 사용률이 50%다. 괜찮다고 생각한다.
근데 쿼리가 느리다.
슬로우 쿼리가 치솟고 커넥션이 밀린다.
Load Average를 보면 12다. vCPU가 2개인 인스턴스에서.
CloudWatch Database Insights에서 AAS가 8을 찍고 있다.
CPU 사용률은 부하의 절반만 말한다.
나머지 절반은 대기열에 있다.
CPU 사용률보다 Load Average를 먼저 봐라.
AAS가 vCPU 수를 넘으면 병목이다.
Wait Event 없는 AAS는 CPU 경합이다.
두 지표를 같은 시간축에 놓고 봐라.
숫자가 아니라 vCPU 대비 비율로 읽어라.
CPU가 50%라서 괜찮다고 생각한 순간, 대기열은 이미 터지고 있다.

## Load Average란

리눅스가 말하는 "바쁜 정도"다.
CPU를 쓰고 있거나 CPU를 기다리고 있거나 디스크 I/O를 기다리는 프로세스의 평균 수.
1분, 5분, 15분 이동평균으로 나온다.
vCPU가 2개인 인스턴스에서 Load Average가 2면 딱 맞게 돌고 있다.
4면 절반은 줄을 서고 있다. 8이면 네 배가 기다린다.
CPU 사용률이 "지금 얼마나 일하고 있는가"라면 Load Average는 "얼마나 밀려 있는가"다.

## AAS(Average Active Sessions)란

CloudWatch Database Insights의 DB Load를 읽는 핵심 지표다.
DB에서 쿼리를 실행 중인 세션의 평균 수.
CPU를 쓰고 있는 세션과 뭔가를 기다리고 있는 세션을 합친 것이다.
PI 그래프의 가로선이 vCPU 수다.
AAS가 이 선 아래면 여유 있다.
이 선을 넘으면 병목이 시작된다.
AAS가 6이고 vCPU가 2라면 항상 4개의 세션이 줄을 서고 있다는 뜻이다.

## 둘은 같은 이야기다

Load Average는 OS 레벨이다. CPU와 I/O를 기다리는 프로세스가 몇 개인가.
AAS는 DB 레벨이다. 쿼리를 실행 중이거나 대기 중인 세션이 몇 개인가.
계층만 다르지 본질은 같다.
일하고 있는 것 + 기다리는 것의 합계.
DB 서버에서 가장 많은 스레드를 만드는 건 쿼리를 실행하는 DB 프로세스다.
AAS가 올라가면 Load Average도 따라 올라간다.
그래서 이 두 지표가 함께 움직인다.

## CPU 사용률이 속이는 순간

CPU 사용률은 비율이다. 전체 CPU 시간 중 몇 퍼센트를 일했는가.
2 vCPU에서 50%면 코어 1개가 풀로 돌고 있는 것이다.
근데 Load Average가 8이다.
I/O 대기 때문이다.
디스크를 기다리는 프로세스는 CPU를 안 쓰지만 Load Average에는 잡힌다.
`CPU 사용률 = 일하는 시간의 비율`.
`Load Average = 일하려는 프로세스의 수`.
하나가 50%라도 다른 하나가 8이면 DB는 고통받고 있다.

## AAS의 색깔을 읽어라

PI 그래프에서 AAS는 색깔로 나뉜다.
초록색은 CPU. 실제로 CPU에서 쿼리를 실행 중인 시간.
나머지 색은 전부 Wait다.
주황은 I/O 대기. 빨강은 Lock 대기. 파랑은 네트워크 대기.
AAS가 6인데 초록이 2, 주황이 4라면 vCPU만큼은 일하고 있고 나머지 4개는 디스크를 기다리는 것이다.
이때 CPU 사용률은 높게 나온다. Load Average는 더 높게 나온다.
I/O 대기까지 합산되니까.

## Load Average가 높고 AAS도 높을 때

가장 흔한 상황이다.

[풀스캔 쿼리]
인덱스를 안 타면 디스크 I/O가 폭발한다.
AAS 상승 + Load Average 상승.
EXPLAIN부터 확인.

[동시 접속 폭증]
커넥션이 한꺼번에 밀리면 CPU 경합과 I/O 경합이 동시에 온다.
커넥션 풀 상한 확인.

[배치 + OLTP 충돌]
새벽 배치가 도는 동안 서비스 쿼리도 들어오면 두 워크로드가 자원을 나눠 먹는다.
시간대 분리가 답이다.

## Load Average만 높고 AAS는 낮을 때

DB 바깥이 원인이다.
DB 프로세스가 아닌 OS 레벨 작업이 CPU를 잡고 있다.
모니터링 에이전트, 로그 수집기, 백그라운드 OS 태스크.
AAS는 DB 세션만 본다. Load Average는 OS 전체를 본다.
AAS가 낮은데 Load Average가 높으면 DB 밖을 의심한다.
Enhanced Monitoring에서 `os.cpuUtilization`을 열면 DB 프로세스 외의 CPU 사용이 보인다.

## AAS만 높고 Load Average는 낮을 때

Lock 대기가 주범이다.
한 세션이 행 잠금을 잡고 있고 10개 세션이 그 잠금을 기다린다.
AAS는 11이다.
하지만 이 10개 세션은 CPU도 안 쓰고 I/O도 안 한다. 그냥 기다린다.
Lock 대기는 Load Average에 안 잡힌다. CPU와 디스크를 안 쓰니까.
PI에서 빨간색이 지배적이면 Load Average는 평온한데 쿼리가 안 끝나는 상황이 된다.
Lock을 잡고 있는 세션을 찾아야 한다.

## vCPU 기준선의 의미

PI 그래프의 가로선. 이게 전부의 시작이다.
vCPU가 2면 기준선은 2다. 동시에 CPU에서 일할 수 있는 세션은 2개라는 뜻이다.
AAS가 기준선 아래면 들어오는 쿼리를 바로바로 처리하고 있다.
기준선을 넘는 순간 큐가 생긴다.
Load Average의 기준도 같다.
vCPU 수를 넘으면 프로세스가 줄을 선다.
두 지표 모두 vCPU 수 대비 얼마나 초과하는가로 읽는다.
절대값이 아니라 비율이 핵심이다.

## 실전: 세 지표를 같이 보는 법

CloudWatch에서 같은 시간축에 놓는다.

[CPUUtilization]
얼마나 일했는가. 비율.

[Enhanced Monitoring의 Load Average]
얼마나 밀려 있는가. 큐 깊이.

[CloudWatch Database Insights의 AAS]
어떤 종류의 부하가 밀려 있는가. Wait 분해.

CPU가 올라가고 AAS의 초록(CPU)이 지배적이면 쿼리 최적화 또는 스케일업.
CPU는 낮은데 Load Average가 높고 AAS의 주황(I/O)이 지배적이면 인덱스 점검 또는 스토리지 성능 확인.
둘 다 낮은데 AAS만 높으면 Lock이다. 트랜잭션을 분석한다.

## DBA 관점에서의 정리

CPU 사용률보다 Load Average를 먼저 봐라.
AAS가 vCPU 수를 넘으면 병목이다.
Wait Event 없는 AAS는 CPU 경합이다.
두 지표를 같은 시간축에 놓고 봐라.
숫자가 아니라 vCPU 대비 비율로 읽어라.
CPU 사용률은 요약이다. 지금 바쁜가에만 답한다.
Load Average는 깊이다. 얼마나 밀려 있는가를 말한다.
AAS는 원인이다. 뭘 기다리고 있는가를 보여준다.
한 지표만 보면 부하의 단면만 보인다.
셋을 같이 읽을 때 비로소 DB의 상태가 입체적으로 드러난다.
CPU가 50%라서 괜찮다고 생각한 순간, 대기열은 이미 터지고 있다.
