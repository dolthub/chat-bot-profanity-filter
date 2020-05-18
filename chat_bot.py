#!/usr/bin/env python

import os
import random
import argparse
import mysql.connector

from doltpy.core import Dolt, clone_repo

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
NEW_BAD_WORD_STR = "!bad!"

NEW_BAD_WORD_QUERY = '''INSERT INTO bad_words (language_code, bad_word) 
VALUES ('%s','%s');'''

CHANGE_QUERY = '''SELECT to_bad_word, to_language_code, from_bad_word, from_language_code
FROM dolt_diff_bad_words 
WHERE to_commit='WORKING';'''

BAD_WORDS_QUERY = '''SELECT bad_word
FROM bad_words;'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote-name',
                        default='Liquidata/bad-words',
                        help='The DoltHub remote from which to pull a set of bad words')
    parser.add_argument('--checkout-dir',
                        default='bad-words',
                        help='The local directory to clone the remote too')
    args = parser.parse_args()

    # Read in bad words
    repo = clone_or_pull_latest(args.remote_name, args.checkout_dir)
    repo.start_server()

    cnx = None

    try:
        cnx = mysql.connector.connect(user="root", host="127.0.0.1", port=3306, database="bad_words")
        cnx.autocommit = True

        languages_df = repo.read_table(LANGUAGES_TABLE)
        language_codes = {x: True for x in languages_df['language_code']}

        # Enter chat loop
        chat_loop(repo, cnx, language_codes)
    finally:
        commit_new_bad_and_stop_server(repo, cnx)


def chat_loop(repo, cnx, language_codes):
    """
    Maintains a censored conversation with the user
    :param repo:
    :param cnx:
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
            censored_text, censored = censor_text(user_resp_lwr, repo, cnx)
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


def censor_text(text, repo, cnx):
    """
    Given the string text, uses the bad_words_df['bad_words'] to censor text, returns
    :param text:
    :param repo:
    :param cnx:`
    :return:
    """
    cursor = repo.query_server(BAD_WORDS_QUERY, cnx)
    bad_words = {row[0]: True for row in cursor}

    censored = False
    censored_text = text
    for bad_word in bad_words.keys():
        bad_len = len(bad_word)
        pos = text.find(bad_word)
        # If `bad_word` exists as a substring of `text`, replace the substring with asterisks
        while pos != -1:
            censored_text = censored_text[0:pos] + '*'*bad_len + censored_text[pos+bad_len:]
            censored = True
            pos = text.find(bad_word, pos+1)

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


def commit_new_bad_and_stop_server(repo, cnx=None):
    """
    checks to see if any new bad words were added during the session. If there are the user will
    be prompted for a commit message for a new commit written to master.
    :param repo:
    :param cnx:
    :return:
    """
    try:
        if cnx is not None:
            cursor = repo.query_server(CHANGE_QUERY, cnx)
            new_words = {row[0]: row[1] for row in cursor}

            if len(new_words) > 0:
                print('> ChatBot: %d new words added.' % len(new_words))

                for word, language_code in new_words.items():
                    print("\tword: %16s, language code: %s" % (word, language_code))

                print('> Chatbot: Add a description for these changes.')

                commit_msg = input("> Me: ")

                repo.add_table_to_next_commit("bad_words")
                repo.commit(commit_msg)
    finally:
        repo.stop_server()


if __name__ == '__main__':
    main()
