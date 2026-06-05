import contextlib
import io
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from garner import cli
from garner import dictionary
from garner import text


FIXTURES = Path(__file__).parent / "fixtures" / "definitions"


def create_fixture_db(source_dir=FIXTURES):
    temp_dir = tempfile.TemporaryDirectory()
    db_path = Path(temp_dir.name) / "dictionary.sqlite"
    with contextlib.redirect_stdout(io.StringIO()):
        dictionary.build(source_dir, db_path, verbose=False)
    return temp_dir, db_path


def run_cli(args):
    stdout = io.StringIO()
    with mock.patch.object(sys, "argv", ["garner"] + args):
        with contextlib.redirect_stdout(stdout):
            cli.main()
    return stdout.getvalue()


def run_cli_expecting_exit(args):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with mock.patch.object(sys, "argv", ["garner"] + args):
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                cli.main()
            except SystemExit as error:
                return error.code, stdout.getvalue(), stderr.getvalue()

    raise AssertionError("expected SystemExit")


class HelperBehaviorTest(unittest.TestCase):
    def test_normalize_key_removes_punctuation_and_folds_whitespace(self):
        self.assertEqual(text.normalize_key(" Hypercorrection,  Essay! "), " hypercorrection essay ")

    def test_extract_first_heading_returns_level_one_heading(self):
        body = (FIXTURES / "h" / "hypercorrection.md").read_text(encoding="utf-8")

        self.assertEqual(text.extract_first_heading(body), "Hypercorrection, Essay")

    def test_is_essay_heading_identifies_essay_heading(self):
        self.assertTrue(text.is_essay_heading("Hypercorrection, Essay"))
        self.assertFalse(text.is_essay_heading("affect"))

    def test_parse_headword_removes_essay_suffix_for_lookup_keys(self):
        headword, is_essay = text.parse_headword("Hypercorrection, Essay")

        self.assertEqual(headword, "Hypercorrection")
        self.assertTrue(is_essay)

    def test_parse_lookup_query_strips_trailing_essay(self):
        key, is_essay = text.parse_lookup_query("Etymology (essay)")

        self.assertEqual(key, "etymology")
        self.assertTrue(is_essay)

    def test_extract_forwarding_target_returns_final_see_reference(self):
        body = text.markdown_to_plain_text((FIXTURES / "e" / "effects.md").read_text(encoding="utf-8"))

        self.assertEqual(text.extract_forwarding_target(body, "effects"), "effect")

    def test_extract_forwarding_target_ignores_long_entries_ending_in_see_reference(self):
        body = text.markdown_to_plain_text((FIXTURES / "h" / "hypercorrection.md").read_text(encoding="utf-8"))

        self.assertIsNone(text.extract_forwarding_target(body, "Hypercorrection"))

    def test_extract_forwarding_target_matches_escaped_markdown_headword(self):
        body = text.markdown_to_plain_text("# \\*wrapt\n\n\\*wrapt. See **rapt**.\n")

        self.assertEqual(text.extract_forwarding_target(body, "\\*wrapt"), "rapt")


class DictionaryBehaviorTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir, self.db_path = create_fixture_db()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_lookup_finds_exact_entry(self):
        row = dictionary.lookup("affect", self.db_path)

        self.assertIsNotNone(row)
        self.assertEqual(row["headword"], "affect")
        self.assertIn("To influence", row["body_plain"])

    def test_lookup_normalizes_punctuation(self):
        row = dictionary.lookup("affect!", self.db_path)

        self.assertIsNotNone(row)
        self.assertEqual(row["headword"], "affect")

    def test_lookup_keeps_forwarding_metadata(self):
        row = dictionary.lookup("effects", self.db_path)

        self.assertIsNotNone(row)
        self.assertEqual(row["forwarding"], "effect")

    def test_lookup_prefers_regular_entry_when_essay_has_same_key(self):
        row = dictionary.lookup("etymology", self.db_path)

        self.assertIsNotNone(row)
        self.assertEqual(row["headword"], "etymology")
        self.assertFalse(row["is_essay"])

    def test_lookup_uses_essay_hint_when_essay_has_same_key(self):
        row = dictionary.lookup("etymology essay", self.db_path)

        self.assertIsNotNone(row)
        self.assertEqual(row["headword"], "Etymology")
        self.assertTrue(row["is_essay"])

    def test_lookup_uses_parenthesized_essay_hint(self):
        row = dictionary.lookup("etymology (essay)", self.db_path)

        self.assertIsNotNone(row)
        self.assertEqual(row["headword"], "Etymology")
        self.assertTrue(row["is_essay"])

    def test_search_returns_matching_entries(self):
        rows = dictionary.search("affect", 10, self.db_path)

        self.assertIn("affect", [row["headword"] for row in rows])

    def test_search_ranks_exact_before_prefix_matches(self):
        rows = dictionary.search("effect", 3, self.db_path)

        self.assertEqual(rows[0]["headword"], "effect")
        self.assertEqual(rows[1]["headword"], "effects")

    def test_search_ranks_prefix_before_word_prefix_matches(self):
        rows = dictionary.search("effect", 10, self.db_path)
        headwords = [row["headword"] for row in rows]

        self.assertLess(headwords.index("effective"), headwords.index("side effect"))

    def test_search_includes_fuzzy_matches_for_misspellings(self):
        rows = dictionary.search("efect", 5, self.db_path)

        self.assertIn("effect", [row["headword"] for row in rows])

    def test_search_keeps_close_long_misspellings(self):
        rows = dictionary.search("recieved", 5, self.db_path)

        self.assertEqual(rows[0]["headword"], "receive")

    def test_search_excludes_similar_but_distant_fuzzy_matches(self):
        rows = dictionary.search("recieved", 10, self.db_path)

        self.assertNotIn("recitative", [row["headword"] for row in rows])

    def test_search_excludes_distant_fuzzy_matches(self):
        rows = dictionary.search("effe", 10, self.db_path)

        self.assertNotIn("affect", [row["headword"] for row in rows])

    def test_search_does_not_fill_short_prefix_searches_with_fuzzy_noise(self):
        rows = dictionary.search("hyper", 10, self.db_path)
        headwords = [row["headword"] for row in rows]

        self.assertIn("hyperbola", headwords)
        self.assertNotIn("cypher", headwords)

    def test_search_normalizes_query_punctuation(self):
        rows = dictionary.search("affect!", 10, self.db_path)

        self.assertIn("affect", [row["headword"] for row in rows])

    def test_search_honors_max_results(self):
        rows = dictionary.search("e", 1, self.db_path)

        self.assertEqual(len(rows), 1)

    def test_search_deduplicates_repeated_candidates(self):
        conn = dictionary.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = dictionary.search_query("affect", conn)
        conn.close()

        with mock.patch("garner.dictionary.search_query", return_value=rows + rows):
            results = dictionary.search("affect", 10, self.db_path)

        self.assertEqual(
            len(results),
            len({row["headword"] for row in results}),
        )

    def test_list_essays_returns_essay_entries(self):
        rows = dictionary.list_essays(self.db_path)
        headwords = [row["headword"] for row in rows]

        self.assertIn("Hypercorrection", headwords)
        self.assertIn("Etymology", headwords)
        self.assertTrue(all(row["is_essay"] for row in rows))

    def test_build_indexes_essays_by_parsed_headword(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "dictionary.sqlite"

            with contextlib.redirect_stdout(io.StringIO()):
                dictionary.build(FIXTURES, db_path, verbose=False)

            self.assertIsNotNone(dictionary.lookup("hypercorrection", db_path))
            self.assertIsNotNone(dictionary.lookup("hypercorrection essay", db_path))

    def test_build_allows_regular_entry_and_essay_with_same_sort_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "dictionary.sqlite"

            with contextlib.redirect_stdout(io.StringIO()):
                dictionary.build(FIXTURES, db_path, verbose=False)

            self.assertFalse(dictionary.lookup("etymology", db_path)["is_essay"])
            self.assertTrue(dictionary.lookup("etymology essay", db_path)["is_essay"])

    def test_failed_lookup_shows_short_search_suggestions(self):
        output = run_cli(["--db", str(self.db_path), "recieved"])

        self.assertIn("No exact entry found for recieved. Did you mean:", output)
        self.assertIn("receive", output)
        self.assertLessEqual(
            len([line for line in output.splitlines() if line and not line.startswith("No exact")]),
            cli.LOOKUP_SUGGESTIONS_SHOWN,
        )

    def test_failed_lookup_without_suggestions_still_says_no_entry_found(self):
        output = run_cli(["--db", str(self.db_path), "zzzzzzzz"])

        self.assertEqual(output.strip(), "No entry found")

    def test_search_option_combines_extra_words_into_search_query(self):
        output = run_cli(["--db", str(self.db_path), "-s", "hypercorrection", "essay"])

        self.assertIn("Hypercorrection  (essay)", output)
        self.assertNotIn("No exact entry found for essay", output)

    def test_maxresults_requires_search(self):
        code, stdout, stderr = run_cli_expecting_exit(["--db", str(self.db_path), "--maxresults", "3", "affect"])

        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("--maxresults can only be used with --search", stderr)


if __name__ == "__main__":
    unittest.main()
