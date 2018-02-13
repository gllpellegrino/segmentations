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
                ss, sy, ds = int(mc.group(1)),int(mc.group(2)), int(mc.group(5))
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


# given a model loaded from RTI+ output, hence by calling mdload() of this module, and given a RTI+ training
# sample referenced by path, this module estimates the final probability since the output of RTI+ does not provide
# such an information
def finprobs((i, f, s, t), path):
    probs = {}
    # @todo ci serve prima l'iteratore che ci fottiamo dall'altro progetto.
    return probs


# given a sample in RTI+ format (inpath), it calls RTI+ and stores the output file (in RTI+ format) in oupath.
def mdtrain(inpath, oupath):
    cmd = RTI_CMD.format(TRAIN=inpath, MODEL=oupath)
    os.system(cmd)


if __name__ == "__main__":
    mut = "/home/nino/Scrivania/canc.rti"
    tut = "/home/nino/Scrivania/canc.rtimod"
    mdut = mdload(tut)
    print mdut[3][0][4], mdut[2][4][0]
    # mdtrain(mut, tut)
