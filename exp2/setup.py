# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'


"""
Utility to setup the experiment by creating all the training and evaluating sequences.

It create directory "results".
For each pautomac problem, it generates a subdirectory of "results" containing the following subdirectories:
gold -> it contains the training and testing samples, and the solution (probabilities for all sessions in the test)
sliding -> it contains the sliding window training file, the sliding window model learned with RTI+, and the evaluation
[
seg_5
seg_10
seg_15
...
seg_100
]
all those directories contain REPLICAS (se meta) subdirectories. Each of them contain a model learned with RTI+,
the training sample, and the evaluation.

"""


import meta as mt
import pautomac_utility as pu
from os import mkdir, walk, rmdir, remove
from os.path import exists, join


def clean():
    # cleans everything removing all data files
    for root, dirs, files in walk(mt.RESDIR, topdown=False):
        for name in files:
            remove(join(root, name))
        for name in dirs:
            rmdir(join(root, name))
    # removes the base directory
    if exists(mt.RESDIR):
        rmdir(mt.RESDIR)


def setup():
    # 1) for each pautomac problem:
    # 2)    we generate train and test  by using the Pautomac model (gold).
    # 3)    we generate the train sample for the sliding window model (sw)
    # 4)    for each step of 5%
    #           5) generate train sample for 10 replicas of the partially correct segmentation
    # ------------------------------------------------------------------------------------
    # setting general parameters for all the utility moduli called in this script
    pu.SEED, pu.SESSLIMIT = mt.BASESEED, mt.SESSLIMIT
    # creating the base directories
    if not exists(mt.RESDIR):
        mkdir(mt.RESDIR)
    # STEP 1)
    for pp in mt.PAUTPROBS:
        print "setting up Pautomac problem number", pp
        ppdir = mt.RESDIR + str(pp) + "/"
        if not exists(ppdir):
            mkdir(ppdir)
        # STEP 2) now we generate train and test for the gold model
        print "setting up the gold"
        emd = mt.PAUTDIR + str(pp) + "/" + str(pp) + ".pautomac_model.txt"
        edir = ppdir + "gold/"
        gtr, gts = edir + "train.ptm", edir + "test.ptm"
        if not exists(edir):
            mkdir(edir)
        md = pu.mdload(emd)
        pu.sample(md, mt.TRAINSIZE, gtr)
        pu.SEED += 1
        pu.sample(md, mt.TESTSIZE, gts)
        print "setting up the sliding window"
        # STEP 2) now we generate train for the sliding window model
        edir = ppdir + "sw/"
        etr, ert = edir + "train.ptm", edir + "train.rti"
        if not exists(edir):
            mkdir(edir)
        wsize = 2 * int(pu.meta(gtr)[pu.AVGSSIZE])
        pu.toslided(gtr, wsize, etr)
        pu.torti(etr, ert)
        # STEP 3) now we can start
        pu.SEED += 1
        for tc in xrange(0, 100 + mt.STEP, mt.STEP):
            print "setting up random segmentation with", tc, "% correct bounds"
            # creating the test case data directory
            tcdir = ppdir + "/seg_" + str(tc) + "/"
            if not exists(tcdir):
                mkdir(tcdir)
            for tk in xrange(mt.TAKES):
                print "take", tk
                # setting the data directory for test case tc
                tkdir = tcdir + "/take_" + str(tk) + "/"
                # creating the test case data directory
                if not exists(tkdir):
                    mkdir(tkdir)
                # setting the training paths5
                etr = tkdir + "train.rti"
                # setting a specific seed for this test case (for the flat sequences generation)
                pu.SEED += tk
                # esporting the sample to rti
                pu.torti(gtr, etr, tc * 1e-2)


if __name__ == "__main__":
    clean()
    setup()