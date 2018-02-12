# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'

"""
Unitilty to train all the required models.
"""

import exp1.meta as mt
import rti_utility as ru
import os


# only cleans the files produced by learn()
def clean():
    # first we remove the sliding window model
    print "cleaning learning products for the sliding window test case"
    pt = mt.RESDIR + "sw/model.rtimd"
    if os.path.exists(pt):
        os.remove(pt)
    # now we scan the remaining directories, still to remove training products
    for tc in xrange(0, 100 + mt.STEP, mt.STEP):
        print "cleaning learning products for test case", tc
        # setting the base directory for test case tc
        for tk in xrange(mt.TAKES):
            tkdir = mt.RESDIR + "seg_" + str(tc) + "/take_" + str(tk) + "/"
            # cleaning starts
            for item in os.listdir(tkdir):
                if item.endswith(".rtimd"):
                    os.remove(os.path.join(tkdir, item))


# learns automata for all the test cases
def train():
    # 1) Learn the sliding window model
    # 2) for each segmentation
    # 3)    for each take
    # 4)        Learn the RTI+ model and store it
    # ----------------------------------------------------------
    # special case: sliding window
    print "learning automaton for sliding window test case"
    trpath = mt.RESDIR + "sw/train.rti"
    mdpath = mt.RESDIR + "sw/model.rtimd"
    ru.mdtrain(trpath, mdpath)
    # general case: partially correct segmentations
    for tc in xrange(0, 100 + mt.STEP, mt.STEP):
        print "learning automata for test case", tc
        # setting the base directory for test case tc
        for tk in xrange(mt.TAKES):
            print "learning automaton for take", tk
            trpath = mt.RESDIR + "seg_" + str(tc) + "/take_" + str(tk) + "/train.rti"
            mdpath = mt.RESDIR + "seg_" + str(tc) + "/take_" + str(tk) + "/model.rtimd"
            ru.mdtrain(trpath, mdpath)


if __name__ == "__main__":
    # clean()
    train()
