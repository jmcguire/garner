import sqlite3
import tempfile
import unittest
from pathlib import Path

from garner import cli


FIXTURES = Path(__file__).parent / "fixtures" / "definitions"


def create_fixture_db(source_dir=FIXTURES):
    temp_dir = tempfile.TemporaryDirectory()
    db_path = Path(temp_dir.name) / "dictionary.sqlite"
    conn = sqlite3.connect(db_path)
    conn.executescript(cli.SCHEMA.replace("DROP TABLE entries;", "DROP TABLE IF EXISTS entries;"))

    for path in source_dir.rglob("*.md"):
        body = path.read_text(encoding="utf-8")
        plain_body = cli.markdown_to_plain(body)
        headword = cli.first_heading(body)
        sortword = cli.normalize(headword)
        phonetic_code = cli.get_phonetic_code(headword)
        forwarding = cli.get_forwarding(plain_body)
        is_essay = cli.get_is_essay(headword)

        if is_essay:
            headword = headword.removesuffix(", Essay")

        conn.execute(
            """
            INSERT INTO entries
                (headword, sort_key, phonetic_code, filename, body_markdown, body_plain, forwarding, is_essay)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                headword,
                sortword,
                phonetic_code,
                str(path),
                body,
                plain_body,
                forwarding,
                is_essay,
            ),
        )

    conn.commit()
    conn.close()
    return temp_dir, db_path


class HelperBehaviorTest(unittest.TestCase):
    def test_normalize_removes_punctuation_and_folds_whitespace(self):
        self.assertEqual(cli.normalize(" Hypercorrection,  Essay! "), " hypercorrection essay ")

    def test_first_heading_returns_level_one_heading(self):
        body = (FIXTURES / "h" / "hypercorrection.md").read_text(encoding="utf-8")

        self.assertEqual(cli.first_heading(body), "Hypercorrection, Essay")

    def test_get_is_essay_identifies_essay_heading(self):
        self.assertTrue(cli.get_is_essay("Hypercorrection, Essay"))
        self.assertFalse(cli.get_is_essay("affect"))

    def test_get_forwarding_returns_final_see_reference(self):
        body = cli.markdown_to_plain((FIXTURES / "e" / "effects.md").read_text(encoding="utf-8"))

        self.assertEqual(cli.get_forwarding(body), "effect")


class DictionaryBehaviorTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir, self.db_path = create_fixture_db()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_lookup_finds_exact_entry(self):
        row = cli.lookup("affect", self.db_path)

        self.assertIsNotNone(row)
        self.assertEqual(row["headword"], "affect")
        self.assertIn("To influence", row["body_plain"])

    def test_lookup_normalizes_punctuation(self):
        row = cli.lookup("affect!", self.db_path)

        self.assertIsNotNone(row)
        self.assertEqual(row["headword"], "affect")

    def test_lookup_keeps_forwarding_metadata(self):
        row = cli.lookup("effects", self.db_path)

        self.assertIsNotNone(row)
        self.assertEqual(row["forwarding"], "effect")

    def test_search_returns_matching_entries(self):
        rows = cli.search("affect", 10, self.db_path)

        self.assertIn("affect", [row["headword"] for row in rows])

    def test_list_essays_returns_essay_entries(self):
        rows = cli.list_essays(self.db_path)

        self.assertEqual([row["headword"] for row in rows], ["Hypercorrection"])
        self.assertTrue(rows[0]["is_essay"])


if __name__ == "__main__":
    unittest.main()

