#caller for han1 which is used for pre-training
import numpy as np
import pandas as pd
import cPickle
#import cv2
from collections import defaultdict
import re

from bs4 import BeautifulSoup

import sys
import os
import json

os.environ['KERAS_BACKEND']='theano'

from keras.preprocessing.text import Tokenizer, text_to_word_sequence
from keras.preprocessing.sequence import pad_sequences
from keras.utils.np_utils import to_categorical

from keras.layers import Embedding
from keras.layers import Dense, Input, Flatten
from keras.layers import Conv1D, MaxPooling1D, Embedding, Merge, Dropout, LSTM, GRU, Bidirectional, TimeDistributed
from keras.models import Model, model_from_json

from keras import backend as K
from keras.engine.topology import Layer, InputSpec
from keras import initializers

from keras import regularizers, constraints

from glove import Corpus, Glove

from nltk import tokenize
import ast
from keras.preprocessing import sequence

from pretrain import HAN1
from keras import callbacks

import ast
import sys
import cPickle

EMBEDDING_DIM = 100
WORDGRU = EMBEDDING_DIM/2
DROPOUTPER = 0.3

#---------------------------------------------------------------------------------------------------------------------------

print ('loading files...')
train_headlines = cPickle.load(open('Dataset/train_headlines_seq.p', 'rb'))
train_y = cPickle.load(open('Dataset/train_y.p', 'rb'))

val_headlines = cPickle.load(open('Dataset/val_headlines_seq.p', 'rb'))
val_y = cPickle.load(open('Dataset/val_y.p', 'rb'))


MAX_WORDS = 2967
MAX_SENTS = 979
AVE_WORDS = 32
AVE_SENTS = 21
WORD_LIMIT = int(1*AVE_WORDS)
SENT_LIMIT = int(1*AVE_SENTS)

print ("Train")
print (train_headlines.shape)

print ("val")
print (val_headlines.shape)


#--------------------------------------------------------------------------------------------------------------------------
with open('Dataset/word_index.json', 'r') as fp:
    word_index = json.load(fp)
MAX_NB_WORDS = len(word_index)+2
#ref:https://richliao.github.io/supervised/classification''/2016/12/26/textclassifier-HATN/
#creating word embeddings using GloVe
print ("Creating word embedding matrix")
#TODO: get word2vec pre trained on news corpus
GLOVE_DIR="Glove/glove.6B"
embeddings_index = {}
f = open(os.path.join(GLOVE_DIR, 'glove.6B.100d.txt'))
i = 0
for line in f:
    values = line.split()
    #glove file contains a word and then list of values which are the coefficients corresponding to the k-dimensional embedding
    word = values[0]
    coefs = np.asarray(values[1:], dtype='float32')
    embeddings_index[word] = coefs
f.close()
print('Total words in embedding dictionary: {}'.format(len(embeddings_index)))
#creating final matrix just for vocabulary words
#all elements in particular the zeroth element is initialized to all zeroes 
#all elements except the zeroth element will be changed later
embedding_matrix = np.zeros(shape=(MAX_NB_WORDS, EMBEDDING_DIM), dtype='float32')
embedding_matrix[1] = np.random.uniform(-0.25, 0.25, EMBEDDING_DIM)
for word, i in word_index.items():
    embedding_vector = embeddings_index.get(word) #glove coeffs wrt to the words
    if embedding_vector is not None:
        # words not found in embedding index will be all-zeros.
        embedding_matrix[i] = embedding_vector
    #0.25 is chosen so the unknown vectors have (approximately) same variance as pre-trained ones
    #ref: https://github.com/yoonkim/CNN_sentence/blob/master/process_data.py                              
    else:
        embedding_matrix[i] = np.random.uniform(-0.25,0.25, EMBEDDING_DIM) 

#-----------------------------------------------------------------------------------------------------------------------------        
print ('Build model...')
model = HAN1(MAX_NB_WORDS, WORD_LIMIT, SENT_LIMIT, EMBEDDING_DIM, WORDGRU, embedding_matrix, DROPOUTPER)
print model.summary()
#model1 is the word encoder model


print ('Model fit....')


class ModelSave(callbacks.Callback):
    def on_epoch_end(self, epoch, logs={}):
        model.save('SavedModels/han1_epoch_{}.h5'.format(epoch))
        
modelsave = ModelSave()
        
callbacks = [callbacks.EarlyStopping(monitor='val_acc', min_delta=0, patience=3, verbose=1, mode='auto'), modelsave]


model.fit(train_headlines, train_y, validation_data=(val_headlines, val_y), shuffle=True, batch_size=32, epochs=1000, callbacks=callbacks)

del train_headlines
del train_y
del val_headlines
del val_y


test_headlines = cPickle.load(open('Dataset/test_headlines_seq.p', 'rb'))
test_y = cPickle.load(open('Dataset/test_y.p', 'rb'))

'''
test_articles = test_articles[:10]
test_headlines = test_headlines[:10]
test_y = test_y[:10]
'''

print ("test")
print (test_headlines.shape)

print model.evaluate(test_headlines, test_y, batch_size=32)

#model.save('SavedModels/3han_model50.h5')
#model1.save('SavedModels/3han_model_wordEncoder50.h5')
