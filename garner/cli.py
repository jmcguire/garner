#!/usr/bin/env python3

import argparse
import re
import sqlite3
import jellyfish
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown as Markdown2
from markdown import Markdown
from markdown_plain_text.extention import PlainTextExtension

script_dir = Path(__file__).resolve().parent
DEFAULT_DB = (script_dir.parent / "var" / "dictionary.sqlite").resolve()
DEFAULT_DEFINITIONS = (script_dir.parent / "definitions").resolve()
MAX_RESULTS_SHOWN = 10
SEARCH_EXACT = 0
SEARCH_PREFIX = 1
SEARCH_WORD_PREFIX = 2
SEARCH_SUBSTRING = 3
SEARCH_PHONETIC = 4
SEARCH_FUZZY = 5
SEARCH_MAX_FUZZY_RATIO = 0.45
SEARCH_MIN_FUZZY_SIMILARITY = 0.86

SCHEMA = """
DROP TABLE IF EXISTS entries;

CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    headword TEXT NOT NULL UNIQUE,
    sort_key TEXT NOT NULL,
    phonetic_code TEXT NOT NULL,
    filename TEXT NOT NULL,
    body_markdown TEXT NOT NULL,
    body_plain TEXT NOT NULL,
    forwarding TEXT NULL,
    is_essay BOOLEAN NOT NULL CHECK (is_essay in (0,1)),
    UNIQUE (sort_key, is_essay)
);

CREATE INDEX IF NOT EXISTS idx_entries_sort_key ON entries(sort_key);
CREATE INDEX IF NOT EXISTS idx_entries_phonetic_code ON entries(phonetic_code);
"""

# get rid of stuff we don't want the user looking up on, the results should be unique
def normalize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s'-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text, flags=re.UNICODE)
    return text


# the phonetic code helps the user search, despite mispellings
def get_phonetic_code(text):
    text = normalize(text)
    text = re.sub(r"[^a-zA-Z]", "", text, flags=re.UNICODE)
    phonetic_code = jellyfish.metaphone(text)
    return phonetic_code


# our entries are in markdown by default, this converts them to plain text
def markdown_to_plain(text):
    md = Markdown(extensions=[PlainTextExtension()])
    return md.convert(text)


# the heading at the top is the actual word(s) to match on
def first_heading(markdown):
    match = re.search(r"^#\s+(.+?)\s*$", markdown, flags=re.MULTILINE)
    return match.group(1) if match else None


# open and connect to a db
def connect(db_path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# is this entry actually just a forward to another entry? is so return that other entry name
def get_forwarding(body):
    pattern = r"\. See ([\w\s-]+)\.\Z"
    match = re.search(pattern, body, flags=re.DOTALL)
    if match:
        return match.group(1)
    else:
        return None


def get_is_essay(title):
    return title.endswith(", Essay")


def clean_headword(headword):
    is_essay = get_is_essay(headword)
    if is_essay:
        headword = headword.removesuffix(", Essay")
    return headword, is_essay


def lookup_key_and_essay_hint(word):
    key = normalize(word).strip()
    if key.endswith(" essay"):
        return key.removesuffix(" essay").strip(), True
    return key, None


def search_words(text):
    return [word for word in re.split(r"[\s'-]+", text) if word]


def search_score(word, row):
    sort_key = row["sort_key"]
    phonetic_code = row["phonetic_code"]
    phonetic_key = get_phonetic_code(word)

    if sort_key == word:
        bucket = SEARCH_EXACT
    elif sort_key.startswith(word):
        bucket = SEARCH_PREFIX
    elif any(part.startswith(word) for part in search_words(sort_key)):
        bucket = SEARCH_WORD_PREFIX
    elif word in sort_key:
        bucket = SEARCH_SUBSTRING
    elif phonetic_code == phonetic_key or phonetic_code.startswith(phonetic_key):
        bucket = SEARCH_PHONETIC
    else:
        bucket = SEARCH_FUZZY

    distance = jellyfish.levenshtein_distance(word, sort_key)
    similarity = jellyfish.jaro_winkler_similarity(word, sort_key)
    return (bucket, distance, -similarity, row["is_essay"], sort_key)


def is_search_match(score, word):
    bucket, distance, negative_similarity, _, _ = score
    if bucket < SEARCH_FUZZY:
        return True

    return (
        distance / max(len(word), 1) <= SEARCH_MAX_FUZZY_RATIO
        and -negative_similarity >= SEARCH_MIN_FUZZY_SIMILARITY
    )


# build the SQL database from the source directory, that has all the entries
def build(source_dir, db, verbose):
    db_path = Path(db).expanduser()
    conn = connect(db_path)
    conn.executescript(SCHEMA)

    console = Console()

    source_dir = Path(source_dir)
    console.print(f"Loading definitions from {source_dir}")

    for path in source_dir.rglob("*.md"):

        body = path.read_text(encoding="utf-8")
        plain_body = markdown_to_plain(body)

        heading = first_heading(body)
        if not heading:
            console.print(f"Skipping {path}: no level 1 heading", style="yellow")
            continue

        headword, is_essay = clean_headword(heading)
        sortword = normalize(headword)
        phonetic_code = get_phonetic_code(headword)
        forwarding = get_forwarding(plain_body)

        if verbose:
            if forwarding:
                console.print(f"loading {headword} ({sortword}) from {path}, forwards to {forwarding}", style="green")
            elif is_essay:
                console.print(f"loading {headword} ({sortword}) from {path}, an essay", style="green")
            else:
                console.print(f"loading {headword} ({sortword}) from {path}", style="green")

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
                is_essay
            ),
        )

    conn.commit()
    conn.close()

    print(f"Built database: {db_path}")


# a straight lookup for word
def lookup(word, db):
    db_path = Path(db).expanduser()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    key, is_essay = lookup_key_and_essay_hint(word)

    if is_essay is None:
        row = conn.execute(
            """
            SELECT headword, body_markdown, body_plain, filename, forwarding, is_essay
            FROM entries
            WHERE sort_key = ?
            ORDER BY is_essay ASC
            LIMIT 1
            """,
            (key,),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT headword, body_markdown, body_plain, filename, forwarding, is_essay
            FROM entries
            WHERE sort_key = ? AND is_essay = ?
            """,
            (key, is_essay),
        ).fetchone()


    conn.close()
    return row


def search(word, max_results, db):
    db_path = Path(db).expanduser()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    normalized_word = normalize(word).strip()
    if not normalized_word:
        conn.close()
        return []

    rows = search_query(normalized_word, conn)

    candidates = []
    seen = set()
    for row in rows:
        row_key = row["id"]
        if row_key in seen:
            continue

        seen.add(row_key)
        score = search_score(normalized_word, row)
        if not is_search_match(score, normalized_word):
            continue

        candidates.append((score, row))

    candidates.sort(key = lambda x: x[0])
    candidates = [candidate[1] for candidate in candidates]

    conn.close()
    return candidates[0:max_results]


# a helper function for search
def search_query(word, conn):
    # Return all entry headings so ranking can combine exact, prefix, phonetic, and fuzzy matches.
    rows = conn.execute(
        """
        SELECT id, headword, sort_key, phonetic_code, body_markdown, body_plain, filename, forwarding, is_essay
        FROM entries
        """
    ).fetchall()

    return rows


# get the complete list of essays
def list_essays(db):
    db_path = Path(db).expanduser()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT headword, sort_key, is_essay
        FROM entries
        WHERE is_essay = 1
        """,
    ).fetchall()

    conn.close()
    return rows


# prints the entry and/or the list of entries
def display(row, rows, verbose, plain):
    console = Console()

    if row:
        if verbose:
            console.print("filename: " + row["filename"])

        if plain:
            console.print(row["body_plain"])
        else:
            console.print(Markdown2(row["body_markdown"]))

    if rows:
        if row:
            print("\n\n")
        if verbose:
            for row in rows:
                console.print(f"{row['headword']} ({row['sort_key']}) @ {row['filename']} {' (essay)' if row['is_essay'] else ''}")
        else:
            for row in rows:
                console.print(f"{row['headword']} {' (essay)' if row['is_essay'] else ''}")

    if not row and not rows:
        print(f"No entry found")


def main():
    parser = argparse.ArgumentParser(prog="dict")

    parser.add_argument(
        "-d", "--db",
        default=str(DEFAULT_DB),
        help=f"SQLite database path; default: {DEFAULT_DB}",
    )

    parser.add_argument(
        "-b", "--build",
        nargs="?",
        const=True,
        metavar="DIR",
        help=f"Build the database from definition files; default: {DEFAULT_DEFINITIONS}",
    )

    parser.add_argument(
        "-e", "--essays",
        action="store_true",
        help="List the \"essays\" in this dictionary",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    parser.add_argument(
        "-p", "--plain",
        action="store_true",
        help="Output plain text, no fancy styling.",
    )

    parser.add_argument(
        "-s", "--search",
        help="Search for a word, instead of doing a straight lookup.",
    )

    parser.add_argument(
        "-m", "--maxresults",
        default=str(MAX_RESULTS_SHOWN),
        type=int,
        help=f"The maximum number of results to return when searching for a word; default: {MAX_RESULTS_SHOWN}",
    )

    parser.add_argument(
        "word",
        nargs="*",
        help="Word to look up. If multiple words are passed in, they will be concatenated.",
    )

    args = parser.parse_args()

    if args.word:
        word = " ".join(args.word)
        row = lookup(word, args.db)
        display(row, None, args.verbose, args.plain)

        if row and row["forwarding"]:
            print("\n")
            row = lookup(row["forwarding"], args.db)
            display(row, None, args.verbose, args.plain)
    
    elif args.build is not None:
        if args.build is True:
            source_dir = DEFAULT_DEFINITIONS
        else:
            source_dir = args.build
        build(source_dir, args.db, args.verbose)

    elif args.search is not None:
        rows = search(args.search, args.maxresults, args.db)
        display(None, rows, args.verbose, args.plain)

    elif args.essays is True:
        rows = list_essays(args.db)
        display(None, rows, args.verbose, args.plain)

    else:
        parser.print_help()
        parser.exit(1)


if __name__ == "__main__":
    main()
