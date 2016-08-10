#!/usr/bin/env python3
import sys
import urllib.request
import re
from bs4 import BeautifulSoup
from collections import defaultdict
from unidecode import unidecode
import itertools
import time
import csv

LV = '187'  # Language variety ID for English
REASON = "special_char"
NULL = '\\N'

# Utility function for printing text to stderr.
# 
def eprint(*args, **kwargs):
    print("[[DEBUG]] ", *args, file=sys.stderr, **kwargs)


if __name__ == '__main__':
    
    db_fn = sys.argv[1]
    baddies_fn = sys.argv[2]
    output_fn = sys.argv[3]
    
    db_lines = [line.rstrip('\n') for line in open(db_fn)]
    baddies = [line.rstrip('\n') for line in open(baddies_fn)]
    
    count = 0
    exprs_by_unided = {}
    
    baddies_set = set(baddies)
    exprs_by_baddie = {}
    
    eprint("loading database dump ... ")
    for line in db_lines:
        exid, rest = line.split(',', maxsplit=1)
        tt, dncount = rest.rsplit(',', maxsplit=1)
        
        # don't include bad expressions in exprs_by_unided
        if tt not in baddies_set:
            exprs_by_unided[unidecode(tt)] = {'id' : exid, 'tt' : tt, 'dncount' : int(dncount)}
        else:
            exprs_by_baddie[tt] = {'id' : exid, 'tt' : tt, 'dncount' : int(dncount)}

        count+=1
        if count % 100000 == 0: eprint('{}: {}'.format(count, tt))
    eprint("finished loading!")
    eprint("{} expressions in exprs_by_unided".format(len(exprs_by_unided)))
    
    count = 0
    rows = []
    nofindums = []
    for baddie in baddies:
        
        new_expr = exprs_by_unided.get(unidecode(baddie))
        if not new_expr:
            nofindums.append(baddie)
            # eprint("couldn't find expr <{}> in db file!".format(baddie))
            continue
        new_count = new_expr['dncount']

        old_expr = exprs_by_baddie.get(baddie)
        if not old_expr:
            continue
        old_count = old_expr['dncount']
        
        # db record has following rows: int lv, int bad, text good, numeric score, text reason, text comment
        if new_count >= old_count:
            rows.append([LV, old_expr['id'], new_expr['tt'], '{0:.2f}'.format(new_count / old_count), REASON, NULL])
        
        if old_count >= new_count:
            rows.append([LV, new_expr['id'], old_expr['tt'], '{0:.2f}'.format(old_count / new_count), REASON, NULL])

        count+=1            
        if count % 1000 == 0: eprint('{}: {}'.format(count, ','.join(rows[-1])))
    
    eprint("couldn't match {} expressions to db file".format(len(nofindums)))
    eprint(nofindums[0:10])

    with open(output_fn, 'w') as outfile:
        csvwriter = csv.writer(outfile, delimiter='\t', lineterminator="\n")
        for row in rows:
            csvwriter.writerow(row)


