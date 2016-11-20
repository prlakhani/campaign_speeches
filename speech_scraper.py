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
    docs_content = BeautifulSoup(requests.get(docs_url).text, 'html.parser')

    elections_title = docs_content.find('span', class_='doctitle',
            string="Documents Related to Presidential Elections")

    elections_available_list = elections_title.parent.ul.find_all('li')

    return elections_available_list


def get_candidate_speech_links(election_url):
    """
    Gets dict like {candidate name: speech link} for all candidates in a
    given election
    """
    election_content = BeautifulSoup(requests.get(election_url).text,
            'html.parser')

    # Get list of span tags with candidate names
    # TODO: find a better selector for the td, to avoid .parent.parent later
    candidate_names = election_content.select('td.doctext p span.roman')

    # Helper function to find tags with text including "campaign speeches"
    def find_speech_links(string):
        return string and re.search('campaign speeches', string, flags=re.I)

    # Construct dict with keys of candidate names and vals of url
    candidate_links = {candidate.text: app_url+candidate.parent.parent.find(
        'a', string=find_speech_links).get('href')
        for candidate in candidate_names}
    
    return candidate_links
