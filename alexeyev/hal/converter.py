__author__ = 'Anton M Alexeyev'
# I decided to implement HAL, not SAM -- another method for cognitive studies and recommender systems

from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from matrix_management import WordMatrix
import re

# todo: wipe away hardcode

input_text = open("testtext", "r")
text = ""

for line in input_text:
    text += line.lower() + " "

print "Text loaded"
print "Learning..."

# i chose the one everybody knows
stemmer = PorterStemmer()

# dumb tokenization
tokens = re.findall(r"[A-Za-z]+", text)
print "Tokens set built :", tokens

tokens_filtered = []
for token in tokens:
    if token in stopwords.words('english'):
        tokens_filtered += ["*"]
    else:
        tokens_filtered += [ token ]

# stemming
#normalized_tokens = [stemmer.stem(token) for token in tokens if token not in stopwords.words('english')]
normalized_tokens = [stemmer.stem(token) for token in tokens_filtered]

print "Tokens set filtered and stemmed :", normalized_tokens

window_size = 10
matrix = WordMatrix()

win_start = 0
while win_start + window_size <= len(normalized_tokens):
    window = normalized_tokens[win_start:win_start + window_size]
    first = 0
    second = 1
    while first < len(window):
        second = first + 1
        while second < len(window):
            matrix.add(window[first], window[second], window_size - second + first + 1)
            second += 1
        first += 1
    win_start += 1

print "Co-occurence counted"
print "Keys quantity:", len(matrix.get_tokens())

for key in matrix.get_tokens():
    if key <> "*":
        pass#print key, matrix.kn_cooccurences(key, 6)

print "Done"

def get_token_by_word(word):
    word = re.findall(r"[A-Za-z]+", word)[0]
    return stemmer.stem(word.lower())

def get_euclidean_vector_by_token(n, token):
    print "Incoming token:", token
    if token in matrix.token_set:
        return matrix.kn_columns(token, n, matrix.dist_cols_euclidean)
    raise KeyError

def get_cosine_vector_by_token(n, token):
    print "Incoming token:", token
    if token in matrix.token_set:
        return matrix.kn_columns(token, n, matrix.dist_cols_cosine)
    raise KeyError

def get_frequential_vector_by_token(n, token):
    print "Incoming token:", token
    if token in matrix.token_set:
        return matrix.kn_cooccurences(token, n)
    raise KeyError

for key in matrix.get_tokens():
    if key <> "*":
        pass#print key, matrix.kn_columns(key, 6, matrix.dist_cols_euclidean)