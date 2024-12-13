secrets = __import__('secrets')

import json
from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

route = '/repositories/2/archival_objects/74627'

obj = client.get(f'{route}?resolve[]=tree').json()

print(json.dumps(obj, indent=4, sort_keys=True))
