# AGENTS.md

## Project Overview

`garner` is a Python command-line dictionary tool.

It reads Markdown definition files, builds a SQLite database, and lets users look up entries from the terminal.

The project should stay small, fast, and dependency-light.

## Core Concepts

* Markdown files are the editable source of truth.
* SQLite is the runtime lookup database.
* The CLI command is `garner`.
* The default action is lookup.
* The optional build step compiles Markdown definitions into SQLite.
* Generated database files should not be edited by hand.

## Expected CLI Behavior

The CLI should support:

```bash
garner WORD
garner --build
garner --build path/to/definitions
garner --db path/to/dictionary.sqlite WORD
garner --verbose WORD
```

Flags:

* `-b`, `--build`: build the SQLite database from Markdown definition files.
* `-d`, `--db`: specify the SQLite database location.
* `-v`, `--verbose`: show extra diagnostic output.
* Optional positional argument: lookup term.

If neither lookup nor build is provided, print help.

## Repository Layout

Expected structure:

```text
garner/
    __init__.py
    cli.py
    db.py
    parser.py
    builder.py

definitions/
    a/
    b/
    c/

tests/
```

Definitions are split into subdirectories by first letter.

The code should recursively discover Markdown files under `definitions/`.

## Definition File Format

Each entry is one Markdown file.

Each file starts with a single H1 heading:

```md
# Word or Phrase

Definition text here.
```

The H1 heading is the display term.

The Markdown body is the entry definition.

Do not infer the display term from the filename unless explicitly needed as a fallback.

## Filename Normalization

Filenames should be derived from the entry heading by normalizing to lowercase, replacing non-alphanumeric runs with hyphens, and trimming leading/trailing hyphens.

Example:

```text
"Death's Head!" -> deaths-head.md
```

Keep filename normalization separate from lookup normalization.

## Lookup Rules

Lookup should be forgiving.

Normalize lookup input independently from display text.

Expected behavior:

* Preserve original capitalization in displayed terms.
* Match case-insensitively.
* Ignore simple punctuation differences where practical.
* Support multi-word terms.
* Return a clear “not found” message when missing.

## Database Rules

Use SQLite from the Python standard library.

Suggested table fields:

* `term`: display term
* `lookup_key`: normalized lookup term
* `body`: Markdown definition body
* `source_path`: path to original Markdown file

Detect duplicate lookup keys during build and report them clearly.

Do not silently overwrite duplicate entries.

## Python Standards

* Use Python 3.13-compatible code unless project config says otherwise.
* Prefer standard library tools.
* Use `argparse` for the CLI.
* Use `pathlib` instead of `os.path`.
* Use type hints for public functions.
* Keep parsing, database access, and CLI code separate.
* Prefer explicit errors over silent fallbacks.
* Avoid global mutable state.
* Keep functions small and testable.

## Testing

Tests should be runnable from the repository root with:

```bash
pytest
```

Existing `unittest` tests may remain, but they should still be discoverable by `pytest`.

Add or update tests for:

* Markdown parsing
* heading extraction
* filename normalization
* lookup normalization
* database build
* duplicate detection
* CLI behavior
* missing lookup behavior
* recursive discovery under letter subdirectories

## Common Commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

Run legacy unittest discovery if needed:

```bash
python3 -m unittest discover -s tests
```

Run linting:

```bash
ruff check .
```

Format code:

```bash
ruff format .
```

Build the dictionary:

```bash
garner --build
```

Look up a term:

```bash
garner example
```

## Dependency Policy

Avoid new dependencies unless they materially simplify the project.

Before adding a dependency, explain:

* why the standard library is insufficient
* what the dependency does
* whether it affects CLI startup time

For Markdown parsing, prefer simple parsing unless the project needs full Markdown compatibility.

## Output Style

Terminal output should be readable and compact.

Colored output is allowed, but plain text behavior should remain correct.

Do not make colored output required for tests unless color handling is explicitly being tested.

## Things To Avoid

* Do not edit generated SQLite files by hand.
* Do not silently ignore malformed Markdown files.
* Do not silently overwrite duplicate entries.
* Do not mix parsing logic into CLI argument handling.
* Do not add heavyweight frameworks.
* Do not require network access.
* Do not assume the current working directory is always the repository root.
* Do not break macOS/Linux compatibility.

## Completion Checklist

Before considering a change complete:

1. Add tests for new behavior.
2. Run `pytest`.
3. If any tests fail, decide whether the test is valid and the code needs to be changed, or if the test is no longer testing the right thing and needs to be changed.
4. Rebuild the generated database from Markdown source, and check that output.
5. Confirm CLI examples still work.
6. Update this file and README and TODO if project commands or structure change.

