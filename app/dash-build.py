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

#start = time.time()

# db location
#print('Reading database location...')
#dbpath = Path(Path(__file__).resolve().parent).joinpath('../instance/ead2dc.db')

# establish API connection
print('Establishing API connection...')
secrets = __import__('secrets')
client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)
client.authorize()

# initialize resources, archival object, and digital object sets
resources, accessions, archival_objects, digital_objects = set(), set(), set(), set()

dao_count = 0

print('Finding digital content...')

numb_do = 0 # number of digital objects
numb_ao = 0 # number of archival objects
numb_ac = 0 # number of accessions
numb_re = 0 # number of resources

linked_dict = dict()
collections_dict = dict()

# iterate over digital objects
for obj in client.get_paged('/repositories/2/digital_objects'):
    numb_do += 1
    n = len(obj.get('linked_instances', []))
    m = len(obj.get('collection', []))
    if linked_dict.get(n):
        linked_dict[n] += 1
    else:
        linked_dict[n] = 1
    if collections_dict.get(m):
        collections_dict[m] += 1
    else:
        collections_dict[m] = 1

print(numb_do, 'digital objects found')
print(dict(sorted(linked_dict.items())), 'digital objects with linked instances')
print(dict(sorted(collections_dict.items())), 'digital objects with collections')

for obj in client.get_paged('/repositories/2/digital_objects'):
    digital_objects.add(obj.get('uri'))

for obj in client.get_paged('/repositories/2/archival_objects'):
    archival_objects.add(obj.get('uri'))

for obj in client.get_paged('/repositories/2/resources'):
    resources.add(obj.get('uri'))

for obj in client.get_paged('/repositories/2/accessions'):
    accessions.add(obj.get('uri'))
'''
    n = len(obj.get('linked_instances', []))
    if n > 2:
        print(obj.get('uri'), 'is linked to', n, 'instances:')
        for o in obj.get('linked_instances', []):
            print('                    ', o.get('ref'))

    m = len(obj.get('collection', []))
    if m > 2:
        print(obj.get('uri'), 'is associated with', m, 'collections:')
        for o in obj.get('collection', []):
            print('                    ', o.get('ref'))
'''
print('Found', len(digital_objects), 'digital objects')
print('Found', len(archival_objects), 'archival objects')
print('Found', len(resources), 'resources')
print('Found', len(accessions), 'accessions')