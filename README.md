# next

cleaning up:

 - look for things with many \* in a row. I think these are happening when it's a in a sectino title, like "E. As for like", where the whole thing is bold, and the "As" and "like" are also italicized.
 - look for things where the first paragraph is a list. that means it should have been appended to the previous thing by my parsing screwed up
 - an incorrect usage example inside a paragraph is preceded by an asterisk, \*, but these need to be encoded with a slash \\. i need something like `s/(\*\*[\w\s]+?\*(?!\*))/\\$1/`.
 - turn those bolded and lettered subsections into second-level headings?
 - what to do with the lists that should be tables?

easy features:

 - a list of essays, again with numbers. need an essay column. need to identify essays programatically from the md file. maybe with a -e/--essays.
 - help should explain "current ratio" and "language change index". also the point of this project. what a usage dictionary is.
 - look for internal links, like "(see blah blah)", and wrap them in a markdown link so they "look" appropriate on a screen, even if they can't be clicked
 - also look for entries that only an internal link, and store that forwarding entry
 - need a way to look for those endings, like -ality, these are suffixes. they're currently marked as essays. a separate tag for prefixes or siuffixes

harder features:

 - a separate table for misspellings?
 - how to package this up as an app. maybe a separate "compiled" thing?
 - what if it's part of word that matches, show a likely list? then let the the user either type the correct word, or a number, like `garner 2`, as a shortcut to an item in the last list shown. (which would require state.)
 - basically need a search if something doesn't match, also an actual -search flag
 - for long entries, give "page x/y" in the paging
 - tab-completion?

# usage

**garner <word>**

- if usage is found, print the markdown text, paged
- if "see xxx" is found, print "see <new word>" and print that word's text
- if word isn't found, finds spelling variants and display them

Before you do that, you need to build the sqllite database from the definitions folder. You only have to do this once.

**garner --build**

# common commands to clean up files

vi commands to remove extra lines and delete blank lines, between current location and mark a

    :, 'a g/^$/d
    :.,'as/^/ - /

and to do it backwards, so the mark is kept the same

    :'a,.g/\S/s/^/ - /
    :'a,.g/^\s*$/d

perl convert titles into filenames

    grep '^# ' body.txt

    perl -MUnicode::Normalize -pe'$_ = NFD($_); s/\p{NonspacingMark}//g; s/# //; s/[",\.]/_/g; s/[^\w_-]//g; print "$_\n"' titles

