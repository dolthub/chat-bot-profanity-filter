#!/usr/bin/env python

import random
from doltpy.core import Dolt, clone_repo
import mysql.connector
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

EXIT_STR = "bye"

BAD_WORDS_TABLE = "bad_words"
LANGUAGES_TABLE = "languages"
NEW_BAD_WORD_STR = "!youcantsaythat!"

NEW_BAD_WORD_QUERY = '''INSERT INTO bad_words (language_code, bad_word) 
VALUES ('%s','%s');'''

COMMIT_QUERY = '''UPDATE dolt_branches 
SET hash=commit('%s') 
WHERE name = 'master';'''

CHANGE_QUERY = '''SELECT to_bad_word, to_language_code, from_bad_word, from_language_code
FROM dolt_diff_bad_words 
WHERE to_commit='WORKING';'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote-name',
                        default='Liquidata/bad-words',
                        help='The DoltHub remote from which to pull a set of bad words')
    parser.add_argument('--checkout-dir',
                        default='bad-words',
                        help='The local directory to clonet the remote too')
    args = parser.parse_args()

    # Read in bad words
    repo = clone_or_pull_latest(args.remote_name, args.checkout_dir)
    repo.start_server()

    cnx = mysql.connector.connect(user="root", host="127.0.0.1", port=3306, database="bad_words")
    cnx.autocommit = False

    bad_words_df = repo.read_table(BAD_WORDS_TABLE)
    languages_df = repo.read_table(LANGUAGES_TABLE)
    language_codes = {x: True for x in languages_df['language_code']}

    try:
        # Enter chat loop
        chat_loop(repo, cnx, bad_words_df, language_codes)
    finally:
        commit_new_bad(repo, cnx)


def chat_loop(repo, cnx, bad_words_df, language_codes):
    """
    Maintains a censored conversation with the user
    :param repo:
    :param cnx:
    :param bad_words_df:
    :param language_codes:
    :return:
    """
    print(ON_LOAD_TEXT)
    keep_chatting = True
    while keep_chatting:
        try:
            user_response = input("> Me: ")
        except KeyboardInterrupt:
            user_response = EXIT_STR

        user_resp_lwr = user_response.lower()
        if user_resp_lwr == EXIT_STR:
            print("> ChatBot: Thanks for chatting!")
            keep_chatting = False
        elif user_resp_lwr.startswith(NEW_BAD_WORD_STR):
            new_bad = user_resp_lwr[len(NEW_BAD_WORD_STR):].strip()
            process_new_bad(repo, cnx, language_codes, new_bad)
        else:
            censored_text, censored = censor_text(user_resp_lwr, bad_words_df)
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


def process_new_bad(repo, cnx, language_codes, new_bad):
    """
    processes user input corresponding to a new bad word that should be added to the database
    :param repo:
    :param cnx:
    :param language_codes:
    :param new_bad:
    :return:
    """

    if len(new_bad) != 0:
        words = new_bad.split()
        if len(words) == 2:
            language_code, bad_word = words[0], words[1]
            if language_code in language_codes:
                add_bad_word(repo, cnx, language_code, bad_word)
                print("> ChatBot: New bad word '%s' will be reviewed." % bad_word)
            else:
                print("> ChatBot: Unknown language code '%s' talk to the admin about adding it." % language_code)
        else:
            print("> ChatBot: Usage '%s <LANGUAGE_CODE> <WORD>'" % NEW_BAD_WORD_STR)
    else:
        print("> ChatBot: Usage '%s <LANGUAGE_CODE> <WORD>'" % NEW_BAD_WORD_STR)


def add_bad_word(repo, cnx, language_code, word):
    """
    writes a new entry into the bad_word table
    :param repo:
    :param cnx:
    :param language_code:
    :param word:
    :return:
    """
    query_str = NEW_BAD_WORD_QUERY % (language_code, word)
    repo.query_server(query_str, cnx)


def commit_new_bad(repo, cnx):
    """
    checks to see if any new bad words were added during the session. If there are the user will
    be prompted for a commit message for a new commit written to master.
    :param repo:
    :param cnx:
    :return:
    """
    cursor = repo.query_server(CHANGE_QUERY, cnx)
    new_words = {row[0]: row[1] for row in cursor}

    if len(new_words) > 0:
        print('> ChatBot: %d new words added.' % len(new_words))

        for word, language_code in new_words.items():
            print("\tword: %16s, language code: %s" % (word, language_code))

        print('> Chatbot: Add a description for these changes.')

        commit_msg = input("> Me: ")
        commit_query = COMMIT_QUERY % commit_msg
        repo.query_server(commit_query, cnx)


if __name__ == '__main__':
    main()
