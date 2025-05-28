# -*- coding: utf-8 -*-
#
# resources.py
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
resources = set()
resources_dict = dict()

print('Reading resources...')
for obj in client.get_paged('/repositories/2/resources'):
    resources.add(obj.get('uri'))
print('Found', len(resources), 'resources')

resources = list(resources)

for uri in resources:
    obj = client.get(uri)
    print(obj['title'])
    #resources_dict[obj['uri']] = {'title': obj['title']}
end = time.time()
print('Elapsed time:', round(end - start, 2), 'seconds')
print(resources_dict)



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
