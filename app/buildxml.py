# -*- coding: utf-8 -*-
#
# xml-build.py
#
# Generates static OAI-PMH XML for Caltech Archives digital objects
# Data source is ArchivesSpace API
# Output is a single XML file: caltecharchives.xml
# Only archival objects with digital objects are included
# An SQLite3 database, instance/ead2dc.db, is used to store collection information
# Tables: 
#   logs - logs data provider requests
#   collections - records data about collections with digital content
#   last_update - records dates of last updates of XML file and collection selection

import time, os
import sqlite3 as sq
import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

from asnake.client import ASnakeClient

#-----------------------------------------------------------------------#
# FUNCTIONS                                                             #
#-----------------------------------------------------------------------#

# returns a "pretty" XML string
def prettify(elem):
    xml_string = ET.tostring(elem)
    xml_file = dom.parseString(xml_string)
    pretty_xml = xml_file.toprettyxml(indent="  ")
    return pretty_xml

#-----------------------------------------------------------------------#

# create collection description string from collection notes
def create_collection_description(coll_info):

    try:
        description = [note for note in coll_info['notes'] if (note['type'] == 'scopecontent' or note['type'] == 'abstract') and note['publish']]
    except:
        description = None
    if description:
        try:
            notepart1 = ' '.join([note['content'][0] for note in description if note['jsonmodel_type'] == 'note_singlepart'])
        except:
            notepart1 = ''
        try:
            notepart2 = ' '.join([note['subnotes'][0]['content'] for note in description if note['jsonmodel_type'] == 'note_multipart'])
        except:
            notepart2 = ''
        description = notepart1 + ' ' + notepart2
    else:
        description = ''

    return description.strip()

#-----------------------------------------------------------------------#

# establish API connection
def authorize_api():
    secrets = __import__('secrets')
    client = ASnakeClient(baseurl = secrets.baseurl,
                        username = secrets.username,
                        password = secrets.password)
    client.authorize()
    return client

#-----------------------------------------------------------------------#

# build collections dictionary
def build_collections_dict():

    # initialize collections dictionary
    # this dictionary references archival objects with related digital objects
    collections_dict = dict()
    # initialize collections set
    collections = set()

    # iterate over digital objects
    digital_objects = client.get_paged('/repositories/2/digital_objects')

    n = 0

    for obj in digital_objects:

        n += 1
        print (n, end='\r')

        do = obj['uri']

        # only include objects that are published and not suppressed
        if obj.get('publish') == True and obj.get('suppressed') == False:

            # capture the id of the collections
            colls_list = obj.get('collection')

            if colls_list:

                # iterate over the linked instances to find archival records
                for linked_instance in obj['linked_instances']:

                    # if linked to an archival object
                    if linked_instance['ref'][:33] == '/repositories/2/archival_objects/':

                        ao = linked_instance['ref']

                        # build dictionary of collections, digital objects, and archival objects
                        # dict has the form {collection: {ao: {do}}}
                        # ao: 'archival object' is an id
                        # do: 'digital object' is an id
                        for collection in colls_list:

                            # add to collections set
                            coll = collection['ref']
                            collections.add(coll)
            
                            if collections_dict.get(coll):

                                # add to existing collection
                                if collections_dict[coll].get(ao):

                                    # add digital object to existing archival object
                                    collections_dict[coll][ao].append(do)

                                else:

                                    # create new archival object entry
                                    collections_dict[coll][ao] = [do]

                            else:

                                # create new collection
                                collections_dict[coll] = {ao: [do]}

    print('Done building collections dictionary...')

    # convert collections dictionary to archival objects dictionary
    # form: {ao: {'collections': [collection], 'digital_objects': [do]}}

    # initialize archival objects dictionary
    archival_objects_dict = dict()

    n = 0

    for collection, ao_dict in collections_dict.items():

        n += 1
        print (n, end='\r')

        for ao, do_list in ao_dict.items():

            if archival_objects_dict.get(ao):

                archival_objects_dict[ao]['collections'].append(collection)
                archival_objects_dict[ao]['digital_objects'].extend(do_list)

            else:

                archival_objects_dict[ao] = {'collections': [collection], 'digital_objects': do_list}

    print('Done building archival objects dictionary...')

 
    return collections_dict, archival_objects_dict


#-----------------------------------------------------------------------#

def published_file_uris(do_list):

    # create file_uris set
    file_uris = set()

    # use_statements to exclude
    # 'image-thumbnail' - thumbnails not full images
    # 'URL-Redirected' - redirected URLs not direct links
    use_exclude = ['image-thumbnail', 'URL-Redirected']

    # iterate over digital objects linked to archival object
    for do in do_list:
        for file_version in client.get(do).json()['file_versions']:
            if file_version.get('use_statement') not in use_exclude \
                    and file_version.get('publish', False):
                file_uris.add(file_version['file_uri'])

    return file_uris                    


#-----------------------------------------------------------------------#

def create_valid_hostnames_set(file_uris):

    # hostnames to exclude
    # github.com - github links are not direct links to digital content
    # www.github.com - ditto
    host_exclude = ['github.com', 'www.github.com']
    
    hostnames = {urlparse(file_uri).netloc for file_uri in file_uris}

    # remove excluded
    for host in host_exclude:
        hostnames.discard(host)

    # remove direct targets is resolver.caltech.edu is present
    if 'digital.archives.caltech.edu' in hostnames and 'resolver.caltech.edu' in hostnames:
        hostnames.discard('digital.archives.caltech.edu')
    if 'californiarevealed.org' in hostnames and 'resolver.caltech.edu' in hostnames:
        hostnames.discard('californiarevealed.org')

    return hostnames


#-----------------------------------------------------------------------#

def get_set_id(collection_id):

    id_list = collection_id.split('/')
    collection_type = id_list[-2][:-1]
    collection_number = id_list[-1]
    setid = collection_type + '_' + collection_number

    return setid


#-----------------------------------------------------------------------#
# START OF SCRIPT                                                       #
#-----------------------------------------------------------------------#

start = time.time()

# db location
print('Reading database location...')
dbpath = Path(Path(__file__).resolve().parent).joinpath('../instance/ead2dc.db')

# authorize API
print('Authorizing API...')
client = authorize_api()

# build collections dictionary
print('Building collections dictionary...')
collections_dict, archival_objects_dict = build_collections_dict()

# read included collections from db
connection = sq.connect(dbpath)
cursor = connection.cursor()

# retrieve earliest date stamp from previous build
query = 'SELECT earliest FROM dates;'
result = cursor.execute(query)
earliestDatestamp = result.fetchone()[0]

# retrieve included collections from db
# return dictionary of collection numbers and inclusion status
includedcollections = dict()
query = 'SELECT collno,incl FROM collections;'
for row in cursor.execute(query).fetchall():
    includedcollections[row[0]] = row[1]

# write ISO last update
now = datetime.now()
last_update = now.isoformat()
query = 'UPDATE last_update SET dt=? WHERE fn=?;'
cursor.execute(query, [last_update, 'xml'])
  
# delete all records from db
query = 'DELETE FROM collections;'
cursor.execute(query)

# save query to insert collection records into db
query = 'INSERT INTO collections \
            (collno,colltitle,description,collid,aocount,docount,incl,caltechlibrary,internetarchive,youtube,other,typ) \
         VALUES \
            (?,?,?,?,?,?,?,?,?,?,?,?);'

# iterate over collections dictionary to insert collection records into db
print ('Collection summary...')
for collection in collections_dict:

    # get collection info
    coll_info = client.get(collection).json()

    # extract collection data
    collid = coll_info['uri']
    colltitle = coll_info['title']
    description = create_collection_description(coll_info)

    # initialize sets to count unique digital objects and archival objects
    coll_dos = set()
    coll_aos = set()

    # identify collection type and number
    if collid[16:25] == 'resources':
        colltyp = 'resource'
        collno = collid[26:]
    else:
        colltyp = 'accession'
        collno = collid[27:]

    # iterate over collection to count unique digital objects and archival objects
    for ao in collections_dict[collection]:
        coll_aos.add(ao)
        for dos in collections_dict[collection][ao]:
            for do in dos:
                coll_dos.add(do)

    # insert collection record into db
    cursor.execute(query, [collno,                              # coll[0] = collno (str)
                           colltitle,                           # coll[1] = colltitle (str)
                           description,                         # coll[2] = description (str)                 
                           collid,                              # coll[3] = collid (str) 
                           0,                                   # coll[4] = aocount (int) 
                           0,                                   # coll[5] = docount (int) 
                           includedcollections.get(collno, 0),  # coll[6] = incl (Boolean) 
                           0,                                   # coll[7] = caltechlibrary (int)
                           0,                                   # coll[8] = internetarchive (int)
                           0,                                   # coll[9] = youtube (int) 
                           0,                                   # coll[10] = other (int) 
                           colltyp])                            # coll[11] = typ ('resource'|'accession')
    
    print('>', collection, '(' + client.get(collection).json()['title'] + ')', 
          len(coll_aos), 'archival objects;', len(coll_dos), 'digital objects')

# commit changes to db before reading
connection.commit()

# read collection info from db
# colls is a list of tuples
query = 'SELECT collno,colltitle,description,collid,aocount,docount,incl,caltechlibrary,internetarchive,youtube,other,typ FROM collections'
colls = cursor.execute(query).fetchall()
cursor.close()
connection.close()

# build XML
print('Building static repository...')

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
oaixml = ET.Element('OAI-PMH', {'xmlns':'http://www.openarchives.org/OAI/2.0/',
    'xmlns:xsi':'http://www.w3.org/2001/XMLSchema-instance',
    'xsi:schemaLocation':'http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd'})

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
earliestDate = ET.SubElement(Identify, 'earliestDatestamp')
earliestDate.text = earliestDatestamp
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
    oaiset = ET.SubElement(ListSets, 'set')
    setSpec = ET.SubElement(oaiset, 'setSpec')
    setSpec.text = coll[11]+'_'+coll[0]
    setName = ET.SubElement(oaiset, 'setName')
    setName.text = coll[1]
    setDescription = ET.SubElement(
        ET.SubElement(
            ET.SubElement(oaiset, 'setDescription'), 'oai_dc', {
                    'xmlns:oai_dc':'http://www.openarchives.org/OAI/2.0/oai_dc/',
                    'xmlns:dc':'http://purl.org/dc/elements/1.1/',
                    'xmlns:xsi':'http://www.w3.org/2001/XMLSchema-instance',
                    'xsi:schemaLocation':'http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd'
            }
        ), 'dc:description'
    )
    setDescription.text = coll[2]

#dao_count = 0
#dao_skipped = 0

# build ListRecords segment
ListRecords = ET.SubElement(oaixml, 'ListRecords', {'metadataPrefix': 'oai_dc'})

#print('Elapsed time:', round(time.time() - start, 1), 'secs')

intertime = time.time()

# temp
#devrecordcount = 0
#devtest_textfile = Path(Path(__file__).resolve().parent).joinpath('../xml/devtest_textfile.csv')
#if os.path.exists(devtest_textfile):
#    os.remove(devtest_textfile)

# initialize stats_dict for collection statistics
# {setid: {'archival_objects': #, 'digital_objects': {hostcategory: #}}
stats_dict = dict()

# initialize coll_mdate_dict to track most recently modified record by collection
# {collid: 'mdate'}
coll_mdate_dict = dict()

# iterate over archival object dictionary
# do = digital object, ao = archival object
# archival_objects_dict = {ao: {'collections': [collids], 'digital_objects: [dos]}}        
j = 0
for ao, colls_dict in archival_objects_dict.items():

    print(ao, end='\r')

    # temp
    # limit records for testing
    #j += 1
    #if j > 3000:
    #    break

    # get archival object metadata
    uri = ao + "?resolve[]=ancestors" \
            + "&resolve[]=digital_object" \
            + "&resolve[]=linked_agents" \
            + "&resolve[]=repository" \
            + "&resolve[]=subjects" \
            + "&resolve[]=top_container"
    archival_object_metadata = client.get(uri).json()

    # string form of date to write to each record
    create_time = archival_object_metadata['create_time']
    system_mtime = archival_object_metadata['system_mtime']
    user_mtime = archival_object_metadata['user_mtime']
    last_modified_date = max([create_time, system_mtime, user_mtime])[:10]
    
    # temp
    # limit to subset of collections for testing
    #if len(set(colls_dict['collections']) & set(['/repositories/2/resources/30', '/repositories/2/resources/312'])) == 0:
    #    continue

    #collection_number = coll[0]
    #collection_title = coll[1]
    #collection_type = coll[11]
    #setid = '/repositories/2/' + collection_type + 's/' + collection_number
    #dao_dict[setid] = dict() # initialize dictionary for collection's statistics

    #recs_created = 0
    #recs_skipped = 0


    # skip archival object if no published digital object file URIs
    do_list = colls_dict['digital_objects']
    file_uris = published_file_uris(do_list)
    if len(file_uris) == 0:
        continue

    # create hostnames set
    hostnames = create_valid_hostnames_set(file_uris)

    # update archival object record count
    #if dao_dict[setid].get('aocount'):
    #    dao_dict[setid]['aocount'] += 1
    #else:
    #    dao_dict[setid]['aocount'] = 1
    
    # record element
    record = ET.SubElement(ListRecords, 'record')

    # header element
    header = ET.SubElement(record, 'header')

    # identifier elements
    #identifier = ET.SubElement(header, 'identifier')
    #identifier.text = 'collections.archives.caltech.edu' + do
    #identifier.attrib = {'type': 'digital'}

    identifier = ET.SubElement(header, 'identifier')
    identifier.text = 'collections.archives.caltech.edu' + ao
    #identifier.attrib = {'type': 'archival'}

    #identifier = ET.SubElement(header, 'identifier')
    #identifier.text = 'collections.archives.caltech.edu' + setid
    #identifier.attrib = {'type': 'collection'}
    
    # datestamp element
    datestamp = ET.SubElement(header, 'datestamp')
    datestamp.text = last_modified_date

    # setSpec element
    for collid in colls_dict['collections']:

        setspec = ET.SubElement(header, 'setSpec')
        setspec.text = get_set_id(collid)

        # add archival record to stats_dict
        # {collid: {'archival_objects': #, 'digital_objects': {hostcategory: #}}
        if stats_dict.get(collid):
            stats_dict[collid]['archival_objects'] += 1
        else:
            stats_dict[collid] = {'archival_objects': 1, 'digital_objects': dict()}

        # track last modified date by collection
        if coll_mdate_dict.get(collid):
            if last_modified_date > coll_mdate_dict[collid]:
                coll_mdate_dict[collid] = last_modified_date
        else:
            coll_mdate_dict[collid] = last_modified_date

    # create metadata element
    metadata = ET.SubElement(record, 'metadata')

    # dc element
    dc = ET.SubElement(metadata, 'oai_dc:dc', {'xmlns:oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                                        'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
                                        'xmlns:dcterms': 'http://purl.org/dc/terms/'})
    
    # title elements
    #title = ET.SubElement(dc, 'dc:title')
    #title.text = client.get(do).json()['title']
    #title.attrib = {'type': 'digital'}

    title = ET.SubElement(dc, 'dc:title')
    title.text = archival_object_metadata['title']
    #title.attrib = {'type': 'archival'}

    #title = ET.SubElement(dc, 'dc:title')
    #title.text = client.get(setid).json()['title']
    #title.attrib = {'type': 'collection'}

    # ancestor titles
    # print('testing:', ao[33:])
    # ancestors = get_ancestors('archival_objects', ao[33:])
    ancestors = list()
    for a in archival_object_metadata.get('ancestors', []):
        level = a.get('level')
        if a.get('_resolved'):
            if a['_resolved'].get('title'):
                title = a['_resolved']['title']
                ancestors.append((title, level))

    #print(ancestors)
    for a in ancestors:
        if a:
            ancestor = ET.SubElement(dc, 'dc:title')
            ancestor.text = a[0]
            if a[1]:
                ancestor.attrib = {'level': a[1]}

    # relation element
    #relation = ET.SubElement(dc, 'dc:relation')
    #relation.text = collectiontitle
    #relation.attrib = {'label': 'Collection'}

    # description element
    #description = ET.SubElement(dc, 'dc:description')
    #description.text = 'Digital object in ' + collectiontitle

    # warning for no file_uris
    uri_test = False
    
    for file_uri in file_uris: 

        # skip urls not in hostnames set
        hostname = urlparse(file_uri).netloc
        if hostname not in hostnames:
            continue

        # categorize hostname
        if hostname in ['resolver.caltech.edu', 'digital.archives.caltech.edu', 'californiarevealed.org']:
            hostcategory = 'caltechlibrary'
        elif hostname == 'archive.org':
            hostcategory = 'internetarchive'
        elif hostname in ['youtube.com', 'youtu.be', 'www.youtube.com', 'www.youtu.be']:
            hostcategory = 'youtube'
        else:
            hostcategory = 'other'

        # add archival record to stats_dict
        # {setid: {'archival_objects': #, 'digital_objects': {hostcategory: #}}
        for collid in colls_dict['collections']:

            if stats_dict[collid].get('digital_objects'):

                if stats_dict[collid]['digital_objects'].get(hostcategory):
                    stats_dict[collid]['digital_objects'][hostcategory] += 1

                else:
                    stats_dict[collid]['digital_objects'][hostcategory] = 1

            else:
                stats_dict[collid]['digital_objects'][hostcategory] = 1

        # identifier element
        identifier = ET.SubElement(dc, 'dc:identifier')
        identifier.text = file_uri
        identifier.attrib = {'scheme': 'URI', 'type': 'resource'}
        uri_test = True
    
    if not uri_test:
        print('> warning: no file URIs for archival object:', ao)

    # identifier element
    if archival_object_metadata.get('component_id'):
        identifier = ET.SubElement(dc, 'dc:identifier')
        identifier.text = archival_object_metadata['component_id']
        identifier.attrib = {'type': 'localid'}

    # dates
    dates = list()
    #obj = get_json(category, id)
    for dt in archival_object_metadata.get('dates', []):
        dates.append(dt.get('begin', ''))

    #print(ao[33:])
    #print(dates)
    for d in dates:
        if d != '':
            dt = ET.SubElement(dc, 'dc:date')
            dt.text = d                

    # extents
    extents = list()
    #obj = get_json(category, id)
    #print(archival_object_metadata.get('extents'))
    for extent in archival_object_metadata.get('extents', []):
        #print(extent)
        #print('number:', extent.get('number'))
        #print('details:', extent.get('physical_details'))
        #print('type:', extent.get('extent_type'))
        s = extent.get('number', '') + ' ' + extent.get('extent_type', '') + ' ' + extent.get('physical_details', '').strip()
        #print('string:', s)
        extents.append(s)

    #print('extents:', extents)

    #print(extents)
    for e in extents:
        if e.strip() != '':
            extent = ET.SubElement(dc, 'dc:format')
            extent.text = e.strip()

    # subjects
    #subjects = get_subjects('archival_objects', ao[33:])

    subjects = list()
    #obj = get_json(category, id)
    for s in archival_object_metadata.get('subjects', []):
        if s.get('_resolved'):
            source = s['_resolved'].get('source')
            if s['_resolved'].get('title'):
                subject = s['_resolved']['title']
                subjects.append((subject, source))

    #print(subjects)
    for s in subjects:
        if s:
            subject = ET.SubElement(dc, 'dc:subject')
            subject.text = s[0]
            if s[1]:
                subject.attrib = {'source': s[1]}

    #recs_created += 1
    #print(recs_created, end='\r')

#print('>', collection_title, '('+str(recs_created), 'records created)')

#print('>', round(time.time() - intertime, 1), 'secs', '(' + datetime.now().isoformat() + ')')
intertime = time.time()

# temp
#print('devrecordcount:', devrecordcount)

# update collection statistics in db
# {collid: {'archival_objects': #, 'digital_objects': {hostcategory: #}}
connection = sq.connect(dbpath)
db = connection.cursor()

for collid, values in stats_dict.items():
    query = 'UPDATE collections SET aocount=? WHERE collid=?;'
    db.execute(query, [values['archival_objects'], collid])

    do_count = 0
    for category, count in values['digital_objects'].items():
        do_count += count
        query = 'UPDATE collections SET '+category+'=? WHERE collid=?;'
        db.execute(query, [count, collid])

    query = 'UPDATE collections SET docount=? WHERE collid=?;'
    db.execute(query, [do_count, collid])

# string form of today's date to write to each record
today = date.today().strftime('%Y-%m-%d')

earliestDatestamp = today
query = 'UPDATE collections SET last_edit=? WHERE collid=?;'
for collid, mod_date in coll_mdate_dict.items():
    db.execute(query, [mod_date, collid])
    earliestDatestamp = min(earliestDatestamp, mod_date)

query = 'UPDATE dates SET earliest = ?'
db.execute(query, [earliestDatestamp])

query = 'UPDATE last_update SET dt=? WHERE fn=?;'
db.execute(query, [last_update, 'xml'])
db.close()
connection.commit()
connection.close()

#write to disk

# production file
fileout = Path(Path(__file__).resolve().parent).joinpath('../xml/caltecharchives.xml')

#dev file
#fileout = Path(Path(__file__).resolve().parent).joinpath('../xml/caltecharchives-dev.xml')

with open(fileout, 'w') as f:
    #f.write(ET.tostring(oaixml, encoding='unicode', method='xml'))
    f.write(prettify(oaixml))

'''
for collection in dao_dict:
    print(collection)
    for url in dao_dict[collection]:
        print('>', url, dao_dict[collection][url])
'''

#print(dao_count, 'total records created')
#print(dao_skipped, 'total records skipped')

#print(dao_dict)

print('\nTotal elapsed time:', round(time.time() - start, 1))

print('Done.')