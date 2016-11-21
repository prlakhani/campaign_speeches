#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import re
import os

"""Gets text of speeches from presidential elections"""

app_url = "http://www.presidency.ucsb.edu/"

def get_available_elections():
    """Gets dict like {election year: election url} for all available elections"""

    docs_url = app_url + "index_docs.php"
    docs_page = requests.get(docs_url)
    docs_content = BeautifulSoup(docs_page.text, 'html.parser')

    elections_title = docs_content.find('span', class_='doctitle',
            string="Documents Related to Presidential Elections")

    elections_available_list = elections_title.parent.ul.select('li')

    election_links = {election.text.replace(' Election',''):
            app_url + election.a.get('href')
            for election in elections_available_list}

    return election_links


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
        speech_id = re.search('\?pid=(?P<pid>[0-9]+)$', link).group('pid')
        # Only re-download (and more importantly, append to all_speeches) if
        # this has not already been done for this file. Assumes files don't
        # change over time (better transcriptions, etc.).
        if not os.path.isfile(os.path.join(candidate_path, speech_id + '.txt')):
            speech_page = requests.get(link)
            speech_content = BeautifulSoup(speech_page.text, 'html.parser')
            speech_title = speech_content.select_one('span.paperstitle').text
            speech_date = speech_content.select_one('span.docdate').text
            speech = speech_content.select_one('span.displaytext').text
            with open(os.path.join(candidate_path, speech_id + '.txt'), 'w') as f:
                f.write(os.linesep.join([speech_title, speech_date, speech]))
            # unclear given the size of these writes whether keeping all speech text
            # in a giant string and writing to all_speeches.txt  once, or
            # continually opening and appending to a running file is better. The
            # latter is slower, but safer if errors occur during this loop.
            with open(os.path.join(candidate_path, 'all_speeches.txt'), 'a') as fall:
                fall.write(speech + os.linesep)


def main(args):
    elections = get_available_elections()
    election_year = str(args.year)
    if election_year not in elections:
        year_options = "Your options are: {}".format(
                ", ".join(sorted(elections.keys())))
        raise ValueError("No speeches for this year. "+year_options)

    candidates = get_candidate_speech_links(elections[election_year])
    candidate_name = None
    candidate_url = None
    search_string = args.candidate.strip()

    while not search_string:
        # prompt for candidate based on available ones
        prompt = "Pick a candidate from {}: ".format(
                election_year, ", ".join(candidates.keys()))
        search_string = input(prompt)

    while not candidate_name:
        # try to match search string
        search_matches = [candidate for candidate in candidates
                if search_string.lower() in candidate.lower()]

        if not search_matches:
            prompt = ("Sorry, no matches to your candidate search string. "
                    "It must be one of {}: ".format(", ".join(candidates.keys())))
            search_string = input(prompt)
        elif len(search_matches) > 1:
            prompt = ("Multiple candidates match your search string: {}. "
                    "Please enter a more specific search string: ".format(
                        ", ".join(search_matches)))
            search_string = input(prompt)
        else:
            candidate_name = search_matches[0]
            candidate_url = candidates[candidate_name]

    save_candidate_speeches(candidate_name, candidate_url, election_year)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Save speech transcripts given an election year and candidate")
    parser.add_argument('-y', '--year', type=int, required=True,
            help="Election year from which to scrape speech transcripts")
    parser.add_argument('-c', '--candidate', type=str,
            help="Candidate name search string. Remember to quote if it has spaces")
    args = parser.parse_args()
    main(args)
