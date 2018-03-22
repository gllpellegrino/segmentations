# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'


PAUTDIR = "/home/nino/PycharmProjects/segmentation/pautomac/"

RESDIR = "/mnt/ata-TOSHIBA_MQ01ABD100_52DOT1CIT-part1/SEGMENTATIONS/results/"

BASESEED = 1984

PAUTPROBS = [6, 7, 9, 11, 13, 16, 18, 24, 26, 27, 32, 35, 40, 42, 47, 48]
# PAUTPROBS = [i for i in xrange(1, 49)]

# we generate random segmentations with progressive amount of correct bounds
# the progression rateo is 5%, meaning that every segmentation has 5% more correct bounds.
STEP = 5

# how many times we generate the randomic part of each segmentation (for statistical relevance)
TAKES = 10

# maximal length of a session (string) in the samples we generate
SESSLIMIT = 1000

# amount of sessions within the training sample
TRAINSIZE = 4000

# amount of session within the testing sample
TESTSIZE = 1000

# minimal probability correction to avoid 0s in the perplexity computation (used in analyze.py)
MINPROB = 1e-200

# maximal window length for sliding window samples (it affect performance in terms of memory requirements)
MAXWSIZE = 5

# RTI+ bash command (used in train.py)
RTI_CMD = "/home/nino/bin/RTI/build/rti 1 0.05 {TRAIN} > {MODEL}"
