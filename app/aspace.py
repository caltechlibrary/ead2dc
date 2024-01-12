# aspace.py
# functions for accessing the ASpace API

from pathlib import Path
import json
import time

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

def update_collections(ids):

    # ids is list of coll ids to include in harvesting
    # searches for digital content and returns (n, len(colls), colls, delta)
    #       n = number of digital objects found
    #       len(colls) = number of collections with digital objects
    #       colls = list collections (title, number, number of dig. objs.)
    #       time elapsed

    client.authorize()

    start = time.time()
    n = 0
    colls = dict()

    # iterate over digital objects
    for obj in client.get_paged('repositories/2/digital_objects'):
        # select published objects only
        if obj['publish'] == True:
            # iterate over collection references (usually only one)
            for c in obj['collection']:
                # filter out accession records
                if c['ref'][16:26] != 'accessions':
                    # use object reference as key
                    if c['ref'] in colls.keys():
                        # if the collection is already in colls, increment
                        colls[c['ref']] = colls[c['ref']] + 1
                    else:
                        # otherwise add reference to collection
                        colls[c['ref']] = 1
                    # increment overall count of do's
                    n += 1

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

    # function for sorting by number of do's
    def sortfunc(e):
        return e[2]
    # sort in place
    out.sort(reverse=True, key=sortfunc)
    
    # elapsed time
    end = time.time()
    delta = end - start
    
    # return total number of do's, number of collections, a list of collections [coll id, title, no. of do's, incl], elapsed time
    return (n, len(colls), out, round(delta))


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

        description = description + ' (' + note_type + ') ' + ' '.join(note_list)

    return description
