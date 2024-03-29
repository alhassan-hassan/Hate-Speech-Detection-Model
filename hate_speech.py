# -*- coding: utf-8 -*-
"""Final_Proj_Hate_Speech

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/134Ild5vQT0g3qba7QgUUe2HITgP1Sur6
"""

import pandas as pd
import nltk
from nltk.util import pr
import pandas as pd
import numpy as np

from keras.layers.embeddings import Embedding
from keras import models
from keras import layers
from keras import regularizers
from keras.layers import LSTM
from tensorflow.keras.layers import Dense
from keras.regularizers import l2
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import string

import re 
nltk.download('stopwords')
stemmer = nltk.SnowballStemmer("english")
from nltk.corpus import stopwords


stopword=set(stopwords.words('english'))

"""WHY DID WE USE KERAS INSTEAD OF TORCH?
Keras is easy to use when defining and training deep learning models. It uses both Theano and TensorFlow models with Multiple GPU support and Modularity
"""

# DOWNLOADING THE DATASET

!pip install datasets
import datasets 
dataset = datasets.load_dataset('ucberkeley-dlab/measuring-hate-speech', 'binary')   
datatset = dataset['train'].to_pandas()

"""**DEFINING PARAMETERS AND HYPERPARAMETERS**"""

# HYPERPARAMETERS
LEARNING_RATE   = 0.005
BATCH_SIZE      = 32
NUM_EPOCHS      = 15
embedding_dim = 16   #This is a multiplier to the vocab to make a matrix for the texts
vocab_size = 30226   #This means a set of possible unique words that the model can learn

# OTHER PARAMETERS
training_size = 0.60
testing_size = 0.4801

"""**PREPROCESSING OF DATA**

1. GET ALL THE RELEVANT INFORMATION FROM THE DATASET INTO A LIST
"""

# FISHING OUT THE RELEVANT INFORMATION IN THE MODEL TRAINING 
from pprint import pprint
text = list()
score = list()
label = list ()

# ITERATE AND GET EACH DATA INTO THE DIFFERENT LIST OBJECTS
for row in range(len(dataset['train'])):
  text.append(dataset['train'][row]['text'])
  score.append(dataset['train'][row]['hate_speech_score'])
  if dataset['train'][row]['hate_speech_score'] > 0:
    label.append(1)
  else:
    label.append(0)

"""2. TRANFORM THOSE LISTS INTO A DATAFRAME WITH COLUMN NAMES.

      *This makes it easier to index full colums at a go*
"""

# CREATE A DATAFRAME FOR THE THREE COLUMNS (TWEETS, THE SCORE AND THE LABEL)
dataset = pd.DataFrame({
    "tweets" : text,
    "hate_speech_score" : score,
    "label" : label
})

# a preview of the dataframe
print(dataset.head())

"""3. CLEANING UP THE TWEETS USING A CUSTOM FUNCTION

    *This is intended to remove all the noise from the dataset*
"""

# THIS FUNCTION DEEP CLEANS THE DATASET BASED ON THE PATTERN OBSERVED IN THE DATASET
def clean(text):
    # make all words lowercase
    text = str(text).lower() 

    # remove any leading and training whitespaces
    text = text.strip() 

    # remove emphasies, symbols and character leading words example @wjdsd should be removed
    text = re.sub(r'@[A-Za-z0-9]+', '', text)    
    text = re.sub('\[.*?\]', '', text) 
    text = re.sub('#', '', text) 
    text = re.sub('https?://\S+|www\.\S+', '', text)  # remove hyperlinks also
    text = re.sub('<.*?>+', '', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text)

    # remove new lines
    text = re.sub('\n', '', text)
    text = re.sub('\w*\d\w*', '', text)
    text = [word for word in text.split(' ') if word not in stopword]
    text=" ".join(text)
    text = [stemmer.stem(word) for word in text.split(' ')]
    text=" ".join(text)
    return text

# CLEAN THE DATASET BY APPLYTING THE FUNCTION TO IT
dataset["tweets"] = dataset["tweets"].apply(clean)
print(dataset.head())

"""4. CONVERT THE DATASET INTO NUMPY ARRAYS"""

#How the texts will be represented
dataset = np.array(dataset[["tweets", "label"]])

"""**SPLITTING THE LARGE DATASET INTO TRAINING AND TESTING**"""

training = dataset[0: int(len(dataset) * training_size)]
testing = dataset[int(len(dataset) * training_size) : ]
print(len(testing))

"""SEPARATING THE TWEETS FROM THE LABELS OF THE TRAINING DATASET"""

# Get both tweets and their corresponding labels independently
sentences = []
labels = []
for eachTweet in training:
  sentences.append(eachTweet[0])
  labels.append(eachTweet[1])

print(len(sentences) * 0.8)

"""SPLITTING THE TRAINING INTO TRAINING AND VALIDATION

"""

# THE SPLIT WAS DONE USING THE 80% (TRAINING) AND 20% (VALIDATION) PARTITIONING
train_set = sentences[0:int(0.8*len(sentences))]
train_labels = labels[0:int(0.8*len(sentences))]

val_set = sentences[int(0.8*len(sentences)):]
val_labels = labels[int(0.8*len(sentences)):]

print(len(train_set), len(train_labels))

"""**TOKENIZING, SEQUENCING AND PADDING THE TRAINING SENTENCES (TWEETS)**"""

# tokenize the sentences
tokenizer = Tokenizer(num_words=vocab_size, oov_token="<OOV>") 
tokenizer.fit_on_texts(train_set)

# this simple=y gets the total number of independent words discovered
word_ind = tokenizer.word_index

# Pad and sequence the tokenized dataset
training_sequences = tokenizer.texts_to_sequences(train_set)
train_padded = pad_sequences(training_sequences, maxlen=100, padding="post", truncating="post")

# apply the same action for the validation dataset
validating_sequences = tokenizer.texts_to_sequences(val_set)
validating_padded = pad_sequences(validating_sequences, maxlen=100, padding="post", truncating="post")

print(len(word_ind), " tokenized words")

#CONVERTING PADDED DATA TO NUMPY ARRAYS
training_padded = np.array(train_padded)
training_labels = np.array(train_labels)
validating_padded = np.array(validating_padded)
validating_labels = np.array(val_labels)

print(training_labels)

"""**TRAINING THE MODEL**

1. BUILDING THE MODEL
"""

# USING LSTM SEQUENTIAL MODEL FOR THE MODEL
model = tf.keras.Sequential([
    # introducing an embedding layer
    tf.keras.layers.Embedding(vocab_size, embedding_dim, input_length=100),
    # introducing a bidirectional layer to the model
    tf.keras.layers.Bidirectional(LSTM(24)),
    # introducing a dense regularized layer to the model
    tf.keras.layers.Dense(24, activation='relu', kernel_regularizer=l2(0.01)),
    # introducing the output layer
    tf.keras.layers.Dense(1, activation='sigmoid')
])

# COMPILING THE MODEL
model.compile(loss='binary_crossentropy',optimizer='adam',metrics=['accuracy'])

"""2. GETTING A SUMMARY OF THE MODEL

"""

model.summary()

"""2. TRAINING THE MODEL"""

#TRAINING THE MODEL HAPPENS HERE
# the fir method has both back and forward propagation.
from keras import callbacks
num_epochs = 15
history = model.fit(
    training_padded, training_labels, 
    epochs=num_epochs, 
    validation_data=(validating_padded, validating_labels), 
    verbose=2)

"""**PLOTTING THE TRAINING AND VALIDATION ACCURACIES AND THEIR LOSSES**"""

import matplotlib.pyplot as plt

def plot_graphs(history, string):
  plt.plot(history.history[string])
  plt.plot(history.history['val_'+string])
  plt.xlabel("Epochs")
  plt.ylabel(string)
  plt.legend([string, 'val_'+string])
  plt.show()
  
plot_graphs(history, "accuracy")
plot_graphs(history, "loss")

"""**PEEKING AT THE WEIGHTS OF THE MODEL**"""

# monitoring the weights if the model
e = model.layers[0]
weights = e.get_weights()[0]
print(weights.shape) # shape: (vocab_size, embedding_dim)

reverse_word_index = dict([(value, key) for (key, value) in word_ind.items()])

def decode_sentence(text):
    return ' '.join([reverse_word_index.get(i, '?') for i in text])

# Get both tweets and their corresponding labels independently
testing_ = 0.48001
testing = dataset[0 : int(0.48001*len(dataset))]
def split(data):
  test_set = []
  labels_ = []
  for eachTweet in testing:
    test_set.append(eachTweet[0])
    labels_.append(eachTweet[1])

  return (test_set, labels_)

test_set, labels_ = split(testing)

# tokenize the sentences
tokenizer = Tokenizer(num_words=vocab_size, oov_token="<OOV>") #
tokenizer.fit_on_texts(test_set)

# this simple=y gets the total number of independent words discovered
word_ind = tokenizer.word_index

# Pad and sequence the tokenized dataset
test_sequences = tokenizer.texts_to_sequences(test_set)
test_padded = pad_sequences(test_sequences, maxlen=100, padding="post", truncating="post")
print(len(word_ind), " tokenized words")

# CONVERTING PADDED DATA TO NUMPY ARRAY
testing_padded = np.array(test_padded)
testing_labels = np.array(labels_)
print(len(testing_labels))

"""**EVALUATING THE ACCURACY OF THE MODEL AGAINST THE TEST DATASET**"""

model.evaluate(testing_padded, testing_labels, batch_size=128)

# A CUSTOMIZED FUNCTION TO PREPARE THE TEST DATASET FOR PREDICTION
def prepare_data(text):
  sequences = tokenizer.texts_to_sequences(text)
  padded = pad_sequences(sequences, maxlen=100, padding="post", truncating="post")
  return padded

!pip install tabulate

# PRINTING A SERIES OF TWEETS AND THE MODEL'S PERFORMANCE AGAINST THEM
from tabulate import tabulate
# print("Tweet \t \t \t \t \t \t \t \t  Class \t \t   model Prediction")
table = []
for row in range(len(test_set[0:50])):
  tempt = []
  mod_pred = ""
  class_ = ""
  padded = prepare_data([test_set[row]])
  pred = float(model.predict(padded))
  if pred > 0.5:
    mod_pred = "Hate Speech"
  else:
    mod_pred = "Not Hate Speech"
  if labels_[row] == 1:
    class_ = "Hate speech"
  else:
    class_ = "Not Hateful Speech"

  tempt.append(test_set[row][0:90])
  tempt.append(class_)
  tempt.append(pred)
  tempt.append(mod_pred)

  table.append(tempt)


head = ["Tweet", "Classification","Model Rating", "Model Prediction"]

print(tabulate(table, headers = head, tablefmt = "grid"))
