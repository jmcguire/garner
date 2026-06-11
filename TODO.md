# cleaning up definitions:

 - look for things where the first paragraph is a list. that means it should have been appended to the previous thing but my parsing screwed up
 - my initial parsing may not have gotten the headwords exactly correct, in entries with semicolons?

# features:

 - look for internal links, like "See blah blah.", and wrap them in a markdown link so they "look" appropriate on a screen, even if they can't be clicked
 - need a way to look for those endings, like -ality, these are suffixes. they're currently marked as essays. a separate tag for prefixes or suffixes? should we require the -ality or can we search by ality?

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
