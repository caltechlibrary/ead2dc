secrets = __import__('secrets')

from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

for obj in client.get_paged('repositories/2/digital_objects'):
    print(obj['uri'])
