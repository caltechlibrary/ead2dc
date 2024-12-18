secrets = __import__('secrets')

from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()
links1, links2 = dict(), dict()
archival_objects = set()
collections = set()
items = dict()
# iterate over digital objects
for obj in client.get_paged('/repositories/2/digital_objects'):
    # if there is a value for 'collection' add that value to the collections set
    if obj.get('collection'):
        coll = obj['collection'][0]['ref']
        if coll[:26] == '/repositories/2/resources/':
            collections.add(coll)
            # iterate over the linked instances
            for linked_instance in obj['linked_instances']:
                if linked_instance['ref'][:33] == '/repositories/2/archival_objects/':
                    # build dictionary of collections and archival objects
                    if items.get(coll[26:]):
                        items[coll[26:]].add(linked_instance['ref'][33:])
                    else:
                        items[coll[26:]] = {linked_instance['ref'][33:]}
#            links1[obj['uri']] = items

for collection in collections:
    print(collection)

print(items)

for collid in items.keys():
    print(collid)
'''
for archival_object in archival_objects:
    links2[archival_object[33:]] = set()

for digital_object, archival_objects in links1.items():
    for archival_object in archival_objects:
        links2[archival_object[33:]].add(digital_object[32:])

for archival_object_id in links2:
    links2[archival_object_id] = list(links2[archival_object_id])

#print(links2)

print('colls not found:', coll_not_found1, coll_not_found2)
 
'''




    
        
