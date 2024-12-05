secrets = __import__('secrets')

from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

links1, links2 = dict(), dict()
archival_objects = set()

for obj in client.get_paged('/repositories/2/digital_objects'):
    items = set()
    for linked_instance in obj['linked_instances']:
        if linked_instance['ref'][:33] == '/repositories/2/archival_objects/':
            items.add(linked_instance['ref'])
            archival_objects.add(linked_instance['ref'])
    links1[obj['uri']] = items

print(links1)

for archival_object in archival_objects:
    links2[archival_object] = set()

for digital_object, archival_objects in links1.items():
    for archival_object in archival_objects:
        links2[archival_object].add(digital_object)

for archival_object in links2:
    links2[archival_object] = list(links2[archival_object])

print(links2)

    





    
        
