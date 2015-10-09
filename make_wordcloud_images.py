#!/usr/bin/env python

import json, os, pandas as pd, numpy as np, random as rd
from scipy.misc import imread
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import operator


MASK_PATH = os.path.expanduser('~/concept-navigator/lip_modules/mask_image.png')
FONT_PATH = os.path.expanduser('~/concept-navigator/lip_modules/EuphemiaCAS.ttc')
WORD_CLOUD_WIDTH = 2000
WORD_CLOUD_HEIGHT = 1000

def dct_max_key(dct):
    return max(dct.iteritems(), key=operator.itemgetter(1))[0]

def blue_red_color_func(word=None, font_size=None, position=None,
                        orientation=None, font_path=None, random_state=None,
                        ordinal=None, **kwargs):
    dct = kwargs['word_partisanship'][ordinal]
    huedict = {'Lab': 360, 'Con': 220, 'LD': 35}
    saturation, threshold = 70, 0.45
    key = dct_max_key(dct)
    if dct[key] > threshold:
        hue, luminance = huedict[key], int(dct[key] * 50.0)
    else:
        hue, saturation, luminance = 0, 0, 60.0
    colour_val = 'hsl(%d, %d%%, %d%%)' % (hue, saturation, luminance)
    return colour_val

def create_wordcloud(wordcloud_data):
    mask = imread(MASK_PATH)
    wordcloud = WordCloud(max_words=1000, mask=mask, stopwords=None, margin=10, random_state=1,
                          font_path=FONT_PATH, prefer_horizontal=1.0, width=WORD_CLOUD_WIDTH,
                          height = WORD_CLOUD_HEIGHT, background_color='black', mode='RGBA')
    word_importance_list = [(dct['word'], dct['importance']) for dct in wordcloud_data['words']]
    partisanship_list = [dct['partisanship'] for dct in wordcloud_data['words']]
    kwargs = {'word_partisanship': partisanship_list}
    wordcloud.generate_from_frequencies(word_importance_list, **kwargs)
    return wordcloud

def save_wordcloud(wordcloud, wcfile):
    with open(wcfile, 'w') as f:
        plt.imshow(wordcloud.recolor(color_func=blue_red_color_func_6))
        plt.axis("off")
        plt.savefig(f, format='png')
        plt.close()

def get_cluster_model_data(numdict, key):
    val = numdict[key]
    wilfilepath = '/Users/enrightward/Desktop/coding/wordclouds/ukhansard/%s/alldatanew/cluster_model_data_%i.txt' % (key, val)
    with open(wilfilepath, 'r') as f:
        wordcloud_data = [json.loads(entry) for entry in f.read().split('\n') if len(entry) > 0]
    return wordcloud_data

def make_wc_images(cluster_model_data, numdict, key):
    val = numdict[key]
    for i, wordcloud_data in enumerate(cluster_model_data):
        wcfile = '/Users/enrightward/Desktop/coding/wordclouds/ukhansard/%s/alldatanew/ukh_wordcloud_alldata_%i_%i.png' % (key, val, i)
        wordcloud = create_wordcloud(wordcloud_data)
        save_wordcloud(wordcloud, wcfile)

numdict = {'five': 5, 'ten': 10, 'twenty': 20, 'thirty': 30, 'fifty': 50}

for key in numdict.keys():
    cluster_model_data = get_cluster_model_data(numdict, key)
    make_wc_images(cluster_model_data, numdict, key)
