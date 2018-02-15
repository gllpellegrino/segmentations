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
# path is an RTI+ output file.
def mdload(path):
    # first we parse the file
    trp = re.compile(RTI_TRANS_RE)
    stp = re.compile(RTI_STATE_RE)
    q, sigma, delta, omega = set(), set(), set(), {}
    with open(path, "r") as rh:
        for line in rh:
            mc = stp.match(line)
            # state check
            if mc is not None:
                st = int(mc.group(1))
                # we skip the sink state (id:-1)
                if st >= 0:
                    probs = map(int, mc.group(2).strip().split(" "))
                    psum = sum(probs)
                    probs = [pr / float(psum) if psum > 0 else 0. for pr in probs]
                    q.add(st)
                    for i in xrange(len(probs)):
                        sigma.add(i)
                        omega[(st, i)] = probs[i]
            mc = trp.match(line)
            if mc is not None:
                ss, sy, ds = int(mc.group(1)), int(mc.group(2)), int(mc.group(5))
                # and we skip transitions to and from the sink state
                # furthermore, we drop imposible transitions (with probability = 0)
                if ss >= 0 and ds >= 0 and omega[(ss, sy)] > 0.:
                    # we skip the sink state
                    q.add(ds)
                    sigma.add(sy)
                    delta.add((ss, sy, ds))
    # second, we create the model
    i = [1. if st == 0 else 0. for st in q]
    f = [0.] * len(q)
    s = [[0. for _ in sigma] for _ in q]
    for st, sy in omega:
        s[st][sy] = omega[(st, sy)]
    t = [[[0. for _ in q] for _ in q] for _ in sigma]
    for ss, sy, ds in delta:
        t[sy][ss][ds] = 1.
    return i, f, s, t


# given a RTI+ training file, it generates all the sessions (strings).
def sessionize(path):
    with open(path, "r") as th:
        th.readline()
        for line in th:
            yield map(int, line.strip().split(" "))[1::2]


# given a model loaded from RTI+ output, hence by calling mdload() of this module, and given a RTI+ training
# sample referenced by inpath, this module estimates the final probability since the output of RTI+ does not provide
# such an information.
def restimate((i, f, s, t), inpath):
    probs = [[0, 0] for _ in xrange(len(i))]
    # setting the initial state
    ss = -1
    for ix in xrange(len(i)):
        if i[ix] > 0.:
            ss = ix
            break
    # now we collect how many times we pass through each state, and how many time we stop in each state
    for sess in sessionize(inpath):
        cs = ss
        for ix in xrange(len(sess)):
            if cs < 0:
                break
            # updating amount of times we reached state cs, and the amount of times we end in cs
            probs[cs][1] += 1
            if ix == len(sess) - 1:
                probs[cs][0] += 1
            # now we move to the next state
            sy, ns = sess[ix], -1
            for ix in xrange(len(t[sy][cs])):
                if t[sy][cs][ix] > 0.:
                    ns = ix
                    break
            cs = ns
    # now we are ready to update the final probabilities
    newf = [0.] * len(f)
    for st in xrange(len(probs)):
        if probs[st][1] > 0:
            # print st, probs[st][0], probs[st][1]
            newf[st] = probs[st][0] / float(probs[st][1])
    return i, newf, s, t


# given a sample in RTI+ format (inpath), it calls RTI+ and stores the output file (in RTI+ format) in oupath.
def mdtrain(inpath, oupath):
    cmd = RTI_CMD.format(TRAIN=inpath, MODEL=oupath)
    os.system(cmd)


if __name__ == "__main__":
    mut = "/home/nino/PycharmProjects/segmentation/exp2/results/14/sw/train.rti"
    tut = "/home/nino/PycharmProjects/segmentation/exp2/results/14/sw/model.rtimd"
    rut = "/home/nino/Scrivania/canc.pa"
    # mdut = mdload(tut)
    # print len(mdut[3])
    # print mdut[3][0][4], mdut[2][4][0]
    # mdtrain(mut, tut)
    # for sut in sessionize(mut):
    #     print sut

    import pautomac_utility as pu
    canc = "/home/nino/PycharmProjects/segmentation/exp2/results/14/sw/model.rtimd"
    md = mdload(canc)
    md = restimate(md, mut)
    pu.mdstore(md, rut)
    md = pu.mdload(rut)
    print len(md[3])

    # mdut2 = restimate(mdut, mut)
    # print len(mdut2[3])
    # print len(mdut[3])
    # print mdut2[1]

