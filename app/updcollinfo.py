#from app.aspace import update_collections, get_notes
#from app.oaidp import write_last_update
#from app.db import get_db

from pathlib import Path
from datetime import datetime
from collections import defaultdict
import sqlite3 as sq
import json
import time
import re

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

# db file location
dbpath = Path(Path(__file__).resolve().parent).joinpath('../instance/ead2dc.db')

from asnake.client import ASnakeClient
client = ASnakeClient(baseurl=config['ASPACE_API_URL'],
                      username=config['ASPACE_USERNAME'],
                      password=config['ASPACE_PASSWORD'])


# FUNCTIONS

# get collection info for a list of collection ids
def get_collectioninfo(ids):

    client.authorize()

    for id in ids:
        # initiate list of collections
        colls = list()
        # construct uri from id
        uri = '/repositories/2/resources/'+id
        # retrieve collection
        collection = client.get(uri)
        # construct url for ead
        ead_url = pub_url+'oai?verb=GetRecord&identifier='+cbase+id+'&metadataPrefix=oai_ead'
        # retrieve collection identifier, e.g. 'HaleGE'
        id_0 = collection.json()["id_0"]
        # retrieve title, e.g. 'George Ellery Hale Collection'
        title = collection.json()["title"]
        # retrieve notes dict
        notes = get_notes(id)
        k = notes.keys()
        description = notes[k]
        # assemble collection info as list
        coll_info = [id_0, ead_url, title, description]
        print(coll_info)
        colls.append(coll_info)

    # return list of lists containing collection info
    #[collection['id'], collection['ead url'], collection['title'], collection['description']
    
    return colls


# return domain of digital object
def url_domain(url):
    # remove spaces, split on '//', then split on '/' to find domain
    domain = re.split('/', re.split('//', url.replace(' ', ''))[1])[0]
    if 'archives.caltech.edu' in domain:
        return 'caltecharchives'
    elif 'archive.org' in domain:
        return 'internetarchive'
    elif 'library.caltech.edu' in domain:
        return 'caltechlibrary'
    elif 'resolver.caltech.edu' in domain:
        return 'caltechlibrary'
    elif 'data.caltech.edu' in domain:
        return 'caltechlibrary'
    elif 'youtube.com' in domain:
        return 'youtube'
    elif 'youtu.be' in domain:
        return 'youtube'
    else:
        return 'other'
    

# return formatted last_update
def get_last_update(fn):
    db = sq.connect(dbpath).cursor()
    query = 'SELECT dt FROM last_update WHERE fn=?;'
    last_update = db.execute(query, [fn]).fetchone()[0]
    dt = datetime.fromisoformat(last_update).strftime("%b %-d, %Y, %-I:%M%p")
    return dt

# write ISO last update; return formatted last_update (i.e. now)
def write_last_update(fn):
    db = sq.connect(dbpath).cursor()
    query = 'UPDATE last_update SET dt=? WHERE fn=?;'
    now = datetime.now()
    last_update = now.isoformat()
    db.execute(query, [last_update, fn])
    db.commit()
    dt = now.strftime("%b %-d, %Y, %-I:%M%p")
    return dt

def update_collections(ids):

    # ids is list of coll ids to include in harvesting
    # searches for digital content and returns (n, len(colls), colls, delta)
    #       docount = total number of published digital objects
    #       len(colls) = number of collections with digital objects
    #       colls = list collections (title, number, number of dig. objs., 5 domain categories)
    #       domains are:
    #           'archives.caltech.edu' -> 'caltecharchives'
    #           'library.caltech.edu' -> 'caltechlibrary'
    #           'archive.org' -> 'internetarchive'
    #           'youtube.com' -> 'youtube'
    #           'other'
    #       time elapsed

    client.authorize()

    start = time.time()

    colls = dict()

    archival_ids, digitalobject_ids = set(), set()

    totals = {'total'           : 0, 
              'caltecharchives' : 0, 
              'caltechlibrary'  : 0, 
              'internetarchive' : 0, 
              'youtube'         : 0, 
              'other'           : 0}

    # iterate over digital objects in all collections
    for obj in client.get_paged('repositories/2/digital_objects'):
        # select published objects only
        if obj['publish'] and not obj['suppressed']:
            # iterate over file versions in object record
            counted = False
            for file_version in obj['file_versions']:
                # published versions only
                if file_version['publish']:
                    # http and https links only
                    uri = file_version['file_uri'].strip()
                    if uri[:4]=='http':
                        # iterate over collection references (usually only one)
                        for collectionid in obj['collection']:
                            # filter out accession records
                            if collectionid['ref'][16:26] != 'accessions' and not counted:
                                # use object reference as key
                                coll_id = collectionid['ref']
                                # if the collection is already in colls, increment
                                if coll_id in colls.keys():
                                    colls[coll_id]['docount'] += 1
                                # otherwise initialize count
                                else:
                                    colls[coll_id] = defaultdict(int)
                                    colls[coll_id]['docount'] = 1
                                totals['total'] += 1
                                counted = True
                                # identify/count domain
                                colls[coll_id][url_domain(uri)] += 1
                                totals[url_domain(uri)] += 1
                                digitalobject_ids.add(obj['uri'])
                                for ref in obj['linked_instances']:
                                    if '/repositories/2/archival_objects/' in ref['ref']:
                                        archival_ids.add(ref['ref'])

    # remove collections that are suppressed or not published
    for coll in colls:
        # set collection count to zero for suppressed or not published
        if client.get(coll).json()['suppressed'] or not client.get(coll).json()['publish']:
            colls[coll]['docount']=0
    # regenerate dict removing those with zero count
    colls = {key:val for key, val in colls.items() if val['docount'] != 0}
    # calculate total count
    docount = 0
    for coll in colls:
        docount += colls[coll]['docount']

    # create list for output
    out = list()

    # iterate over collections
    for key in colls:
        # test for inclusion
        if key[26:] in ids:
            i=1
        else:
            i=0
        # output tuples include id, title, do count, include T/F for each collection
        out.append((key[26:], client.get(key).json()['title'], colls[key], i))

    # sort in place, in reverse order by number of digital objects (i.e. 'colls[key]'docount')
    out.sort(key=lambda item: item[2]['docount'], reverse=True)
    
    # elapsed time
    end = time.time()
    delta = end - start
    
    # return total number of do's, number of collections, a list of collections [coll id, title, no. of do's, incl], elapsed time
    return (docount, len(colls), out, round(delta)), len(digitalobject_ids), len(archival_ids), totals


# read notes from collection; returns string
def get_notes(id):

    description = ''

    client.authorize()

    uri = '/repositories/2/resources/'+id
    collection = client.get(uri)

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

        #description = description + ' (' + note_type + ') ' + ' '.join(note_list)

    return description

# read collections data for display
def read_colls():
    query = "SELECT collno, colltitle, docount, carchives, clibrary, \
            iarchive, youtube, other, incl FROM collections ORDER BY docount DESC;"
    colls = sq.connect(dbpath).cursor().execute(query).fetchall()
    n = sum(k for (_,_,k,_,_,_,_,_,_) in colls)
    return (n, len(colls), colls)

# update collections json
def update_coll_json(ids):
    db = sq.connect(dbpath).cursor()
    # initialize dict for json output
    coll_dict = dict()
    query = "SELECT colltitle FROM collections WHERE collno=?;"
    for id in ids:
        coll_dict[id] = {'title' : db.execute(query, [id]).fetchone()[0],
                         'description' : get_notes(id),
                         'eadurl' : pub_url+'oai?verb=GetRecord&identifier=/'+cbase+id+'&metadataPrefix=oai_ead'}
    # save included collections to JSON file
    with open(Path(Path(__file__).resolve().parent).joinpath('collections.json'), 'w') as f:
        json.dump(coll_dict, f)
    return

# MAIN PROGRAM

db = sq.connect(dbpath).cursor()

# list of collections to include in OAI DP
# this is used to update incl field after update
incl = list() 
for e in db.execute('SELECT collno FROM collections WHERE incl=1;'):
    incl.append(e[0])

update_coll_json(incl)

# get data from ArchivesSpace as list
# output[0] = total number of do's
# output[1] = number of collections
# output[2] = a list of collections [coll id, title, stats(dict), incl]
# output[3] = elapsed time
output, digitalobject_count, archivalobject_count, totals = update_collections(incl) 

# update totals in db
#totals = {'total'           : , 
#          'caltecharchives' : , 
#          'caltechlibrary'  : , 
#          'internetarchive' : , 
#          'youtube'         : , 
#          'other'           : }
db.execute('DELETE FROM totals')
query='INSERT INTO totals(total,caltecharchives,caltechlibrary,internetarchive,youtube,other) \
        VALUES (?,?,?,?,?,?)'
db.execute(query, list(totals.values()))

# isolate collections info
colls=output[2]
    
# delete collections (easiest way to refresh data)
db.execute('DELETE FROM collections')

# insert updated data from ArchivesSpace into db
query = 'INSERT INTO collections(collno,colltitle,docount,carchives,clibrary,\
                    iarchive,youtube,other,incl) \
                    VALUES (?,?,?,?,?,?,?,?,?);'
for coll in colls:
    db.execute(query, [coll[0], coll[1], \
                coll[2]['docount'], coll[2]['caltecharchives'], coll[2]['caltechlibrary'], \
                coll[2]['internetarchive'], coll[2]['youtube'], coll[2]['other'], \
                coll[3]])
    
# update incl field
query = 'UPDATE collections SET incl=1 WHERE collno=?;'
for id in incl:
    db.execute(query, [id])

# commit changes
db.commit()
    
# record time of update
dt=write_last_update('col')