secrets = __import__('secrets')

import json, argparse
from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

# Initialize parser
parser = argparse.ArgumentParser()
parser.add_argument('-o', '--object_type', default='')
parser.add_argument('-i', '--identifier', default='')
parser.add_argument('-r', '--resolve_linked_instances', default='')

# Read arguments from command line
args = parser.parse_args()
object_type = args.object_type
identifier = int(args.identifier)

proceed = True

if object_type not in ['digital', 'archival', 'resource']:
    print('Invalid arguments. Must provide object type ("digital", "archival", or "resource").')
    proceed = False

if identifier == 0:
    print('Invalid arguments. Must provide an identifier.')
    proceed = False

if object_type == 'digital':
    uri = f'/repositories/2/digital_objects/'
elif object_type == 'archival': 
    uri = f'/repositories/2/archival_objects/'
elif object_type == 'resource':
    uri = f'/repositories/2/resources/'
else:
    proceed = False

if proceed:

    obj = client.get(f'{uri}{identifier}?resolve[]=linked_instances').json()
    print(json.dumps(obj, indent=4, sort_keys=True))

'''

uri = '/repositories/2/digital_objects/8889'
uri = '/repositories/2/digital_objects/27551'
uri = '/repositories/2/archival_objects/74627'
uri = '/repositories/2/resources/219'
'''