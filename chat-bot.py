#!/usr/bin/env python

from time import sleep
import random
from doltpy.core import Dolt, clone_repo
import os

def fetch_bad_words_repo():
    clone_dir = 'bad-words-clone'

    # Make directory to hold Dolt repo if it doesn't exist
    if os.path.exists(clone_dir) == False:
        os.mkdir(clone_dir)
    dir = os.listdir(clone_dir)

    # If the Dolt repo is empty, clone it
    if len(dir) == 0:
        print("Cloning bad-words repo...")
        os.chdir(clone_dir)
        clone_repo("Liquidata/bad-words")
        print("Done cloning.")
        os.chdir("../")
        
    # Otherwise, pull the latest version
    else:
        repo = Dolt(clone_dir)
        print("Pulling latest bad-words...")
        repo.pull()
        print("Done pulling.")
    
    return Dolt(clone_dir) 


def censor_text(text):
    censored = False
    censored_text = text
    for _, row in bad_words_df.iterrows():
        bad_word = row['bad_word'].lower()
        # If `bad_word` exists as a substring of `text`, replace the substring with asterisks
        if text.find(bad_word) > -1:
            censored_text = censored_text.replace(bad_word, '*'*len(bad_word))
            censored = True
    return censored_text, censored

responses = ['Cool', 'Sounds good', 'Thanks', 'Thank you', 'Okay...', 'I guess', 'Great', 'Good job', 'Congratulations', 'Wow', 'Sick', '👍','🤙', "I don't care", "Whatever", "Sure"]
repo = fetch_bad_words_repo()
KEEP_CHATTING = True

on_load_text = "\n Hello! This is a simple chat bot with profanity filter. \n Respond 'bye', or use CTRL+C to exit. \n You can type anything you want, and I will censor the bad words.\n Say something: \n"
print(on_load_text)

while KEEP_CHATTING:
    bad_words_df = repo.read_table('bad_words')
    user_response = input("> Me: ")
    if user_response.lower() == "bye":
        print("> ChatBot: Thanks for chatting!")
        KEEP_CHATTING = False
    else:
        censored_text, censored = censor_text(user_response.lower())
        if censored == True:
           print("> ChatBot sees:", censored_text)
        print("> ChatBot:",random.choice(responses))
        