# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'

"""
Unitilty to train all the required models.
"""

import meta as mt
import rti_utility as ru
import os


# only cleans the files produced by learn()
def clean():
    for pp in mt.PAUTPROBS:
        print "cleaning learning products for Pautomac problem number", pp
        ppdir = mt.RESDIR + str(pp) + "/"
        # first we remove the sliding window model
        print "cleaning learning products for the sliding window test case"
        pt = ppdir + "sw/model.rtimd"
        if os.path.exists(pt):
            os.remove(pt)
        # now we scan the remaining directories, still to remove training products
        for tc in xrange(0, 100 + mt.STEP, mt.STEP):
            print "cleaning learning products for test case", tc
            # setting the base directory for test case tc
            for tk in xrange(mt.TAKES):
                tkdir = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/"
                # cleaning starts
                for item in os.listdir(tkdir):
                    if item.endswith(".rtimd") or item.endswith("model.bin"):
                        os.remove(os.path.join(tkdir, item))


# learns automata for all the test cases
def train():
    # 1) For each pautomac problem
    # 2) Learn the sliding window model
    # 3) for each segmentation
    # 4)    for each take
    # 5)        Learn the RTI+ model and store it
    # -----------------------------------------------------------------------------------------------
    for pp in mt.PAUTPROBS:
        print "learning automata for Pautomac problem number", pp
        ppdir = mt.RESDIR + str(pp) + "/"
        # special case: sliding window
        print "learning automaton for sliding window test case"
        trpath = ppdir + "sw/train.rti"
        mdrpath = ppdir + "sw/model.rtimd"
        mdepath = ppdir + "sw/model.bin"
        ru.mdtrain(trpath, mdrpath)
        ru.restimate(ru.mdload(mdrpath), trpath, mdepath)
        # general case: partially correct segmentations
        for tc in xrange(0, 100 + mt.STEP, mt.STEP):
            print "learning automata for test case", tc
            # setting the base directory for test case tc
            for tk in xrange(mt.TAKES):
                print "learning automaton for take", tk
                trpath = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/train.rti"
                mdrpath = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/model.rtimd"
                mdepath = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/model.bin"
                ru.mdtrain(trpath, mdrpath)
                ru.restimate(ru.mdload(mdrpath), trpath, mdepath)


if __name__ == "__main__":
    clean()
    print "------------------------------------------------------------------------------------------------------------"
    train()
