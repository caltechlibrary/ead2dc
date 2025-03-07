secrets = __import__('secrets')

import json, sys, argparse
from asnake.client import ASnakeClient

client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)

client.authorize()

args = sys.argv[1:]

proceed = True

if len(args) != 2:
    print('Invalid number of arguments. Must be 2.')
    proceed = False
else:
    if args[0] not in ['digital', 'archival', 'resource']:
        print('Invalid type. Must be "digital", "archival", or "resource"')
        proceed = False
    try:
        int(args[1])
    except:
        print('Invalid ID. Must be an integer.')
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