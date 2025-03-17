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

# Read arguments from command line
args = parser.parse_args()

proceed = True

if not isinstance(args.identifier, int) or args.object_type not in ['digital', 'archival', 'resource']:
    print(args.identifier, args.object_type)
    print(type(args.identifier), type(args.object_type))
    print('Invalid arguments. Must provide object type ("digital", "archival", or "resource") and identifier (integer).')
    proceed = False

if proceed:
    if args[0] == 'digital':
        uri = f'/repositories/2/digital_objects/{args[1]}'
    elif args[0] == 'archival':
        uri = f'/repositories/2/archival_objects/{args[1]}'
    elif args[0] == 'resource':
        uri = f'/repositories/2/resources/{args[1]}'
    obj = client.get(f'{uri}?resolve[]=linked_instances').json()
    print(json.dumps(obj, indent=4, sort_keys=True))

'''

uri = '/repositories/2/digital_objects/8889'
uri = '/repositories/2/digital_objects/27551'
uri = '/repositories/2/archival_objects/74627'
uri = '/repositories/2/resources/219'
'''