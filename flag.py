#!/usr/bin/env python3
import argparse
import sys
import numpy as np
import re
import random
from collections import defaultdict
from operator import itemgetter
from itertools import groupby

MAX_PARTICLE_LEN = 5        # a "bad" particle must be this length or smaller
MIN_PARTICLE_FREQ = 0.001   # a "bad" particlemust appear in the file at least this often
MAX_CHAR_FREQ = 0.0001      # a "bad" character must appear in the file no more than this often

BAD_CHARS = [
    r'\uff10-\uff19', # ０-９ [fixed-width numerals]
    r'\u002a',  # *
]

QUOTE_CHARS = [
    u'\u0022', # "
    u'\u0027', # '
    u'\u00ab', # «
    u'\u00bb', # »
    u'\u0060', # `
    u'\u00b4', # ´
    u'\u2018', # ‘
    u'\u2019', # ’
    u'\u201a', # ‚
    u'\u201b', # ‛
    u'\u201c', # “
    u'\u201d', # ”
    u'\u201e', # „
    u'\u201f', # ‟
    u'\u2358', # ⍘
    u'\u235e', # ⍞
    u'\u2015', # ―
    u'\u2039', # ‹
    u'\u203a', # ›
    u'\u2e42', # ⹂
    u'\u275b', # ❛
    u'\u275c', # ❜
    u'\u275d', # ❝
    u'\u275e', # ❞
    u'\u275f', # ❟
    u'\u2760', # ❠
    u'\u276e', # ❮
    u'\u276f', # ❯
    u'\u300c', # 「
    u'\u300d', # 」
    u'\u300e', # 『
    u'\u300f', # 』
    u'\u301d', # 〝
    u'\u301e', # 〞
    u'\u301f', # 〟
    u'\ua404', # ꐄ
    u'\ufe41', # ﹁
    u'\ufe42', # ﹂
    u'\ufe43', # ﹃
    u'\ufe44', # ﹄
    u'\uff02', # ＂
    u'\uff07', # ＇
    u'\uff62', # ｢
    u'\uff63', # ｣
    u'\U0001f676', # 🙶
    u'\U0001f677', # 🙷
    u'\U0001f678', # 🙸
]


# Utility function for printing text to stderr.
# 
def eprint(*args, **kwargs):
    print("[[DEBUG]] ", *args, file=sys.stderr, **kwargs)


# Parse out arguments from command line and return them as a big ol' tuple.
# 
def check_args(args=None):
    parser = argparse.ArgumentParser(description='Search file of expressions for errors.')
    
    parser.add_argument('filename', metavar='file', type=str,
        help='path to file')
    parser.add_argument('limit', type=int, nargs='?',
        help='maximum number of deviant expressions to print')
    parser.add_argument('-a', '--analyze', metavar='[lcpq]*', type=str, default='lcpq',
        help='choose kinds of analysis to perform: ' +
             'l=length, c=character, p=particle, q=quote (defaults to all)')
    parser.add_argument('-s', '--sigmas', metavar='<N>', type=int, default=1,
        help='number of standard deviations that defines deviant length')
    parser.add_argument('-p', '--plot_length', action='store_true',
        help='plot expression lengths as histogram')
    parser.add_argument('-u', '--unicode_freqs', action='store_true',
        help='print out Unicode code point frequencies')
    parser.add_argument('-r', '--particle_freqs', action='store_true',
        help='print out particle frequencies')
    parser.add_argument('-w', '--show_why', action='store_true',
        help='show why expression got flagged')

    results = parser.parse_args(args)
    return (results.filename, results.limit, results.analyze, results.sigmas,
            results.plot_length, results.unicode_freqs, results.particle_freqs,
            results.show_why)


# Returns a list of all unusually long expressions, where "unusually long" is
# defined as greater than SIGMA standard deviations outide the mean.
# 
def get_long_exprs(exprs, sigma):
    # create numpy array of expression lengths and do statistics on it
    lengths = np.array([len(expr) for expr in exprs])
    mean = np.mean(lengths)
    std = np.std(lengths)
    
    # build a list of all unusually long expressions
    min_length = mean + sigmas*std
    long_exprs = []
    for expr in exprs:
        if len(expr) > min_length:
            long_exprs.append((expr, 'LENGTH={}'.format(len(expr))))

    # print out statistics
    eprint("mean expression length: ", mean)
    eprint("standard deviation: ", std)
    eprint(len(long_exprs), "unusually long expressions found")
    
    return long_exprs
    

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
    (fn, limit, analyze, sigmas, plot_lengths, unicode_freqs, particle_freqs, show_why) = check_args(sys.argv[1:])

    # read in expressions from file
    exprFile = open(fn,'r')    
    exprs = [expr.strip() for expr in exprFile.readlines()]
    
    # get a list of all unusually long expressions, where "unusually long" is
    # defined as greater than sigma standard deviations outide the mean
    long_exprs = get_long_exprs(exprs, sigmas) if 'l' in analyze else []
    
    # create a list of "bad" characters that we can use to find questionable
    # ("seedy") expressions, and then get those expressions
    seedy_exprs = []
    if 'c' in analyze:
        bad_chars = get_bad_chars(exprs, unicode_freqs)
        bad_chars.extend(BAD_CHARS)
        seedy_exprs = get_seedy_exprs(exprs, bad_chars)
    
    # get a list of "bad particles", short words that appear often at the start
    # or end of expressions, and collect these "particular" expressions
    particular_exprs = []
    if 'p' in analyze:
        bad_particles = get_bad_particles(exprs, particle_freqs)
        particular_exprs = get_particular_exprs(exprs, bad_particles)
    
    # get a list of all expressions appearing in quotation marks of some kind
    quoted_exprs = get_quoted_exprs(exprs) if 'q' in analyze else []
    
    # create formatting string to show the matched part of the expression, if
    # user signaled to do so
    format_string = r'{0}'
    if show_why == True: format_string = '{} ({{1}})'.format(format_string)
    
    # combine all deviant expressions into one list
    deviant_exprs = sorted(long_exprs + seedy_exprs + particular_exprs + quoted_exprs,
                           key=itemgetter(0))
    deviants_with_reasons = []
    for expr, reasons in groupby(deviant_exprs, itemgetter(0)):
        reasons = ' && '.join([item[1] for item in reasons])
        deviants_with_reasons.append((expr, reasons))
    
    eprint('{} different deviant expressions found'.format(len(deviants_with_reasons)))
    
    # print out $limit deviant expressions (or all if no $limit specified)
    if limit == None: limit = len(deviants_with_reasons)
    for expr in deviants_with_reasons[0:limit]:
        print(format_string.format(expr[0], expr[1]))
    
    # chart histogram
    if plot_lengths:
        display_expr_length_histogram(exprs)

    
