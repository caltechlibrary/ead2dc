secrets = __import__('secrets')

import json
from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

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
