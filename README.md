# next

## cleaning up definitions:

 - look for things where the first paragraph is a list. that means it should have been appended to the previous thing by my parsing screwed up
 - an incorrect usage example inside a paragraph is preceded by an asterisk, \*, but these need to be encoded with a slash \\. i need something like `s/(\*\*[\w\s]+?\*(?!\*))/\\$1/`.
 - turn those bolded and lettered subsections into second-level headings?
 - what to do with the lists that should be tables?

## easy features:

 - help should explain "current ratio" and "language change index". also the point of this project. what a usage dictionary is.
 - look for internal links, like "(see blah blah)", and wrap them in a markdown link so they "look" appropriate on a screen, even if they can't be clicked
 - need a way to look for those endings, like -ality, these are suffixes. they're currently marked as essays. a separate tag for prefixes or suffixes?
 - if a lookup on a word isn't found, search instead?

## harder features:

 - how to package this up as an app. maybe a separate "compiled" thing?
 - what if it's part of word that matches, show a likely list? then let the the user either type the correct word, or a number, like `garner 2`, as a shortcut to an item in the last list shown. (which would require state.)
 - for long entries, give "page x/y" in the paging
 - tab-completion?

## bugs:

 - the search isn't correctly searching for essays, e.g. "Hypercorrection (essay)"

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

