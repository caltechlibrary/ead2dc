secrets = __import__('secrets')

from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

n, zero, one, multiple = 0, 0, 0, 0

for obj in client.get_paged('repositories/2/digital_objects'):
    linked_instances = obj['linked_instances']
    if len(linked_instances) == 0:
        zero += 1
    elif len(linked_instances) == 1:
        one = +1
    elif len(linked_instances) > 1:
        multiple += 1
        for linked_instance in linked_instances:
            print('-->', linked_instance['ref'])

    print('--------------------')
    n += 1
    
print('links found:', found)
print('not found:', not_found)
print('no links:', zero)
print('multiple links:', multiple)
print('total:', n)
        
