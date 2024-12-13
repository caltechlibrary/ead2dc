secrets = __import__('secrets')

import json
from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

id = '8889'

obj = client.get(f'/repositories/2/digital_objects/'+id+'?resolve[]=parent').json()

print(json.dumps(obj, indent=4, sort_keys=True))
