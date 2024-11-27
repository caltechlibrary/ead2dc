secrets = __import__('secrets')

from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

n, found, not_found = 0, 0, 0

for obj in client.get_paged('repositories/2/digital_objects'):
    print(obj['uri'])
    for linked_instance in obj['linked_instances']:
        if linked_instance['ref'][:33] == '/repositories/2/archival_objects/':
            print('-->>', linked_instance['ref'])
            found += 1
        else:
            print('not found')
            not_found += 1
    
    print('links found:', found)
    print('not found:', not_found)
    print('total:', n)
          
print(n)
