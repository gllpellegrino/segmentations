# -*- coding: utf-8 -*-


__author__ = 'Gaetano "Gibbster" Pellegrino'

"""
Utility to work with Pautomac suite. All it is required to load and store sequences, models, etc.
"""

import random as rn
import numpy as np
from scipy import stats as ts

# seed for random number generation
SEED = 1984
# maximal session length allowd when sampling
SESSLIMIT = 1000

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
            values = map(int, line.strip().split(" ")[1:])
            # pay attention here, we do not skip possible empty sessions
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
            oh.write(" ".join(map(str, window)))


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
                    oh.write(" " + str(wsy) + " 0")
                oh.write(" " + str(sym) + " 0")
                # ok, now reset
                wind = []
            ind += 1


# load a pautomac PDFA in memory as a tuple (initial probabilities, final probabilities, emission probabilities,
# and transition probabilities)
# Emission: Q x Sigma, Transition: Sigma x Q_0 x Q_1
# where dict is a dictionary of states. Each state has a list of transitions.
# Each transition is a triple (destination_state, symbol, probability).
def mdload(path):
    pars_state, sigma, q = "I", set(), set()
    i, f, s, t = [], [], [], []
    # file parsing
    with open(path, 'r') as mh:
        for line in mh:
            line = line.strip()
            if line[0] == 'I':
                pars_state = 'I'
            elif line[0] == 'F':
                pars_state = 'F'
            elif line[0] == 'S':
                pars_state = 'S'
            elif line[0] == 'T':
                pars_state = 'T'
            else:
                prob = float(line.split(' ')[1])
                values = map(int, (line.split(' ')[0]).translate(None, '()').split(','))
                if pars_state == 'I':
                    q.add(values[0])
                    i.append((values, prob))
                elif pars_state == 'F':
                    q.add(values[0])
                    f.append((values, prob))
                elif pars_state == 'S':
                    q.add(values[0])
                    sigma.add(values[1])
                    s.append((values, prob))
                elif pars_state == 'T':
                    q.add(values[0])
                    q.add(values[2])
                    sigma.add(values[1])
                    t.append((values, prob))
    # building the model
    ni = [0. for _ in q]
    for sid, prob in i:
        ni[sid[0]] = prob
    nf = [0. for _ in q]
    for sid, prob in f:
        nf[sid[0]] = prob
    ns = [[0. for _ in sigma] for _ in q]
    for sid, prob in s:
        ns[sid[0]][sid[1]] = prob
    net = [[[0. for _ in q] for _ in q] for _ in sigma]
    for sid, prob in t:
        net[sid[1]][sid[0]][sid[2]] = prob
    return ni, nf, ns, net


# given a model loaded with mdload(), it stores it in path in Pautomac format
def mdstore((i, f, s, t), path):
    with open(path, "w") as oh:
        # first, the initial probabilities
        oh.write("I: (state)")
        for ix in xrange(len(i)):
            if i[ix] > 0.:
                oh.write("\n\t(" + str(ix) + ") " + str(i[ix]))
        # second, the final probabilities
        oh.write("\nF: (state)")
        for ix in xrange(len(f)):
            if f[ix] > 0.:
                oh.write("\n\t(" + str(ix) + ") " + str(f[ix]))
        # third, the emission probabilities
        oh.write("\nS: (state,symbol)")
        for ix in xrange(len(s)):
            for jx in xrange(len(t)):
                # if s[ix][jx] > 0.:
                oh.write("\n\t(" + str(ix) + "," + str(jx) + ") " + str(s[ix][jx]))
        # fourth, the transitions
        oh.write("\nT: (state,symbol,state)")
        for ix in xrange(len(t)):
            for jx in xrange(len(t[ix])):
                for zx in xrange(len(t[ix][jx])):
                    if t[ix][jx][zx] > 0.:
                        oh.write("\n\t(" + str(jx) + "," + str(ix) + "," + str(zx) + ") " + str(t[ix][jx][zx]))


# given a model loaded with mdload(), it converts it to dot format and store it at path.
def mdtodot((i, f, s, t), path):
    with open(path, "w") as eh:
        eh.write("digraph a {")
        for q0 in xrange(len(i)):
            ln = "\n" + str(q0) + " [shape=circle, label=\"" + str(q0)
            ln += "\\n" + '{:.2f}'.format(i[q0])
            ln += "\\n" + '{:.2f}'.format(f[q0])
            eh.write(ln + "\"];")
            for a in xrange(len(t)):
                for q1 in xrange(len(t[a][q0])):
                    prob = t[a][q0][q1]
                    if prob > 0.:
                        ln = "\n\t" + str(q0) + " -> " + str(q1) + " [label=\"" + str(a) + " "
                        ln += "{:.2f}".format(prob) + " "
                        ln += "{:.2f}".format(s[q0][a]) + "\"];"
                        eh.write(ln)
        eh.write("\n}")


# given a model loaded with mdload(), it generate howmany sessions and store them in path in the pautomac format
def sample((i, f, s, t), howmany, path):
    rn.seed(SEED)
    np.random.seed(SEED)
    with open(path, "w") as sh:
        # writing the header
        sh.write(str(howmany) + " " + str(len(t)))
        # generating and writing the body
        di = tuple([ix for ix in xrange(len(i))])
        dv = tuple([vx for vx in i])
        ind = ts.rv_discrete(values=(di, dv))
        for _ in xrange(howmany):
            # sampling the initial state
            cs, sess = list(ind.rvs(size=1))[0], []
            while True:
                # PLEASE NOTE: we do notgenerate empty sequences at the moment
                if sess and (f[cs] >= rn.random() or len(sess) > SESSLIMIT):
                    break
                # sampling a symbol
                di = tuple([ix for ix in xrange(len(s[cs]))])
                dv = tuple([vx for vx in s[cs]])
                sid = ts.rv_discrete(values=(di, dv))
                sy = list(sid.rvs(size=1))[0]
                # sampling the next state (for nondeterministic models makes sense)
                di = tuple([ix for ix in xrange(len(t[sy][cs]))])
                dv = tuple([vx for vx in t[sy][cs]])
                tid = ts.rv_discrete(values=(di, dv))
                ns = list(tid.rvs(size=1))[0]
                # ready to continue
                sess.append(sy)
                cs = ns
            # we can print session sess
            sh.write("\n" + str(len(sess)))
            for sy in sess:
                sh.write(" " + str(sy))


# PLEASE NOTE: this function is not meant to get launched by the client. It should use prob() instead.
# -----------------------------------------------------------------------------------------------------------
# this auxiliary recursive function computes the forward probability by using dynamic programming.
# (i, f, s, t) is a model loaded in memory by using mdload()
# session is a string of symbols represented by integers in a list
# index is the index within session where to start the probability computation
# state is the state from which we need to compute the probability of sessions' suffix starting in index.
# dp is a dictionary representing the dynamic programming table where the subproblems get stored.
def _prob((i, f, s, t), session, index, state, dp):
    # base case: end of session. (probability = f(state))
    if index == len(session):
        dp[tuple([state])] = f[state]
        return f[state]
    # base case: we have already solved this subproblem. (return the already hashed solution)
    sp = tuple([state] + session[index:len(session)])
    if sp in dp:
        return dp[sp]
    # general case: for every possible next state s, compute Probability += P(symbol)*P(transition to s)*P(future)
    sprob, fprob = s[state][session[index]], f[state]
    prob = 0.
    for nextstate in range(len(t[session[index]][state])):
        if t[session[index]][state][nextstate] > 0.:
            tprob = t[session[index]][state][nextstate]
            fprob = _prob((i, f, s, t), session, index + 1, nextstate, dp)
            prob += (1. - fprob) * sprob * tprob * fprob
    # we store the subproblem in the dynamic programming table
    dp[sp] = prob
    return prob


# given a model loaded with mdload(), and a session or string in form of list,
# it returns the probability of the session given the model.
def probability((i, f, s, t), session):
    pr, dp = 0., {}
    for ss in xrange(len(i)):
        if i[ss] > 0.:
            pr += i[ss] * _prob((i, f, s, t), session, 0, ss, dp)
    return pr


# given a model loaded with mdload(), a sample in Pautomac format stored in inpath,
# it computes the probability of each session in the sample according to the model, and stores it in oupath.
# PLEASE NOTE: those probabilities does not form a distribution, and no smoothing is applied.
def evaluate((i, f, s, t), inpath, oupath):
    # first, we gather probabilities for each session in sample
    dis = []
    for sess in sessionize(inpath):
        dis.append(probability((i, f, s, t), sess))
    # second, we store the values
    with open(oupath, "w") as oh:
        oh.write(str(len(dis)))
        for vl in dis:
            oh.write("\n" + str(vl))


if __name__ == "__main__":
    put = "/home/nino/PycharmProjects/segmentation/pautomac/24/24.pautomac.train"
    rut = "/home/nino/Scrivania/canc.rti"
    mut = "/home/nino/PycharmProjects/segmentation/exp2/results/14/sw/model.pa"
    dut = "/home/nino/Scrivania/canc.dot"
    sut = "/home/nino/PycharmProjects/segmentation/exp2/results/14/sw/train.ptm"
    eut = "/home/nino/Scrivania/canc.eval"
    wut = "/home/nino/Scrivania/canc.sw"
    nut = "/home/nino/Scrivania/canc.mdrti"
    # iut = 0
    # for v in streamize(put):
    #     iut += 1
    #     print v
    # print iut
    # print meta(put)
    # for w in windowize(put, 3):
    #     print w
    # for w in sessionize(put):
    #     print w
    # torti(put, rut, .3)
    x = mdload(mut)
    print len(x[3])
    # sample(x, 100, sut)
    # mdtodot(x, dut)
    # evaluate(x, sut, eut)
    # toslided(put, 4, wut)
    # mdstore(x, nut)
