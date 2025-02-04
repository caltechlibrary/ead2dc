from app.db import get_db

from pathlib import Path
from datetime import datetime
import json

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

