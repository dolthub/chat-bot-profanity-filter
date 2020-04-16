#!/usr/bin/env python

from time import sleep
import random
from doltpy.core import Dolt, clone_repo
import os


def censor_text(text, bad_words_df):
    censored = False
    censored_text = text
    for bad_word in bad_words_df['bad_word']:
        # If `bad_word` exists as a substring of `text`, replace the substring with asterisks
        if text.find(bad_word) > -1:
            censored_text = censored_text.replace(bad_word, '*'*len(bad_word))
            censored = True
    return censored_text, censored

RESPONSES = ['Cool',
             'Sounds good',
             'Thanks',
             'Thank you',
             'Okay...',
             'I guess',
             'Great',
             'Good job',
             'Congratulations',
             'Wow',
             'Sick',
             '👍',
             '🤙',
             "I don't care",
             "Whatever",
             "Sure"]


CHECKOUT_DIR = 'bad-words-clone'

def clone_or_pull_latest():
    if os.path.exists(CHECKOUT_DIR):
        repo = Dolt(CHECKOUT_DIR)
        repo.pull()
        return repo
    else:
        return clone_repo('Liquidata/bad-words', CHECKOUT_DIR)

KEEP_CHATTING = True

on_load_text = '''
Hello! This is a simple chat bot with profanity filter.
Respond 'bye', or use CTRL+C to exit.
You can type anything you want, and I will censor the bad words.
Say something
'''
print(on_load_text)

while KEEP_CHATTING:
    repo = clone_or_pull_latest()
    bad_words_df = repo.read_table('bad_words')
    user_response = input("> Me: ")
    if user_response.lower() == "bye":
        print("> ChatBot: Thanks for chatting!")
        KEEP_CHATTING = False
    else:
        censored_text, censored = censor_text(user_response.lower(), bad_words_df)
        if censored == True:
           print("> ChatBot sees:", censored_text)
        print("> ChatBot:",random.choice(RESPONSES))
