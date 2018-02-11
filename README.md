## 08/02/2018

The idea is:

We have a stream with a notion of session. There are sessions there, but we need to extract them in order to learn 
state machines effectively. 


As a consequence, we first need to show that by learning a model with correctly identified sessions we
we get better results than by using a sliding window or by using uncorrectly identified sessions. 


To do so we need a way of evaluating the goodness of the models we learn by using any method.
It is hard to come with a measure of similarity between models. Even by assuming the same alphabet, 
and even by assuming to known the target right model, how to evauate if two models are similar is an open question.
IDEA: the similarity between two state machines may be seen as a problem of graph isomorphism, which is a
complex problem (NP-intermediate) BUT, for trees, it is solvable i polynomial time.
So we could in principle compute a similarity at the prefix tree level.
That could work if we want to compare a segmenter having the same learning algorithm and the same target model.
If we want to compare with other models we need to act with probabilities for example (ngrams, HMMs, are probabilistic
models)

The polnomial algorithm to assess tree isomorphism made by Ullman et al. does not consider transition labels, it only
cares about the structure of the tree. Furthermore, it is boolean. It answers YES or NOT to the question: are T_1 and 
T_2 isomorphic?

## 09/02/2018

We plan 3 experiments.
In the first experiment we just show that sliding window is better than segmentation when the segmentation is poor.
However, it also shows that when the segmentation starts becoming better, it is better than sliding window.
We test that on all the problems we select from Pautomac suite (maybe the smaller ones only), and by means of
perplexity. 
A big question is to test on the probability to assign to every string in the test file.
If we do that, we train on flat sequences and test on segmentations ... a bit weird.
In the second experiment we introduce HMM, ngrams, and our semisupervised tecnique. And we compare each other.
In the third experiment we generate the right model for each stratosphere sequence, and we do the same as experiment 2
on real data.