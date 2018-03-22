# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'


"""
Utility to work with TREBA learning tool:
[https://code.google.com/archive/p/treba]
"""


import re
import os


# transition probability regular expression
TREGEX = r"^(-?\d+) (\d+) (\d+) ([+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)"
# final probability regular expression
FREGEX = r"^(-?\d+) ((\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)"
# triba learning command line
TRB_COMMAND = "/home/nino/bin/treba/bin/linux64/treba --train=merge {TRAIN} > {MODEL}"
# conventional null symbol (used when we extract emtpy sequences)
EPSILON = -1


# this method loads a model, inferred by treba, in memory
# path is a treba output file.
# it is a NON-HMM model.
def mdload(path):
    # first we gather the data
    trp = re.compile(TREGEX)
    ftp = re.compile(FREGEX)
    q, phi, sigma, delta, teta = set(), {}, set(), {}, {}
    with open(path, "r") as th:
        for line in th:
            mc = trp.match(line)
            if mc is not None:
                # print line
                # we are facing a transition line
                ss, ds, sy, pr = int(mc.group(1)), int(mc.group(2)), int(mc.group(3)), float(mc.group(4))
                q.add(ss), q.add(ds), sigma.add(sy)
                delta[(ss, sy, ds)] = pr
                teta[(ss, sy)] = pr
            else:
                mc = ftp.match(line)
                if mc is not None:
                    # we are facing a final probability line
                    st, pr = int(mc.group(1)), float(mc.group(2))
                    q.add(st)
                    phi[st] = pr
    # now we reshape them to the conventional structures
    i = [1. if st == 0 else 0. for st in q]
    f = [phi[st] if st in phi else 0. for st in q]
    s = [[teta[(st, sy)] if (st, sy) in teta else 0. for sy in sigma] for st in q]
    t = [[[delta[(ss, sy, ds)] if (ss, sy, ds) in delta else 0. for ds in q] for ss in q] for sy in sigma]
    return i, f, s, t


# learning command for treba.
# inpath is the observation file, outpath is the resulting model path
def mdtrain(inpath, oupath):
    cmd = TRB_COMMAND.format(TRAIN=inpath, MODEL=oupath)
    os.system(cmd)


# given a treba training file, it generates one value at once as in a stream.
# for each symbol, we have a flag telling if AFTER the symbol we have a boundary.
def streamize(path):
    with open(path, "r") as ih:
        for line in ih:
            values = map(int, line.strip().split(" "))
            # pay attention here, we do not skip possible empty sessions
            for vl in values[:-1]:
                yield (vl, False)
            yield (values[-1], True) if values else (EPSILON, True)


if __name__ == "__main__":
    mp = "/home/nino/Scrivania/pr.rtimd"
    fp = "/home/nino/Scrivania/pr.train"
    i, f, s, t = mdload(mp)
    print len(t[0])