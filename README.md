# usage

Start with basic python stuff:

```sh
python3 -m venv venv
. ./venv/bin/activate
python3 -m pip install
```

Before you can use this dictionary utility, you need to build the local database with the definition files. You only have to do this once, the SQL db will be stored on disk.

```
garner --build
```

Then you can lookup words simply like:

```
garner <word>
```

Or search for words like:

```
garner -s <word>
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
