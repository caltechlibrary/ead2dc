# -*- coding: utf-8 -*-
#
# dash-build.py
#
# Builds data for dashboard
# Data source is ArchivesSpace API

import time
import sqlite3 as sq
import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from asnake.client import ASnakeClient

# FUNCTIONS

# MAIN

start = time.time()

# db location
print('Reading database location...')
dbpath = Path(Path(__file__).resolve().parent).joinpath('../instance/ead2dc.db')

# establish API connection
print('Establishing API connection...')
secrets = __import__('secrets')
client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)
client.authorize()

# initialize collections dictionary
# this dictionary references archival objects with related digital objects
collections_dict = dict()

# initialize collection and archival object sets
# contain collections and archival objects with related digital objects
collections, archival_objects = set(), set()

dao_count = 0

print('Finding digital content...')


numb_do = 0 # number of digital objects
numb_ao = 0 # number of archival objects

# iterate over digital objects
for obj in client.get_paged('/repositories/2/digital_objects'):
    numb_do += 1
    li = obj.get('linked_instances', 0)
    if li:
        print(li)
print('Number of digital objects:', numb_do)
'''    print(obj['uri'], obj['linked_instances'][0]['ref'])

    try:
        print('-->', obj['collection'][0]['ref'])
    except:
        print('--> None')
    try:
        print('---->', obj['linked_instances'][0]['ref'])
    except:
        print('----> None')
        '''