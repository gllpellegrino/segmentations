# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'


"""
Utility to load, store, and work with segmentations.

A segmentation is internally represented as a dictionary.
"sec" field contains the flat sequence (list of integers)
"alph" contains the alphabet as a set of integers
"bins" contains the indexes of the boundary locations
"nbins" contains the indexes of the non-boundary locations.
"""


import random as rn
from sortedcontainers import SortedList


# seed for the random selection of the boundaries
SEED = 1984
# conventional null symbol (for empty sessions)
EPSILON = -1


# load a segmentation in memory by using streamize() of pautomac_utility.py or rti_utility.py
def load(stream):
    sg = {"bins": SortedList([]), "nbins": set(), "alph": set(), "seq": [], "pool": set()}
    ind = 0
    for sy, fl in stream:
        # PLEASE NOTE: streamize() in Pautomac may have empty sequences in it.
        # we just discard those sequences.
        if sy != EPSILON:
            sg["seq"].append(sy)
            sg["alph"].add(sy)
            if fl:
                sg["bins"].add(ind)
            else:
                sg["nbins"].add(ind)
            ind += 1
    return sg


# stores a segmentation loaded with load() in RTI+ format
def torti(sg, path):
    with open(path, "w") as oh:
        oh.write(str(max(1, len(sg["bins"]))) + " " + str(len(sg["alph"])))
        ind, sess = 0, []
        for sy in sg["seq"]:
            if ind in sg["nbins"]:
                sess.append(sy)
            else:
                oh.write("\n" + str(len(sess) + 1))
                for ssy in sess:
                    oh.write(" " + str(ssy) + " 0")
                oh.write(" " + str(sy) + " 0")
                sess = []
            ind += 1
        if sess:
            oh.write("\n" + str(len(sess)))
            for ssy in sess:
                oh.write(" " + str(ssy) + " 0")


# stores a segmentation loaded with load() in treba format
def totreba(sg, path):
    with open(path, "w") as oh:
        first, ind, sess = True, 0, []
        for sy in sg["seq"]:
            sess.append(sy)
            if ind in sg["bins"]:
                if first:
                    first = False
                    oh.write(str(sess[0]))
                    for ssy in sess[1:]:
                        oh.write(" " + str(ssy))
                    oh.write(" " + str(sy))
                else:
                    oh.write("\n" + str(sess[0]))
                    for ssy in sess[1:]:
                        oh.write(" " + str(ssy))
                    oh.write(" " + str(sy))
                sess = []
            ind += 1
        if sess:
            oh.write("\n" + str(sess[0]))
            for ssy in sess[1:]:
                oh.write(" " + str(ssy))


# stores a segmentation loaded with load() in pautomac format
def topautomac(sg, path):
    with open(path, "w") as oh:
        oh.write(str(max(1, len(sg["bins"]))) + " " + str(len(sg["alph"])))
        ind, sess = 0, []
        for sy in sg["seq"]:
            if ind in sg["nbins"]:
                sess.append(sy)
            else:
                oh.write("\n" + str(len(sess) + 1))
                for ssy in sess:
                    oh.write(" " + str(ssy))
                oh.write(" " + str(sy))
                sess = []
            ind += 1
        if sess:
            oh.write("\n" + str(len(sess)))
            for ssy in sess:
                oh.write(" " + str(ssy))


# it is a generator which returns tuples from the segmentation loaded in memory by using load().
# tuples are the sessions within the segmentations. Basically they are the segments.
def sessionize(sg):
    ind, sess = 0, []
    for sy in sg["seq"]:
        if ind not in sg["bins"]:
            sess.append(sy)
        else:
            yield tuple(sess + [sy])
            sess = []
        ind += 1


# given a segmentation loaded with load(),
# it turns off a given number of boundaries and returns only them.
# bounds to get selected are chosen randomly.
# please note: it generates a new sequence and does not modify the input sequence.
# please note: even if you pass nb = 0, there will always be at least one bound in the sequence: the last bound.
# please note: if you want to turn off more bounds than those available in the sequence, all of them will get
# turned off but the one located at the end of the sequence
def debound(sg, nb):
    # assert 0 <= nb < len(sg["bins"])
    assert nb >= 0
    nsg = {"bins": SortedList([]), "nbins": set(), "alph": set(), "seq": [], "pool": set()}
    rn.seed(SEED)
    # we want to keep those boundaries in the resulting segentation (nsg)
    # PLEASE NOTE: we cannot remove the boundary located at the very end of the sequence.
    # that's why we avoid it to get sampled
    tosample = min(nb - 1, len(sg["bins"]) - 1)
    bns = {sg["bins"][-1]}
    if tosample > 0:
        bns = bns.union(set(rn.sample(sg["bins"][:-1], tosample)))
    ind = 0
    for sy in sg["seq"]:
        nsg["alph"].add(sy)
        nsg["seq"].append(sy)
        if ind in sg["bins"]:
            if ind in bns:
                nsg["bins"].add(ind)
            else:
                nsg["nbins"].add(ind)
                bind = sg["bins"].index(ind)
                lastind = sg["bins"][bind - 1] + 1 if bind - 1 >= 0 else 0
                nextind = sg["bins"][bind + 1] if bind + 1 < len(sg["bins"]) else sg["bins"][-1]
                # for pind in xrange(lastind + 1, max(nextind, ind), 1):
                for pind in xrange(lastind, nextind, 1):
                    # print pind, sg["seq"][pind]
                    nsg["pool"].add(pind)
        else:
            nsg["nbins"].add(ind)
        ind += 1
    return nsg


# given a segmentation loaded with load(), it generates a NEW sequence
# similar to the first, but nb non boundary locations turned into boundaries.
# those non boundary locations are chosen by chance
# please note: no more than the amount of bounds in the pool can be turned on, therefore if
# you provide an ng bigger than the pool ... then all the candidates in the pool will get turned on.
def bound(sg, nb):
    assert nb >= 0
    nsg = {"bins": SortedList([]), "nbins": set(), "alph": set(), "seq": [], "pool": set()}
    rn.seed(SEED)
    tosample = min(nb, len(sg["pool"]))
    bns = set(rn.sample(sg["pool"], tosample))
    ind = 0
    for sy in sg["seq"]:
        nsg["alph"].add(sy)
        nsg["seq"].append(sy)
        if ind in bns or ind in sg["bins"]:
            nsg["bins"].add(ind)
        else:
            nsg["nbins"].add(ind)
        ind += 1
    return nsg


# given a segmentation as gold, and a segmentation as candidate
# (both segmentations come from the same original sequence)
# it prints some precision metrics of the boundaries of the candidate.
# bot segmentations are supposed to get loaded in memory by using the load() method of this module.
def evaluate(gold, cand):
    tp, fp, tn, fn = 0, 0, 0, 0
    for ind in xrange(len(cand["seq"])):
        if ind in gold["bins"] and ind in cand["bins"]:
            tp += 1
        elif ind in gold["bins"] and ind not in cand["bins"]:
            fn += 1
        elif ind not in gold["bins"] and ind in cand["bins"]:
            fp += 1
        else:
            tn += 1
    # now we have the contingency table thus we can compute the measures
    assert tp + tn + fp + fn > 0
    acc = (tp + tn) / float(tp + tn + fp + fn)
    assert tp + fp > 0
    pre = tp / float(tp + fp)
    assert tp + fn > 0
    rec = tp / float(tp + fn)
    # time to print
    print "Accuracy:", acc, "Precision:", pre, "Recall:", rec


if __name__ == "__main__":
    import pautomac_utility as pu
    import rti_utility as ru

    # put = "/mnt/ata-TOSHIBA_MQ01ABD100_52DOT1CIT-part1/SEGMENTATIONS/results/21/gold/train.ptm"
    # rut = "/home/nino/Scrivania/canc.rti"
    # rut2 = "/home/nino/Scrivania/decanc.rti"
    # rut3 = "/home/nino/Scrivania/deadd.rti"
    # s = load(pu.streamize(put))
    # torti(s, rut)
    # topautomac(s, rut)
    # s2 = debound(s, 100)
    #s3 = bound(s, 100)
    # torti(s3, rut3)
    # for t in sessionize(s):
    #     print t

    # gd = "/mnt/ata-TOSHIBA_MQ01ABD100_52DOT1CIT-part1/SEGMENTATIONS/results/1/gold/train.ptm"
    # ss = "/mnt/ata-TOSHIBA_MQ01ABD100_52DOT1CIT-part1/SEGMENTATIONS/results/1/seg_40/take_0/sss.rti"
    # rn = "/mnt/ata-TOSHIBA_MQ01ABD100_52DOT1CIT-part1/SEGMENTATIONS/results/1/seg_40/take_0/train.rti"
    # gds = load(pu.streamize(gd))
    # cns = load(ru.streamize(ss))
    # rns = load(ru.streamize(rn))
    # print "SSS"
    # evaluate(gds, cns)
    # print "PRN"
    # evaluate(gds, rns)

    # sp = "/home/nino/Scrivania/ss.train"
    # sp2 = "/home/nino/Scrivania/canc_random.train"
    # sgg = load(ru.streamize(sp))
    # n = int(.4 * (19999 - 1))
    # sg2 = debound(sgg, n)
    # sg3 = bound(sg2, 19999 - n)
    # torti(sg3, sp2)

    sp = "/home/nino/Scrivania/toy.train"
    sgg = load(ru.streamize(sp))
    print sgg
    sgg2 = debound(sgg, 3)
    totreba(sgg2, sp + ".canc")
    print sgg2
    print bound(sgg2, 0)