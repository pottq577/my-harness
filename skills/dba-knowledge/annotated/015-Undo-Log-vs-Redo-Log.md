---
id: DBA-015
title: "Undo Log vs Redo Log: 되돌리는 기록과 다시 쓰는 기록"
status: stable

topics:
  - undo-log
  - redo-log
  - mvcc
  - crash-recovery
  - write-ahead-log

triggers:
  - MVCC가 UNDO 로그로 구현되는 원리
  - 커밋 커서와 히스토리 슬롯의 명령어
  - UNDO 로그가 클 때 병목이 나는 쿼리 유형
  - 롤백이 커밋보다 오래 걸리는 이유
  - crash recovery에서 REDO 로그가 하는 일

code_signals:
  - "performance_schema"
  - "UNDO"
  - "REDO"
  - "innodb_undo_tablespaces"
  - "SHOW ENGINE INNODB STATUS"

applies_to:
  - transaction-design
  - schema-design
  - performance-tuning
  - backup-recovery

risk_signals:
  - undo 로그 부하로 특정 쿼리 유형이 느려짐
  - 트랜잭션이 오래 열린 채 대량 DML 수행
  - redo 로그 크기에 대한 기준 부재

read_when:
  - MVCC 구현을 이해해야 할 때
  - 특정 쿼리 유형만 느려지는 원인을 조사할 때
  - 롤백이나 crash recovery 동작을 확인할 때

read_also:
  - DBA-013
  - DBA-016
  - DBA-009

summary: >
  UNDO 로그는 MVCC를 구현하기 위한 순수한 데이터베이스 내부 메커니즘으로,
  서비스가 직접 쓰지 않아도 로그 히스토리가 커지면 서비스 성능에 영향을
  준다는 점을 통해, 어떤 쿼리 유형이 병목인지를 설명한다. REDO 로그와의
  역할 구분과 crash recovery 과정을 다룬다.
---
# Undo Log vs Redo Log: 되돌리는 기록과 다시 쓰는 기록

트랜잭션이 커밋되기 전에 DB가 죽으면 어떻게 될까.
커밋된 줄 알았는데 디스크엔 아직 안 쓰여 있다면?
이 두 가지 질문에 답하는 게 Undo Log와 Redo Log다.
Undo는 되돌린다. Redo는 다시 쓴다.
둘 다 없으면 트랜잭션은 성립하지 않는다.

## 왜 두 가지가 필요한가

트랜잭션에는 네 가지 속성이 있다. ACID. 이 중 A(Atomicity)와 D(Durability)가 핵심이다.
Atomicity.
트랜잭션은 전부 반영되거나 전부 취소된다.
반쯤 반영된 상태는 허용되지 않는다.
이걸 보장하는 게 Undo Log다.
Durability.
커밋된 트랜잭션은 절대 사라지지 않는다.
서버가 꺼져도, 디스크에 남아 있어야 한다.
이걸 보장하는 게 Redo Log다.

## Redo Log의 역할

InnoDB는 데이터를 변경할 때 디스크의 데이터 파일에 바로 쓰지 않는다.
먼저 Buffer Pool(메모리)에서 수정하고 Redo Log에 변경 내용을 기록한다.
이게 Write-Ahead Logging(WAL)이다. "쓰기 전에 먼저 로그를 기록한다."
커밋 시점에 Redo Log만 디스크에 flush하면 트랜잭션은 안전하다.
실제 데이터 페이지는 나중에 쓴다.
Redo Log는 순차 쓰기다. 데이터 파일은 랜덤 쓰기다.
순차 쓰기가 압도적으로 빠르다.

## Redo Log의 구조

InnoDB의 Redo Log는 순환 버퍼다. 파일 끝에 도달하면 처음으로 돌아가서 덮어쓴다.
MySQL 8.0.30 이전에는 ib_logfile0, ib_logfile1 두 파일이 기본이었다.
8.0.30부터는 #innodb_redo 디렉토리 아래 여러 파일로 자동 관리된다.
순환 구조에서 중요한 건 checkpoint다.
"여기까지는 데이터 파일에 반영 완료했다."
checkpoint 이전의 Redo는 덮어써도 안전하다.
checkpoint가 밀리면 Redo 공간이 부족해진다.

## Crash Recovery

서버가 갑자기 꺼졌다. 재시작하면 InnoDB는 이렇게 복구한다.

[Redo 단계]
Redo Log를 순서대로 읽는다.
커밋된 트랜잭션인데 데이터 파일에 없는 것. 다시 반영한다.

[Undo 단계]
커밋되지 않은 트랜잭션이 있다면 Undo Log를 사용해서 롤백한다.
Redo가 먼저, Undo가 나중이다. 먼저 앞으로 감고, 그다음 되감는다.

## Undo Log의 역할

Undo Log는 "변경 전 상태"를 저장한다.
`UPDATE users SET user_name='재환' WHERE user_id=1` 이 쿼리가 실행되면 Undo Log에는 변경 전 값이 기록된다.
`{user_id:1, user_name:'도트'}` 롤백이 발생하면 이 Undo 레코드를 읽어서 원래 상태로 되돌린다.
단순하다. 하지만 Undo의 진짜 역할은 따로 있다.

## MVCC와 Undo

InnoDB에서 SELECT는 락을 잡지 않는다. 읽기와 쓰기가 서로를 차단하지 않는다.
이게 가능한 이유가 MVCC(Multi-Version Concurrency Control)다. 여러 버전의 데이터를 동시에 유지하는 것이다.
트랜잭션 A가 행을 수정 중이어도 트랜잭션 B는 수정 전 버전을 읽을 수 있다.
그 "수정 전 버전"이 Undo Log에 있다. Undo Log는 버전의 체인이다.
현재 값 → 직전 값 → 그 전 값.
각 트랜잭션은 자기 시작 시점의 버전을 찾아 읽는다.

## Undo가 문제되는 순간

긴 트랜잭션이 Undo를 비대하게 만든다.
트랜잭션 A가 30분째 열려 있다. 그 사이 다른 트랜잭션들이 수만 건을 수정한다.
A가 시작 시점의 데이터를 읽으려면 그 수만 건의 Undo 레코드가 전부 살아 있어야 한다.
Undo purge가 멈춘다.
A가 끝나지 않으면 A 시점 이후의 모든 Undo를 정리할 수 없다.
History List Length가 치솟는다. 이 값이 수백만을 넘으면 체감이 시작된다.
SELECT가 느려진다. Undo 체인을 따라가는 비용이 커지기 때문이다.

## 실무에서 마주치는 Undo 사고

DBA라면 이런 상황을 한 번쯤 겪는다.
슬로우 쿼리가 갑자기 늘어났다. 실행 계획은 안 변했다. 인덱스도 정상이다.
그런데 같은 쿼리가 평소보다 10배 느리다.
History List Length를 확인한다. 수백만이다.
어딘가에 긴 트랜잭션이 열려 있다.
커넥션 풀에서 반환 안 된 세션. 개발 서버에서 열어놓은 BEGIN. 배치 잡이 실패했는데 롤백이 안 된 것.
범인을 찾아 끊으면 purge가 돌면서 Undo가 정리된다.
쿼리 속도가 원래대로 돌아온다.

## Redo가 문제되는 순간

대량 쓰기가 Redo를 병목으로 만든다.
수백만 건의 INSERT가 한꺼번에 들어온다.
모든 변경이 Redo Log에 기록된다.
커밋마다 Redo flush가 발생한다.
innodb_flush_log_at_trx_commit 값이 핵심이다.
1이면 매 커밋마다 flush. 가장 안전하지만 가장 느리다.
2이면 OS 버퍼까지만. 1초마다 flush.
0이면 InnoDB 버퍼에만. 가장 빠르지만 위험하다.
운영 환경에서는 1이 원칙이다.
하지만 대량 마이그레이션 중에는 잠시 0로 바꾸는 판단을 할 때가 있다.
그 판단의 무게를 아는 게 DBA다.

## Undo Tablespace

MySQL 5.6까지는 Undo Log가 시스템 테이블스페이스(ibdata1) 안에 있었다.
한번 커지면 줄어들지 않는 파일이다.
5.7부터 별도 Undo Tablespace로 분리가 가능해졌다. 8.0부터는 기본이다.
undo_001, undo_002 파일로 나뉜다. 8.0.14부터 Undo Tablespace truncation이 자동이다.
innodb_undo_log_truncate = ON이면 비활성화된 Undo Tablespace를 자동으로 축소한다.
"Undo가 커지면 ibdata1이 수십 GB"라는 고전적 사고가 이제는 발생하지 않는다.
다만 긴 트랜잭션의 위험은 여전하다.

## Aurora에서의 Redo

Amazon Aurora는 Redo Log의 위치를 바꿨다. 일반 MySQL에서 Redo는 로컬 디스크에 쓴다.
Aurora에서는 네트워크를 통해 분산 스토리지 레이어에 직접 쓴다.
"Log is the database." Aurora의 설계 철학이다.
DB 인스턴스는 Redo 레코드만 스토리지로 보낸다.
스토리지가 Redo를 받아서 데이터 페이지를 재구성한다.
데이터 페이지 자체를 네트워크로 보내지 않는다.
네트워크 I/O가 극적으로 줄어든다.
복제도 빨라진다.
Replica는 Redo 스트림만 받으면 된다.

## 마무리

Undo와 Redo는 동전의 양면이다.
Redo는 미래를 보장한다.
"커밋한 건 반드시 살린다." 이게 Durability다.
Undo는 과거를 보장한다.
"커밋 안 한 건 반드시 되돌린다." 이게 Atomicity다.
실무에서는 둘 다 "문제가 생겼을 때" 보인다.
History List Length가 올라가면 Undo를 의심한다.
쓰기 지연이 발생하면 Redo flush를 의심한다.
평소에는 존재감이 없다.
하지만 이 두 로그가 없으면 트랜잭션이라는 약속 자체가 성립하지 않는다.
조용히 일하는 것들이 가장 중요하다. Undo와 Redo가 딱 그렇다.
