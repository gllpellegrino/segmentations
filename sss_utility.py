# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'

"""
Semi-Supervised Segmenter (SSS) utility.
Our "best" alternative approach. It uses a small amount of correct bounds to determine the rest.
The input is a segmentation (we imagine it to contain some correct bounds), and the output is an other
segmentation where we extend the known bounds to the entire training unsegmented sequence.
"""

import segmentations_utility as su
from sortedcontainers import SortedList


# minimal number of occurrences (counts)
MIN_OCC = 5


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
# the difference here is in the empty context probability estimation.
def counter(contexts):
    # we need to account for the empty context, and for the totals
    # we store conditionals (cnd) and past priors (prs)
    cnd, prs = {}, {}
    for past, fut in contexts:
        # special case if past is ()
        if past == ():
            # updating priors
            if () not in prs:
                prs[()] = 0
            prs[()] += 1
            # caring of the future
            if fut == ():
                # past == () and fut == ()
                # print past, fut
                if () not in cnd:
                    cnd[()] = {}
                if () not in cnd[()]:
                    cnd[()][()] = 0
                cnd[()][()] += 1
            else:
                # past == () and fut != ()
                for pref in [fut[:i] for i in xrange(1, len(fut) + 1)]:
                    # print "\t", past, pref
                    if () not in cnd:
                        cnd[()] = {}
                    if pref not in cnd[()]:
                        cnd[()][pref] = 0
                    cnd[()][pref] += 1
        else:
            # for each past subsequence (suffixes) including the empty sequence ()
            for suff in [past[i:] for i in xrange(len(past))]:
                # updating priors
                if suff not in prs:
                    prs[suff] = 0
                prs[suff] += 1
                # special case if fut is ()
                if fut == ():
                    # past != null, fut == ()
                    # print "\t", suff, ()
                    if suff not in cnd:
                        cnd[suff] = {}
                    if () not in cnd[suff]:
                        cnd[suff][()] = 0
                    cnd[suff][()] += 1
                else:
                    # past != () and fut != ()
                    # for each future subsequence (prefixes) including the empty sequence ()
                    for pref in [fut[:i] for i in xrange(1, len(fut) + 1)]:
                        # print "\t", suff, pref
                        if suff not in cnd:
                            cnd[suff] = {}
                        if pref not in cnd[suff]:
                            cnd[suff][pref] = 0
                        cnd[suff][pref] += 1
    return cnd, prs


# probability of a future given the past
def prob((cnd, prs), past, fut):
    if past not in cnd:
        return 0.
    if fut not in cnd[past]:
        return 0.
    # if fut[:-1] not in cns[past]:
    #     return 0.
    # return cns[past][fut] / float(cns[past][fut[:-1]])
    return cnd[past][fut] / float(prs[past])


# it looks for the maximal difference in probability in placing or not a boundary between past and
# future and considering all the possible prefixes of the future and suffixes of the past.
def test((cns, prs), past, fut):
    assert past != () and fut != ()
    mdiff, mpnb, mppb = -1., None, None
    # print past, fut
    for suff in [past[i:] for i in xrange(len(past))]:
        for pref in [fut[:i] for i in xrange(1, len(fut) + 1)]:
            # print "\t", suff, pref
            # we do not evaluate the () () combination, and any combination having suff lesser than MIN_OCC counts
            # otherwise we get a 1.0 probability which may affect the results
            # print "deleteme", suff, pref
            if cns[suff] > MIN_OCC:
                # probability of not placing a boundary
                pnb = prob((cns, prs), suff, pref)
                # probability of placing a boundary by past
                ppb = prob((cns, prs), (), pref)
                # difference
                diff = pnb - ppb
                if diff > mdiff:
                    mdiff, mpnb, mppb = diff, pnb, ppb
                # probability of placing a boundary by future
                ppb = prob((cns, prs), suff, ())
                # difference
                diff = pnb - ppb
                if diff > mdiff:
                    mdiff, mpnb, mppb = diff, pnb, ppb
    # print mpnb, mppb
    # print "\t", pslice, fslice
    return mdiff


# it looks for the min product P(cut | past) x P(future | cut)
# among all the possible prefixes of the future and suffixes of the past.
def test2((cns, prs), past, fut):
    assert past != () and fut != ()
    minp, maxpast, maxfut = 1., None, None
    for suff in [past[i:] for i in xrange(len(past))]:
        for pref in [fut[:i] for i in xrange(1, len(fut) + 1)]:
            if cns[suff] > MIN_OCC:
                pbefore = prob((cns, prs), (), pref)
                pafter = prob((cns, prs), suff, ())
                prod = pbefore * pafter
                if prod < minp:
                    minp, maxpast, maxfut = prod, suff, pref
    return minp


# sg is a segmentation loaded in memory by using load() in segmentations_utility.py.
# cs is the context size (for both past and future), an integer > 0.
# rb is the amount of correct bounds selected from the gold sample; it is a value in [0.0,1.0],
# it returns a segmentation obtained by propagating the information
# about the right bounds to the whole sequence.
def boundOLD(sg, cs, rb):
    assert rb >= 0
    nsg = {"bins": set(), "nbins": set(), "alph": set(), "seq": [], "pool": set()}
    cnt = counter(contestualize(su.sessionize(sg), cs))
    ind, top = 0, SortedList([], key=lambda x: x[1])
    toset = min(rb, len(sg["pool"]))
    # first we fill the alphabet and the sequence
    # furthermore we collect informations about the statistical test we use to place boundaries
    for past, fut in contestualize(su.sessionize(sg), cs):
        if past != ():
            sy = past[-1]
            if ind in sg["bins"]:
                nsg["bins"].add(ind)
            else:
                nsg["nbins"].add(ind)
                if ind in sg["pool"]:
                    ts = test(cnt, past, fut)
                    if ts > -float("inf"):
                        top.add((ind, ts))
                        if len(top) > toset:
                            del top[-1]
            nsg["alph"].add(sy)
            nsg["seq"].append(sy)
            ind += 1
    # now we can extend the original segmentation
    for ind, _ in top:
        nsg["nbins"].remove(ind)
        nsg["bins"].add(ind)
    return nsg


def bound(sg, cs, rb):
    assert rb >= 0
    nsg = {"bins": set(), "nbins": set(), "alph": set(), "seq": [], "pool": set()}
    cnt = counter(contestualize(su.sessionize(sg), cs))
    ind, top = 0, SortedList([], key=lambda x: x[1])
    toset = min(rb, len(sg["pool"]))
    # first we fill the alphabet and the sequence
    # furthermore we collect informations about the statistical test we use to place boundaries
    for past, fut in contestualize(su.sessionize(sg), cs):
        if past != ():
            sy = past[-1]
            if ind in sg["bins"]:
                nsg["bins"].add(ind)
            else:
                nsg["nbins"].add(ind)
                if ind in sg["pool"]:
                    ts = test2(cnt, past, fut)
                    top.add((ind, ts))
                    if len(top) > toset:
                        del top[0]
            nsg["alph"].add(sy)
            nsg["seq"].append(sy)
            ind += 1
    # now we can extend the original segmentation
    for ind, _ in top:
        nsg["nbins"].remove(ind)
        nsg["bins"].add(ind)
    return nsg


# # the only difference here is that the algorithm places as many boundaries it likes.
# # it does not work with totally random sequences since the ts will be always > 0.
# # and therefore not one boundary will be set
# def extend2(sg, cs):
#     nsg = {"bins": set(), "nbins": set(), "alph": set(), "seq": []}
#     cnt = counter(contestualize(su.sessionize(sg), cs))
#     ind, top = 0, []
#     for past, fut in contestualize(su.sessionize(sg), cs):
#         if past != ():
#             sy = past[-1]
#             ts = test(cnt, past, fut)
#             if ind in sg["bins"] or -float("inf") < ts < 0.:
#                 nsg["bins"].add(ind)
#             else:
#                 nsg["nbins"].add(ind)
#             nsg["alph"].add(sy)
#             nsg["seq"].append(sy)
#             ind += 1
#     return nsg


if __name__ == "__main__":
    # import pautomac_utility as pu
    # gld = "/mnt/ata-TOSHIBA_MQ01ABD100_52DOT1CIT-part1/SEGMENTATIONS/results/7/gold/train.ptm"
    # cn = counter(contestualize(pu.sessionize(gld), 3))
    # for ps, ft in contestualize(pu.sessionize(gld), 3):
    #     print ps, ft
    #     print "\t- - ", prob(cn, ps, ft)
    #     print "\t() -", prob(cn, (), ft)
    #     print "\t- ()", prob(cn, ps, ())

    # import rti_utility as ru
    # import segmentations_utility as su
    # gld = "/home/nino/Scrivania/toy.train"
    # sgg = su.load(ru.streamize(gld))
    # sgg2 = su.debound(sgg, 2)
    # ind = 0
    # cts = counter(contestualize(su.sessionize(sgg), 3))
    # for ps, ft in contestualize(su.sessionize(sgg), 3):
    #     if ps != () and ft != ():
    #         print ps, ft
    #         print test(cts, ps, ft)
    #         ind += 1


    # WHOLE EVALUATION
    # from seg to eval on a single take
    import pautomac_utility as pu
    import exp3.analyze as an
    import rti_utility as ru
    import treba_utility as tu
    pid = 35
    # setting the paths
    tr = "/mnt/ata-TOSHIBA_MQ01ABD100_52DOT1CIT-part1/SEGMENTATIONS/results/" + str(pid) + "/gold/train.ptm"
    gdsol = "/home/nino/PycharmProjects/segmentation/pautomac/" + str(pid) + "/" + str(pid) + ".pautomac_solution.txt"
    ev = "/home/nino/PycharmProjects/segmentation/pautomac/" + str(pid) + "/" + str(pid) + ".pautomac.test"
    # creating the segmentations
    cbp = "/home/nino/Scrivania/cbounds.txt"
    n = int(.05 * 4000)
    cosegN = su.debound(su.load(pu.streamize(tr)), n)
    su.torti(cosegN, cbp)
    cosegZERO = su.debound(su.load(pu.streamize(tr)), 0)
    prseg = "/home/nino/Scrivania/pr.train"
    psg = su.bound(cosegZERO, 4000)
    # psg = su.bound(cosegN, 20000 - n)
    # su.torti(psg, prseg)
    su.totreba(psg, prseg)
    sseg = "/home/nino/Scrivania/ss.train"
    ssgm = bound(cosegN, 3, 4000 - n)
    # su.torti(ssgm, sseg)
    su.totreba(ssgm, sseg)
    print "PRN"
    su.evaluate(su.load(pu.streamize(tr)), su.load(ru.streamize(prseg)))
    print "SSS"
    su.evaluate(su.load(pu.streamize(tr)), su.load(ru.streamize(sseg)))
    # learning the models
    prrti = "/home/nino/Scrivania/pr.rtimd"

    tu.mdtrain(prseg, prrti)
    prmd = tu.mdload(prrti)
    # ru.mdtrain(prseg, prrti)
    # prmd = ru.estimate(ru.mdload(prrti), prseg)

    ssrti = "/home/nino/Scrivania/ss.rtimd"

    tu.mdtrain(sseg, ssrti)
    ssmd = tu.mdload(ssrti)
    # ru.mdtrain(sseg, ssrti)
    # ssmd = ru.estimate(ru.mdload(ssrti), sseg)

    # creating solutions
    # swsol = "/mnt/ata-TOSHIBA_MQ01ABD100_52DOT1CIT-part1/SEGMENTATIONS/results/" + str(pid) + "/sw/solution.txt"
    prsol = "/home/nino/Scrivania/pr.sol"
    sssol = "/home/nino/Scrivania/ss.sol"
    pu.evaluate(prmd, ev, prsol)
    pu.evaluate(ssmd, ev, sssol)
    # loading distributions
    gd = an.distload(gdsol)
    # sw = an.distload(swsol)
    pr = an.distload(prsol)
    ses = an.distload(sssol)
    # perplexity
    # print "SW", an.perplexity(gd, sw)
    print "PR", an.perplexity(gd, pr)
    print "SS", an.perplexity(gd, ses)
    print "GLD", an.perplexity(gd, gd)