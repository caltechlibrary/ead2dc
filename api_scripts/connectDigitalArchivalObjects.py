secrets = __import__('secrets')

from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()
digital_objects = dict()
archival_objects = set()
collections = dict()

for obj in client.get_paged('/repositories/2/digital_objects'):
    items = set()
    coll = obj['collection'][0]['ref']
    for linked_instance in obj['linked_instances']:
        if linked_instance['ref'][:33] == '/repositories/2/archival_objects/':
            items.add(linked_instance['ref'])
            archival_objects.add(linked_instance['ref'])
    digital_objects[obj['uri']] = items
    if collections.get(coll):
        collections[coll] = [digital_objects[obj['uri']]]
    else:
        collections[coll].append(digital_objects[obj['uri']])
    

print(collections)
'''
for archival_object in archival_objects:
    links2[archival_object[33:]] = set()

for digital_object, archival_objects in links1.items():
    for archival_object in archival_objects:
        links2[archival_object[33:]].add(digital_object[32:])

for archival_object_id in links2:
    links2[archival_object_id] = list(links2[archival_object_id])

print(links2)

print('colls not found:', coll_not_found1, coll_not_found2)
''' 





    
        
