secrets = __import__('secrets')

from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

n, zero, found, not_found, multiple = 0, 0, 0, 0, 0

for obj in client.get_paged('repositories/2/digital_objects'):
    linked_instances = obj['linked_instances']
    if len(linked_instances) == 0:
        zero += 1
    elif len(linked_instances) > 1:
        multiple += 1
    for linked_instance in linked_instances:
        if linked_instance['ref'][:33] == '/repositories/2/archival_objects/':
            #print('-->', linked_instance['ref'])
            found += 1
        else:
            print('not found')
            not_found += 1

        n += 1
    
print('links found:', found)
print('not found:', not_found)
print('no links:', zero)
print('multiple links:', multiple)
print('total:', n)
        
