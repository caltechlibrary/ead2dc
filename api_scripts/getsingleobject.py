secrets = __import__('secrets')

import json, sys, argparse
from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

args = sys.argv[1:]

if args[1] == 'digital':
    uri = f'/repositories/2/digital_objects/{args[2]}'
elif args[1] == 'archival':
    uri = f'/repositories/2/archival_objects/{args[2]}'
else args[1] == 'resource':
    uri = f'/repositories/2/resources/{args[2]}'

uri = '/repositories/2/digital_objects/8889'
#obj = client.get(f'{uri}?resolve[]=linked_instances').json()
obj = client.get(f'{uri}').json()
print(json.dumps(obj, indent=4, sort_keys=True))

'''
print()

uri = '/repositories/2/digital_objects/27551'
#obj = client.get(f'{uri}?resolve[]=linked_instances').json()
obj = client.get(f'{uri}').json()
for key in obj.keys():
    print(key)
print(json.dumps(obj, indent=4, sort_keys=True))

print()

uri = '/repositories/2/archival_objects/74627'
obj = client.get(f'{uri}?resolve[]=ancestors').json()
obj = client.get(f'{uri}').json()
for key in obj.keys():
    print(key)
print(json.dumps(obj, indent=4, sort_keys=True))

print()

uri = '/repositories/2/resources/219'
obj = client.get(f'{uri}').json()
print(json.dumps(obj, indent=4, sort_keys=True))
'''