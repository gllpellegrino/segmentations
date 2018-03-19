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


# seed for the random selection of the boundaries
SEED = 1984


# load a segmentation in memory by using streamize() of pautomac_utility.py or rti_utility.py
def load(stream):
    sg = {"bins": set(), "nbins": set(), "alph": set(), "seq": []}
    ind = 0
    for sy, fl in stream:
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
def debound(sg, nb):
    nsg = {"bins": set(), "nbins": set(), "alph": set(), "seq": []}
    rn.seed(SEED)
    bns = set(rn.sample(sg["bins"], nb))
    ind = 0
    for sy in sg["seq"]:
        nsg["alph"].add(sy)
        nsg["seq"].append(sy)
        if ind in bns:
            nsg["bins"].add(ind)
        else:
            nsg["nbins"].add(ind)
        ind += 1
    return nsg


# given a segmentation loaded with load(), it generates a NEW sequence
# similar to the first, but nb non boundary locations turned into boundaries.
# those non boundary locations are chosen by chance
def bound(sg, nb):
    nsg = {"bins": set(), "nbins": set(), "alph": set(), "seq": []}
    rn.seed(SEED)
    bns = set(rn.sample(sg["nbins"], nb))
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

    gd = "/mnt/ata-TOSHIBA_MQ01ABD100_52DOT1CIT-part1/SEGMENTATIONS/results/1/gold/train.ptm"
    ss = "/mnt/ata-TOSHIBA_MQ01ABD100_52DOT1CIT-part1/SEGMENTATIONS/results/1/seg_70/take_0/sss.rti"
    rn = "/mnt/ata-TOSHIBA_MQ01ABD100_52DOT1CIT-part1/SEGMENTATIONS/results/1/seg_70/take_0/train.rti"
    gds = load(pu.streamize(gd))
    cns = load(ru.streamize(ss))
    rns = load(ru.streamize(rn))
    print "SSS"
    evaluate(gds, cns)
    print "PRN"
    evaluate(gds, rns)