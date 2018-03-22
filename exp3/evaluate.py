# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'


"""
Utility to generate the distributions of the models learned by using train.py
"""


import meta as mt
import pautomac_utility as pu
import rti_utility as ru
import os


# only cleans the files produced by learn()
def clean():
    for pp in mt.PAUTPROBS:
        print "cleaning evaluation products for Pautomac problem number", pp
        ppdir = mt.RESDIR + str(pp) + "/"
        # first we remove the gold solution
        print "cleaning evaluation products for the gold case"
        pt = ppdir + "gold/solution.txt"
        if os.path.exists(pt):
            os.remove(pt)
        # second we remove the sliding window solution
        print "cleaning evaluation products for the sliding window test case"
        pt = ppdir + "sw/solution.txt"
        if os.path.exists(pt):
            os.remove(pt)
        # now we scan the remaining directories, still to remove training products
        for tc in xrange(0, 100 + mt.STEP, mt.STEP):
            print "cleaning evaluation for test case", tc
            # setting the base directory for test case tc
            for tk in xrange(mt.TAKES):
                tkdir = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/"
                # cleaning starts
                for item in os.listdir(tkdir):
                    if item.endswith("solution.txt"):
                        os.remove(os.path.join(tkdir, item))


# learns automata for all the test cases
def evaluate():
    # 1) For each Pautomac problem
    # 2)    Generate the solution for the gold case
    # 3)    Generate the solution for the sliding window case
    # 4)    for each segmentation
    # 5)        for each take
    # 6)            Generate the solution
    # ----------------------------------------------------------
    for pp in mt.PAUTPROBS:
    # @todo ocio qui
    # for pp in xrange(24, 25, 1):
        print "evaluating for Pautomac problem number", pp
        ppdir = mt.RESDIR + str(pp) + "/"
        # print "generating the solution for the gold case"
        evpath = mt.PAUTDIR + str(pp) + "/" + str(pp) + ".pautomac.test"
        # special case: sliding window
        print "generating the solution for the sliding window case"
        solpath = ppdir + "sw/solution.txt"
        mdpath = ppdir + "sw/model.pa"
        md = pu.mdload(mdpath)
        # ru.evaluate(md, pu.sessionize(evpath), solpath)
        pu.evaluate(md, evpath, solpath)
        # general case: partially correct segmentations
        for tc in xrange(0, 100 + mt.STEP, mt.STEP):
            print "generating the solution for the case", tc
            # setting the base directory for test case tc
            for tk in xrange(mt.TAKES):
                print "generating the partially random solution for take", tk
                prsolpath = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/prn.sol"
                prmdpath = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/prn.pa"
                prmd = pu.mdload(prmdpath)
                # ru.evaluate(md, pu.sessionize(evpath), solpath)
                if tc > 0:
                    pu.evaluate(prmd, evpath, prsolpath)
                    print "generaing the semi-supervised solution for take", tk
                    sssolpath = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/sss.sol"
                    ssmdpath = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/sss.pa"
                    ssmd = pu.mdload(ssmdpath)
                    pu.evaluate(ssmd, evpath, sssolpath)


if __name__ == "__main__":
    # clean()
    evaluate()
