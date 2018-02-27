# -*- coding: utf-8 -*-

__author__ = 'Gaetano "Gibbster" Pellegrino'


import numpy as np
import matplotlib.pyplot as plt


def pf_iterator(path, pl, fl):
    with open(path, 'r') as th:
        th.readline()
        pastw = ()
        futw = ()
        initialization = True
        for row in th:
            reading = row.strip().split(' ')[1:]
            while reading:
                if initialization:
                    futw += (reading.pop(0), )
                    if len(futw) == fl:
                        initialization = False
                        yield pastw, futw
                else:
                    pastw = pastw + (futw[0], ) if len(pastw) < pl else pastw[1:] + (futw[0], )
                    futw = futw[1:] + (reading.pop(0), )
                    yield pastw, futw
        while len(futw) > 1:
            pastw = pastw + (futw[0], ) if len(pastw) < pl else pastw[1:] + (futw[0], )
            futw = futw[1:]
            yield pastw, futw


def training_with_priors_iterator(path, dp, df, segmenter, k):
    # segmentation = ppm_segmenter(path, k, tresh)
    segmentation = segmenter(path, dp, df, k)
    # segmentation = load_from_pautomac(path)
    past, future = (), ()
    restarts = []
    index = 0
    for symbol, flag in segmentation:
        if len(future) < df:
            future += (symbol, )
        else:
            yield past, future
            past = past + (future[0], ) if len(past) < dp else past[1:] + (future[0], )
            future = future[1:] + (symbol, )
        if flag:
            restarts.append(index)
        index += 1
    # trailing nonboundary contexts
    while future:
        yield past, future
        past = past[1:] + (future[0], )
        future = tuple(future[1:])
    # boundary contexts
    for r in restarts:
        if r > 0:
            if r + df < len(segmentation):
                # yield (), tuple(map(lambda x: x[0], segmentation[r:r + k]))
                yield (), tuple(map(lambda x: x[0], segmentation[r:r + df]))
            else:
                yield (), tuple(map(lambda x: x[0], segmentation[r:len(segmentation)]))


def counter_gold(iterator):
    # coglione, quando sei col gold devi distinguere il null past dai totali
    counts = {'totals': {}}
    for past, future in iterator:
        # special case: null past context
        if past == ():
            if not () in counts:
                counts[()] = [{}, {}, {}]
            for fu in xrange(len(future)):
                future_slice = future[:fu + 1]
                if not future_slice in counts[()][0]:
                    counts[()][0][future_slice] = 1
                    if not len(future_slice) in counts[()][2]:
                        counts[()][2][len(future_slice)] = 1
                    else:
                        counts[()][2][len(future_slice)] += 1
                else:
                    counts[()][0][future_slice] += 1
                if not len(future_slice) in counts[()][1]:
                    counts[()][1][len(future_slice)] = 1
                else:
                    counts[()][1][len(future_slice)] += 1
        # general case
        for ps in xrange(len(past)):
            past_slice = past[ps:]
            if not past_slice in counts:
                counts[past_slice] = [{}, {}, {}]
            # managing totals
            if not past_slice in counts['totals']:
                counts['totals'][past_slice] = 0
            counts['totals'][past_slice] += 1
            # past and future slices
            for fu in xrange(len(future)):
                future_slice = future[:fu + 1]
                if not future_slice in counts[past_slice][0]:
                    counts[past_slice][0][future_slice] = 1
                    if not len(future_slice) in counts[past_slice][2]:
                        counts[past_slice][2][len(future_slice)] = 1
                    else:
                        counts[past_slice][2][len(future_slice)] += 1
                else:
                    counts[past_slice][0][future_slice] += 1
                if not len(future_slice) in counts[past_slice][1]:
                    counts[past_slice][1][len(future_slice)] = 1
                else:
                    counts[past_slice][1][len(future_slice)] += 1
    return counts


def _prob_nino(counts, past, future):
    if not future in counts[past][0]:
        return 0, 0, .0
    return counts[past][0][future], \
           counts[past][1][len(future)], \
           counts[past][0][future] / float(counts[past][1][len(future)])


def maxtest(counts, past, future):
    maxdiff = -1
    for i in xrange(len(past) - 1, -1, -1):
        past_slice = tuple(past[i:])
        for j in xrange(1, len(future) + 1):
            future_slice = tuple(future[:j])
            f, _, p = _prob_nino(counts, past_slice, future_slice)
            _, _, ppr = _prob_nino(counts, (), future_slice)
            diff = p - ppr
            if diff > maxdiff and f > 10:
                maxdiff = diff
    return maxdiff


# def valuegetter(training_path, testing_path, kp, kf, segmenter, candidatesno):
#     segmented = load_from_pautomac(training_path)
#     counts = counter_gold(training_with_priors_iterator(training_path, kp, kf, segmenter, candidatesno))
#     values = []
#     boundaries = []
#     index = 0
#     returned, tp, fp = 0, 0, 0
#     for past, future in pf_iterator(testing_path, kp, kf):
#         #memoization managing
#         alogl = maxtest(counts, past, future)
#         if segmented[index][1]:
#             boundaries.append(index)
#         values.append(alogl)
#         if alogl < .0:
#             returned += 1
#             if segmented[index][1]:
#                 tp += 1
#             else:
#                 fp += 1
#         index += 1
#     truerate = tp / float(returned) if returned > 0 else .0
#     # falserate = fp / float(returned) if returned > 0 else .0
#     # print 'stats', returned, tp, fp, truerate, falserate
#     # return np.array(values), np.array(boundaries)
#     return returned, truerate


def segmenter(training_path, testing_path, kp, kf, segmntr, candidatesno):
    counts = counter_gold(training_with_priors_iterator(training_path, kp, kf, segmntr, candidatesno))
    segmentation = []
    for past, future in pf_iterator(testing_path, kp, kf):
        alogl = maxtest(counts, past, future)
        segmentation.append((future[0], alogl < 0.))
    return segmentation


# def prior_vs_expected_comparison(path, k, tresh):
#     c_estimated = counter_gold(training_with_priors_iterator(path, k, tresh))
#     c_gold = counter_gold(pf_iterator_gold(path, k, k))
#     keys = sorted(c_estimated[()][0].keys(), key=lambda x: (len(x), x))
#     for f in keys:
#         if f in c_gold[()][0]:
#             print f, c_estimated[()][0][f], c_gold[()][0][f]


def plot_signal(values, boundaries):
    x = np.arange(len(values))
    plt.plot(x, values, 'b', label='signal')
    plt.plot(x[boundaries], values[boundaries], 'yd', label='boundary')
    plt.legend()
    plt.show()


if __name__ == "__main__":
    pcode = 1
    pt = '/home/npellegrino/LEMMA/sicco_challenge/prova/pfa_toy/pfatoy.train'
    ml = '/home/npellegrino/LEMMA/sicco_challenge/prova/smtp_traces.txt'
    ptr = '/home/nino/PycharmProjects/segmentation/pautomac/1/' + str(pcode) + '.pautomac.train'
    pts = '/home/npellegrino/LEMMA/dataflow/alergia/pautomac_test_sets/' + str(pcode) + '.pautomac.test'
    ka = 5
    #print valuegetter(ptr, ptr, ka, ka, 0.01)
    #prior_vs_expected_comparison(ptr, ka, 0.1)
    # print valuegetter(ptr, ptr, ka, ka, ppm_topk_segmenter, 200)
    ind = 0
    for p, f in pf_iterator(ptr, ka, ka):
        if ind >= 5:
            break
        print p, f
        ind += 1
    print 'bomba'