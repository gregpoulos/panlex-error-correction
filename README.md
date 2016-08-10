# PanLex Error Correction Stuff

This repo contains various Python script that are useful for processing expression lists into candidates for error correction.

## Scripts

### flag.py

This script can perform a variety of processing tasks to detect expressions that are potentially problematic.

 - Input: a simple list of expressions (i.e., one expression per line, without any other fields).
 - Output: variable, based on user flags, but essentially a simple list of expressions as well 

Here's a handy way to get a list of all Arabic expressions from the PanLex database:

```
\copy (select tt from ex WHERE lv = 34) To '~/path/to/dir/arb-000.txt' With CSV
```

### editdist.py

This script detects pairs of expressions that are within some edit distance of each other. It's a long-running script, as you might imagine.

 - Input: a simple list of expressions.
 - Output: ???

### doppelgang.py

This script finds "doppelganger pairs", which are pairs of expressions that have similar-looking characters in the same string positions. (Think 'HELLO' with a capital letter 'O' and 'HELL0' with a zero in the final position.)

 - Input: a list of confusable characters, a simple list of expressions
 - Output: a list of pairs of expressions ("doppelgangers")

### prep_for_db.py

This script takes a list of potentially erroneous expressions and creates a .tsv file that can be loaded into the PanLex database with the following command:

```
\copy dev.exmod_candidates_generated (lv, bad, good, score, reason, comment) FROM '~/path/to/source/my_errors.tsv'
```

As opposed to the previous scripts, this script asks for a more complicated input file---not just simple expressions, but expressions with IDs and reference counts. Here's a helpful command to get a list of all Mandarin expressions, with their IDs and reference counts:

```
\copy (select ex.ex, ex.tt, count(*) as dncount from ex join dn on (dn.ex = ex.ex) where lv = 1627 group by ex.ex) To '~/path/to/dir/cmn-000.csv' With CSV
```

For a different language, set 'lv' to an integer other than 1627. (English is 187.)

 - Input: ???
 - Output: a db-ready .ts

## Directories

### confusables/

Directory full of lists of characters that are easily confusable. The delimiter in these files are triple semicolons ';;;', although in retrospect it may have been better to use tabs. It kind of depends on whether tabs ever appear in PanLex expressions. I don't think they do, but I don't know, I could be wrong.

