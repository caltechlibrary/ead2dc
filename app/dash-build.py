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
import pickle
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from asnake.client import ASnakeClient

# FUNCTIONS

# MAIN

start = time.time()

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

# iterate over digital objects
print('Reading digital objects...')
for obj in client.get_paged('/repositories/2/digital_objects'):
    digital_objects.add(obj.get('uri'))
print('Found', len(digital_objects), 'digital objects')

print('Reading archival objects...')
for obj in client.get_paged('/repositories/2/archival_objects'):
    archival_objects.add(obj.get('uri'))
print('Found', len(archival_objects), 'archival objects')

print('Reading resources...')
for obj in client.get_paged('/repositories/2/resources'):
    resources.add(obj.get('uri'))
print('Found', len(resources), 'resources')

print('Reading accessions...')
for obj in client.get_paged('/repositories/2/accessions'):
    accessions.add(obj.get('uri'))
print('Found', len(accessions), 'accessions')

digital_objects_dict = dict()
for uri in digital_objects:
    obj = client.get(uri)
    digital_objects_dict[obj['uri']] = {'collection': [], 'linked_instances': []}
    for o in obj['linked_instances']:
        digital_objects_dict[uri]['linked_instances'].append(o['ref'])
    for o in obj['collection']:
        digital_objects_dict['uri']['collection'].append(o['ref'])

end = time.time()
print('Elapsed time:', round(end - start, 2), 'seconds')



'''
linked_dict = dict()
collections_dict = dict()

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
'''

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
