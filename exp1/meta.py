# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'


BASEDIR = "/home/nino/PycharmProjects/segmentation/exp1/"

PAUTDIR = "/home/nino/PycharmProjects/segmentation/pautomac/"

RESDIR = "/home/nino/PycharmProjects/segmentation/exp1/results/"

BASESEED = 1984

# PAUTPROBS = [6, 7, 9, 11, 13, 16, 18, 24, 26, 27, 32, 35, 40, 42, 47, 48]

# reference problem
PAUPROB = 24

# we generate random segmentations with progressive amount of correct bounds
# the progression rateo is 5%, meaning that every segmentation has 5% more correct bounds.
STEP = 5

# how many times we generate the randomic part of each segmentation (for statistical relevance)
TAKES = 10

# maximal length of a session (string) in the samples we generate
SESSLIMIT = 50

# amount of sessions within the training sample
TRAINSIZE = 20000

# amount of session within the testing sample
TESTSIZE = 5000