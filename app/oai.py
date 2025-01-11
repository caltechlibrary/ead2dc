import json
import sqlite3 as sq
import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from datetime import date, datetime
from pathlib import Path
from asnake.client import ASnakeClient

# FUNCTIONS

# read collection info from db
def read_colls_from_db():
    connection = sq.connect(dbpath)
    db = connection.cursor()
    query = 'SELECT collno, eadurl, colltitle, description FROM collections'
    colls = db.execute(query).fetchall()
    db.close()
    connection.close()
    return colls

# write time of last update to db
# update collections info to db
# colls = set of collection ids
def update_db(colls):
    # write ISO last update
    now = datetime.now()
    last_update = now.isoformat()
    connection = sq.connect(dbpath)
    db = connection.cursor()
    
    query = 'UPDATE last_update SET dt=? WHERE fn=?;'
    db.execute(query, [last_update, 'xml'])
    
    query = 'DELETE FROM collections;'
    db.execute(query)

    query = 'INSERT INTO collections (collno, eadurl, colltitle, description) VALUES (?, ?, ?, ?);'
    for coll in colls:
        coll_info = client.get(coll).json()
        print('updating dbase:', coll_info['title'])
        collno = coll_info['uri'][26:]
        eadurl = 'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/'+collno+'&metadataPrefix=oai_ead'
        title = coll_info['title']
        description = [note for note in coll_info['notes'] if note['type'] == 'scopecontent'][0]
        db.execute(query, collno, eadurl, title, description)
    
    db.close()
    connection.commit()
    connection.close()
    return

# returns a "pretty" XML string
def prettify(elem):
    xml_string = ET.tostring(elem)
    xml_file = dom.parseString(xml_string)
    pretty_xml = xml_file.toprettyxml(indent="  ")
    return pretty_xml

# MAIN

# read config file
with open(Path(Path(__file__).resolve().parent).joinpath('config.json'), "r") as f:
    config = json.load(f)

# db location
dbpath = Path(Path(__file__).resolve().parent).joinpath('../instance/ead2dc.db')

# string form of date to write to each record
today = date.today().strftime("%Y-%m-%d")

# establish API connection
secrets = __import__('secrets')
client = ASnakeClient(baseurl = secrets.baseurl,
                      username = secrets.username,
                      password = secrets.password)
client.authorize()

# initialize collections dictionary
# this dictionary references archival objects with related digital objects
collections_dict = dict()

# initialize collection and archival object sets
# contain collections and archival objects with related digital objects
collections, archival_objects = set(), set()

dao_count = 0

# iterate over digital objects
for obj in client.get_paged('/repositories/2/digital_objects'):
    # if there is a value for 'collection' add that value to the collections set
    if obj.get('collection') and obj['publish'] and not obj['suppressed']:
        coll = obj['collection'][0]['ref']
        if coll[:26] == '/repositories/2/resources/':
            collections.add(coll)
            # iterate over the linked instances
            for linked_instance in obj['linked_instances']:
                if linked_instance['ref'][:33] == '/repositories/2/archival_objects/':
                    # build dictionary of collections, digital objects, and archival objects
                    # dict has the form {collection: {(digital object, archival object)}}
                    dao_count += 1
                    if collections_dict.get(coll):
                        collections_dict[coll].add((obj['uri'], linked_instance['ref']))
                    else:
                        collections_dict[coll] = {(obj['uri'],linked_instance['ref'])}

print('Number of digital objects:', dao_count)
print('Number of collections with digital objects:', len(collections))
print()

dao_count = 0

for item in collections_dict.items():
    # print title of collection and number of digital objects
    print(client.get(item[0]).json()['title'], ':', len(item[1]), 'digital objects')
    # iterate over digital objects and archival objects
    for do, ao in item[1]:
        # print archival object title and digital object URI
        generator = (file_version for file_version in client.get(do).json()['file_versions']
                     if file_version['publish'] == True
                     and file_version.get('use_statement', 'ok') not in ['image-thumbnail', 'URL-Redirected'])
        # print title of archival object and URI of digital object
        try:
            do_title = client.get(ao).json()['title']
            file_uri = next(generator)['file_uri']
            dao_count += 1
        except:
            continue

# update collections info in database
update_db(collections)

colls = read_colls_from_db()

# namespace dictionary
ns = {'': 'urn:isbn:1-931666-22-9', 
      'xlink': 'http://www.w3.org/1999/xlink',
      'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
      'dc': 'http://purl.org/dc/elements/1.1/'}
ET.register_namespace('', 'http://www.openarchives.org/OAI/2.0/')
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
ET.register_namespace('oai_dc', 'http://www.openarchives.org/OAI/2.0/oai_dc/')
ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')

# create OAI-PMH XML object
oaixml = ET.Element('OAI-PMH', {'xmlns': 'http://www.openarchives.org/OAI/2.0/'})

# build Identify segment
Identify = ET.SubElement(oaixml, 'Identify')
repositoryName = ET.SubElement(Identify, 'repositoryName')
repositoryName.text = 'Caltech Archives Digital Collections'
baseURL = ET.SubElement(Identify, 'baseURL')
baseURL.text = 'http://apps.library.caltech.edu/ead2dc/oai'
protocolVersion = ET.SubElement(Identify, 'protocolVersion')
protocolVersion.text = '2.0'
adminEmail = ET.SubElement(Identify, 'adminEmail')
adminEmail.text = 'archives@caltech.edu'
deletedRecord = ET.SubElement(Identify, 'deletedRecord')
deletedRecord.text = 'no'
granularity = ET.SubElement(Identify, 'granularity')
granularity.text = 'YYYY-MM-DD'

# build ListMetadataFormats segment
ListMetadataFormats = ET.SubElement(oaixml, 'ListMetadataFormats')
metadataFormat = ET.SubElement(ListMetadataFormats, 'metadataFormat')
metadataPrefix = ET.SubElement(metadataFormat, 'metadataPrefix')
metadataPrefix.text = "oai_dc"
schema = ET.SubElement(metadataFormat, 'schema')
schema.text = "http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
metadataNamespace = ET.SubElement(metadataFormat, 'metadataNamespace')
metadataNamespace.text = "http://www.openarchives.org/OAI/2.0/oai_dc/"

# build ListSets segment
ListSets = ET.SubElement(oaixml, 'ListSets')
                         
for coll in colls:
    set = ET.SubElement(ListSets, 'set')
    setSpec = ET.SubElement(set, 'setSpec')
    setSpec.text = coll[0]
    setName = ET.SubElement(set, 'setName')
    setName.text = coll[2]
    setDescription = ET.SubElement(ET.SubElement(ET.SubElement(
        set, 'setDescription'), 'oai_dc', {'xmlns:oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                                           'xmlns:dc': 'http://purl.org/dc/elements/1.1/'}), 'dc:description')
    setDescription.text = coll[3]

no_records = 0

#write to disk
fileout = Path(Path(__file__).resolve().parent).joinpath('../xml/caltecharchives.xml')
with open(fileout, 'w') as f:
    f.write(prettify(oaixml))

print(dao_count)
