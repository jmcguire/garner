# Releasing Garner

Garner has one version number for both the application code and bundled
dictionary database. Entry-only changes need a release version because users
receive them through a new packaged SQLite database.

Use normal semantic-ish versions:

- Patch, such as `1.1.1`: typo/content fixes and small display or ranking fixes.
- Minor, such as `1.2.0`: new CLI behavior or a substantial dictionary refresh.
- Major, such as `2.0.0`: incompatible CLI or data behavior.

## Distribution Policy

This project supplies independent tooling and packaging; it is not an official
publication of Bryan A. Garner or the Garner Usage Dictionary. The code is
MIT-licensed, while the bundled dictionary content remains copyrighted by Bryan
A. Garner and is not licensed by this repository. Recheck [NOTICE](NOTICE)
before every release.

The PyPI package and the Homebrew formula include the same compiled SQLite
database. The Homebrew formula is kept in the maintainer's personal tap,
`jmcguire/homebrew-garner`, rather than submitted to `homebrew/core`. This is a
deliberate transparency and scope decision: it makes the maintainer, source,
and rights notice clear, but it does not represent permission or endorsement
from the dictionary's copyright holder. Do not describe either distribution as
official, and do not remove or weaken the content notice.

## Prerequisites

Begin with a clean working tree:

```sh
git status --short
```

Create a virtual environment and install the development and release tools:

```sh
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python -m pip install twine
```

Use `./venv/bin/python` for release commands. Running `./scripts/release`
directly uses whichever `python3` appears first in `PATH`; that interpreter may
not have Garner's dependencies installed.

## Prepare a Release

Run the release helper with the new version:

```sh
./venv/bin/python scripts/release 1.1.0
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
git add garner/__version__.py garner/data/dictionary.sqlite
git commit -m "Release 1.1.0"
git tag v1.1.0
```

Push the commit and tag after the release artifacts have been reviewed:

```sh
git push
git push origin v1.1.0
```

## Publish to PyPI

Check the artifacts, then upload them to the production PyPI project. The
distribution name is `garner-dict`; the installed command remains `garner`.

```sh
./venv/bin/python -m twine check dist/*
./venv/bin/python -m twine upload dist/*
```

When prompted by Twine, use `__token__` as the username and a PyPI API token as
the password. Confirm the public install in a clean pipx environment:

```sh
pipx install --force garner-dict
garner --version
garner affect
garner --search accomodate
```

TestPyPI is optional and useful for rehearsing an upload. It does not mirror
all normal PyPI dependencies, including `jellyfish` and `rich`, so do not use
it as the sole package index for a normal install. To test a TestPyPI wheel,
download that wheel with `--no-deps` and let pipx resolve its dependencies from
PyPI.

## Update the Homebrew Tap

Publish the PyPI release before changing the formula. The formula's source URL
and checksum must point to the new `garner-dict` source distribution; obtain
both from the release's files on PyPI. Then update the Python dependency
resources in the personal tap:

```sh
brew update-python-resources jmcguire/garner/garner-dict --version 1.1.0
```

Review the formula, making sure its versioned PyPI source URL and `sha256` were
updated along with any resource blocks. Homebrew's command is intended to
maintain the dependency resource blocks; verify the main source archive fields
yourself.

Run the formula checks from the tap checkout:

```sh
brew install --build-from-source jmcguire/garner/garner-dict
brew test jmcguire/garner/garner-dict
brew audit --strict --online jmcguire/garner/garner-dict
brew style jmcguire/garner/garner-dict
```

Commit and push the formula change in `jmcguire/homebrew-garner`. Users can
then install it in one command:

```sh
brew install jmcguire/garner/garner-dict
```

Homebrew formulas for Python applications install their own isolated virtual
environment and declared Python resources. End users do not need to create a
Python virtual environment to run `garner`.
