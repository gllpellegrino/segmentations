# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'


"""
Uitlity to collect, group, and analyze the results.
"""


from math import log
import meta as mt
import matplotlib.pyplot as plt


# minimal probability (session probability must not be 0 otherwise perplexity returns infinite.
# so we set a minmal very low probability instead of 0
MINPROB = mt.MINPROB


# given a file produced by evaluate() in pautomac_utility.py, so basically a solution file (solution.txt),
# it loads the values in memory, and normalize them in order to let them represent a distribution.
# PLEASE NOTE: it replaces 0 values with something very very small otherwise perplexity brakes down.
def distload(path):
    ds, dsum = [], 0.
    with open(path, "r") as sh:
        # skipping the header
        sh.readline()
        # loading the body
        for line in sh:
            vl = float(line.strip())
            vl = vl if vl > 0. else MINPROB
            ds.append(vl)
            dsum += vl
    # normalizing before returning
    return [vl / float(dsum) for vl in ds]


# given two distributions (loaded with distload()) for the same sample of strings, it returns the perplexity
# (see http://ai.cs.umbc.edu/icgi2012/challenge/Pautomac/description.php)
def perplexity(dtarget, dcandidate):
    assert len(dtarget) == len(dcandidate)
    entropy = 0.
    for i in xrange(len(dtarget)):
        entropy += dtarget[i] * log(dcandidate[i], 2)
    return pow(2, - entropy)


# given the perplexity value of the sliding window, and the perplexity values for the segmentations,
# it simply plots them
def _plot(swd, sxs):
    xvs = [i for i in xrange(len(sxs))]
    xls = [str(i * mt.STEP) + "%" for i in xvs]
    plt.xticks(xvs, xls, rotation=45)
    plt.plot(xvs, sxs, color="k", label="PCS")
    plt.plot(xvs, [swd for _ in xrange(len(sxs))], linestyle="-.", color="k", label="SW")
    # plt.xlabel('Correct bounds %')
    plt.ylabel('Perplexity')
    # plt.title('About as simple as it gets, folks')
    plt.grid(True)
    plt.legend()
    plt.show()


# main method for the evaluation.
# it prints out the perplexity of the sliding window compared with the segmentation.
# all the segmentations are reported, and the respective values are averaged on the takes.
# it also shows a plot in the end.
def aggregate():
    # 1) load the distribution of the gold
    # 2) load the distribution of the sliding window and store the perplexity compared to the gold
    # 3) for each segmentation
    #       4) for each take
    #           5) load the distribution and compute perplexity with the gold
    #       6) average perplexities over the takes
    #       7) show averaged perplexity compared with sliding window
    # 8) plot
    # ----------------------------------------------------------------------------------------------------------------
    # step 1)
    gp = mt.RESDIR + "gold/solution.txt"
    gd = distload(gp)
    # step 2)
    swp = mt.RESDIR + "sw/solution.txt"
    swd = distload(swp)
    swx = perplexity(gd, swd)
    # step 3) to 7)
    sxs = []
    for tc in xrange(0, 100 + mt.STEP, mt.STEP):
        print "segmentation with", tc, "% correct bounds:"
        dxs = []
        # setting the base directory for test case tc
        for tk in xrange(mt.TAKES):
            dp = mt.RESDIR + "seg_" + str(tc) + "/take_" + str(tk) + "/solution.txt"
            dd = distload(dp)
            dx = perplexity(gd, dd)
            dxs.append(dx)
        sx = sum(dxs) / float(len(dxs))
        print "\tperplexity:", sx
        print "\tsliding window:", swx
        sxs.append(sx)
    # step 8)
    _plot(swx, sxs)


if __name__ == "__main__":
    s = "/home/nino/PycharmProjects/segmentation/exp1/results/seg_5/take_8/solution.txt"
    go = "/home/nino/PycharmProjects/segmentation/exp1/results/gold/solution.txt"
    c = distload(s)
    g = distload(go)
    # print len(c), len(g)
    # print perplexity(g, c)
    aggregate()
