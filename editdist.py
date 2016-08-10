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
    # parser.add_argument('limit', type=int, nargs='?',
    #     help='maximum number of deviant expressions to print')
    # parser.add_argument('-a', '--analyze', metavar='[lcpq]*', type=str, default='lcpq',
    #     help='choose kinds of analysis to perform: ' +
    #          'l=length, c=character, p=particle, q=quote (defaults to all)')
    # parser.add_argument('-s', '--sigmas', metavar='<N>', type=int, default=1,
    #     help='number of standard deviations that defines deviant length')
    # parser.add_argument('-p', '--plot_length', action='store_true',
    #     help='plot expression lengths as histogram')

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
    

# Counts up how many time each Unicode code point appears in the expression list
# and prints out the results. Ones that appear only rarely across the whole
# expression set are returned as a list of bad characters. Returns a list of
# strings of Unicode code points.
# 
def get_bad_chars(exprs, show_freqs):
    # count up how many times each character appears across all expressions
    code_point_counts = defaultdict(int)
    total_chars = 0
    for expr in exprs:
        for char in expr:
            code_point_counts[ord(char)] += 1
            total_chars += 1
            
    # print a list of character counts, starting with lowest code point, and
    # adding an * if the character is 'bad'
    if show_freqs:
        for code_point, count in sorted(code_point_counts.items(), key=itemgetter(0)):
            seedy = ' *' if (count/total_chars < MAX_CHAR_FREQ) else ''
            print("U+{:04x} {} : {}{}".format(code_point, chr(code_point), count, seedy))
    
    # get list of all characters that appear only once across all expressions,
    # formatting as eight-digit Unicode code point
    bad_chars = ['\\U{:08x}'.format(code_point)
                 for (code_point, count) in code_point_counts.items()
                 if count/total_chars < MAX_CHAR_FREQ]
    
    return bad_chars


# Returns a list of "bad particles", which are defined as small words (defined
# by MAX_PARTICLE_LEN) that appear at the beginning or end of a large number
# (defined by MIN_PARTICLE_FREQ) of expressions. Returns a list of strings.
# 
def get_bad_particles(exprs, show_freqs):
    # count how many times a word appears in an initial or final position across
    # all expressions -- these are our "particle" candidates
    num_exprs = len(exprs)
    particle_counts = defaultdict(int)
    for expr in exprs:
        words = expr.split()
        if len(words) > 1:
            particle_counts[words[0]] += 1
            particle_counts[words[-1]] += 1
    
    # create a list of particles that are relatively short, lowercase, and
    # which appear frequently enough for flagging
    bad_particles = [(p, count) for (p, count) in particle_counts.items()
                     if len(p) <= MAX_PARTICLE_LEN               # particle is short ...
                        and p.islower()                          # is lowercase ...
                        and count/num_exprs > MIN_PARTICLE_FREQ] # and appears often
    
    
    # if requested by user, print out particle frequencies
    if show_freqs:
        for particle, count in bad_particles:
            print('"{}" particle count : {}'.format(particle, count)) 
    
    # we don't need counts anymore -- just return a list of the particles
    return [p[0] for p in bad_particles]


# Returns a list of all expressions containing one or more bad characters.
# Return value is a list of pairs of strings:
#
#    [(expr1, matched character), (expr2, matched character), ... ]
#
def get_seedy_exprs(exprs, bad_chars):
    # the regex we want is just our list of bad characters, wrapped in brackets
    bad_char_re = re.compile('[{}]'.format(''.join(bad_chars)))
    matches = get_matching_exprs(exprs, bad_char_re)
    eprint("{} seedy expressions found".format(len(matches)))
    return matches
    
# Returns a list of all expressions featuring a bad particle. The intuition here
# is that there are certain words, like "be" or "a", that shouldn't be part of
# lemmas, but get in there during data entry anyway.
#
#    [(expr1, matched particle), (expr2, matched particle), ... ]
#    
def get_particular_exprs(exprs, bad_particles):
    bad_or = '|'.join(bad_particles)
    regex = re.compile('^({0}) | ({0})$'.format(bad_or))
    matches = get_matching_exprs(exprs, regex)
    eprint("{} particular expressions found".format(len(matches)))
    return matches

# Returns a list of all expressions wrapped in quotation marks. Return value is
# a list of pairs of strings, where the second element of the pair is simply the
# string "quoted":
#
#    [(expr1, "quoted"), (expr2, "quoted"), ... ]
# 
def get_quoted_exprs(exprs):
    quote_re = re.compile('^[{0}].*[{0}]$'.format(''.join(QUOTE_CHARS)))
    matches = get_matching_exprs(exprs, quote_re, reason='quoted')
    eprint("{} quoted expressions found".format(len(matches)))
    return matches


# Returns a list of tuples containing expressions that match a certain $regex,
# along with the part of the expression that matched. I.e., each item in the
# list is a tuple of the form:   (<expression>, <match string>).
# 
# PARAMETERS---
#    reason: string to use in the place of <match string>
# 
def get_matching_exprs(exprs, regex, reason=None):
    matches = []
    for expr in exprs:
        match = regex.search(expr)
        if match: matches.append((expr, reason or match.group(0)))

    return matches


# Display a fancy histogram showing the frequency of every expression length in
# the language.
# 
def display_expr_length_histogram(exprs):
    import matplotlib.pyplot as plt
    lengths = np.array([len(expr) for expr in exprs])
    plt.hist(lengths, bins=max(lengths))
    plt.title(fn)
    plt.show()
    plt.close()

    
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
