---
id: DBA-067
title: "Aurora MySQL failover 62초의 비밀: JDBC URL 한 줄이 만드는 차이"
status: stable

topics:
  - aurora
  - failover
  - hikaricp
  - jdbc
  - driver
  - blue-green

triggers:
  - failover 순단이 왜 앱마다 다르지
  - Aurora JDBC URL에 aurora 스킴을 써야 하나
  - cluster-ro 엔드포인트를 왜 병기하나
  - HikariCP max-lifetime이 failover와 무슨 상관이지

code_signals:
  - "jdbc:mysql:aurora://"
  - "cluster-ro"
  - "maxLifeTime"
  - "max-lifetime"
  - "AWS JDBC Wrapper"
  - "failover"

applies_to:
  - application-architecture
  - incident-response
  - monitoring
  - performance-tuning

risk_signals:
  - aurora 스킴 없이 클러스터를 단일 서버로 봄
  - 설정 파일의 값과 런타임 적용값이 다름
  - reader 삭제 시 에러 버스트가 남
  - JVM DNS 캐시를 무기한으로 둠

read_when:
  - Aurora failover 순단을 줄이려 할 때
  - JDBC 드라이버와 커넥션 풀 설정을 검토할 때
  - Blue/Green 전환의 읽기 순단을 분석할 때

read_also:
  - DBA-042
  - DBA-049
  - DBA-065

source_sections:
  - "raw/8.md:780-962"

verified_at: 2026-09-22

references:
  - "https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Overview.Endpoints.html"
  - "https://github.com/aws/aws-jdbc-wrapper"

summary: >
  Aurora failover 순단이 JDBC URL 한 줄로 달라지는 구조를 다룬다. aurora
  프로토콜과 cluster-ro 병기, HikariCP max-lifetime이 62초 순단을 만드는
  과정, 설정 파일과 런타임 값의 불일치, AWS JDBC Wrapper 선택지를 설명한다.
---
# Aurora MySQL failover 62초의 비밀: JDBC URL 한 줄이 만드는 차이

> failover 순단이 왜 길었는지 못 찾은 개발자에게 바치는 글

failover 순단은 10초쯤이라고들 한다.
같은 클러스터, 같은 순간에 한 앱은 9.5초, 다른 앱은 62초.
차이는 URL 프로토콜 한 단어다.
11번 중 8번이 62초였다.
62초가 기본값이고 10초가 예외다.

- URL 프로토콜을 aurora로 쓰라.
- URL host에 cluster-ro를 반드시 병기하라.
- 드라이버는 MariaDB Connector/J 2.7.x를 쓰라.
- max-lifetime은 50초~58초 사이에 두라.
- 설정 파일이 아니라 런타임 적용값을 확인하라.

62초가 기본값인 줄 모르면 10초라는 기대가 사고가 된다.

## aurora 프로토콜이 뭘 하는가

`jdbc:mysql:aurora://`는 드라이버에게 한 가지를 알린다.
"이 주소는 서버 한 대가 아니라 클러스터다."
이 표시가 있으면 드라이버가 현재 writer를 계속 확인한다.
failover로 writer가 바뀌면 스스로 옮겨간다.
빼면 평범한 MySQL 서버 한 대로 본다.
끊기면 URL 주소로 다시 붙을 뿐, 붙은 노드가 writer인지 확인하지 않는다.
cluster endpoint는 DNS다.
failover 직후 잠깐은 옛 노드를 가리킨다.
DNS 갱신이 먼저냐, 재접속이 먼저냐. 거기서 갈린다.

## 62초가 만들어지는 구조

재접속이 DNS 갱신보다 빠르면 드라이버는 강등된 옛 writer에 붙는다.
강등된 옛 writer는 죽지 않는다.
접속도 받고 읽기도 정상 처리한다.
쓰기만 read-only 에러로 거부한다.
풀의 health check를 통과한다.
그래서 계속 재사용된다.
이 커넥션을 버릴 수단은 하나다.
수명 만료. HikariCP의 `max-lifetime`.
62초 = 재접속 12초 + max-lifetime 50초.
DNS가 먼저 갱신되어 10초에 끝난 건 11번 중 2번이었다.

## 함께 어기면 복구가 안 된다

aurora 없이 JVM DNS 캐시를 무기한으로 두면?
712초가 지나도 복구되지 않았다. 3번 전부.
aurora가 없으면 수명 만료가 유일한 회복 경로다.
DNS 캐시를 무기한으로 두면 그 경로까지 막힌다.
JVM DNS TTL은 5초로 둔다.
max-lifetime을 20초로 줄이면?
HikariCP가 30초 미만을 기각한다.
경고 한 줄 남기고 기본값 30분으로 돌아간다.
파일만 보면 20초다.
순단은 max-lifetime + 약 12초에 수렴한다.
70초면 81.7초, 35초면 47.0초.
aurora를 지킨 앱에서는 나머지를 어겨도 차이가 측정되지 않았다.

## reader를 지우면 1,533건이 터진다

failover만 위험한 게 아니다.
reader 삭제에서 더 극적인 차이가 난다.
writer cluster endpoint만 쓰는 앱에서 부하 중 최다 사용 reader를 지웠다.
에러 1,533건. 순단 71.7초.
같은 설정에 `cluster-ro`를 병기하면 에러 0건. 순단 0초.
드라이버 버전, socketTimeout, max-lifetime을 바꿔도 결과는 같았다.
cluster-ro 병기만이 전 조합에서 0이다.
매일 새벽 reader가 삭제되는 운영 서비스에서도 없는 쪽은 16~24건 버스트, 있는 쪽은 0건이었다.

## Blue/Green은 다른 게임이다

B/G 스위치오버는 클라이언트 설정으로 줄일 수 없다.
failover에서 가장 좋았던 구성이 B/G에서 가장 나빴다.
읽기 순단 1.2초가 18.7초로.
순단이 DNS 재작성 대기에 지배되기 때문이다.
어떤 조합으로도 5초 아래로 내려가지 않았다.
더 조심할 것이 있다.
aurora 앱이 폐기된 blue로 55초간 읽기를 보냈다.
1,060건 전부 성공. p99 0ms. 순단 지표에 잡히지 않는다.
구 blue는 복제가 끊긴 독립 클러스터라 그 사이 새 클러스터의 쓰기가 반영되지 않는다.
에러 없는 오염이다.

## 설정 파일 값과 런타임 값이 다르다

이 패턴이 세 번 나왔다.
셋 다 파일만 grep하는 감사를 통과한다.
max-lifetime 20000을 썼다. 런타임은 1800000.
30초 미만이라 HikariCP가 기각했다.
maxLifeTime 58000을 썼다. 런타임은 180000.
공용 라이브러리 기본값으로 떨어졌다.
기동 에러도, 경고도 없었다.
세 번째는 이 글을 보충하게 한 사건이다.
failover 작업 일주일 전 점검에서 온라인 서빙 두 서비스가 같은 이유로 3분 타이머 위에 있었다.
예측 순단 192초.

## yml에서 풀까지, 값이 끊기는 자리

설정값은 여러 손을 거친다.
yml, 설정 바인딩 클래스, Properties 조립, 공용 라이브러리, 그리고 풀.
끊긴 곳은 두 번째였다.
클래스에 username, password, resource만 있고 maxLifeTime 필드가 없다.
Spring Boot의 ignoreUnknownFields 기본값은 true다.
모르는 키는 에러 없이 버린다.
기동은 정상, 로그는 조용, 값은 없다.
라이브러리는 키를 못 찾으면 catch 블록에서 기본값 180000을 돌려준다.
관측된 180초의 정체다.
필드 하나가 3분을 만들었다.

## 세 번의 failover가 증명한 것

같은 앱에 failover를 세 번 일으켰다.
1차, 설정 전: 쓰기 순단 175.65초.
2차, maxLifeTime 58000 배포 직후: 175.66초.
3차, 값이 실제로 실린 뒤: 21.10초.
1차와 2차 차이는 12ms다.
트래픽이 달랐는데 순단은 같았다.
순단을 정하는 건 트래픽이 아니라 고정 타이머라는 뜻이다.
180초 타이머에 재접속 12초를 더하면 실험실 공식 그대로다.
값이 실리자 175초가 21초가 됐다.
파일에 58000이 적힌 건 2차부터였다.
적힌 것과 실린 것은 다르다.

## 같은 라이브러리를 쓰는 레포 다섯 곳

한 곳에서 찾은 구멍은 대개 한 곳이 아니다.
같은 공용 라이브러리로 DB 설정을 받는 레포 다섯 곳을 훑었다.
온라인 서빙 모듈에 필드가 있는 곳 0.
배치 모듈에는 있는 곳이 둘.
yml에 값을 적어 둔 곳도 있었다. 필드가 없으니 무효다.
설정 클래스를 복사하면 구멍도 복사된다.
문제를 인지한 팀조차 배치만 고치고 서빙은 놓쳤다.
확인 수단도 막혀 있었다.
actuator가 health만 열고 configprops는 404였다.
런타임 값을 볼 창이 없으면 감사는 추측이 된다.

## AWS JDBC Wrapper라는 선택지

Spring Boot 3.x BOM이 3.5.x를 가리킨다.
버전업하면 3.x가 되고, 3.x는 aurora 프로토콜을 못 쓴다.
이번 점검에서도 3.0.9가 나왔다.
2.7.12인데 스킴만 빠진 앱도 있었다. 이쪽은 URL 한 줄이다.
3.x에는 AWS JDBC Wrapper가 틈을 메운다.

- 3.5.7 단독: 62.6초.
- 3.5.7 + Wrapper(mariadb 스킴): 9.3초.
- 9.1.0 + Wrapper(mysql 스킴): 2.6초.
- B/G에서는 기준 앱 17~70초가 Wrapper 3.7~4.5초로.

표준은 두 갈래다. mariadb 2.7 + aurora, 또는 mysql + Wrapper.

## Wrapper를 쓰려면 함께 지켜야 할 것

넷 다 "안 하면 조용히 잘못 동작"한다.

[rds_topology 읽기 권한]
B/G 생성 전에 GRANT SELECT.
없으면 bg 플러그인이 에러 없이 무력화된다. 3.7초가 20초대로.

[clusterId와 bgdId]
기본값이 둘 다 "1"이다.
한 JVM에 클러스터가 둘이면 토폴로지 캐시를 공유해 엉뚱한 곳으로 라우팅한다.

[Hibernate dialect 명시]
mariadb 스킴 + ddl-auto validate에서 기동 실패.
메시지는 missing table인데 실제는 DB 이름을 대문자로 조회한 것이다.

[스킴은 mysql]
mariadb 스킴은 failover가 4배 느리고 dialect 문제도 여기서만 난다.

## failover 작업 전 5분 점검

일정이 잡혔다면 순서대로 본다.

1. 드라이버 버전. 3.x면 aurora 스킴은 선택지가 아니다.
2. URL 스킴. 2.7인데 `:aurora`가 빠진 앱은 코드 없이 URL만 고친다.
3. cluster-ro 병기 여부.
4. 런타임 max-lifetime. actuator configprops로 본다. 파일 말고.
5. JVM DNS TTL.

클라이언트 교체는 영향도가 크다.
작업이 코앞이면 max-lifetime부터 맞춘다.
그것만으로 3분이 1분 아래로 내려온다.
드라이버 표준화는 그 다음 일이다.