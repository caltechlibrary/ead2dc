from pathlib import Path
import json

# read config file
with open(Path(Path(__file__).resolve().parent).joinpath('config.json'), "r") as f:
    config = json.load(f)

from asnake.client import ASnakeClient
client = ASnakeClient(baseurl=config['ArchivesSpace Credentials']['ASPACE_API_URL'],
                      username=config['ArchivesSpace Credentials']['ASPACE_USERNAME'],
                      password=config['ArchivesSpace Credentials']['ASPACE_PASSWORD'])
client.authorize()
repos=client.get('repositories').json()

print(client.get('schemas/sub_container').json())
print()
print(list(client.get('schemas').json().keys()))
print()
resource = client.get('repositories/2/archival_objects/106628').json()
print(resource)
print(resource['title'])
print(client.get('repositories/2/resources/219').json())
print()
#resources = list()
#i = 0
#for resource in client.get_paged('repositories/2/archival_objects'):
#    print(resource['title'])
#    resources.append(resource)
#    i += 1
#print(resources[:5])
#print(len(resources))
#print(i)
print('ancestors:', resource['ancestors'])
print('uri:', resource['uri'])
print('resource:', resource['resource'])