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

# create collection description from collection notes
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
    print('Establishing API connection...')
    secrets = __import__('secrets')
    client = ASnakeClient(baseurl = secrets.baseurl,
                        username = secrets.username,
                        password = secrets.password)
    client.authorize()
    return client

#-----------------------------------------------------------------------#
# START OF SCRIPT                                                       #
#-----------------------------------------------------------------------#

start = time.time()

# db location
print('Reading database location...')
dbpath = Path(Path(__file__).resolve().parent).joinpath('../instance/ead2dc.db')

# string form of date to write to each record
today = date.today().strftime("%Y-%m-%d")

print('Authorizing API...')
client = authorize_api()

def build_collections_dict():

    # initialize collections dictionary
    # this dictionary references archival objects with related digital objects
    collections_dict = dict()

    # initialize collection and archival object sets
    # contain collections and archival objects with related digital objects
    collections = set()

    dao_count = 0

    print('Finding digital content...')

    # counters for various categories of record
    #published = 0
    #notpublished = 0
    #suppressed = 0
    #notsuppressed = 0
    #orphandigitalobjects = 0
    #numbresources = 0
    #numbaccessions = 0

    # retrieve all digital objects
    digital_objects = client.get_paged('/repositories/2/digital_objects')

    print("Linking digital objects to archival objects...")

    # iterate over digital objects
    for obj in digital_objects:

        do_uri = obj['uri']
        keep = True

        # only include objects that are published and not suppressed
        # check for published
        if obj.get('publish') == False:
            #notpublished += 1
            keep = False
        #else:
        #    published += 1

        # check for suppressed
        if obj.get('suppressed') == True:
            #suppressed += 1
            keep = False
        #else:
        #    notsuppressed += 1

        # capture the id of the collections
        coll = obj.get('collection')
        if coll == []:
            keep = False
            typ = 'orphan'
        #    orphandigitalobjects += 1
        else:
            coll = obj['collection'][0]['ref']
            # identify the type of collection
            # add to collections set
            if coll[:26] == '/repositories/2/resources/':
                collections.add(coll)
                typ = 'resource'
        #        numbresources += 1
            elif coll[:27] == '/repositories/2/accessions/':
                #collections.add(coll)
                #typ = 'accession'
        #        numbaccessions += 1
                keep = False
            else:
                keep = False
                print('> error: cannot identify record type:', do_uri)
        
        # iterate over the linked instances to find archival records
        for linked_instance in obj['linked_instances']:

            # if linked to an archival object
            if linked_instance['ref'][:33] == '/repositories/2/archival_objects/':

                ao = linked_instance['ref']

                # build dictionary of collections, digital objects, and archival objects
                # dict has the form {collection: {archival object: {(digital object, type, keep)}}}
                # i.e. a dictionary where the key is the collection id, and values are sets of tuples
                # 'digital object' is an id
                # 'archival object' is an id
                # 'type' is 'resource' or 'accession'
                # 'keep' is True or False
                dao_count += 1
                if coll != []:
                    if collections_dict.get(coll):
                        # add to existing collection
                        if collections_dict[coll].get(ao):
                            # add digital object to existing archival object
                            collections_dict[coll][ao].add((do_uri, typ, keep))
                        else:
                            # create new archival object entry
                            collections_dict[coll][ao] = {(do_uri, typ, keep)}
                    else:
                        # create new collection
                        collections_dict[coll] = {ao: {(do_uri, typ, keep)}}
                        #ttl = client.get(coll).json()['title']
                        #print('> added', coll, '('+ttl+')')

    return collections_dict

#-----------------------------------------------------------------------#
#-----------------------------------------------------------------------#

# read included collections from db
# retrieve included collections from db
# returns dictionary of collection numbers and inclusion status
connection = sq.connect(dbpath)
cursor = connection.cursor()
query = 'SELECT collno,incl FROM collections'
includedcollections = dict()
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

query = 'INSERT INTO collections \
            (collno,colltitle,description,collid,aocount,docount,incl,caltechlibrary,internetarchive,youtube,other,typ) \
         VALUES \
            (?,?,?,?,?,?,?,?,?,?,?,?);'

# print summary of collections and objects found
for collection in collections_dict:

    # collection info
    coll_info = client.get(collection).json()
    collid = coll_info['uri']
    colltitle = coll_info['title']
    description = create_collection_description(coll_info)
    coll_dos = set()
    coll_aos = set()

    if collid[16:25] == 'resources':
        colltyp = 'resource'
        collno = collid[26:]
    elif collid[16:26] == 'accessions':
        colltyp = 'accession'
        collno = collid[27:]
    else:
        colltyp = 'unknown'
        print('> error: cannot identify record type:', collid)
    # collid is the URI of the collection

    for ao in collections_dict[collection]:
        coll_aos.add(ao)
        for (do, typ, keep) in collections_dict[collection][ao]:
            coll_dos.add(do)

    cursor.execute(query, [collno, colltitle, description, collid, len(coll_aos), len(coll_dos), includedcollections.get(collno, 0), 0, 0, 0, 0, colltyp])
    print('>', collection, '(' + client.get(collection).json()['title'] + ')', len(coll_aos), 'archival objects;', len(coll_dos), 'digital objects')

# commit changes to db before reading
connection.commit()

# read collection info from db
# colls is a list of tuples
query = 'SELECT collno,colltitle,description,collid,aocount,docount,incl,caltechlibrary,internetarchive,youtube,other,typ FROM collections'
colls = cursor.execute(query).fetchall()
cursor.close()
connection.close()

#temp
#for coll in colls:
#    print(coll[1])

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
earliestDatestamp = '2025-01-01'
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
    setSpec.text = coll[0]
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

dao_count = 0
dao_skipped = 0
dao_dict = dict()

# build ListRecords segment
ListRecords = ET.SubElement(oaixml, 'ListRecords', {'metadataPrefix': 'oai_dc'})

#print('Elapsed time:', round(time.time() - start, 1), 'secs')

print('Building static repository...')

urls = set()

intertime = time.time()

# temp
devrecordcount = 0
devtest_textfile = Path(Path(__file__).resolve().parent).joinpath('../xml/devtest_textfile.csv')
if os.path.exists(devtest_textfile):
    os.remove(devtest_textfile)

for coll in colls:

    # temp
    #check_for_duplicates = set()
    #duplicate_recs_skipped = 0

    # coll[0] = collno
    # coll[1] = colltitle
    # coll[2] = description
    # coll[3] = collid
    # coll[4] = aocount
    # coll[5] = docount
    # coll[6] = incl
    # coll[7] = caltechlibrary
    # coll[8] = internetarchive
    # coll[9] = youtube
    # coll[10] = other
    # coll[11] = typ

    recs_created = 0
    recs_skipped = 0

    setid = '/repositories/2/' + coll[11] + 's/' + coll[0]

    # temp
    # limit to subset of collections for testing
    if coll[0] not in ['30', '34', '80']:
        continue

    #temp
    #print('>', setid)

    collectiontitle = coll[1]
    dao_dict[setid] = dict() # initialize dictionary for collection's statistics

    #temp
    j=0

    if collections_dict.get(setid):
    
        # iterate over collection
        # do = digital object, ao = archival object
        # typ = type of collection resource|accession
        # keep = True if the object is published and not suppressed
        # collections_dict[setid] = {(digital object, archival object, type, keep)}        
        for ao in collections_dict[setid]:

            duplicate_dos = set()

            for (do, typ, keep) in collections_dict[setid][ao]:

                # skip duplicate digital objects for this archival object
                if do in duplicate_dos:
                    continue
                else:
                    duplicate_dos.add(do)

                file_uri_list = list()

                for file_version in client.get(do).json()['file_versions']:
                    
                    if keep \
                        and typ == 'resource' \
                        and file_version.get('use_statement', 'ok') not in ['image-thumbnail', 'URL-Redirected']:

                        file_uri_list.append(file_version['file_uri'])

#                generator = (file_version for file_version in client.get(do).json()['file_versions']
#                         if keep
#                            and typ == 'resource'
#                            #and file_version['publish'] == True
#                            and file_version.get('use_statement', 'ok') 
#                            not in ['image-thumbnail', 'URL-Redirected'])


                            

                            # check for duplicates
                            #if do in check_for_duplicates:
                                # skip duplicate
                            #    print('>> duplicate "do" found, skipping:', do)
                            #    duplicate_recs_skipped += 1
                            #    continue
                            #else:
                            #    check_for_duplicates.add(do)
                            #    devrecordcount += 1
                            #    with open(devtest_textfile, 'a') as f:
                            #        f.write(do + ',' + ao + '\n')

            # update archival object record count
            if dao_dict[setid].get('aocount'):
                dao_dict[setid]['aocount'] += 1
            else:
                dao_dict[setid]['aocount'] = 1
            
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
            datestamp.text = today

            # setSpec element
            setspec = ET.SubElement(header, 'setSpec')
            setspec.text = coll[0]

            # get archival object metadata
            uri = ao + "?resolve[]=ancestors" \
                    + "&resolve[]=digital_object" \
                    + "&resolve[]=linked_agents" \
                    + "&resolve[]=repository" \
                    + "&resolve[]=subjects" \
                    + "&resolve[]=top_container"
            archival_object_metadata = client.get(uri).json()

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

            # list of unique hostnames
            hostnames = list(set([urlparse(file_uri).netloc for file_uri in file_uri_list]))

            if 'digital.archives.caltech.edu' in hostnames and 'resolver.caltech.edu' in hostnames:
                hostnames.remove('digital.archives.caltech.edu')
            if 'github.com' in hostnames:
                hostnames.remove('github.com')
            if 'www.github.com' in hostnames:
                hostnames.remove('www.github.com')
            if 'californiarevealed.org' in hostnames and 'resolver.caltech.edu' in hostnames:
                hostnames.remove('californiarevealed.org')

            for file_uri in file_uri_list: 

                hostname = urlparse(file_uri).netloc

                if hostname in [None, 'github.com', 'www.github.com'] \
                    or hostname not in hostnames:

                    continue

                # categorize hostname
                if hostname == 'resolver.caltech.edu' or hostname == 'digital.archives.caltech.edu' or hostname == 'californiarevealed.org':
                    hostcategory = 'caltechlibrary'
                elif hostname == 'archive.org':
                    hostcategory = 'internetarchive'
                elif hostname == 'youtube.com' or hostname == 'youtu.be':
                    hostcategory = 'youtube'
                else:
                    hostcategory = 'other'
                if hostname not in urls:
                    urls.add(hostname)
                if dao_dict[setid].get(hostcategory):
                    dao_dict[setid][hostcategory] += 1
                else:
                    dao_dict[setid][hostcategory] = 1
                dao_count += 1

                # identifier element
                identifier = ET.SubElement(dc, 'dc:identifier')
                identifier.text = file_uri
                identifier.attrib = {'scheme': 'URI', 'type': 'resource'}

            # identifier element
            if archival_object_metadata.get('component_id'):
                identifier = ET.SubElement(dc, 'dc:identifier')
                identifier.text = archival_object_metadata['component_id']
                identifier.attrib = {'type': 'localid'}

            # dates
            dates = list()
            #obj = get_json(category, id)
            for date in archival_object_metadata.get('dates', []):
                dates.append(date.get('begin', ''))

            #print(ao[33:])
            #print(dates)
            for d in dates:
                if d != '':
                    date = ET.SubElement(dc, 'dc:date')
                    date.text = d                

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

            recs_created += 1
            print(recs_created, end='\r')

            #temp
            #j += 1
            #if j >= 20:
            #    break

        print('>', collectiontitle, '('+str(recs_created), 'records created)')

        #print('>', round(time.time() - intertime, 1), 'secs', '(' + datetime.now().isoformat() + ')')
        intertime = time.time()

# temp
#print('devrecordcount:', devrecordcount)

connection = sq.connect(dbpath)
db = connection.cursor()
for collid in dao_dict:
    docount = 0
    for hostcategory in dao_dict[collid]:
        query = 'UPDATE collections SET '+hostcategory+'=? WHERE collid=?;'
        db.execute(query, [dao_dict[collid][hostcategory], collid])
        docount += dao_dict[collid][hostcategory]
    if docount == 0:
        query = 'DELETE FROM collections WHERE collid=?;'
        db.execute(query, [collid])
    else:
        query = 'UPDATE collections SET docount=? WHERE collid=?;'
        db.execute(query, [docount, collid])
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

print(dao_count, 'total records created')
#print(dao_skipped, 'total records skipped')

#print(dao_dict)

#print(urls)

print('Total elapsed time:', round(time.time() - start, 1))

print('Done.')