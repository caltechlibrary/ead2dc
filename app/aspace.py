from app.db import get_db

from pathlib import Path
from datetime import datetime
import json, csv

# read config file
with open(Path(Path(__file__).resolve().parent).joinpath('config.json'), "r") as f:
    config = json.load(f)

# max number of records to return
maxrecs = config['MAXIMUM_RECORDS_RETURNED']
# data provider URL
dpurl = config['DATA_PROVIDER_URL']
# base uri
idbase = config['ID_BASE_URI'] 
# public url
pub_url = config['PUBLIC_URL']
# collection base
cbase = config['COLLECTION_BASE_URI']

from asnake.client import ASnakeClient
client = ASnakeClient(baseurl=config['ASPACE_API_URL'],
                      username=config['ASPACE_USERNAME'],
                      password=config['ASPACE_PASSWORD'])


def csv_gen(filename, fieldnames, category):

    client.authorize()

    rec_count = 0
    with open(Path(Path(__file__).resolve().parent).joinpath(filename), 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for obj in client.get_paged('/repositories/2/'+category):
            writer.writerow({fieldname: obj.get(fieldname)for fieldname in fieldnames})
            rec_count += 1

    return rec_count


# read notes from collection; returns string
def get_notes(id):

    description = ''

    client.authorize()

    uri = '/repositories/2/resources/'+id
    collection = client.get(uri)

    try:
        for note in collection.json()['notes']:
            note_type = note['type']
            note_list = list()
            if note['jsonmodel_type']=='note_multipart':
                try:
                    for subnote in note['subnotes']:
                        note_list.append(subnote['content'])
                except:
                    continue
            elif note['jsonmodel_type']=='note_singlepart':
                try:
                    for content in note['content']:
                        note_list.append(content)
                except:
                    continue
            else:
                continue

            if description == '' and note_type == 'abstract':
                description = ' '.join(note_list)
            elif description == '' and note_type == 'scopecontent':
                description = ' '.join(note_list)
    except:
        pass
            #description = description + ' (' + note_type + ') ' + ' '.join(note_list)
    return description

# return formatted last_update
def get_last_update(fn):
    db = get_db()
    query = 'SELECT dt FROM last_update WHERE fn=?;'
    last_update = db.execute(query, [fn]).fetchone()[0]
    dt = datetime.fromisoformat(last_update).strftime("%b %-d, %Y, %-I:%M%p")
    return dt

# write ISO last update; return formatted last_update (i.e. now)
def write_last_update(fn):
    db = get_db()
    query = 'UPDATE last_update SET dt=? WHERE fn=?;'
    now = datetime.now()
    last_update = now.isoformat()
    db.execute(query, [last_update, fn])
    db.commit()
    dt = now.strftime("%b %-d, %Y, %-I:%M%p")
    return dt

def get_json(category, id):
    client.authorize()
    uri = '/repositories/2/'+category+'/'+id
    obj = client.get(uri)
    return obj.json()

def get_ids(category):
    client.authorize()
    id_list = list()
    for obj in client.get_paged('/repositories/2/'+category):
        id = obj['uri'][obj['uri'].rfind('/')+1: ]
        id_list.append((id, obj['uri']))
    return id_list

def get_elements(element, category, id):
    elements = list()
    client.authorize()
    obj = get_json(category, id)
    for ref in obj.get(element, []):
        uri = ref.get('ref', None)
        if uri:
            elements.append(client.get(uri).json().get('title', ''))
    return elements



