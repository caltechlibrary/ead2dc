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
client.authorize()

start = time.time()
print(start)

#i = 0
#for resource in client.get_paged('repositories/2/archival_objects'):
#    i += 1
#print(i)

#print(resource['title'], resource['level'], resource['uri'], resource['resource'])
#for ancestor in resource['ancestors']:
#    ref = client.get(ancestor['ref']).json()
#    print(ref['title'], ref['level'], ref['uri'], resource['resource'])

n = 0
colls = dict()
for obj in client.get_paged('repositories/2/digital_objects'):
    try:
        for c in obj['collection']:
            if c['ref'][16:26] != 'accessions':
                if c['ref'] in colls.keys():
                    colls[c['ref']] = colls[c['ref']] + 1
                else:
                    colls[c['ref']] = 1
                n += 1
    except:
        try:
            c = obj['resource']['ref']
            if c['ref'][16:26]!='accessions':
                if c['ref'] in colls.keys():
                    colls[c['ref']] = colls[c['ref']] + 1
                else:
                    colls[c['ref']] = 1
                n += 1
        except:
            print('failed')
for key in colls:
    print(client.get(key).json()['title'], '(coll. numb.:', key[26:] + ', count:', str(colls[key]) + ')')
print('number of digital objects:', n)
print('number of collections:', len(colls))

end = time.time()
delta = end - start
print('time:', delta, 'seconds')