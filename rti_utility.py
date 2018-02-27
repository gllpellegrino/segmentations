# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'

"""
Utility to deal with RTI+ (training models, interpreting the output).
"""

import re
import os


# regular expressions
RTI_STATE_RE = "^(-?\d+) prob: symbol=(( \d+)+)"
RTI_TRANS_RE = "^(-?\d+) (\d+) \[(\d+), (\d+)\]->(-?\d+)\\n$"

# RTI+ bash command
RTI_CMD = "/home/nino/bin/RTI/build/rti 1 0.05 {TRAIN} > {MODEL}"


# this method loads a model, inferred by RTI+, in memory
# path is an RTI+ output file. IT DOES NOT HAVE THE PROBABILITIES, since they are not reliable in the RTI+output.
# to estimate them you need to call estimate().
def mdload_wo_sinks(path):
    # first we parse the file
    trp = re.compile(RTI_TRANS_RE)
    stp = re.compile(RTI_STATE_RE)
    q, sigma, delta = set(), set(), set()
    with open(path, "r") as rh:
        for line in rh:
            mc = stp.match(line)
            # state check
            if mc is not None:
                st = int(mc.group(1))
                # we skip the sink state (id:-1)
                if st >= 0:
                    q.add(st)
                    for ix in xrange(len(mc.group(2).strip().split(" "))):
                        sigma.add(ix)
            mc = trp.match(line)
            if mc is not None:
                ss, sy, ds = int(mc.group(1)), int(mc.group(2)), int(mc.group(5))
                # and we skip transitions to and from the sink state
                if ss >= 0 and ds >= 0:
                    # we skip the sink state
                    q.add(ds), q.add(ss)
                    sigma.add(sy)
                    delta.add((ss, sy, ds))
    # second, we allocate the model
    i = [1.] + [0.] * (len(q) - 1)
    f = [0.] * len(q)
    s = [[0. for _ in sigma] for _ in q]
    t = [[[1. if (q0, sy, q1) in delta else 0. for q1 in q] for q0 in q] for sy in sigma]
    return i, f, s, t


# this method loads a model, inferred by RTI+, in memory
# path is an RTI+ output file. IT DOES NOT HAVE THE PROBABILITIES, since they are not reliable in the RTI+output.
# to estimate them you need to call estimate().
def mdload(path):
    # first we parse the file
    trp = re.compile(RTI_TRANS_RE)
    stp = re.compile(RTI_STATE_RE)
    q, sigma, delta = set(), set(), set()
    with open(path, "r") as rh:
        for line in rh:
            mc = stp.match(line)
            # state check
            if mc is not None:
                st = int(mc.group(1))
                q.add(st)
                for ix in xrange(len(mc.group(2).strip().split(" "))):
                    sigma.add(ix)
            mc = trp.match(line)
            if mc is not None:
                ss, sy, ds = int(mc.group(1)), int(mc.group(2)), int(mc.group(5))
                q.add(ds)
                q.add(ss)
                sigma.add(sy)
                delta.add((ss, sy, ds))
    # # adding artificial self-loops in the sink state
    # for sx in sigma:
    #     delta.add((-1, sx, -1))
    # second, we allocate the model
    i = [1. if qx == 0 else 0. for qx in q]
    f = [0.] * len(q)
    s = [[0. for _ in sigma] for _ in q]
    t = [[[1. if (q0, sy, q1) in delta else 0. for q1 in q] for q0 in q] for sy in sigma]
    return i, f, s, t


# given a RTI+ training file, it generates all the sessions (strings).
def sessionize(path):
    with open(path, "r") as th:
        th.readline()
        for line in th:
            yield map(int, line.strip().split(" "))[1::2]


# given a RTI+ training file, it generates one value at once as in a stream.
# for each symbol, we have a flag telling if AFTER the symbol we have a boundary.
def streamize(path):
    with open(path, "r") as ih:
        # we skip the first line because it is the header
        ih.readline()
        for line in ih:
            # we skip the first value because it is the length of the sequence
            values = map(int, line.strip().split(" "))[1::2]
            # pay attention here, we do not skip possible empty sessions
            for vl in values[:-1]:
                yield (vl, False)
            yield (values[-1], True)


# given a model loaded from RTI+ output, hence by calling mdload() of this module, and given a RTI+ training
# sample referenced by inpath, this module estimates the probabilities since the output of RTI+ does not provide
# such an information reliably.
def estimate((i, f, s, t), inpath):
    # first, we collect the counts
    rc, fi = [0 for _ in xrange(len(f))], [0 for _ in xrange(len(f))]
    em = [[0 for _ in xrange(len(s[q]))] for q in xrange(len(s))]
    # determining the initial state. It is always the same since the model is deterministic
    ss = None
    for ix in xrange(len(i)):
        if i[ix] > 0.:
            ss = ix
            break
    print i
    assert ss is not None
    for sess in sessionize(inpath):
        cs = ss
        for ix in xrange(len(sess)):
            if cs is None:
                break
            # sy is the current symbol
            sy = sess[ix]
            # we are visiting cs, so we update the reachability counts
            rc[cs] += 1
            # sess[ix] is a symbol, that we are seeing in cs. We update the emission counts.
            em[cs][sy] += 1
            # now we move to the next state
            fs = None
            for jx in xrange(len(t[sy][cs])):
                if t[sy][cs][jx] > 0.:
                    fs = jx
                    break
            cs = fs
        if cs is not None:
            fi[cs], rc[cs] = fi[cs] + 1, rc[cs] + 1
    # second, we estimate the probabilities by MLE
    nf = [fi[q] / float(rc[q]) if rc[q] > 0 else 0. for q in xrange(len(f))]
    ns = [[em[q][sy] / float(sum(em[q])) if sum(em[q]) > 0 else 0. for sy in xrange(len(s[q]))] for q in xrange(len(s))]
    return i, nf, ns, t


# given an RTI+ model loaded with mdload(), a session generator (as sessionize in this module,
# or in pautomac_utility.py), it computes the probability of each session in the sample according to the model,
# and stores it in oupath.
# PLEASE NOTE: those probabilities does not form a distribution, and no smoothing is applied.
def evaluate((i, f, s, t), sessions, oupath):
    # determining the initial state. It is always the same since the models are deterministic
    ss = None
    for ix in xrange(len(i)):
        if i[ix] > 0.:
            ss = ix
            break
    assert ss is not None
    # getting the probability of all sessions given the model
    prs = []
    for sess in sessions:
        cs, pr, = ss, i[ss]
        # cs, pr = 0, 1.
        for sy in sess:
            if cs is None:
                break
            # updating the probability
            pr *= (1. - f[cs]) * s[cs][sy]
            # looking for the next state
            ns = None
            for ix in xrange(len(t[sy][cs])):
                if t[sy][cs][ix] > 0.:
                    ns = ix
                    break
            if ns is None:
                print cs, sy, sess
            cs = ns
        prs.append(pr * f[cs]) if cs is not None else prs.append(0.)
    # writing the solution file
    with open(oupath, "w") as oh:
        oh.write(str(len(prs)))
        for pr in prs:
            oh.write("\n" + str(pr))


# given a sample in RTI+ format (inpath), it calls RTI+ and stores the output file (in RTI+ format) in oupath.
def mdtrain(inpath, oupath):
    cmd = RTI_CMD.format(TRAIN=inpath, MODEL=oupath)
    os.system(cmd)


if __name__ == "__main__":
    mut = "/home/nino/PycharmProjects/segmentation/exp2/results/26/seg_100/take_8/train.rti"
    mut2 = "/home/nino/Scrivania/canc.train"
    mut3 = "/home/nino/Scrivania/canc.rti"
    tut = "/home/nino/PycharmProjects/segmentation/exp2/results/26/seg_100/take_8/model.rtimd"
    tut2 = "/home/nino/Scrivania/canc.rtimd"
    rut = "/home/nino/Scrivania/canc.pa"
    dut = "/home/nino/Scrivania/canc.dot"
    gut = "/home/nino/PycharmProjects/segmentation/pautomac/26/26.pautomac_model.txt"
    sut = "/home/nino/Scrivania/canc.sol"
    eut = "/home/nino/PycharmProjects/segmentation/exp2/results/26/gold/train.ptm"
    put = "/home/nino/PycharmProjects/segmentation/exp2/results/26/seg_100/take_8/model.pa"

    # mdut = mdload(tut)
    # print mdut[1]

    # print mdut[3][0][4], mdut[2][4][0]
    # mdtrain(mut, tut)
    # for sut in sessionize(mut):
    #     print sut

    # # this block was here to spot the problem of mising symbols in the storing of a model in pautomac_utility.py
    # import pautomac_utility as pu
    # canc = "/home/nino/PycharmProjects/segmentation/exp2/results/14/sw/model.rtimd"
    # md = mdload(canc)
    # md = restimate(md, mut)
    # pu.mdstore(md, rut)
    # md = pu.mdload(rut)
    # print len(md[3])

    # mdut2 = estimate(mdut, mut)
    #rint mdut2[1]
    # print mdut2[2][0]

    import pautomac_utility as pu
    mdut2 = mdload(tut2)
    mdut2 = estimate(mdut2, mut2)
    # mdut = pu.mdload(gut)
    # pu.sample(mdut, 20000, mut2)
    # pu.torti(mut2, mut3)
    # pu.mdtodot(mdut2, dut)
    # mdut = pu.mdload(put)
    # print mdut[1]

    # import pautomac_utility as pu
    # evaluate(mdut2, pu.sessionize(eut), sut)
    pu.evaluate(mdut2, mut2, sut)
