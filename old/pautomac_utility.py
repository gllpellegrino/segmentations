# -*- coding: utf-8 -*-


__author__ = 'Gaetano "Gibbster" Pellegrino'

"""
Utility to work with Pautomac suite. All it is required to load and store sequences, models, etc.

PLEASE NOTE: it is deprecated, only works in experiment 1 (exp1).
"""

import random as rn
import numpy as np
from scipy import stats as ts

# seed for random number generation
SEED = 1984
# maximal session length allowd when sampling
SESSLIMIT = 50
# # minimal probability (session probability must not be 0 otherwise perplexity returns infinite.
# # so we set a minmal very low probability instead of 0
# MINPROB = 1e-10
# meta-information accessors
# ---------------------------
# average string size
AVGSSIZE = 0
# minimal string size
MINSSIZE = 1
# maximal string size
MAXSSIZE = 2
# sequence length
LEN = 3
# amount of sessions (strings)
SESSIONS = 4
# alphabet size
ALPHA = 5


# given a pautomac training file, it generates one value at once as in a stream.
# for each symbol, we have a flag telling if AFTER the symbol we have a boundary.
def streamize(path):
    with open(path, "r") as ih:
        # we skip the first line because it is the header
        ih.readline()
        for line in ih:
            # we skip the first value because it is the length of the sequence
            values = line.strip().split(" ")[1:]
            for vl in values[:-1]:
                yield (vl, False)
            yield (values[-1], True)


# given a pautomac training file, it generates slided windows of size size.
def windowize(path, size):
    window = []
    for sym, _ in streamize(path):
        if len(window) < size:
            window.append(sym)
        else:
            yield window
            window = window[1:] + [sym]
    yield window


# given a pautomac training file, it generates all the sessions (strings).
def sessionize(path):
    session = []
    for sym, end in streamize(path):
        if not end:
            session.append(sym)
        else:
            yield session + [sym]
            session = []


# given a pautomac training file, it extracts several meta-informations as the average string size.
def meta(path):
    metas = {AVGSSIZE: 0, MINSSIZE: 0, MAXSSIZE: 0, LEN: 0, SESSIONS: 0}
    with open(path, "r") as ih:
        # getting the header
        header = map(int, ih.readline().strip().split(" "))
        metas[SESSIONS], metas[ALPHA] = header[0], header[1]
        mins, maxs, vals = None, None, []
        for line in ih:
            size = int(line.strip().split(" ")[0])
            # updating minimal size
            if mins is None or mins > size:
                mins = size
            # updating maximal size
            if maxs is None or maxs < size:
                maxs = size
            # updating the size values
            vals.append(size)
        # now we can update all meta-infos
        summ = sum(vals)
        metas[MINSSIZE] = mins
        metas[MAXSSIZE] = maxs
        metas[AVGSSIZE] = summ / float(len(vals))
        metas[LEN] = summ
    return metas


# given a pautomac training/testing sample, it convert it to the sliding window version with size wsize.
# the output file, stored in oupath, has the pautomac format
def toslided(inpath, wsize, oupath):
    metas = meta(inpath)
    with open(oupath, "w") as oh:
        oh.write(str(metas[LEN] - wsize + 1) + " " + str(metas[ALPHA]))
        for window in windowize(inpath, wsize):
            oh.write("\n" + str(wsize) + " ")
            oh.write(" ".join(window))


# given a pautomac training/testing file, exports it to the RTI+ format.
# rb is the percentage of correct bounds included into the exported file; it is a value in [0.0,1.0],
# if set < 1.0, the remaining bounds are set by random.
def torti(inpath, oupath, rb=1.):
    metas = meta(inpath)
    asize, bsize = metas[ALPHA], metas[SESSIONS]
    # first we need to determine the bounds to include into the exported file
    ind, correct, others = 0, [], []
    for sym, end in streamize(inpath):
        if end:
            correct.append(ind)
        else:
            others.append(ind)
        ind += 1
    rn.seed(SEED)
    ncorr = int(rb * bsize)
    bounds = rn.sample(correct, ncorr)
    correct = [vl for vl in correct if vl not in bounds]
    bounds = set(bounds + rn.sample(others + correct, bsize - ncorr))
    # time to export the file
    with open(oupath, "w") as oh:
        oh.write(str(bsize) + " " + str(asize))
        ind, wind = 0, []
        for sym, _ in streamize(inpath):
            if ind not in bounds:
                wind.append(sym)
            else:
                # time to print
                oh.write("\n" + str(len(wind) + 1))
                for wsy in wind:
                    oh.write(" " + wsy + " 0")
                oh.write(" " + sym + " 0")
                # ok, now reset
                wind = []
            ind += 1


# load a pautomac PDFA in memory as a tuple (alphabet_size, start_state, dict)
# where dict is a dictionary of states. Each state has a list of transitions.
# Each transition is a triple (destination_state, symbol, probability).
# The initial state is always state 0.
# NB.: it only works with PDFAs of Pautomac suite.
def mdload(path):
    md, trans, probs, sigma, s0 = {}, {}, {}, set(), 0
    with open(path, "r") as mh:
        parse_state = "I"
        for line in mh:
            line = line.strip()
            if line[0] == "I":
                parse_state = "I"
            elif line[0] == "S":
                parse_state = "S"
            elif line[0] == "T":
                parse_state = "T"
            elif line[0] == "F":
                parse_state = "F"
            else:
                fields = line.split(" ")
                prob = float(fields[1])
                syms = map(int, fields[0].translate(None, "()").split(","))
                if parse_state == "I":
                    s0 = syms[0]
                elif parse_state == "S":
                    st, sy = syms[0], str(syms[1])
                    probs[(st, sy)] = prob
                    if st not in md:
                        md[st] = []
                    sigma.add(sy)
                elif parse_state == "T":
                    ss, sy, ds = syms[0], str(syms[1]), syms[2]
                    if ss not in md:
                        md[ss] = []
                    if ds not in md:
                        md[ds] = []
                    sigma.add(sy)
                    md[ss].append((ds, sy, probs[(ss, sy)]))
    return sigma, s0, md


# given a model loaded with mdload(), it converts it to dot format and store it at path.
def mdtodot((_, s0, md), path):
    with open(path, "w") as eh:
        eh.write("digraph a {")
        eh.write("\n<q0> [shape=point];")
        eh.write("\n\t<q0> -> " + str(s0) + ";")
        for sta in md:
            ln = "\n" + str(sta) + " [shape=circle, label=\"" + str(sta) + "\"];"
            eh.write(ln)
            for ds, sy, pr in md[sta]:
                ln = "\n\t" + str(sta) + " -> " + str(ds) + " [label=\"" + sy + " " + str(pr) + "\"];"
                eh.write(ln)
        eh.write("\n}")


# given a model loaded with mdload(), it generate howmany sessions and store them in path in the pautomac format
def sample((sigma, s0, md), howmany, path):
    rn.seed(SEED)
    np.random.seed(SEED)
    with open(path, "w") as sh:
        # writing the header
        sh.write(str(howmany) + " " + str(len(sigma)))
        # generating and writing the body
        for _ in xrange(howmany):
            ss, sess = s0, []
            # generating a session (sess)
            ms = rn.randint(1, SESSLIMIT)
            for _ in xrange(ms):
                if not md[ss]:
                    break
                # now we need to sample which transition to fire
                # by using the state distribution
                tri = tuple([tr for tr in xrange(len(md[ss]))])
                trd = tuple([pr for _, _, pr in md[ss]])
                ds = ts.rv_discrete(values=(tri, trd))
                ss, sy, _ = md[ss][list(ds.rvs(size=1))[0]]
                sess.append(sy)
            # we can print session sess
            sh.write("\n" + str(len(sess)))
            for ssy in sess:
                sh.write(" " + ssy)


# given a model loaded with mdload(), a sample in Pautomac format stored in inpath,
# it computes the probability of each session in the sample according to the model, and stores it in oupath.
# PLEASE NOTE: those probabilities does not form a distribution, and no smoothing is applied.
def evaluate((_, s0, md), inpath, oupath):
    # first, we gather probabilities for each session in sample
    dis = []
    for sess in sessionize(inpath):
        ss, sp = s0, 1.
        for sy in sess:
            if ss not in md:
                sp = 0.
                break
            if not md[ss]:
                sp = 0.
                break
            # now we look for the right transition
            ds, pr = -1, 0.
            for tds, tsy, tpr in md[ss]:
                if tsy == sy:
                    ds, pr = tds, tpr
                    break
            # now we update session probability and next state
            ss, sp = ds, sp * pr
        dis.append(sp)
    # # we normalize the distribution
    # sm = sum(dis)
    # dis = [vl / float(sm) for vl in dis]
    # finally, we store the values
    with open(oupath, "w") as oh:
        oh.write(str(len(dis)))
        for vl in dis:
            oh.write("\n" + str(vl))


if __name__ == "__main__":
    p = "/home/nino/PycharmProjects/segmentation/pautomac/24/24.pautomac.train"
    r = "/home/nino/Scrivania/canc.rti"
    m = "/home/nino/PycharmProjects/segmentation/pautomac/24/24.pautomac_model.txt"
    d = "/home/nino/Scrivania/canc.dot"
    s = "/home/nino/Scrivania/canc.sample"
    e = "/home/nino/Scrivania/canc.eval"
    w = "/home/nino/Scrivania/canc.sw"
    # i = 0
    # for v in streamize(p):
    #     i += 1
    #     print v
    # print i
    # print meta(p)
    # for w in windowize(p, 3):
    #     print w
    # for w in sessionize(p):
    #     print w
    # torti(p, r, .3)
    # x = mdload(m)
    # print x
    # sample(x, 100, s)
    # mdtodot(x, d)
    # evaluate(x, s, e)
    toslided(p, 4, w)