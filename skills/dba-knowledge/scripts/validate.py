#!/usr/bin/env python3
"""dba-knowledge 구조 정합성 validator.

annotated/ 문서의 frontmatter와 document-index.md, knowledge-map.md,
metadata-schema.md 사이의 구조적 정합성을 검사한다. 지식 내용의 옳고
그름은 평가하지 않는다. 표준 라이브러리만 사용한다.

사용법: python validate.py
정상이면 exit code 0, 오류가 있으면 파일/ID/이유를 출력하고 non-zero를
반환한다. 오류는 가능한 범위에서 한 번에 수집해 출력한다.
"""

import re
import sys
from collections import Counter
from pathlib import Path

REQUIRED_FIELDS = (
    "id",
    "title",
    "status",
    "topics",
    "triggers",
    "applies_to",
    "summary",
)
STATUS_VALUES = ("draft", "stable", "needs-review", "deprecated")
ID_PATTERN = re.compile(r"^DBA-\d{3}$")
FILE_NUM_PATTERN = re.compile(r"^(\d+)-")
INDEX_ROW_PATTERN = re.compile(r"^\|\s*(DBA-\d{3})\s*\|\s*(annotated/[^|]+?\.md)\s*\|")
MAP_ROW_PATTERN = re.compile(r"^\s*-\s*\[(DBA-\d{3})\]\((annotated/[^)]+\.md)\)")


def default_skill_dir():
    return Path(__file__).resolve().parent.parent


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text):
    """문서 첫머리의 --- YAML 블록을 최소 규칙으로 파싱한다."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None

    data = {}
    current_key = None
    mode = None  # None | "list" | "block"

    for line in lines[1:end]:
        if not line.strip():
            if mode != "block":
                current_key = None
            continue
        if line[0] in (" ", "\t"):
            if current_key is None:
                continue
            content = line.strip()
            if mode == "list":
                if content.startswith("- "):
                    data[current_key].append(unquote(content[2:].strip()))
            elif mode == "block":
                data[current_key].append(content)
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?$", line)
        if match:
            key = match.group(1)
            raw_value = (match.group(2) or "").strip()
            current_key = key
            if raw_value == ">":
                mode = "block"
                data[key] = []
            elif raw_value in ("", "|"):
                mode = "list"
                data[key] = []
            else:
                mode = None
                data[key] = unquote(raw_value)
    return data


def parse_document_index(text):
    """document-index.md의 표에서 (id, 파일 경로) 목록을 추출한다."""
    rows = []
    for line in text.splitlines():
        match = INDEX_ROW_PATTERN.match(line)
        if match:
            rows.append((match.group(1), match.group(2)))
    return rows


def parse_knowledge_map(text):
    """knowledge-map.md의 주 라우팅 섹션에서 문서 ID 목록을 추출한다."""
    ids = []
    for line in text.splitlines():
        match = MAP_ROW_PATTERN.match(line)
        if match:
            ids.append(match.group(1))
    return ids


def parse_applies_to_values(text):
    """metadata-schema.md의 applies_to 어휘 표에서 허용값 집합을 추출한다."""
    values = set()
    for line in text.splitlines():
        match = re.match(r"^\|\s*`([a-z][a-z-]*)`\s*\|", line)
        if match:
            values.add(match.group(1))
    return values


def validate_skill(skill_dir=None):
    """스킬 디렉터리의 구조적 정합성을 검사하고 오류 메시지 목록을 반환한다."""
    skill_dir = Path(skill_dir) if skill_dir else default_skill_dir()
    errors = []
    annotated_dir = skill_dir / "annotated"

    index_path = skill_dir / "document-index.md"
    map_path = skill_dir / "knowledge-map.md"
    schema_path = skill_dir / "metadata-schema.md"

    index_text = None
    if index_path.is_file():
        index_text = index_path.read_text(encoding="utf-8")
    else:
        errors.append(f"{index_path}: document-index.md 파일 없음")

    map_text = None
    if map_path.is_file():
        map_text = map_path.read_text(encoding="utf-8")
    else:
        errors.append(f"{map_path}: knowledge-map.md 파일 없음")

    schema_text = None
    if schema_path.is_file():
        schema_text = schema_path.read_text(encoding="utf-8")
    else:
        errors.append(f"{schema_path}: metadata-schema.md 파일 없음")

    allowed_applies = parse_applies_to_values(schema_text) if schema_text else set()
    index_rows = parse_document_index(index_text) if index_text else []
    map_ids = parse_knowledge_map(map_text) if map_text else []

    # 문서 수집
    docs = []  # (relative_path, frontmatter | None)
    for path in sorted(annotated_dir.glob("*.md")):
        rel = path.relative_to(skill_dir)
        docs.append((rel, parse_frontmatter(path.read_text(encoding="utf-8"))))

    # ID 수집 및 중복 검사
    id_by_file = {}
    seen_ids = {}
    for rel, fm in docs:
        if fm is None:
            continue
        doc_id = fm.get("id")
        if not doc_id:
            continue
        id_by_file[str(rel)] = doc_id
        if doc_id in seen_ids:
            errors.append(f"{doc_id}: ID 중복 ({seen_ids[doc_id]}와 {rel})")
        else:
            seen_ids[doc_id] = rel

    all_ids = set(seen_ids)

    # 각 문서 검사
    for rel, fm in docs:
        if fm is None:
            errors.append(f"{rel}: YAML frontmatter가 없거나 --- 블록이 닫히지 않음")
            continue

        for field in REQUIRED_FIELDS:
            if field not in fm:
                errors.append(f"{rel}: 필수 필드 없음: {field}")

        doc_id = fm.get("id")
        if not isinstance(doc_id, str) or not ID_PATTERN.fullmatch(doc_id):
            errors.append(f"{rel}: id 형식 오류 (DBA-XXX 형식이어야 함): {doc_id!r}")
        else:
            file_match = FILE_NUM_PATTERN.match(rel.name)
            if file_match:
                file_num = file_match.group(1)
                id_num = doc_id.split("-", 1)[1]
                if file_num != id_num:
                    errors.append(f"{rel}: 파일 번호({file_num})와 id({doc_id}) 불일치")

        status = fm.get("status")
        if status not in STATUS_VALUES:
            errors.append(
                f"{rel}: status 허용값 아님 (draft|stable|needs-review|deprecated): {status!r}"
            )

        applies = fm.get("applies_to")
        if not isinstance(applies, list) or not applies:
            errors.append(f"{rel}: applies_to는 비어 있지 않은 목록이어야 함")
        else:
            for value in applies:
                if value not in allowed_applies:
                    errors.append(f"{rel}: applies_to 허용값 아님: {value}")

        read_also = fm.get("read_also", [])
        if not isinstance(read_also, list):
            errors.append(f"{rel}: read_also는 목록이어야 함")
        else:
            for ref in read_also:
                if ref not in all_ids:
                    errors.append(f"{rel}: read_also에 존재하지 않는 ID: {ref}")
                if isinstance(doc_id, str) and ref == doc_id:
                    errors.append(f"{rel}: read_also가 자기 자신을 참조: {doc_id}")

    # document-index 검사
    if index_text is not None:
        index_files = [row[1] for row in index_rows]
        index_ids = [row[0] for row in index_rows]
        actual_files = {f"annotated/{rel.name}" for rel, _ in docs}

        file_counts = Counter(index_files)
        for path, count in sorted(file_counts.items()):
            if count > 1:
                errors.append(f"document-index.md: 파일 경로 중복 등록: {path}")

        id_counts = Counter(index_ids)
        for doc_id, count in sorted(id_counts.items()):
            if count > 1:
                errors.append(f"document-index.md: ID 중복 등록: {doc_id}")

        for path in sorted(actual_files - set(index_files)):
            errors.append(f"{path}: annotated 문서지만 document-index.md에 없음")

        for path in sorted(set(index_files) - actual_files):
            errors.append(f"document-index.md: {path} 파일이 실제로 없음")

        for row_id, row_path in index_rows:
            actual_id = id_by_file.get(row_path)
            if actual_id is not None and actual_id != row_id:
                errors.append(
                    f"document-index.md: {row_id} -> {row_path} 의 id가 실제 문서 id({actual_id})와 다름"
                )

        for doc_id in sorted(id_counts):
            if doc_id not in all_ids:
                errors.append(f"document-index.md: 문서에 존재하지 않는 고아 ID: {doc_id}")

    # knowledge-map 검사
    if map_text is not None:
        map_counts = Counter(map_ids)

        for doc_id, count in sorted(map_counts.items()):
            if count > 1:
                errors.append(f"{doc_id}: knowledge-map.md에 {count}번 중복 등록")

        for doc_id in sorted(all_ids - set(map_counts)):
            errors.append(f"{doc_id}: knowledge-map.md의 주 라우팅 섹션에 없음")

        for doc_id in sorted(set(map_counts) - all_ids):
            errors.append(f"{doc_id}: knowledge-map.md에 있지만 존재하지 않는 ID")

    return errors


def main():
    errors = validate_skill()
    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        print(f"검사 실패: 오류 {len(errors)}건", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())