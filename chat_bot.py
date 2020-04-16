#!/usr/bin/env python

import random
from doltpy.core import Dolt, clone_repo
import os
import argparse

ON_LOAD_TEXT = '''
Hello! This is a simple chat bot with profanity filter.
Respond 'bye', or use CTRL+C to exit.
You can type anything you want, and I will censor the bad words.
Say something
'''
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('remote_name', help='The DoltHub remote from which to pull a set of bad words')
    parser.add_argument('checkout_dir', help='The local directory to clone the remote to')
    args = parser.parse_args()

    # Read in bad words
    repo = clone_or_pull_latest(args.remote_name, args.checkout_dir)
    bad_words_df = repo.read_table('bad_words')

    # Enter chat loop
    chat_loop(bad_words_df)


def chat_loop(bad_words_df):
    """
    Maintains a censored conversation with the user
    :param bad_words_df:
    :return:
    """
    print(ON_LOAD_TEXT)
    keep_chatting = True
    while keep_chatting:
        user_response = input("> Me: ")
        if user_response.lower() == "bye":
            print("> ChatBot: Thanks for chatting!")
            keep_chatting = False
        else:
            censored_text, censored = censor_text(user_response.lower(), bad_words_df)
            if censored:
                print("> ChatBot sees:", censored_text)
            print("> ChatBot:", random.choice(RESPONSES))


def clone_or_pull_latest(remote_name, checkout_dir):
    """
    Clones the remote to the specified location if checkout_dir/.dolt does not exist, pulls the latest otherwise
    :param remote_name:
    :param checkout_dir:
    :return:
    """
    if os.path.exists(checkout_dir):
        repo = Dolt(checkout_dir)
        repo.pull()
        return repo
    else:
        return clone_repo(remote_name, checkout_dir)


def censor_text(text, bad_words_df):
    """
    Given the string text, uses the bad_words_df['bad_words'] to censor text, returns
    :param text:
    :param bad_words_df:
    :return:
    """
    censored = False
    censored_text = text
    for bad_word in bad_words_df['bad_word']:
        # If `bad_word` exists as a substring of `text`, replace the substring with asterisks
        if text.find(bad_word) > -1:
            censored_text = censored_text.replace(bad_word, '*'*len(bad_word))
            censored = True
    return censored_text, censored


if __name__ == '__main__':
    main()