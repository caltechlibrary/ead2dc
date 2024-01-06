# aspace.py
# functions for accessing the ASpace API

from pathlib import Path
import json
import time

# read config file
with open(Path(Path(__file__).resolve().parent).joinpath('config.json'), "r") as f:
    config = json.load(f)

from asnake.client import ASnakeClient
client = ASnakeClient(baseurl=config['ASPACE_API_URL'],
                      username=config['ASPACE_USERNAME'],
                      password=config['ASPACE_PASSWORD'])

def update_collections():
    # searches for digital content and returns (n, len(colls), colls, delta)
    #       n = number of digital objects found
    #       len(colls) = number of collections with digital objects
    #       colls = list collections (title, number, number of dig. objs.)
    #       time elapsed
    client.authorize()

    start = time.time()
    n = 0
    colls = dict()

    for obj in client.get_paged('repositories/2/digital_objects'):
        for c in obj['collection']:
            if c['ref'][16:26] != 'accessions':
                if c['ref'] in colls.keys():
                    colls[c['ref']] = colls[c['ref']] + 1
                else:
                    colls[c['ref']] = 1
                n += 1

    out = list()

    for key in colls:
        out.append(client.get(key).json()['title']+' (coll. numb.: '+key[26:]+', count: '+str(colls[key])+')')

    for el in out:
        print(el)
    #print()
    #print('number of digital objects:', n)
    #print('number of collections:', len(colls))

    end = time.time()
    delta = end - start
    #print('time:', delta, 'seconds')
    return (n, len(colls), out.sort(), round(delta))
