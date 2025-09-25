# FUNCTIONS

from asnake.client import ASnakeClient

# establish API connection
print('Establishing API connection...')
secrets = __import__('secrets')
client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)
client.authorize()

# get_json, get_ids, get_subjects, get_extents, get_dates are also in aspace.py

def get_ids(category):
    client.authorize()
    id_list = list()
    for obj in client.get_paged('/repositories/2/'+category):
        id = obj['uri'][obj['uri'].rfind('/')+1: ]
        id_list.append((id, obj['uri']))
    return id_list

def get_json(category, id):
    client.authorize()
    uri = '/repositories/2/'+category+'/'+id
    obj = client.get(uri)
    return obj.json()

def get_subjects(category, id):
    subjects = list()
    client.authorize()
    obj = get_json(category, id)
    for ref in obj.get('subjects', []):
        uri = ref.get('ref', None)
        if uri:
            subjects.append(client.get(uri).json()['title'])
    return subjects

def get_dates(category, id):
    dates = list()
    client.authorize()
    obj = get_json(category, id)
    for date in obj.get('dates', []):
        dates.append(date.get('expression', ''))
    return dates

def get_extents(category, id):
    extents = list()
    client.authorize()
    obj = get_json(category, id)
    for extent in obj.get('extents', []):
        extents.append(extent.get('number', '') + ' ' + extent.get('extent_type', ''))
    return extents

