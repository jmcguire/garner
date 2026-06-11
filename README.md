# usage

Start with basic python stuff:

```sh
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
```

The packaged command includes a compiled SQLite dictionary. If you are working
from the developer checkout and want to rebuild it from the Markdown
definitions, run:

```
./venv/bin/garner --build
```

Then you can lookup words simply like:

```
./venv/bin/garner <word>
```

Or search for words like:

```
./venv/bin/garner -s <word>
```

If you want a paged result, pipe it through `less`.

# tests

Run the tests with:

```sh
./venv/bin/python -m unittest discover -s tests
```

The tests use a small fixture dictionary in `tests/fixtures/definitions`
instead of the full set of parsed definition files. They create a temporary
SQLite database from those fixture entries and check the core lookup/search
behavior against that tiny dictionary.

# releases

Release prep is scripted:

```sh
./scripts/release 1.1.0
```

See `RELEASING.md` for the full release checklist.

# scratchpad

```sh
# to find likely links
# note that i'll need to check for parentheses and ampersands
find . -type file -print | xargs perl -ne'print "$ARGV: $1\n" if /(See ([^.]+)\.)/'

# if it's for an essay it'll be "Cf. retronyms."

# find good candidates for tables
find . -type file -print | xargs perl -ne'print "$ARGV: $_\n" if /^\*+[\w\s]+\*+ \*+[\w\s]+\*+/'
```

```
# and in vi

:'a,.g/\S/s/^/ - /
:'a .g/^\s*$/d
```
