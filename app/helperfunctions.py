# FUNCTIONS

from asnake.client import ASnakeClient

# establish API connection
print('Establishing API connection...')
secrets = __import__('secrets')
client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)
client.authorize()

