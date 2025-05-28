# -*- coding: utf-8 -*-
#
# resources.py
#
# Builds data for dashboard
# Data source is ArchivesSpace API

import time
import csv
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
with open('accessions.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['uri', 'title', 'publish', 'restrictions', 'repository_processing_note', 'ead_id', 'finding_aid_title', 'finding_aid_filing_title', 'finding_aid_date', 'finding_aid_author', 'created_by', 'last_modified_by', 'create_time', 'system_mtime', 'user_mtime', 'suppressed', 'is_slug_auto', 'id_0', 'level', 'resource_type', 'finding_aid_description_rules', 'finding_aid_language', 'finding_aid_script', 'finding_aid_status', 'jsonmodel_type']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for obj in client.get_paged('/repositories/2/accessions'):
        writer.writerow({fieldname: obj.get(fieldname)for fieldname in fieldnames})

print('Found', len(resources), 'resources')


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
