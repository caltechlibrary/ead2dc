# aspace.py
# functions for accessing the ASpace API

from pathlib import Path
from collections import defaultdict
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

from asnake.client import ASnakeClient
client = ASnakeClient(baseurl=config['ASPACE_API_URL'],
                      username=config['ASPACE_USERNAME'],
                      password=config['ASPACE_PASSWORD'])

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
                    uri = file_version['file_uri']
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

        if description == '' and note_type == 'abstract':
            description = ' '.join(note_list)
        elif description == '' and note_type == 'scopecontent':
            description = ' '.join(note_list)

        #description = description + ' (' + note_type + ') ' + ' '.join(note_list)

    return description

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
    
