#!/usr/bin/env python3
import sys
import urllib.request
import re
from unidecode import unidecode
from bs4 import BeautifulSoup
from collections import defaultdict
import itertools
import time

# Utility function for printing text to stderr.
# 
def eprint(*args, **kwargs):
    print("[[DEBUG]] ", *args, file=sys.stderr, **kwargs)


if __name__ == '__main__':
    
    confusables_fn = sys.argv[1]
    expr_fn = sys.argv[2]
    
    confusables = [line.rstrip('\n').split(';;;') for line in open(confusables_fn)]
    equivs = defaultdict(set)
    
    # create equiv classes, but don't transitively link them
    for equiv in confusables:
        for (x, y) in itertools.combinations(equiv, 2):
            equivs[x].add(y)
    
    ### CODE FOR CREATING TRANSITIVE EQUIV CLASSES, FILE MUST BE FORMATTED AS PAIRS ONLY
    # for (x, y) in confusables:
    #     x_equivs = equivs.get(x)
    #     y_equivs = equivs.get(y)
    #
    #     # merge existing equivalence sets for two items we've seen before
    #     if x_equivs and y_equivs:
    #         for y_equiv in y_equivs:
    #             x_equivs.add(y_equiv)
    #             equivs[y_equiv] = x_equivs
    #
    #     # define a new equivalence set for two novel items
    #     elif not x_equivs and not y_equivs:
    #         equivs[x] = equivs[y] = {x, y}
    #
    #     # remaining two cases: add a novel item to an existing equivalent set
    #     elif x_equivs:
    #         x_equivs.add(y)
    #         equivs[y] = x_equivs
    #     else: #if y_equivs:
    #         y_equivs.add(x)
    #         equivs[x] = y_equivs

    ### CODE FOR CREATING A REGEX THAT WILL MATCH ANY CONFUSABLE
    # sorted_confs = sorted(equivs.keys(), key=len)
    # confs_by_len = [list(confs) for i,confs in itertools.groupby(sorted_confs, key=len)]
    # conf_re = '[{}]'.format(''.join(confs_by_len[0]))
    #
    # if len(confs_by_len) > 1:
    #     multi_char_re = '|'.join(['|'.join(confs) for confs in confs_by_len[1:]])
    #     conf_re = '{}|{}'.format(conf_re, multi_char_re)
    #
    # regex = re.compile(conf_re)
    # eprint(regex)
    
    exprs = [line.rstrip('\n') for line in open(expr_fn)]
    expr_set = set(exprs)

    doppelgangers = []
    count = 0
    for expr in exprs:
        # degraded = unidecode(expr)
        # if degraded != expr and degraded in expr_set:
        #     doppelgangers.append((expr, unidecode(expr)))
        
        # check each character in the expression to see if it has confusable
        for i in range(len(expr)):
            # if so ...
            if expr[i] in equivs:
                # loop through all that character's potential equivalents ...
                for equiv in equivs[expr[i]]:
                    # and substitute it in
                    equiv_len = len(equiv)
                    doppelganger = expr[:i] + equiv + expr[i+1:]
                    # check this doppelganger for existence in the set of all expressions 
                    if doppelganger in expr_set: doppelgangers.append((expr, doppelganger))
        count+=1
        if count % 10000 == 0: eprint(count)
    
                
    eprint("number of expressions:", len(exprs))
    eprint("number of doppelganger pairs:", len(doppelgangers))
    
    for (w1, w2) in doppelgangers:
        print('{};;;{}'.format(w1, w2))
    
    # count = 0
    # for x, y in equivs.items():
    #     eprint('{}, {}'.format(x, y))
    #     count += 1
    #     if count >= 10: break
    #
    # klasses = set()
    # for klass in equivs.values():
    #     klasses.add(frozenset(klass))
    # count = 0
    # for klass in klasses:
    #     print(klass)
    #     count += 1
    #     if count >10: break
