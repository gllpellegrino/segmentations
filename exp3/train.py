# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'

"""
Unitilty to train all the required models.
"""

import meta as mt
import rti_utility as ru
import pautomac_utility as pu
import os
from os.path import exists


# only cleans the files produced by learn()
def clean():
    for pp in mt.PAUTPROBS:
        print "cleaning learning products for Pautomac problem number", pp
        ppdir = mt.RESDIR + str(pp) + "/"
        # first we remove the sliding window model
        print "cleaning learning products for the sliding window test case"
        # pt = ppdir + "sw/model.rtimd"
        # if os.path.exists(pt):
        #     os.remove(pt)
        pt = ppdir + "sw/model.pa"
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
                    # if item.endswith(".rtimd") or item.endswith("model.bin"):
                    if item.endswith("model.pa"):
                        os.remove(os.path.join(tkdir, item))


# learns automata for all the test cases
def train():
    # 1) For each pautomac problem
    # 2) Learn the sliding window model
    # 3) for each segmentation
    # 4)    for each take
    # 5)        Learn the RTI+ model and store it
    # -----------------------------------------------------------------------------------------------
    ru.RTI_CMD = mt.RTI_CMD
    #@todo ocio qua
    # for pp in mt.PAUTPROBS:
    for pp in xrange(24, 25, 1):
        print "learning automata for Pautomac problem number", pp
        ppdir = mt.RESDIR + str(pp) + "/"
        # special case: sliding window
        print "learning automaton for sliding window test case"
        trpath = ppdir + "sw/train.rti"
        mdrpath = ppdir + "sw/model.rtimd"
        mdepath = ppdir + "sw/model.pa"
        if exists(mdrpath):
            print "\trti model trained already"
            if exists(mdepath):
                print "\trti model converted to Pautomac already"
            else:
                md = ru.estimate(ru.mdload(mdrpath), trpath)
                pu.mdstore(md, mdepath)
        else:
            ru.mdtrain(trpath, mdrpath)
            md = ru.estimate(ru.mdload(mdrpath), trpath)
            pu.mdstore(md, mdepath)
        # general case: partially correct segmentations
        for tc in xrange(0, 100 + mt.STEP, mt.STEP):
            print "learning automata for test case", tc
            # setting the base directory for test case tc
            for tk in xrange(mt.TAKES):
                print "learning automaton for take", tk
                trpath = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/prn.rti"
                mdrpath = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/prn.rtimd"
                mdepath = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/prn.pa"
                # handling the partially random model
                if exists(mdrpath):
                    print "\trti model for partially random segmentation trained already"
                    if exists(mdepath):
                        print "\trti model for partially random segmentation converted to Pautomac already"
                    else:
                        md = ru.estimate(ru.mdload(mdrpath), trpath)
                        pu.mdstore(md, mdepath)
                else:
                    ru.mdtrain(trpath, mdrpath)
                    md = ru.estimate(ru.mdload(mdrpath), trpath)
                    pu.mdstore(md, mdepath)
                # handling the semi supervised model
                srpath = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/sss.rti"
                sdrpath = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/sss.rtimd"
                sdepath = ppdir + "seg_" + str(tc) + "/take_" + str(tk) + "/sss.pa"
                if exists(sdrpath):
                    print "\trti model for semi-supervised segmentation trained already"
                    if exists(sdepath):
                        print "\trti model for semi-supervised segmentation converted to Pautomac already"
                    else:
                        md = ru.estimate(ru.mdload(sdrpath), srpath)
                        pu.mdstore(md, sdepath)
                else:
                    ru.mdtrain(srpath, sdrpath)
                    md = ru.estimate(ru.mdload(sdrpath), srpath)
                    pu.mdstore(md, sdepath)


if __name__ == "__main__":
    # clean()
    print "------------------------------------------------------------------------------------------------------------"
    train()

    # for i in mt.PAUTPROBS:
    #     pth1 = mt.RESDIR + str(i) + "/sw/model.rtimd"
    #     pth2 =mt.RESDIR + str(i) + "/sw/model.bin"
    #     if exists(pth1):
    #         os.remove(pth1)
    #     if exists(pth2):
    #         os.remove(pth2)
