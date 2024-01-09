# aspace.py
# functions for accessing the ASpace API

from pathlib import Path
import json
import time

# read config file
with open(Path(Path(__file__).resolve().parent).joinpath('config.json'), "r") as f:
    config = json.load(f)

from asnake.aspace import ASpace
from asnake.client import ASnakeClient
client = ASnakeClient(baseurl=config['ASPACE_API_URL'],
                      username=config['ASPACE_USERNAME'],
                      password=config['ASPACE_PASSWORD'])
client.authorize()

def update_collections(incl):
    # incl is list of coll ids to include in harvesting
    # searches for digital content and returns (n, len(colls), colls, delta)
    #       n = number of digital objects found
    #       len(colls) = number of collections with digital objects
    #       colls = list collections (title, number, number of dig. objs.)
    #       time elapsed
    #client.authorize()

    start = time.time()
    n = 0
    colls = dict()

    for obj in client.get_paged('repositories/2/digital_objects'):
        # selection published objects only
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
        if key[26:] in incl:
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

    aspace = ASpace()
    repo = aspace.repositories(2)

    for id in ids:
        file = repo.archival_objects(id)
        print (file.title)

    # return list of lists containing collection info
    #[collection['id'], collection['ead url'], collection['title'], collection['description']
    return
