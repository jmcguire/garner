# cleaning up definitions:

 - look for things where the first paragraph is a list. that means it should have been appended to the previous thing by my parsing screwed up
 - an incorrect usage example inside a paragraph is preceded by an asterisk, \*, but these need to be encoded with a slash \\. i need something like `s/(\*\*[\w\s]+?\*(?!\*))/\\$1/`.
 - turn those bolded and lettered subsections into second-level headings?
 - get rid of the headword if it's the first thing in the first paragraph with just a period after it.
 - my initial parsing may not have gotten the headwords exactly correct, in entries with semicolons?

# easy features:

 - look for internal links, like "See blah blah.", and wrap them in a markdown link so they "look" appropriate on a screen, even if they can't be clicked
 - need a way to look for those endings, like -ality, these are suffixes. they're currently marked as essays. a separate tag for prefixes or suffixes?
 - lookup should also look at the start of a word?

# harder features:

 - how to package this up as an app. maybe a separate "compiled" thing?
 - what if it's part of word that matches, show a likely list? then let the the user either type the correct word, or a number, like `garner 2`, as a shortcut to an item in the last list shown. (which would require state.)
 - tab-completion?
 - right now i'm gaining all the information by parsing a regular entry straight from the book. this is getting clever and all, but at some point i might just need a proper metadata block for each entry.
 - maybe deciding i need a metadata block is my cue that i've gone too far and need to just need to call it.

# bugs:

 - Language Change index is sometimes not at the end of an entry, but just at the end of a lettered section. Just make it bold instead of a subheading? (e.g. often)

