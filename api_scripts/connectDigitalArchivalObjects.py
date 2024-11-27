secrets = __import__('secrets')

from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

for obj in client.get_paged('repositories/2/digital_objects'):
    linked_instances = obj['linked_instances']
    for linked_instance in linked_instances:
        if linked_instance[:33] == '/repositories/2/archival_objects/'
        print(linked_instance['ref'])
    
        
