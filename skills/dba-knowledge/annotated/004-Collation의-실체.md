---
id: DBA-004
title: Collation의 실체: 같은 글자가 다르게 정렬되는 이유
status: stable

topics:
  - collation
  - charset
  - sorting
  - index
  - unicode

triggers:
  - 한글 정렬이 이상하다
  - 같은 값인데 검색이 안 된다
  - collation이 다르다는 에러가 난다
  - 대소문자를 구분해서 검색하고 싶다
  - utf8mb4_bin을 써야 하는 경우

code_signals:
  - "utf8mb4"
  - "utf8mb4_general_ci"
  - "utf8mb4_0900_ai_ci"
  - "utf8mb4_bin"
  - "COLLATE"
  - "CHARACTER SET"
  - "Illegal mix of collations"

applies_to:
  - schema-design
  - migration
  - sql-review

risk_signals:
  - 기존 테이블과 다른 collation이 섞임
  - 대소문자나 악센트 구분이 필요한 컬럼에 ci 사용
  - collation 불일치로 검색이 누락됨

read_when:
  - 정렬이나 검색 결과가 예상과 다를 때
  - 테이블이나 컬럼의 collation을 처음 정할 때
  - collation 변경 마이그레이션을 검토할 때

read_also:
  - DBA-006
  - DBA-001

summary: >
  collation이 인덱스의 weight 정렬에 어떤 영향을 주는지 설명하고, MySQL의
  세 가지 collation인 utf8mb4_general_ci, utf8mb4_0900_ai_ci, utf8mb4_bin이
  같은 데이터를 다르게 판단하는 사례를 비교한다. _bin을 써야 하는 순간과
  collation이 섞였을 때 생기는 문제를 다룬다.
---
# Collation의 실체: 같은 글자가 다르게 정렬되는 이유

collation은 보이지 않는 규칙이다.
보이지 않기 때문에 한 번 어긋나면 찾기도 어렵고 고치기도 비싸다.
인덱스는 정렬된 구조다.
B-Tree에 문자열이 들어갈 때 'A' 다음에 'B'가 오는 건 당연해 보인다.
그런데 'ß'는 어디에 놓이는가.
'á'와 'a'는 같은 자리인가. 'A'와 'a'는 같은 값인가, 다른 값인가.
이걸 결정하는 게 collation이다.
MySQL에서 자주 마주치는 세 가지가 있다.
utf8mb4_general_ci, utf8mb4_0900_ai_ci, 그리고 utf8mb4_bin.
같은 글자를 세 가지 방식으로 계산한다.

## 인덱스는 글자가 아니라 weight로 정렬된다

B-Tree에 문자열이 들어갈 때 원본 글자가 그대로 정렬되는 게 아니다.
각 글자를 weight라는 숫자로 변환하고 그 숫자 순서대로 트리에 꽂는다.
'A'와 'a'가 같은 위치에 들어가는 이유는 둘의 weight가 같기 때문이다.
collation은 이 weight를 계산하는 규칙이다.
규칙이 바뀌면 같은 데이터도 트리 안에서 다른 곳에 놓인다.
그런데 weight 변환 자체를 안 하는 놈도 있다. utf8mb4_bin이다.

## utf8mb4_general_ci: 한 글자에 weight 하나

MySQL이 자체적으로 만든 매핑 테이블이다.
단순하다. 글자 하나에 숫자 하나.

```text
'a' = 'A' = 'á' = 'ä' → 0x0041
'b' = 'B' → 0x0042
'ß' → 0x00DF
```

빠르다. 비교할 숫자가 하나뿐이니까.
대신 정확하지 않은 부분이 있다.
독일어 ß는 ss와 같은 글자인데 general_ci는 이걸 모른다.
각각 다른 weight를 갖는다.
Unicode 표준이 아니라 MySQL의 판단으로 만든 규칙이다.

## utf8mb4_0900_ai_ci: 세 겹의 weight

UCA 9.0.0이라는 Unicode 국제 표준을 따른다.
한 글자에 weight가 세 단계다.

```text
기본 악센트 대소문자
'a' → 1C47 0020 0002
'A' → 1C47 0020 0008
'á' → 1C47 0035 0002
'ß' → 1C47 + 1CA3 (= 'ss')
```

ai는 accent insensitive. 악센트를 무시한다.
ci는 case insensitive. 대소문자를 무시한다.
결국 기본 weight 하나로 비교한다.
단순 매핑이 아니라 국제 규칙이다.
ß가 ss와 같다는 것도 이 규칙이 정한다.

## utf8mb4_bin: weight 없이 바이트 그대로

weight 변환을 하지 않는다. 글자의 Unicode codepoint를 그대로 비교한다.
'A'는 0x41이고 'a'는 0x61이다. 다른 값이다. 다른 위치에 놓인다.
'café'와 'cafe'도 다르다. 'straße'와 'strasse'도 당연히 다르다.
가장 엄격하고 가장 빠르다.
변환할 게 없으니 비교 비용이 가장 낮다.
대소문자도 구분하고 악센트도 구분하고 바이트가 다르면 전부 다른 값이다.

## 같은 데이터, 세 가지 정렬

'strasse'로 WHERE 검색을 한다.
인덱스에 'straße'가 있을 때.
general_ci. ß와 ss는 다른 weight다. 못 찾는다.
0900_ai_ci. ß와 ss는 같은 weight다. 찾는다.
`_bin`. ß는 0xC39F이고 s는 0x73이다. 바이트가 다르니 당연히 못 찾는다.
'Strasse'와 'strasse'도 다른 값이다. 세 규칙이 같은 데이터를 다르게 판단한다.
어떤 collation을 고르느냐가 WHERE = 의 결과를 바꾼다.

## `_bin`을 써야 하는 순간

대부분의 서비스 테이블에는 ci를 쓴다. 대소문자 구분 없이 검색하는 게 자연스러우니까.
그런데 `_bin`이 맞는 경우가 있다.
비밀번호 해시. 'AbCdEf'와 'abcdef'는 달라야 한다.
API 토큰. Base64 인코딩은 대소문자가 의미를 갖는다.
파일 경로. Linux에서 File과 file은 다른 파일이다.
ci로 저장하면 다른 값이 같은 값으로 취급된다.
해시 충돌이 아닌데 충돌처럼 보인다.
정확한 바이트 일치가 필요하면 `_bin`. 사람이 읽는 텍스트면 ci.
이 기준이면 거의 틀리지 않는다.

## 악센트까지 같다고 보는 것

general_ci도 대소문자는 무시한다. 'Batch_User'와 'batch_user'는 같다.
0900_ai_ci는 여기에 악센트까지 무시한다. 'cafe'와 'café'도 같다.
`_bin`은 둘 다 구분한다. 'B'와 'b'도 다르고 'e'와 'é'도 다르다.
한국어 서비스에서는 체감이 적다. 한글에는 악센트가 없으니까.
그런데 글로벌 서비스를 만들면 달라진다.
사용자 이름에 José가 들어온다. jose로 검색해도 나와야 하는지.
이건 코드가 아니라 collation이 결정한다.

## 한글은 차이가 거의 없다

기본 한글 음절은 셋 다 Unicode codepoint 순서로 정렬된다.
가 나 다 순서. 차이가 없다.
차이가 나는 건 두 가지다.
한글 낱자. ㄱ, ㅏ 같은 자모. 0900이 Unicode 정규화를 더 정확히 처리한다.
이모지. general_ci는 4바이트 문자를 codepoint로만 비교한다.
0900은 UCA weight 기반이라 정렬이 더 정확하다.
`_bin`은 codepoint 그대로라 정렬은 되지만 유사 이모지를 묶지 못한다.
한국어 서비스에서 collation을 체감하는 순간은 이모지가 섞인 닉네임을 정렬할 때 정도다.

## UNIQUE 인덱스와 ORDER BY

collation은 "같다"의 기준을 바꾼다.
UNIQUE 인덱스에서 이게 직접적으로 드러난다.
ci에서는 'Admin'과 'admin'이 같은 값이다.
둘 중 하나만 들어간다. Duplicate key.
`_bin`에서는 다른 값이다. 둘 다 들어간다.
같은 UNIQUE 제약인데 collation에 따라 허용 범위가 달라진다.
ORDER BY도 마찬가지다.
ci는 'Apple'과 'apple'을 같은 순위로 본다.
`_bin`은 'Apple'이 먼저다. 대문자의 codepoint가 더 작으니까.
같은 쿼리, 같은 데이터. collation만 다르면 정렬 결과가 달라진다.

## CREATE TABLE의 함정

Aurora MySQL에서 테이블을 만든다.
CHARACTER SET utf8mb4만 지정하고 COLLATE는 안 넣었다.
MySQL 8.0 기본인 utf8mb4_0900_ai_ci가 붙는다. 지금은 맞다. 기본값이니까.
그런데 Aurora는 DB 레벨의 default collation을 나중에 바꿀 수 없다.
파라미터 그룹에서 collation_server를 바꿔도 이미 만들어진 DB에는 반영이 안 된다.
정책은 둘 중 하나여야 한다.
CHARACTER SET과 COLLATE를 항상 같이 명시하거나 둘 다 빼서 서버 기본값에 맡기거나.
charset만 넣고 collation을 빼는 게 가장 위험하다.
의도와 다른 collation이 묵시적으로 들어간다. 명시하거나 전부 맡기거나.
반만 지정하면 Default 값으로밖에 안들어간다.

## collation이 섞이면 생기는 일

MySQL 8.0으로 올리면 기본이 바뀐다.
새 테이블은 utf8mb4_0900_ai_ci로 생기고 기존 테이블은 utf8mb4_general_ci로 남는다.
아무도 모르는 사이에 섞인다.
이 두 테이블을 JOIN하면 MySQL은 한쪽 collation을 변환해야 한다.
변환되는 쪽은 인덱스를 탈 수 없다. 함수를 씌운 것과 같은 효과다.
양쪽 다 인덱스가 있어도 한쪽이 풀스캔으로 빠진다.
데이터가 적을 때는 모른다. 100만 건이 넘으면 쿼리가 갑자기 느려진다.
EXPLAIN을 보면 type이 ALL이다. 인덱스가 있는데 왜 안 타는지 한참 찾는다.
원인은 collation이다.

## Illegal mix of collations

JOIN만 문제가 아니다.
WHERE에서 서로 다른 collation 컬럼을 비교하면 MySQL이 에러를 던진다. "Illegal mix of collations"
UNION도 마찬가지다.
위쪽 SELECT는 general_ci인데 아래쪽이 0900_ai_ci면 에러다.
급할 때는 COLLATE 절로 강제한다.

```sql
ON A.user_name = B.user_name
COLLATE utf8mb4_0900_ai_ci
```

되긴 된다. 그런데 COLLATE를 붙인 쪽은 인덱스를 못 탄다.
급한 불은 끄지만 성능은 포기하는 것이다.
근본적인 해결은 하나다. collation을 통일하는 것이다.

## DBA 관점에서의 정리

하나의 DB에는 하나의 collation. 이게 원칙이다.
섞이는 순간 JOIN이 풀스캔으로 빠지고 UNION이 에러를 뱉고 UNIQUE의 중복 기준이 흔들리고 ORDER BY의 결과가 달라진다.
MySQL 8.0으로 올리면 자연스럽게 섞인다. Aurora에서는 DB 기본값을 나중에 못 바꾼다.
`ALTER TABLE CONVERT TO`는 인덱스 리빌드를 동반한다. 전부 나중에 고치기 비싼 것들이다.
처음에 정하고. 전부 맞추고. 건드리지 않는다.
CREATE TABLE마다 COLLATE를 명시하거나 서버 기본값을 믿고 전부 생략하거나.
collation은 보이지 않는 규칙이다.
보이지 않기 때문에 한 번 어긋나면 찾기도 어렵고 고치기도 비싸다.
