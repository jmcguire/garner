import contextlib
import io
import sqlite3
import tempfile
import unittest
from unittest import mock
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
        heading = cli.first_heading(body)
        headword, is_essay = cli.clean_headword(heading)
        sortword = cli.normalize(headword)
        phonetic_code = cli.get_phonetic_code(headword)
        forwarding = cli.get_forwarding(plain_body)

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

    def test_clean_headword_removes_essay_suffix_for_lookup_keys(self):
        headword, is_essay = cli.clean_headword("Hypercorrection, Essay")

        self.assertEqual(headword, "Hypercorrection")
        self.assertTrue(is_essay)

    def test_lookup_key_and_essay_hint_strips_trailing_essay(self):
        key, is_essay = cli.lookup_key_and_essay_hint("Etymology (essay)")

        self.assertEqual(key, "etymology")
        self.assertTrue(is_essay)

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

    def test_lookup_prefers_regular_entry_when_essay_has_same_key(self):
        row = cli.lookup("etymology", self.db_path)

        self.assertIsNotNone(row)
        self.assertEqual(row["headword"], "etymology")
        self.assertFalse(row["is_essay"])

    def test_lookup_uses_essay_hint_when_essay_has_same_key(self):
        row = cli.lookup("etymology essay", self.db_path)

        self.assertIsNotNone(row)
        self.assertEqual(row["headword"], "Etymology")
        self.assertTrue(row["is_essay"])

    def test_lookup_uses_parenthesized_essay_hint(self):
        row = cli.lookup("etymology (essay)", self.db_path)

        self.assertIsNotNone(row)
        self.assertEqual(row["headword"], "Etymology")
        self.assertTrue(row["is_essay"])

    def test_search_returns_matching_entries(self):
        rows = cli.search("affect", 10, self.db_path)

        self.assertIn("affect", [row["headword"] for row in rows])

    def test_search_normalizes_query_punctuation(self):
        rows = cli.search("affect!", 10, self.db_path)

        self.assertIn("affect", [row["headword"] for row in rows])

    def test_search_honors_max_results(self):
        rows = cli.search("e", 1, self.db_path)

        self.assertEqual(len(rows), 1)

    def test_search_deduplicates_repeated_candidates(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = cli.search_query("affect", conn)
        conn.close()

        with mock.patch("garner.cli.search_query", return_value=rows + rows):
            results = cli.search("affect", 10, self.db_path)

        self.assertEqual(
            len(results),
            len({row["headword"] for row in results}),
        )

    def test_list_essays_returns_essay_entries(self):
        rows = cli.list_essays(self.db_path)
        headwords = [row["headword"] for row in rows]

        self.assertIn("Hypercorrection", headwords)
        self.assertIn("Etymology", headwords)
        self.assertTrue(all(row["is_essay"] for row in rows))

    def test_build_indexes_essays_by_clean_headword(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "dictionary.sqlite"

            with contextlib.redirect_stdout(io.StringIO()):
                cli.build(FIXTURES, db_path, verbose=False)

            self.assertIsNotNone(cli.lookup("hypercorrection", db_path))
            self.assertIsNotNone(cli.lookup("hypercorrection essay", db_path))

    def test_build_allows_regular_entry_and_essay_with_same_sort_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "dictionary.sqlite"

            with contextlib.redirect_stdout(io.StringIO()):
                cli.build(FIXTURES, db_path, verbose=False)

            self.assertFalse(cli.lookup("etymology", db_path)["is_essay"])
            self.assertTrue(cli.lookup("etymology essay", db_path)["is_essay"])


if __name__ == "__main__":
    unittest.main()
