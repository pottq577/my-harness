---
id: DBA-029
title: Wait Event로 읽는 Aurora MySQL: 느릴 때 진짜 원인을 찾는 법
status: stable

topics:
  - wait-event
  - aurora
  - mysql
  - performance
  - cause-analysis

triggers:
  - Aurora MySQL이 느릴 때 무엇부터 확인하나
  - wait event를 조회하는 쿼리
  - 대량 정렬로 파일 소트가 발생할 때
  - 특정 버퍼 확장으로 lock을 유발하는 문제
  - DBA가 진단으로 할 일

code_signals:
  - "performance_schema"
  - "sys.statement_analysis"
  - "events_stages_history_long"
  - "wait/io"
  - "Using filesort"
  - "sync/io/"

applies_to:
  - monitoring
  - performance-tuning
  - incident-response

risk_signals:
  - buffer pool 확대가 lock을 유발하는 시점
  - resources 워크로드에서 file sort 해석 오차
  - wait event 조회 시간이 느린 지표를 그대로 받음

read_when:
  - Aurora MySQL에서 느린 원인을 규명할 때
  - wait event 기반 진단을 시작할 때
  - 슬로우 쿼리와 파일 정렬을 다룰 때

read_also:
  - DBA-008
  - DBA-032
  - DBA-009

summary: >
  대시보드의 전체 CPU/IO 지표가 아닌 'wait event'라는 DB 내부의 관찰
  지점을 통해 느려진 원인을 좁히는 구체적 절차를 다룬다. MySQL의
  performance_schema 기반 조회 쿼리와, buffer pool 설정 확장이 lock을
  유발하는 반사적인 경우를 진단하는 방법을 제시한다.
---
# Wait Event로 읽는 Aurora MySQL: 느릴 때 진짜 원인을 찾는 법

Aurora MySQL이 느려졌다.
CPU는 여유 있고 메모리도 괜찮은데 쿼리가 끝나지 않는다.
이럴 때 봐야 하는 게 Wait Event다. DB가 지금 뭘 기다리고 있는지.
Performance Insights를 열면 상위 Wait가 나온다.
근데 이름만 봐서는 뭔 소린지 모른다.
증상별로 어떤 Wait Event가 뜨는지.
그걸 알면 원인과 대응이 동시에 보인다.

## Wait Event란

쿼리가 실행되는 동안 DB는 항상 뭔가를 기다린다.
디스크를 읽거나, 락을 잡거나, 네트워크로 결과를 보내거나.
그 "기다림"을 분류해서 이름을 붙인 게 Wait Event다.
Performance Schema가 수집하고 Performance Insights가 시각화한다.
CPU 사용률만 보면 병목의 절반을 놓친다.
Wait Event를 봐야 진짜 느린 이유가 보인다.

## io/socket/sql/client_connection

네트워크가 병목일 때 나타난다.
SELECT에 TEXT나 BLOB 컬럼이 포함되면 한 행이 수십 KB를 넘긴다. 1000건이면 수십 MB.
Aurora 인스턴스는 타입별로 네트워크 burst 한도가 있다.
큰 데이터를 한꺼번에 퍼올리면 burst를 소진하고 이 wait가 급등한다.
필요한 컬럼만 SELECT. BLOB은 별도 쿼리로 분리.
LIMIT은 습관이 아니라 생존이다.

## io/aurora_redo_log_flush

쓰기 레이턴시가 치솟을 때 나타난다.
INSERT, UPDATE, DELETE가 몰리면 Aurora는 redo log를 스토리지 레이어에 flush한다.
이 flush가 밀리면 모든 쓰기 쿼리가 대기한다.
대량 배치가 원인일 때가 많다.
1만 건 INSERT를 한 트랜잭션에 몰아넣으면 redo log가 한꺼번에 밀린다.
배치는 1000건 단위로 나눠 커밋. 쓰기를 시간대별로 분산. Writer 인스턴스 스펙 점검.

## io/table/sql/handler

디스크 읽기가 폭발할 때 나타난다. 인덱스를 안 타는 쿼리.
풀 테이블 스캔이 돌면 Aurora 스토리지에서 대량 페이지를 읽어야 한다.
EXPLAIN에서 type이 ALL이면 이 wait가 보일 가능성이 높다.
인덱스를 걸거나, 쿼리를 고치거나, 커버링 인덱스로 I/O를 줄이거나.
답은 항상 실행 계획에 있다.

## io/aurora_respond_to_client

쿼리 자체는 빠른데 응답이 늦을 때.
Aurora가 결과를 클라이언트에게 보내는 과정에서의 대기다.
client_connection과 비슷하지만 이쪽은 Aurora 내부에서 결과를 조립해서 내보내는 구간이다.
결과 행이 수만 건이거나 애플리케이션이 결과를 천천히 소비하면 나타난다.
fetchSize 조정이 의외로 효과 있다.
결과 셋 크기를 줄이는 게 근본이다.

## synch/cond/sql/MDL_context

ALTER TABLE이 끝나지 않고 뒤따르는 쿼리가 줄줄이 멈출 때. Metadata Lock.
DDL이 메타데이터 락을 잡으려는데 앞에서 긴 SELECT가 락을 쥐고 있다.
DDL은 대기하고, 뒤이어 들어오는 SELECT, INSERT도 전부 MDL 대기열에 갇힌다.
한 쿼리의 락이 전체 서비스를 멈추는 순간이다.
긴 트랜잭션을 먼저 정리. DDL은 트래픽 낮은 시간에. pt-online-schema-change를 고려.

## synch/mutex 계열: 버퍼풀과 트랜잭션 경합

CPU는 여유인데 TPS가 안 오를 때.

[buf_pool_mutex]
버퍼풀 접근이 직렬화되면서 생기는 대기.
동시 접근이 많은데 버퍼풀이 작으면 mutex 경합이 심해진다.
버퍼풀 인스턴스 수를 늘리거나 인스턴스를 스케일업.

[trx_mutex / lock_mutex]
같은 행을 여러 세션이 동시에 UPDATE.
InnoDB 내부의 트랜잭션 뮤텍스에서 대기.
핫 로우를 줄이는 설계가 근본 해결이다.
경합은 스펙을 올려도 안 풀린다. 설계를 바꿔야 한다.

## cpu

CPU 사용률이 높고 쿼리도 느릴 때. Wait Event 중에서 cpu는 특별하다.
"기다리는 시간"이 아니라 "일하는 시간"이다.
ORDER BY로 정렬, GROUP BY로 임시 테이블 생성, 복잡한 JOIN 연산.
CPU를 많이 쓴다는 건 쿼리가 무거운 연산을 하고 있다는 뜻이다.
인덱스로 정렬을 대체하거나, 서브쿼리를 풀거나, 불필요한 DISTINCT를 제거하거나.
CPU가 바쁜 건 쿼리가 비효율적이라는 신호다.

## 실전: Performance Insights에서 읽는 법

PI를 열면 상위 5개 Wait가 보인다. 이걸 읽는 순서가 있다.

[1단계: 지배적 Wait 확인]
전체의 50% 이상을 차지하는 Wait. 이게 지금 DB의 주요 병목이다.

[2단계: 시간대 상관관계]
Wait가 치솟는 시점과 슬로우 쿼리 발생 시점을 겹쳐본다.

[3단계: SQL 탭에서 범인 찾기]
해당 Wait를 가장 많이 유발하는 쿼리. 그 쿼리를 튜닝하면 Wait가 줄어든다.
Wait Event는 증상이다. SQL이 원인이다.

## DBA 관점에서의 정리

"DB가 느려요." 이 한 마디에서 시작하는 모든 대화.
CPU? 메모리? 디스크? 전부 정상인데 느리다고 한다. 그때 Wait Event를 연다.
client_connection이면 네트워크.
redo_log_flush면 쓰기 부하.
handler면 풀스캔.
MDL이면 긴 트랜잭션.
cpu면 쿼리를 뜯어본다.
DB는 항상 말하고 있다. 다만 Wait Event라는 언어로 말할 뿐이다.
그 언어를 읽을 줄 아는 사람이 DBA다.
