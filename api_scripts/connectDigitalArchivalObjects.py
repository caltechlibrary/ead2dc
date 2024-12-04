secrets = __import__('secrets')

from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

links = dict()

for obj in client.get_paged('/repositories/2/digital_objects'):
    items = list()
    for linked_instance in obj['linked_instances']:
        if linked_instance['ref'][:33] == '/repositories/2/archival_objects/':
            items.append(linked_instance['ref'])
    links[obj['uri']] = items

print(links)
    
        
