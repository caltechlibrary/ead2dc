secrets = __import__('secrets')

from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

links1, links2 = dict(), dict()
archival_objects = set()

coll_not_found1, coll_not_found2 = 0, 0
for obj in client.get_paged('/repositories/2/digital_objects'):
    coll1 = obj.get('collection', 'not found')
    if coll1 == 'not found':
        coll_not_found1 += 1
    items = set()
    for linked_instance in obj['linked_instances']:
        if linked_instance['ref'][:33] == '/repositories/2/archival_objects/':
            coll2 = linked_instance.get('collection', 'not found')
            if coll2 == 'not found':
                coll_not_found2 += 1
            items.add(linked_instance['ref'])
            archival_objects.add(linked_instance['ref'])
    links1[obj['uri']] = items

print(links1)

for archival_object in archival_objects:
    links2[archival_object[33:]] = set()

for digital_object, archival_objects in links1.items():
    for archival_object in archival_objects:
        links2[archival_object[33:]].add(digital_object[32:])

for archival_object_id in links2:
    links2[archival_object_id] = list(links2[archival_object_id])

print(links2)

print('colls not found:', coll_not_found1, coll_not_found2)

    





    
        
