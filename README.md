# panlex-error-correction

This repo contains various Python script that are useful for processing expression lists into candidates for error correction.

## flag.py

This script can perform a variety of processing tasks to detect expressions that are potentially problematic.

 - Input: a simple list of expressions (i.e., one expression per line, without any other fields).
 - Output: variable, based on user flags, but essentially a simple list of expressions as well 

## editdist.py

This script detects pairs of expressions that are within some edit distance of each other. It's a long-running script, as you might imagine.

 - Input: a simple list of expressions.
 - Output: ???

## doppelgang.py

This script finds "doppelganger pairs", which are pairs of expressions that have similar-looking characters in the same string positions. (Think 'HELLO' with a capital letter 'O' and 'HELL0' with a zero in the final position.)

 - Input: a list of confusable characters, a simple list of expressions
 - Output: a list of pairs of expressions ("doppelgangers")

## prep_for_db.py

This script takes a list of potentially erroneous expressions and creates a .tsv file that can be loaded into the PanLex database with the following command:

```
\copy dev.exmod_candidates_generated (lv, bad, good, score, reason, comment) FROM '~/path/to/source/my_errors.tsv'
```

 - Input: ???
 - Output: a db-ready .tsv
