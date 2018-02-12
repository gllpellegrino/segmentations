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
    trp = re.compile(RTI_TRANS_RE)
    stp = re.compile(RTI_STATE_RE)
    sigma, s0, rt, prob = set(), 0, {}, {}
    with open(path, "r") as rh:
        ci = -1
        for line in rh:
            mc = stp.match(line)
            # state check
            if mc is not None:
                sta = int(mc.group(1))
                # we skip the sink state (id:-1)
                if sta >= 0:
                    rt[sta] = []
                    ci = 0
                    counts = map(int, mc.group(2).strip().split(" "))
                    csum = sum(counts)
                    prob[sta] = [cn / float(csum) if csum > 0 else 0. for cn in counts]
                    if not sigma:
                        for i in xrange(len(counts)):
                            sigma.add(str(i))
            mc = trp.match(line)
            if mc is not None:
                sr = int(mc.group(1))
                sy = mc.group(2)
                ds = int(mc.group(5))
                # and we skip transitions to and from the sink state
                # furthermore, we drop imposible transitions (with probability = 0)
                if sr >= 0 and ds >= 0 and prob[sr][ci] > 0.:
                    # we skip the sink state
                    if ds not in rt:
                        rt[ds] = []
                    tr = (ds, sy, prob[sr][ci])
                    rt[sr].append(tr)
                ci += 1
    return sigma, s0, rt


# given a sample in RTI+ format (inpath), it calls RTI+ and stores the output file (in RTI+ format) in oupath.
def mdtrain(inpath, oupath):
    cmd = RTI_CMD.format(TRAIN=inpath, MODEL=oupath)
    os.system(cmd)


if __name__ == "__main__":
    m = "/home/nino/Scrivania/canc.rti"
    t = "/home/nino/Scrivania/canc.rtimod"
    # print mdload(m)
    mdtrain(m, t)
