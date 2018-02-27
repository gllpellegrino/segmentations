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
import segmentations_utility as su
import sss_utility as ssu
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
    pu.SEED, su.SEED, pu.SESSLIMIT = mt.BASESEED, mt.BASESEED, mt.SESSLIMIT
    # creating the base directories
    if not exists(mt.RESDIR):
        mkdir(mt.RESDIR)
    # STEP 1)
    for pp in mt.PAUTPROBS:
        # for pp in xrange(21, 49, 1):
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
        if not exists(gtr):
            pu.sample(md, mt.TRAINSIZE, gtr)
        print "gold training set up"
        pu.SEED += 1
        if not exists(gts):
            pu.sample(md, mt.TESTSIZE, gts)
        print "gold testing set up"
        print "setting up the sliding window"
        # STEP 2) now we generate train for the sliding window model
        edir = ppdir + "sw/"
        etr, ert = edir + "train.ptm", edir + "train.rti"
        if not exists(edir):
            mkdir(edir)
        if not exists(etr):
            # wsize = min(int(pu.meta(gtr)[pu.AVGSSIZE]), mt.MAXWSIZE)
            wsize = mt.MAXWSIZE
            pu.toslided(gtr, wsize, etr)
            pu.torti(etr, ert)
        print "sliding window training set up"
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
                # setting the seeds for this take
                pu.SEED += tk
                su.SEED = pu.SEED
                # setting the data directory for test case tc
                tkdir = tcdir + "/take_" + str(tk) + "/"
                # creating the test case data directory
                if not exists(tkdir):
                    mkdir(tkdir)
                # setting the paths of the files we will generate
                etr = tkdir + "train.rti"
                ctr = tkdir + "cbounds.rti"
                sstr = tkdir + "sss.rti"
                # exporting the correct bounds in rti format
                if exists(ctr):
                    sgc = su.load(pu.streamize(ctr))
                else:
                    sgd = su.load(pu.streamize(gtr))
                    sgc = su.debound(sgd, int(tc * 1e-2 * mt.TRAINSIZE))
                    su.torti(sgc, ctr)
                # completing the correct bounds with random boundaries
                # and exporting the random/correct sample to to rti
                if not exists(etr):
                    sgt = su.bound(sgc, int((1. - tc * 1e-2) * mt.TRAINSIZE))
                    su.torti(sgt, etr)
                    # pu.torti(gtr, etr, tc * 1e-2)
                print "rti training set up"
                # adding the semisupervised segmenteations
                if not exists(sstr):
                    ssgm = ssu.extend(sgc, mt.MAXWSIZE, int((1. - tc * 1e-2) * mt.TRAINSIZE))
                    su.torti(ssgm, sstr)
                print "semi supervised segmentation rti training set up"


if __name__ == "__main__":
    # clean()
    setup()

    # for pp in mt.PAUTPROBS:
    #     print "setting up the sliding window for problem", pp
    #     ppdir = mt.RESDIR + str(pp) + "/"
    #     # STEP 2) now we generate train for the sliding window model
    #     edir = ppdir + "sw/"
    #     gtr = mt.RESDIR + str(pp) + "/gold/train.ptm"
    #     etr, ert = edir + "train.ptm", edir + "train.rti"
    #     if not exists(edir):
    #         mkdir(edir)
    #     wsize = int(pu.meta(gtr)[pu.AVGSSIZE])
    #     pu.toslided(gtr, wsize, etr)
    #     pu.torti(etr, ert)

    # for pp in mt.PAUTPROBS:
    #     swdir = mt.RESDIR + str(pp) + "/sw/"
    #     for root, dirs, files in walk(swdir, topdown=False):
    #         for name in files:
    #             remove(join(root, name))
    #         for name in dirs:
    #             rmdir(join(root, name))

    # for pp in mt.PAUTPROBS:
    #     ppdir = mt.RESDIR + str(pp) + "/"
    #     for tc in xrange(0, 100 + mt.STEP, mt.STEP):
    #         tcdir = ppdir + "seg_" + str(tc)
    #         for tk in xrange(mt.TAKES):
    #             for root, dirs, files in walk(tcdir, topdown=False):
    #                 for name in files:
    #                     remove(join(root, name))

    # for ppp in mt.PAUTPROBS:
    #     ppd = mt.RESDIR + str(ppp) + "/"
    #     for tec in xrange(0, 100 + mt.STEP, mt.STEP):
    #         tcd = ppd + "seg_" + str(tec)
    #         for tkey in xrange(mt.TAKES):
    #             ppth = tcd + "/take_" + str(tkey) + "/sss.rti"
    #             if exists(ppth):
    #                 remove(ppth)
