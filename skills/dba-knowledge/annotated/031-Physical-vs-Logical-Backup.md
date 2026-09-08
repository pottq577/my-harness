---
id: DBA-031
title: "Physical vs Logical Backup: 백업이 빠르면 복구는 느리다"
status: stable

topics:
  - backup
  - recovery
  - physical-backup
  - logical-backup
  - rpo
  - rto

triggers:
  - physical과 logical 백업의 차이
  - 파일 스냅샷과 툴 기반 백업을 고를 때
  - 백업 보관 주기인 rr 설정
  - 복구에 이미지가 오래 걸리는 이유
  - 백업이 많아졌을 때 낭비되는 용량

code_signals:
  - "pg_basebackup"
  - "xtrabackup"
  - "mysqldump"
  - "pg_dump"
  - "S3"
  - "ZFS"
  - "복구"

applies_to:
  - backup-recovery
  - monitoring

risk_signals:
  - physical bucket이 아니라 로직 백업만으로 운영
  - 사고 시 백업 파일을 못 찾는 보관 구조
  - 백업 파일이 스토리지 제한을 넘겨 실패
  - 백업이 빠르다며 복구 속도를 검증하지 않음

read_when:
  - 백업 방식을 선택하거나 혼용할 때
  - 복구 시간(RTO) 목표를 정할 때
  - 백업 저장/스토리지 전략을 세울 때

read_also:
  - DBA-030
  - DBA-032
  - DBA-005

summary: >
  물리 백업이 전체 파일 단위라 백업은 빠르고 복구는 느린 반면, 논리 백업은
  데이터 단위라 백업은 느리고 세부 복구는 가능하다는 성격이 서로 반대임을
  비교한다. 탐색과 보관 때문에 생기는 복구 곤란 사례를 통해 두 방식의
  복구 속도와 비용을 정리한다.
---
# Physical vs Logical Backup: 백업이 빠르면 복구는 느리다

백업은 보험이다.
드는 건 꼬박꼬박 들면서 한 번도 써본 적 없는 보험.
문제는 써야 할 순간에 안 되는 보험이 있다는 거다.

## 최소 복구 체크리스트

먼저 이 다섯 가지부터 확인해봐라. AI가 만든 백업이든 손으로 짠 백업이든 똑같다.

- [ ] 백업 파일 크기가 0이 아닌가?
- [ ] 덤프 파일 끝에 Dump completed가 있는가?
- [ ] 빈 DB에 복원했을 때 에러 없이 끝나는가?
- [ ] 원본과 주요 테이블 row count가 일치하는가?
- [ ] 복구에 걸리는 시간을 기록했는가?
- [ ] 최근 30일 안에 이걸 해봤는가?

하나라도 No가 있으면 이 글을 끝까지 읽어라. 전부 Yes면 당신의 백업은 진짜 백업이다.
두 번째 항목이 가장 싸게 먹히는 검증이다.
mysqldump는 파일 끝에 `-- Dump completed`를, pg_dump는 `-- PostgreSQL database dump complete`를 남긴다.
이게 없으면 백업이 중간에 끊긴 거다. 매일 cron 돌린 뒤 tail 한 줄이면 잡을 수 있다.

## 백업의 두 갈래

DB 백업은 크게 두 가지로 나뉜다.

[논리 백업]
데이터를 SQL 문장으로 추출한다. mysqldump, pg_dump가 대표적이다.
결과물은 텍스트다.
`CREATE TABLE`과 `INSERT INTO`의 나열.

[물리 백업]
데이터 파일 자체를 복사한다. Percona XtraBackup, pg_basebackup이 대표적이다.
결과물은 바이너리 파일이다.
DB가 디스크에 쓰는 그대로를 가져온다.
같은 데이터를 담지만 속도, 크기, 복구 방식이 완전히 다르다.

## 논리 백업: mysqldump와 pg_dump

mysqldump는 MySQL DBA의 오래된 친구다.
테이블 구조를 CREATE TABLE로, 데이터를 INSERT로 뽑아낸다.

```sql
-- mysqldump 출력 예시
CREATE TABLE orders (
order_id BIGINT PRIMARY KEY,
user_name VARCHAR(100),
amount DECIMAL(10,2)
);
INSERT INTO orders VALUES (1,'dot',15000.00);
```

pg_dump도 마찬가지다.
텍스트라 사람이 읽을 수 있고 특정 테이블만 뽑거나 다른 DB 엔진으로 옮길 수도 있다.

## 논리 백업의 한계

100GB 데이터베이스를 mysqldump로 뽑는다. 몇 시간이 걸린다.
복구할 때도 INSERT를 한 줄씩 실행하므로 백업보다 복구가 더 오래 걸린다.
1TB라면? 하루가 걸릴 수도 있다.
장애 상황에서 하루를 기다릴 수 있는 서비스는 없다.
또 다른 문제.
mysqldump는 기본적으로 일관성을 위해 락을 잡는다.
`--single-transaction` 옵션이 있지만 InnoDB가 아닌 테이블이 섞여 있으면 `FLUSH TABLES WITH READ LOCK`이 걸린다.
백업이 서비스를 멈추는 역설이 발생한다.

## 물리 백업: XtraBackup과 pg_basebackup

Percona XtraBackup은 InnoDB 데이터 파일을 핫 카피한다. 서비스를 멈추지 않고 백업한다.
백업 중 변경된 데이터는 redo log로 추적해서 복구 시 apply한다.
pg_basebackup은 PostgreSQL의 데이터 디렉터리를 통째로 스트리밍 복사한다.
WAL 파일을 함께 아카이빙해서 특정 시점 복구(PITR)까지 지원한다.
두 도구 모두 바이너리 레벨 복사라 속도가 빠르다.
100GB를 30분 안에 끝낼 수 있다.

## 복구 속도의 차이

여기서 제목의 의미가 드러난다. "백업이 빠르면 복구는 느리다"는 논리 백업의 이야기다.
논리 백업은 백업은 쉬운데 복구가 느리다.
INSERT를 수십억 건 실행해야 하고 인덱스를 다시 빌드해야 한다.
물리 백업은 반대다.
백업 자체는 디스크 I/O에 의존하지만 복구는 파일을 제자리에 놓으면 끝이다.
XtraBackup이면 prepare 단계가 필요하고 pg_basebackup이면 WAL replay가 필요하지만 논리 복구보다 수십 배 빠르다.
장애 상황의 RTO(복구 목표 시간)는 물리 백업이 압도적으로 유리하다.

## 용량의 차이

논리 백업은 텍스트다.
숫자 1000000이 7바이트 문자열이 된다. 바이너리로는 4바이트면 될 값이다.
압축하면 줄어들지만 원본은 크다.
물리 백업은 디스크의 데이터 파일 크기와 같다.
인덱스, undo 영역까지 포함하므로 실제 데이터보다 클 수 있다.
결국 비슷하거나 물리 백업이 약간 더 크다.
하지만 압축 효율은 물리 백업이 좋다.
바이너리 데이터는 패턴이 반복되어 gzip으로도 높은 압축률을 얻는다.

## 유연성의 차이

논리 백업이 빛나는 순간이 있다.
"orders 테이블만 복구해주세요."
mysqldump로 테이블 단위 백업이 있으면 그 테이블만 복구할 수 있다.
"MySQL에서 PostgreSQL로 옮기고 싶어요."
논리 백업은 SQL이므로 약간의 변환으로 다른 엔진에 넣을 수 있다.
물리 백업은 이게 안 된다.
InnoDB 파일을 PostgreSQL에 넣을 수 없다. 테이블 하나만 꺼내는 것도 복잡하다.
전체를 복구한 뒤 필요한 것만 추출해야 한다.
유연성은 논리 백업의 유일하면서도 강력한 장점이다.

## PITR: 특정 시점 복구

장애 복구에서 가장 많이 쓰는 시나리오. "오늘 오후 2시 30분으로 되돌려주세요."
물리 백업 + binlog(MySQL) 또는 WAL(PostgreSQL) 조합으로 특정 시점까지 정확히 복구할 수 있다.
물리 백업을 복원하고 그 시점부터 원하는 시점까지 binlog/WAL을 재생한다. 분 단위, 초 단위 복구가 가능하다.
논리 백업만으로는 PITR이 어렵다. 마지막 덤프 시점으로만 돌아갈 수 있다.
그 사이의 데이터는 binlog가 따로 있어야 한다. 조합은 가능하지만 절차가 복잡하고 느리다.

## "AI한테 백업 스크립트 짜달라고 했어요"

바이브코딩 시대의 가장 흔한 함정이다. AI가 백업 스크립트를 짜줬다.
cron에 등록했다. 알림도 온다. 안심한다.
그런데 복구해 본 적은 있는가?
백업 파일이 0바이트일 수 있다.
SQL이 중간에 잘려 있을 수 있다.
권한 문제로 복원이 안 될 수 있다.
디스크 용량이 부족할 수 있다.
AI는 백업을 잘 짠다. 복구를 대신 검증해주진 않는다.
테스트 안 한 백업은 보험증서 없는 보험이다.

## 직접 해보기: mysqldump

먼저 덤프 파일이 온전한지 확인한다.

```bash
# 백업 완료 여부 확인
tail -1 backup.sql | grep -q "Dump completed" && echo "OK" || echo "BROKEN"
```

이게 OK면 복원을 해본다.

```bash
mysql -u root -e "CREATE DATABASE backup_test"
mysql -u root backup_test < backup.sql
mysql -u root -e "SELECT COUNT(*) FROM backup_test.orders"
```

에러 없이 끝나고 count가 원본과 같으면 합격.
끝나면 `DROP DATABASE backup_test`로 정리한다.

## 직접 해보기: pg_dump

Supabase나 PostgreSQL 사용자는 이쪽이다.
먼저 덤프 파일이 온전한지 확인한다.

```bash
tail -5 backup.sql | grep -q "dump complete" && echo "OK" || echo "BROKEN"
```

OK면 로컬 PG에 복원해본다.

```bash
createdb backup_test
psql backup_test < backup.sql
psql backup_test -c "SELECT COUNT(*) FROM orders"
```

에러 없이 끝나고 count가 원본과 같으면 합격.
끝나면 `dropdb backup_test`로 정리한다.

## crontab에 검증 걸기

백업만 cron에 걸고 검증은 안 거는 사람이 많다.
백업 끝난 직후에 tail 한 줄이면 된다.
매일 새벽 3시 백업 + 검증

```bash
0 3 \* \* \* mysqldump -u root --single-transaction mydb > /backup/mydb*$(date +\%Y\%m\%d).sql && tail -1 /backup/mydb_$(date +\%Y\%m\%d).sql | grep -q "Dump completed" || echo "BACKUP BROKEN: mydb" | mail -s "backup alert" you@email.com
```

한 줄이 길지만 하는 일은 단순하다. 덤프 뜨고, 마지막 줄 확인하고, 없으면 알림 보낸다.
pg_dump 사용자는 mysqldump를 `pg_dump -U postgres`로, `Dump completed`를 `dump complete`로 바꾸면 된다.
이것만 걸어도 0바이트 백업에 당하진 않는다.

## 직접 해보기: RDS 스냅샷

AWS 콘솔에서 세 단계면 된다.
자동 스냅샷 목록에서 최신 스냅샷을 고른다.
"스냅샷에서 복원"을 누른다.
인스턴스가 뜨면 접속해서 데이터를 확인한다.
CLI로 하면 이렇다.

```bash
aws rds restore-db-instance-from-db-snapshot \
--db-instance-identifier test-restore \
--db-snapshot-identifier my-snapshot
```

Available 상태가 되면 접속해서 count를 센다.
확인 끝나면 인스턴스 삭제. 비용은 분 단위다.

## 실전 전략: 물리 + 논리 병행

둘 중 하나만 쓰면 안 되는가? 안 되는 건 아니지만 위험하다.

[물리 백업]
매일 전체 백업. 빠른 복구를 위한 1차 방어선.
PITR 용도로 binlog/WAL 아카이빙 병행.

[논리 백업]
주 1회 또는 월 1회. 특정 테이블 복구, 크로스 엔진 마이그레이션, 데이터 감사용 아카이브로 활용.

물리 백업이 주력이고 논리 백업은 보조다.
보조가 없으면 물리 백업 파일이 깨졌을 때 할 수 있는 게 없다.

## DBA 관점에서의 정리

백업 전략을 세울 때 물어야 할 질문은 세 가지다.

1. 얼마나 빨리 복구해야 하는가? (RTO)
2. 어디까지 데이터를 잃어도 되는가? (RPO)
3. 복구를 실제로 해봤는가?

RTO가 짧으면 물리 백업이 필수다. RPO가 0에 가까워야 하면 PITR이 필수다.
복구 테스트를 안 했으면 둘 다 의미 없다.
AI에게 백업 스크립트를 시켰으면 복구 테스트 스크립트도 시켜라.
검증 코드까지 받아야 백업이 완성된다.
"백업 돌아가고 있습니다"는 답이 아니다. "지난주 복구 테스트 성공했습니다"가 답이다.
