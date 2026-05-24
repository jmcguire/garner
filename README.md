# next

 - need a way to look for those endings, like -ality
 - store actual connections of  "see x" in db
 - get rid of the essays. maybe store them separately? they might be referred to.
 - maybe a table for misspellings

# usage

**garner <word>**

- if usage is found, print text, paged
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

