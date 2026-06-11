# Releasing Garner

Garner has one version number for both the application code and the bundled
dictionary database. Entry-only changes still need a release version because
users receive those changes through a new packaged SQLite database.

Use normal semantic-ish versions:

 - Patch, such as `1.1.1`: typo fixes, content fixes, small display/ranking fixes.
 - Minor, such as `1.2.0`: new CLI behavior or a substantial dictionary refresh.
 - Major, such as `2.0.0`: incompatible CLI or data behavior.

## Prerequisites

Start from a clean working tree:

```sh
git status --short
```

Install development and release dependencies:

```sh
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
```

## Prepare a Release

Run the release helper with the new version:

```sh
./scripts/release 1.1.0
```

The script:

 - updates `garner/__version__.py`
 - rebuilds `garner/data/dictionary.sqlite` from `definitions/`
 - runs the test suite
 - builds the wheel and source distribution
 - verifies that the wheel contains the bundled SQLite database
 - installs the wheel into a temporary virtual environment and smoke-tests it

If the script fails, fix the problem and rerun it. Do not edit the generated
SQLite database by hand.

## Review, Commit, and Tag

After the script passes, review the generated changes:

```sh
git status --short
git diff --stat
```

Then commit and tag:

```sh
git add pyproject.toml MANIFEST.in RELEASING.md requirements.txt scripts/release
git add garner/__version__.py garner/data/__init__.py garner/data/dictionary.sqlite
git commit -m "Release 1.1.0"
git tag v1.1.0
```

## Publish

PyPI/TestPyPI and Homebrew publishing are not wired up yet. When they are, add
the exact upload commands here.

For now, the built files are in `dist/`.
