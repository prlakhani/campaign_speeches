#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import re
import os

"""Gets text of speeches from presidential elections"""

app_url = "http://www.presidency.ucsb.edu/"

def get_available_elections():
    """Gets list of li tags of available elections"""

    docs_url = app_url + "index_docs.php"
    docs_page = requests.get(docs_url)
    docs_content = BeautifulSoup(docs_page.text, 'html.parser')

    elections_title = docs_content.find('span', class_='doctitle',
            string="Documents Related to Presidential Elections")

    elections_available_list = elections_title.parent.ul.select('li')

    return elections_available_list


def get_candidate_speech_links(election_url):
    """
    Gets dict like {candidate name: speech link} for all candidates in a
    given election
    """

    election_page = requests.get(election_url)
    election_content = BeautifulSoup(election_page.text, 'html.parser')

    # Get list of span tags with candidate names
    # TODO: find a better selector for the td, to avoid .parent.parent later
    candidate_names = election_content.select('td.doctext p span.roman')

    # Helper function to find tags with text including "campaign speeches"
    def find_speech_links(string):
        return string and 'campaign speeches' in string.lower()

    # Construct dict with keys of candidate names and vals of url
    candidate_links = {candidate.text: app_url + candidate.parent.parent.find(
        'a', string=find_speech_links).get('href')
        for candidate in candidate_names}

    return candidate_links


def save_candidate_speeches(candidate_name, candidate_url, election_year):
    """
    Given a url to a page with a list of links to speech transcripts, saves
    all such transcripts to a folder structure organized by election year and
    candidate. Also saves a single file with all speech text for that candidate.
    """

    candidate_page = requests.get(candidate_url)
    candidate_content = BeautifulSoup(candidate_page.text, 'html.parser')

    speech_links = [app_url + (link.get('href')[3:]) for link in
            candidate_content.select('td.listdate a')]

    # make sure we have a directory to which to save transcripts
    candidate_path = os.path.join(os.getcwd(), 'speeches', election_year, candidate_name)
    if not os.path.isdir(candidate_path):
        os.makedirs(candidate_path)

    # save transcripts and combined file
    for link in speech_links:
        speech_page = requests.get(link)
        speech_content = BeautifulSoup(speech_page.text, 'html.parser')
        speech_title = speech_content.select_one('span.paperstitle').text
        speech_date = speech_content.select_one('span.docdate').text
        speech = speech_content.select_one('span.displaytext').text
        speech_id = re.search('\?pid=(?P<pid>[0-9]+)$', link).group('pid')
        with open(os.path.join(candidate_path, speech_id + '.txt'), 'w') as f:
            f.write(os.linesep.join([speech_title, speech_date, speech]))
        # unclear given the size of these writes whether keeping all speech text
        # in a giant string and writing to all_speeches.txt  once, or
        # continually opening and appending to a running file is better. The
        # latter is slower, but safer if errors occur during this loop.
        with open(os.path.join(candidate_path, 'all_speeches.txt'), 'a') as fall:
            fall.write(speech + os.linesep)


def main():
    pass


if __name__ == '__main__':
    main()
