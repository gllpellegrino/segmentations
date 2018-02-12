# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'



"""
Utility to generate the distributions of the models learned by using train.py
"""


import exp1.meta as mt
import pautomac_utility as pu
import rti_utility as ru
import os


# only cleans the files produced by learn()
def clean():
    # first we remove the gold solution
    print "cleaning evaluation products for the gold case"
    pt = mt.RESDIR + "gold/solution.txt"
    if os.path.exists(pt):
        os.remove(pt)
    # second we remove the sliding window solution
    print "cleaning evaluation products for the sliding window test case"
    pt = mt.RESDIR + "sw/solution.txt"
    if os.path.exists(pt):
        os.remove(pt)
    # now we scan the remaining directories, still to remove training products
    for tc in xrange(0, 100 + mt.STEP, mt.STEP):
        print "cleaning evaluation for test case", tc
        # setting the base directory for test case tc
        for tk in xrange(mt.TAKES):
            tkdir = mt.RESDIR + "seg_" + str(tc) + "/take_" + str(tk) + "/"
            # cleaning starts
            for item in os.listdir(tkdir):
                if item.endswith("solution.txt"):
                    os.remove(os.path.join(tkdir, item))


# learns automata for all the test cases
def eval():
    # 1) Generate the solution for the gold case
    # 2) Generate the solution for the sliding window case
    # 3) for each segmentation
    # 4)    for each take
    # 5)        Generate the solution
    # ----------------------------------------------------------
    # special case: gold
    print "generating the solution for the gold case"
    mdpath = mt.PAUTDIR + str(mt.PAUPROB) + "/" + str(mt.PAUPROB) + ".pautomac_model.txt"
    evpath = mt.RESDIR + "gold/test.ptm"
    solpath = mt.RESDIR + "gold/solution.txt"
    md = pu.mdload(mdpath)
    pu.evaluate(md, evpath, solpath)
    # special case: sliding window
    print "generating the solution for the sliding window case"
    solpath = mt.RESDIR + "sw/solution.txt"
    mdpath = mt.RESDIR + "sw/model.rtimd"
    md = ru.mdload(mdpath)
    pu.evaluate(md, evpath, solpath)
    # general case: partially correct segmentations
    for tc in xrange(0, 100 + mt.STEP, mt.STEP):
        print "generating the solution for the case", tc
        # setting the base directory for test case tc
        for tk in xrange(mt.TAKES):
            print "generating the solution for take", tk
            solpath = mt.RESDIR + "seg_" + str(tc) + "/take_" + str(tk) + "/solution.txt"
            mdpath = mt.RESDIR + "seg_" + str(tc) + "/take_" + str(tk) + "/model.rtimd"
            md = ru.mdload(mdpath)
            pu.evaluate(md, evpath, solpath)



if __name__ == "__main__":
    # clean()
    eval()