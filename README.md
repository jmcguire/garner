# Basic instalation

If you want to use this tool, just install it through pipx:

`pipx install garner`

Then read the help instructions with `garner -h`.

The basic usage is `garner WORD` to see the usage for WORD, or `garner -s WORD` to search for WORD. The search is pretty generous.

If you want a paged result, pipe it through `less`.

You don't need to read anymore. The rest of this document is for developers.

# Developer Notes

Clone this repo, obviously.

Start with basic python stuff:

```sh
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
```

All the definitions are stored in definitions/, but the tool doesn't use those directly. Instead it uses that to build an SQLite database, and then queries that. (We do this for speed and for searching).

So the first thing you need to do is build the DB.

```
./venv/bin/garner --build
```

Now you can use the tool like normal.

## Tests

Run the tests with:

```sh
./venv/bin/python -m unittest discover -s tests
```

The tests use a small fixture dictionary in `tests/fixtures/definitions` instead of the full set of parsed definition files. They create a temporary SQLite database from those fixture entries and check the core lookup/search behavior against that tiny dictionary.

## Licensing

The code in this repository is MIT licensed. See `LICENSE`.

The dictionary content and bundled definitions are copyrighted by Bryan A.  Garner. See `NOTICE`.

## Releases

Release prep is scripted:

```sh
./scripts/release 1.1.0
```

See `RELEASING.md` for the full release checklist.
