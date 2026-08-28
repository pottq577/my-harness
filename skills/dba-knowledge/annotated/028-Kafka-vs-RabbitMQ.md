---
id: DBA-028
title: Kafka vs RabbitMQ: 메시지를 보내는 것과 로그를 남기는 것의 차이
status: stable

topics:
  - kafka
  - rabbitmq
  - message-queue
  - event-streaming
  - log-compaction
  - consumer-group

triggers:
  - Kafka와 RabbitMQ 중 무엇을 고를까
  - 이벤트를 여러 컨슈머가 각자 처리하게 하려면
  - backpressure 처리를 위한 큐 선택
  - 로그 컴팩션을 이용한 상태 보존
  - 컨슈머가 죽었을 때 메시지 재처리

code_signals:
  - "kafka"
  - "rabbitmq"
  - "topic"
  - "partition"
  - "consumer_group"
  - "ack"
  - "retry"

applies_to:
  - event-design
  - application-architecture
  - monitoring

risk_signals:
  - 백프레셔가 없는 조합(spark와 같은 빅데이터)을 무리하게 연결
  - 순서 보장이 필요한 지점에 파티션 수를 잘못 설계
  - ack/retry 정책이 없어 데이터 유실

read_when:
  - 메시지 큐 서버를 고를 때
  - 이벤트 기반 아키텍처를 설계할 때
  - 백프레셔나 순서 보장을 설계할 때

read_also:
  - DBA-017
  - DBA-016
  - DBA-036

summary: >
  Kafka가 '로그'로 동작하는 구조(파티션과 오프셋, log compaction, offset
  reset)와 RabbitMQ가 '메시지'로 동작하는 구조(큐, ack, dead letter)의
  차이를 다룬다. 이벤트 스트리밍과 일회 소비를 구분해서 어떤 쪽이 맞는지
  선택하는 기준을 제시한다.
---
# Kafka vs RabbitMQ: 메시지를 보내는 것과 로그를 남기는 것의 차이

"우리도 카프카 써야 하나요?"
개발팀에서 가장 많이 듣는 질문 중 하나다. 대답하기 전에 먼저 물어봐야 한다.
메시지를 보내고 싶은 건가, 이벤트를 기록하고 싶은 건가.
RabbitMQ는 메시지를 전달한다.
받는 쪽이 처리하면 메시지는 사라진다. 편지를 보내는 것과 같다.
Kafka는 이벤트를 기록한다.
Consumer가 읽어도 로그는 남아 있다. 일기장에 쓰는 것과 같다.
이 차이를 모르면 아무리 비교해도 결론이 안 난다.

## 근본적인 구조 차이

RabbitMQ는 메시지 브로커다.
Producer가 메시지를 보내면 브로커가 큐에 넣고 Consumer가 꺼내 간다. 처리가 끝나면 큐에서 삭제된다.
Kafka는 분산 로그다.
Producer가 이벤트를 보내면 브로커가 파티션에 append한다. Consumer가 읽어도 로그는 그대로 남는다. retention 기간이 지나야 삭제된다.

"메시지가 처리되면 사라지는가?"
이 질문 하나로 둘의 철학이 갈린다.

## RabbitMQ의 세계

AMQP 프로토콜 기반이다.
Exchange가 메시지를 받아서 라우팅 키에 따라 큐로 분배한다.

[Direct Exchange]
정확히 일치하는 큐로 보낸다.
주문 큐에는 주문만, 결제 큐에는 결제만.

[Topic Exchange]
패턴 매칭으로 보낸다.
`order.*` 라우팅 키로 주문 관련 큐 전부에 전달.

[Fanout Exchange]
바인딩된 모든 큐에 복사한다.
브로드캐스트다. 라우팅이 유연하다.
메시지를 "어디로 보낼 것인가"에 초점이 맞춰져 있다.

## Kafka의 세계

토픽과 파티션이 핵심이다.
토픽은 이벤트의 카테고리. 파티션은 토픽 안의 물리적 로그 파일.
Producer가 이벤트를 보내면 파티션 끝에 순서대로 붙는다. append-only 로그다.
Consumer는 offset으로 읽는다. "나는 여기까지 읽었다"는 위치를 기억한다. 같은 이벤트를 다시 읽을 수 있다.
Kafka의 초점은 "무슨 일이 일어났는가"를 기록하는 것이다.

## 순서 보장

[RabbitMQ]
단일 큐 안에서는 순서가 보장된다.
하지만 여러 Consumer가 동시에 꺼내 가면 처리 순서는 보장되지 않는다.
Consumer A가 메시지 1을 처리하는 동안 Consumer B가 메시지 2를 먼저 끝낼 수 있다.

[Kafka]
파티션 안에서 순서가 보장된다.
같은 파티션에 들어간 이벤트는 반드시 쓴 순서대로 읽힌다.
키 기반 파티셔닝으로 같은 주문의 이벤트를 같은 파티션에 모은다.
순서가 중요한 도메인이라면 Kafka의 파티션 모델이 더 자연스럽다.

## 재처리

여기서 결정적 차이가 난다.

[RabbitMQ]
Consumer가 ACK를 보내면 메시지는 큐에서 사라진다.
"어제 들어온 주문 이벤트를 다시 처리해줘." 불가능하다. 이미 없다.
Dead Letter Queue에 실패 메시지를 보관할 수는 있지만 전체 재처리와는 다르다.

[Kafka]
Consumer가 읽어도 로그는 남아 있다. offset을 되돌리면 처음부터 다시 읽을 수 있다.
"어제 들어온 이벤트 전부 재처리." 가능하다. offset만 리셋하면 된다.
버그 수정 후 재처리, 새 Consumer 추가 후 과거 이벤트 소급. Kafka에서는 일상이고 RabbitMQ에서는 불가능하다.

## 처리량

[RabbitMQ]
단일 노드에서 초당 수만 메시지를 처리한다. 대부분의 서비스에는 충분하다.
하지만 수십만 이상으로 올라가면 클러스터링과 샤딩이 필요하고 복잡도가 급격히 올라간다.

[Kafka]
파티션을 늘리면 처리량이 선형으로 증가한다. 파티션 10개면 Consumer 10대가 병렬로 읽는다.
초당 수백만 이벤트도 처리 가능하다. LinkedIn에서 태어난 이유가 이것이다.
소규모 서비스에서는 RabbitMQ로 충분하다. 대규모 이벤트 스트림이라면 Kafka가 맞다.

## 운영 복잡도

[RabbitMQ]
설치가 쉽다.
Erlang 기반이라 클러스터링도 내장이다.
관리 UI가 기본 제공된다.
큐 상태, Consumer 수, 메시지 적체를 한눈에 본다.
소규모 팀이 운영하기 좋다.

[Kafka]
ZooKeeper 의존성이 있었다.
KRaft 모드로 벗어나는 중이지만 아직 과도기다.
브로커, 파티션, 리플리카, ISR, 리밸런싱. 알아야 할 개념이 많다.
Kafka는 강력하지만 운영 비용도 강력하다.
전담 인력 없이 Kafka를 운영하는 건 보험 없이 스포츠카를 모는 것과 같다.

## Consumer 모델

[RabbitMQ]
push 모델이다.
브로커가 Consumer에게 메시지를 밀어준다.
prefetch count로 한 번에 받을 양을 조절한다.
Consumer가 느리면 메시지가 큐에 쌓인다.

[Kafka]
pull 모델이다.
Consumer가 브로커에서 직접 가져간다.
자기 속도에 맞춰 읽는다.
느린 Consumer는 느리게 읽을 뿐이다.
다른 Consumer에 영향을 주지 않는다.
pull 모델이 Consumer 장애에 더 강하다.
한 Consumer가 죽어도 다른 Consumer는 영향 없다.

## DB 이벤트 발행 관점

DBA 입장에서 가장 중요한 맥락이다. DB 변경을 외부에 알려야 할 때 어느 쪽을 쓰는가.

[CDC + Kafka]
Debezium이 binlog를 읽어서 Kafka 토픽으로 보낸다.
이벤트가 로그로 남으니 재처리가 가능하다.
새 Consumer를 붙이면 과거 변경분까지 소급한다.
CDC의 자연스러운 파트너다.

[Outbox + RabbitMQ]
outbox 테이블을 폴링해서 RabbitMQ로 보낸다.
단순하고 즉시 전달된다.
하지만 재처리가 필요하면 outbox 테이블을 다시 읽어야 한다.

이벤트를 "한 번 보내면 끝"이면 RabbitMQ.
"기록으로 남기고 여러 번 소비"하면 Kafka.

## "우리도 카프카 써야 하나요?"

이 질문에 대한 현실적 답변.

[RabbitMQ가 맞는 경우]
작업 큐가 필요하다.
이메일 발송, 이미지 변환, 비동기 처리.
메시지를 보내고 처리하면 끝이다.
재처리 요구사항이 없다.
팀 규모가 작다.

[Kafka가 맞는 경우]
이벤트 스트림이 필요하다.
주문 흐름, 결제 흐름, 사용자 행동 추적.
여러 Consumer가 같은 이벤트를 독립적으로 소비한다.
재처리가 필수다.
처리량이 많다.

"카프카가 좋다더라"는 이유가 아니다.
"우리에게 로그가 필요한가"가 기준이다.

## 둘 다 쓰는 현실

대규모 시스템에서는 둘 다 쓴다.
Kafka는 이벤트 백본. 주문 생성, 결제 완료, 배송 상태 변경.
모든 도메인 이벤트가 Kafka를 통해 흐른다.
RabbitMQ는 작업 큐. 알림 발송, PDF 생성, 배치 트리거.
처리하면 끝나는 일에는 RabbitMQ가 가볍다.
양자택일이 아니다. 역할이 다른 도구를 적재적소에 쓰는 것이다.
망치와 드라이버 중 뭐가 좋으냐고 묻는 건 질문 자체가 틀린 것이다.

## DBA 관점에서의 정리

Kafka든 RabbitMQ든 결국 데이터의 출발점은 DB다.
CDC는 DB 로그를 읽고, Outbox는 DB 테이블에 쓰고, 어떤 메시지 시스템을 쓰든 DB의 트랜잭션 안에서 이벤트가 태어난다.
DBA가 신경 쓸 건 Kafka의 파티션 수가 아니다.
binlog가 얼마나 빠르게 소비되는지, outbox 테이블이 얼마나 빠르게 커지는지, CDC 커넥터가 복제 지연을 만들고 있지는 않은지.
메시지 시스템은 전달할 뿐이다. 원본은 언제나 DB에 있고, 그 원본을 지키는 건 DBA의 일이다.
