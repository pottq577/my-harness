"""dba-knowledge 구조 validator 테스트.

실제 annotated/ 문서를 수정하지 않고 임시 디렉터리 fixture로 검증한다.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "dba-knowledge" / "scripts"))

import validate

SCHEMA_TEXT = """# 메타데이터 스키마

| 값 | 의미 |
| --- | --- |
| `schema-design` | 스키마 설계 |
| `sql-review` | SQL 리뷰 |
"""


def write_doc(path, doc_id, status="stable", applies=("schema-design",), read_also=()):
    lines = [
        "---",
        f"id: {doc_id}",
        f'title: "{doc_id} 제목"',
        f"status: {status}",
        "",
        "topics:",
        f"  - topic-{doc_id}",
        "",
        "triggers:",
        f"  - 트리거 {doc_id}",
        "",
        "applies_to:",
    ]
    for value in applies:
        lines.append(f"  - {value}")
    lines.append("")
    lines.append("summary: >")
    lines.append(f"  {doc_id} 문서 요약.")
    if read_also:
        lines.append("")
        lines.append("read_also:")
        for ref in read_also:
            lines.append(f"  - {ref}")
    lines.append("")
    lines.append("---")
    lines.append(f"# {doc_id}")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_index(root, rows):
    lines = ["# 인덱스", "", "| id | file | title |", "| --- | --- | --- |"]
    for doc_id, filename in rows:
        lines.append(f"| {doc_id} | annotated/{filename} | {doc_id} 제목 |")
    (root / "document-index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_map(root, ids):
    lines = ["# 지도", "", "## 섹션 1. Test", ""]
    for doc_id in ids:
        lines.append(f"- [{doc_id}](annotated/{doc_id.lower()}.md) {doc_id}")
    (root / "knowledge-map.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


class ValidatorTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "annotated").mkdir()
        (self.root / "metadata-schema.md").write_text(SCHEMA_TEXT, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self):
        return validate.validate_skill(self.root)

    def test_valid_fixture_passes(self):
        write_doc(self.root / "annotated" / "001-a.md", "DBA-001")
        write_doc(self.root / "annotated" / "002-b.md", "DBA-002", read_also=("DBA-001",))
        write_index(self.root, [("DBA-001", "001-a.md"), ("DBA-002", "002-b.md")])
        write_map(self.root, ["DBA-001", "DBA-002"])
        self.assertEqual(self._run(), [])

    def test_missing_read_also_fails(self):
        write_doc(self.root / "annotated" / "001-a.md", "DBA-001")
        write_doc(self.root / "annotated" / "002-b.md", "DBA-002", read_also=("DBA-999",))
        write_index(self.root, [("DBA-001", "001-a.md"), ("DBA-002", "002-b.md")])
        write_map(self.root, ["DBA-001", "DBA-002"])
        errors = self._run()
        self.assertTrue(any("DBA-999" in e and "존재하지 않는 ID" in e for e in errors))

    def test_duplicate_id_fails(self):
        write_doc(self.root / "annotated" / "001-a.md", "DBA-001")
        write_doc(self.root / "annotated" / "001-b.md", "DBA-001")
        write_index(self.root, [("DBA-001", "001-a.md")])
        write_map(self.root, ["DBA-001"])
        errors = self._run()
        self.assertTrue(any("ID 중복" in e for e in errors))

    def test_invalid_applies_to_fails(self):
        write_doc(self.root / "annotated" / "001-a.md", "DBA-001", applies=("not-a-real-value",))
        write_index(self.root, [("DBA-001", "001-a.md")])
        write_map(self.root, ["DBA-001"])
        errors = self._run()
        self.assertTrue(any("applies_to 허용값 아님" in e for e in errors))

    def test_missing_document_index_fails(self):
        write_doc(self.root / "annotated" / "001-a.md", "DBA-001")
        write_map(self.root, ["DBA-001"])
        errors = self._run()
        self.assertTrue(any("document-index.md 파일 없음" in e for e in errors))

    def test_duplicate_map_entry_fails(self):
        write_doc(self.root / "annotated" / "001-a.md", "DBA-001")
        write_index(self.root, [("DBA-001", "001-a.md")])
        write_map(self.root, ["DBA-001", "DBA-001"])
        errors = self._run()
        self.assertTrue(any("중복 등록" in e for e in errors))


if __name__ == "__main__":
    unittest.main()