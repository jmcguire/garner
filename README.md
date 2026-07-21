# Garner

Garner is a command-line interface for the Garner Usage Dictionary.

## Install

On macOS or Linux with [Homebrew](https://brew.sh/):

```sh
brew install jmcguire/garner/garner-dict
```

Or, on any system with Python 3.9 or newer, install the Python package with
[pipx](https://pipx.pypa.io/):

```sh
pipx install garner-dict
```

Both install the command as `garner`. Try it with:

```sh
garner affect
garner --search accomodate
garner --help
```

Pipe a long entry through `less` for paged output:

```sh
garner affect | less
```

## About Distribution

This is an independent command-line interface and packaging project. It is not
an official publication of Bryan A. Garner or of the Garner Usage Dictionary.
The code is MIT licensed, but the dictionary content is copyrighted by Bryan A.
Garner and is not licensed by this repository. See [NOTICE](NOTICE).

The Homebrew package is intentionally published in the maintainer's personal
tap (`jmcguire/garner`), not in `homebrew/core`. That makes the source,
maintainer, and content notice explicit, and does not imply that the dictionary
content has been approved for official Homebrew distribution. The PyPI package
and Homebrew formula bundle the same compiled dictionary database. Anyone who
uses or redistributes it remains responsible for respecting the applicable
rights.

## Developer Notes

Clone this repository, then create a development environment:

```sh
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
```

The Markdown files in `definitions/` are the editable source of truth. Garner
builds them into an SQLite database for fast lookup and search. Build the local
database before trying source changes:

```sh
./venv/bin/garner --build
```

Then use the tool normally:

```sh
./venv/bin/garner affect
./venv/bin/garner --search accomodate
```

### Tests

Run the tests with:

```sh
./venv/bin/python -m unittest discover -s tests
```

The tests use a small fixture dictionary in `tests/fixtures/definitions`, not
the full definitions collection. They build a temporary SQLite database from
those entries and cover core lookup, search, forwarding, and formatting
behavior without making small source-formatting changes needlessly brittle.

### Licensing

The code in this repository is MIT licensed. See [LICENSE](LICENSE).

The dictionary content and bundled definitions are copyrighted by Bryan A.
Garner. See [NOTICE](NOTICE).

### Releases

Release preparation is scripted:

```sh
./venv/bin/python scripts/release 1.1.0
```

See [RELEASING.md](RELEASING.md) for the release and distribution checklist.
