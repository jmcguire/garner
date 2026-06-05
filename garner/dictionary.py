import sqlite3
from pathlib import Path

from rich.console import Console

from garner.search import is_search_match, search_score
from garner.text import (
    extract_first_heading,
    extract_forwarding_target,
    markdown_to_plain_text,
    normalize_key,
    parse_headword,
    parse_lookup_query,
    phonetic_code,
)


script_dir = Path(__file__).resolve().parent
DEFAULT_DB = (script_dir.parent / "var" / "dictionary.sqlite").resolve()
DEFAULT_DEFINITIONS = (script_dir.parent / "definitions").resolve()

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


def connect(db_path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def build(source_dir, db, verbose):
    """Build a disposable SQLite lookup database from Markdown entries."""
    db_path = Path(db).expanduser()
    conn = connect(db_path)
    conn.executescript(SCHEMA)

    console = Console()

    source_dir = Path(source_dir)
    console.print(f"Loading definitions from {source_dir}")

    for path in source_dir.rglob("*.md"):

        body = path.read_text(encoding="utf-8")
        plain_body = markdown_to_plain_text(body)

        heading = extract_first_heading(body)
        if not heading:
            console.print(f"Skipping {path}: no level 1 heading", style="yellow")
            continue

        headword, is_essay = parse_headword(heading)
        sortword = normalize_key(headword)
        sound_key = phonetic_code(headword)
        forwarding = extract_forwarding_target(plain_body, headword)

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
                sound_key,
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


def lookup(word, db):
    """Look up an exact entry, preferring regular entries unless the query asks for an essay."""
    db_path = Path(db).expanduser()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    key, is_essay = parse_lookup_query(word)

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
    """Return ranked search suggestions; max_results is a ceiling, not a quota."""
    db_path = Path(db).expanduser()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    normalized_word = normalize_key(word).strip()
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


def search_query(word, conn):
    rows = conn.execute(
        """
        SELECT id, headword, sort_key, phonetic_code, body_markdown, body_plain, filename, forwarding, is_essay
        FROM entries
        """
    ).fetchall()

    return rows


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
