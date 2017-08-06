#!/usr/bin/python


import sys
import glob
import re
import numpy as np
import random

from sklearn import preprocessing
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier



def tokenize(text):
    words=filter(None, re.split(r'[ .,;\r\n]', text))
    words=[x.lower() for x in words]
    return words


word_idx=0
def transform(words=[], word_map={}):
    r=[]
    global word_idx
    for w in words:
        if w in word_map:
            r.append(word_map[w])
        else:
            word_idx+=1
            word_map[w]=word_idx
            r.append(word_map[w])
    return r

def inverse_transform(ids=[], word_map={}):
    # XXX performance
    r=[]
    for i in ids:
        for k in word_map.keys():
            if i==word_map[k]:
                r.append(k)
    return r



n_inputs=10
n_outputs=4
if __name__ == '__main__':

    files=glob.glob("datasets/*.dat")

    X=[]
    y=[]

    word_map={}
    for fn in files:
        print "Reading", fn
        with open(fn) as f:
            lines = f.readlines()

        for l in lines:
            text, target = l.split('|')
            tt=tokenize(text)
            tg=[int(x.strip()) for x in target.split(',')]

            tt=transform(tt, word_map)
            tt+=[-1]*(n_inputs-len(tt))

            #tg=transform(tg, word_map)
            tg+=[-1]*(n_outputs-len(tg))

            X.append(tt)
            y.append(tg)


    X=np.array(X)
    y=np.array(y)       

    idx = range(len(X))
    random.shuffle(idx)

    X_train = X[idx[:100]]
    y_train = y[idx[:100]]
    X_test = X[idx[100:]]
    y_test = y[idx[100:]]

    clf=MultiOutputClassifier(RandomForestClassifier(), n_jobs=-1)
    clf.fit(X_train, y_train)
    P=clf.predict(X_test)

    for i in range(len(y_test)):
        print "---"
        res=[]
        for j in y_test[i]:
            if j==-1: continue
            res.append(inverse_transform([X_test[i][j]], word_map))
        print "real:", y_test[i]
        #print "real:", res

        res=[]
        for j in P[i]:
            if j==-1: continue
            res.append(inverse_transform([X_test[i][j]], word_map))
        print "prediction", P[i]
        #print "prediction", res

    print clf.score(X_test, y_test)




