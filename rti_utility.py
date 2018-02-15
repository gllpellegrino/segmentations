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


# given a RTI+ training file, it generates all the sessions (strings).
def sessionize(path):
    with open(path, "r") as th:
        th.readline()
        for line in th:
            yield map(int, line.strip().split(" "))[1::2]


# given a model loaded from RTI+ output, hence by calling mdload() of this module, and given a RTI+ training
# sample referenced by inpath, this module estimates the probabilities since the output of RTI+ does not provide
# such an information reliably.
def estimate((i, f, s, t), inpath):
    # first, we collect the counts
    rc, fi = [0 for _ in xrange(len(f))], [0 for _ in xrange(len(f))]
    em = [[0 for _ in xrange(len(s[q]))] for q in xrange(len(s))]
    for sess in sessionize(inpath):
        cs = 0
        for ix in xrange(len(sess)):
            if cs < 0:
                break
            # sy is the current symbol
            sy = sess[ix]
            # we are visiting cs, so we update the reachability counts
            rc[cs] += 1
            # if we are finishing in cs, we update the count of ending in cs
            if ix == len(sess) - 1:
                fi[cs] += 1
            # sess[ix] is a symbol, that we are seeing in cs. We update the emission counts.
            em[cs][sy] += 1
            # now we move to the next state
            fs = -1
            for jx in xrange(len(t[sy][cs])):
                if t[sy][cs][jx] > 0.:
                    fs = jx
                    break
            cs = fs
    # second, we estimate the probabilities by MLE
    nf = [fi[q] / float(rc[q]) if rc[q] > 0 else 0 for q in xrange(len(f))]
    ns = [[em[q][sy] / float(sum(em[q])) if sum(em[q]) > 0 else 0. for sy in xrange(len(s[q]))] for q in xrange(len(s))]
    return i, nf, ns, t


# given a sample in RTI+ format (inpath), it calls RTI+ and stores the output file (in RTI+ format) in oupath.
def mdtrain(inpath, oupath):
    cmd = RTI_CMD.format(TRAIN=inpath, MODEL=oupath)
    os.system(cmd)


if __name__ == "__main__":
    mut = "/home/nino/PycharmProjects/segmentation/exp2/results/3/seg_100/take_9/train.rti"
    tut = "/home/nino/PycharmProjects/segmentation/exp2/results/3/seg_100/take_9/model.rtimd"
    rut = "/home/nino/Scrivania/canc.pa"
    dut = "/home/nino/Scrivania/canc.dot"
    gut = "/home/nino/PycharmProjects/segmentation/pautomac/3/3.pautomac_model.txt"
    mdut = mdload(tut)
    print mdut
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

    mdut2 = estimate(mdut, mut)
    print mdut2
    # print len(mdut[3])
    # print mdut2[1]

    # import pautomac_utility as pu
    # pu.mdtodot(mdut, dut)
