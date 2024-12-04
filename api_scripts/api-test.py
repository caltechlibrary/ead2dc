secrets = __import__('secrets')

from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

#To get a single object:
print(client.get('/repositories/2/archival_objects/74627').json())

print('------------------------')

#Tp get all objects:
for obj in client.get_paged('repositories/2/digital_objects'):
    print(obj)
