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

i = 0
for resource in client.get_paged('repositories/2/archival_objects'):
    i += 1
print(i)

#print(resource['title'], resource['level'], resource['uri'], resource['resource'])
#for ancestor in resource['ancestors']:
#    ref = client.get(ancestor['ref']).json()
#    print(ref['title'], ref['level'], ref['uri'], resource['resource'])
