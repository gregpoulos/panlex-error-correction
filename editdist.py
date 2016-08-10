#!/usr/bin/env python3
import argparse
import sys
import editdistance
import itertools
import time
import numpy as np

EDIT_DISTANCE_CUTOFF = 1

# Utility function for printing text to stderr.
# 
def eprint(*args, **kwargs):
    print("[[DEBUG]] ", *args, file=sys.stderr, **kwargs)


# Parse out arguments from command line and return them as a big ol' tuple.
# 
def check_args(args=None):
    parser = argparse.ArgumentParser(description='Find candidate pairs of expressions for merging.')
    
    parser.add_argument('filename', metavar='file', type=str,
        help='path to file')

    results = parser.parse_args(args)
    return (results.filename)


# Returns a list of all unusually long expressions, where "unusually long" is
# defined as greater than SIGMA standard deviations outide the mean.
# 
def get_short_exprs(exprs, sigma):
    # create numpy array of expression lengths and do statistics on it
    lengths = np.array([len(expr) for expr in exprs])
    mean = np.mean(lengths)
    std = np.std(lengths)
    
    # build a list of all unusually long expressions
    max_length = mean + sigma*std
    short_exprs = [expr for expr in exprs if len(expr) < max_length]

    # print out statistics
    eprint("mean expression length: ", mean)
    eprint("standard deviation: ", std)
    eprint(len(short_exprs), "normal-length expressions found")
    
    return short_exprs
    
    
if __name__ == '__main__':
    # parse args from command line
    fn = check_args(sys.argv[1:])

    # read in expressions from file
    exprFile = open(fn, 'r')
    exprs = [expr.strip() for expr in exprFile.readlines()]
    # exprs = get_short_exprs(exprs, 1)
    
    count = 0
    pairs = []
    start = time.time()
    eprint('start time: {}'.format(start))

    # ---
    
    # exprs.sort(key=len)
    # length_groups = [list(grp) for i,grp in itertools.groupby(exprs, key=len)]
    #
    # # don't want to check for errors in short expressions
    # length_groups = length_groups[6:]
    #
    # for length_group in length_groups:
    #     # loop through pairs of equal-length strings ...
    #     for i, j in itertools.combinations(length_group, 2):
    #         # compute edit distance and only display close matches
    #         if editdistance.eval(i, j) <= EDIT_DISTANCE_CUTOFF:
    #             eprint('FOUND PAIR: {}, {}'.format(i, j))
    #             pairs.append((i, j))
    #
    #         count += 1
    #         if count % 100000 == 0:
    #             now = time.time()
    #             eprint('number of comparisons: {} | time: {} ({} elapsed)'.format(count, now, now-start))
    #             start = now

    # ---
    expr_set = set(exprs)
    candidates = []
    
    # find words that match some other word with a single deletion
    for expr in exprs:
        for i in range(0, len(expr)):
            # if (expr[:i] + expr[i+1:]) in expr_set:
            if expr[:-1] in expr_set:
                candidates.append(expr)
                break

    eprint(len(candidates))
    eprint('time elapsed: ', time.time() - start)

    # ---
    
    # n = len(exprs)
    # eprint('will be making {} comparisons'.format(int((n*n - n) / 2)))
    # 
    # for i in range(0, len(exprs)-1):
    #     expr_i = exprs[i]
    #     inner_count = 0
    #
    #     for j in range(i+1, len(exprs)):
    #         expr_j = exprs[j]
    #
    #         if abs(len(expr_i) - len(expr_j)) > EDIT_DISTANCE_CUTOFF:
    #             continue
    #
    #         dist = editdistance.eval(expr_i, expr_j)
    #
    #         if dist <= EDIT_DISTANCE_CUTOFF:
    #             print('CUT SHORT: made only {} comparisons instead of {}'.format(inner_count, len(exprs)-(i+1)))
    #             print('inserting pair ({}, {}) with edit distance {}'.format(expr_i, expr_j, dist))
    #             pairs.append((expr_i, expr_j))
    #             break
    #
    #         inner_count += 1
    #         count += 1
    #         if count % 1000000 == 0:
    #             now = time.time()
    #             print('number of comparisons: {} | time elapsed: {}'.format(count, now-start))
    #             start = now
    
    # for i, j in itertools.combinations(exprs, 2):
    #     # quick check on edit length to save on computing edit distance
    #     if abs(len(i) - len(j)) <= EDIT_DISTANCE_CUTOFF:
    #         # compute edit distance and only display close matches
    #         if editdistance.eval(i, j) <= EDIT_DISTANCE_CUTOFF:
    #             print('FOUND PAIR: {}, {}'.format(i, j))
    #             pairs.append((i, j))
    #
    #     count += 1
    #     if count % 1000000 == 0:
    #         now = time.time()
    #         eprint('number of comparisons: {} | time: {} ({} elapsed)'.format(count, now, now-start))
    #         start = now
                
    # for (i, j) in pairs:
    #     print('{}, {}'.format(i, j))
