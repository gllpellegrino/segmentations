# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'

"""
Semi-Supervised Segmenter (SSS) utility.
Our "best" alternative approach. It uses a small amount of correct bounds to determine the rest.
The input is a segmentation (we imagine it to contain some correct bounds), and the output is an other
segmentation where we extend the known bounds to the entire training unsegmented sequence.
"""

import pautomac_utility as pu
import segmentations_utility as su
from sortedcontainers import SortedList


# given a session iterator as sessionize() in pautomac_utility.py, and the context size cs (integer),
# this iterator returns the contexts (PAST), (FUTURE).
# both past and future are tuples.
def contestualize(sessions, cs):
    for sess in sessions:
        # di questa sessione dobbiamo fornire tutti i contesti massimali
        # < (), sess > ... fino a < sess, () >
        if len(sess) < cs:
            past, fut = (), tuple(sess)
            while fut:
                yield past, fut
                past = past + (fut[0],) if len(past) < cs else past[1:] + (fut[0],)
                fut = fut[1:]
            yield tuple(sess), ()
        else:
            past, fut = (), tuple(sess[:cs])
            for sy in sess[cs:]:
                yield past, fut
                past = past + (fut[0], ) if len(past) < cs else past[1:] + (fut[0],)
                fut = fut[1:] + (sy,)
            # trailing futures
            while fut:
                yield past, fut
                past = past + (fut[0],) if len(past) < cs else past[1:] + (fut[0],)
                fut = fut[1:]
            yield past, ()


# it counts the amount of times we observe a context.
# returns two dictionaries, the first containing the context counts
# and the second containing the total counts for each context length.
def counter(contexts):
    # we need to account for the empty context, and for the totals
    cns = {}
    for past, fut in contexts:
        # for each past subsequence (suffixes)
        for suff in [past[i:] for i in xrange(len(past))]:
            if suff not in cns:
                cns[suff] = {}
            if fut not in cns[suff]:
                cns[suff][fut] = 0
            cns[suff][fut] += 1
        # for each future subsequence (prefixes)
        for pref in [fut[:i] for i in xrange(1, len(fut) + 1)]:
            if past not in cns:
                cns[past] = {}
            if pref not in cns[past]:
                cns[past][pref] = 0
            cns[past][pref] += 1
    return cns


# probability of a future given the past
def prob(cns, past, fut):
    if past not in cns:
        return 0.
    if fut not in cns[past]:
        return 0.
    if fut[:-1] not in cns[past]:
        return 0.
    return cns[past][fut] / float(cns[past][fut[:-1]])


# it looks for the maximal difference in probability in placing or not a boundary between past and
# future and considering all the possible prefixes of the future and suffixes of the past.
def test(cns, past, fut):
    mdiff = -float("inf")
    for suff in [past[i:] for i in xrange(len(past))]:
        for pref in [fut[:i] for i in xrange(1, len(fut) + 1)]:
            # probability of placing a boundary
            pnb = prob(cns, suff, pref)
            # probability of non placing a boundary
            ppb = prob(cns, (), pref)
            # difference
            diff = pnb - ppb
            if diff > mdiff:
                mdiff = diff
    return mdiff


# sg is a segmentation loaded in memory by using load() in segmentations_utility.py.
# cs is the context size (for both past and future), an integer > 0.
# rb is the amount of correct bounds selected from the gold sample; it is a value in [0.0,1.0],
# it returns a segmentation obtained by propagating the information
# about the right bounds to the whole sequence.
def extend(sg, cs, rb):
    nsg = {"bins": set(), "nbins": set(), "alph": set(), "seq": []}
    cnt = counter(contestualize(su.sessionize(sg), cs))
    ind, top = 0, SortedList([], key=lambda x: x[1])
    # first we fill the alphabet and the sequence
    # furthermore we collect informations about the statistical test we use to place boundaries
    for past, fut in contestualize(su.sessionize(sg), cs):
        if past != ():
            sy = past[-1]
            ts = test(cnt, past, fut)
            if ind in sg["bins"]:
                nsg["bins"].add(ind)
            else:
                nsg["nbins"].add(ind)
                top.add((ind, ts))
                if len(top) > rb:
                    del top[-1]
            nsg["alph"].add(sy)
            nsg["seq"].append(sy)
            ind += 1
    # now we can extend the original segmentation
    for ind, _ in top:
        nsg["nbins"].remove(ind)
        nsg["bins"].add(ind)
    return nsg


if __name__ == "__main__":
    # gld = "/home/nino/PycharmProjects/segmentation/exp2/results/1/gold/train.ptm"
    # i = 0
    # for ps, ft in contestualize(pu.sessionize(gld), 5):
    #     print ps, ft
    #     i += 1
    # print i, len(su.load(pu.streamize(gld))["seq"])
    # c = counter(contestualize(pu.sessionize(gld), 5))
    # print c[(4, )][(6, )], c[(4, )][()]
    # print prob(c, (4,), (6,))
    # print test(c, (4,), (6, 1))

    import rti_utility as rt
    put = "/mnt/ata-TOSHIBA_MQ01ABD100_52DOT1CIT-part1/SEGMENTATIONS/results/21/seg_5/take_2/cbounds.rti"
    fut = "/home/nino/Scrivania/canc.rti"
    s = su.load(rt.streamize(put))
    s1 = extend(s, 5, int(.95 * 20000))
    su.torti(s1, fut)