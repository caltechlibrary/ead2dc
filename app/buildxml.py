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

import time
import sqlite3 as sq
import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

from asnake.client import ASnakeClient

# get_json, get_subjects, get_extents, get_dates are also in aspace.py

def get_json(category, id):
    client.authorize()
    uri = '/repositories/2/'+category+'/'+id \
        + "?resolve[]=ancestors" \
        + "&resolve[]=digital_object" \
        + "&resolve[]=linked_agents" \
        + "&resolve[]=repository" \
        + "&resolve[]=subjects" \
        + "&resolve[]=top_container"
    obj = client.get(uri)
    return obj.json()

def get_ancestors(category, id):
    ancestors = list()
    obj = get_json(category, id)
    print(obj)
    for a in obj.get('ancestors', []):
        if a.get('_resolved'):
            if a['_resolved'].get('title'):
                title = a['_resolved']['title']
                level = a.get['level']
                ancestors.append((title, level))
    return ancestors

def get_subjects(category, id):
    subjects = list()
    obj = get_json(category, id)
    for s in obj.get('subjects', []):
        if s.get('_resolved'):
            if s['_resolved'].get('title'):
                subject = subject['_resolved']['title']
                if s['_resolved'].get('source'):
                    source = s['_resolved']['source']
                else:
                    source = None
                subjects.append((subject, source))
    return subjects

def get_dates(category, id):
    dates = list()
    obj = get_json(category, id)
    for date in obj.get('dates', []):
        dates.append(date.get('expression', ''))
    return dates

def get_extents(category, id):
    extents = list()
    obj = get_json(category, id)
    for extent in obj.get('extents', []):
        extents.append(extent.get('number', '') + ' ' + extent.get('extent_type', ''))
    return extents

# returns a "pretty" XML string
def prettify(elem):
    xml_string = ET.tostring(elem)
    xml_file = dom.parseString(xml_string)
    pretty_xml = xml_file.toprettyxml(indent="  ")
    return pretty_xml

start = time.time()

# db location
print('Reading database location...')
dbpath = Path(Path(__file__).resolve().parent).joinpath('../instance/ead2dc.db')

# string form of date to write to each record
today = date.today().strftime("%Y-%m-%d")

# establish API connection
print('Establishing API connection...')
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

print('Finding digital content...')

# counters for various categories of record
published = 0
notpublished = 0
suppressed = 0
notsuppressed = 0
orphandigitalobjects = 0
numbresources = 0
numbaccessions = 0

# iterate over digital objects
for obj in client.get_paged('/repositories/2/digital_objects'):

    keep = True

    # only include objects that are published and not suppressed

    # check for published
    if obj.get('publish') == False:
        notpublished += 1
        keep = False
    else:
        published += 1

    # check for suppressed
    if obj.get('suppressed') == True:
        suppressed += 1
        keep = False
    else:
        notsuppressed += 1

    # capture the id of the collections
    coll = obj.get('collection')
    if coll == []:
        keep = False
        typ = 'orphan'
        orphandigitalobjects += 1
    else:
        coll = obj['collection'][0]['ref']
        # identify the type of collection
        # add to collections set
        if coll[:26] == '/repositories/2/resources/':
            collections.add(coll)
            typ = 'resource'
            numbresources += 1
        elif coll[:27] == '/repositories/2/accessions/':
            collections.add(coll)
            typ = 'accession'
            numbaccessions += 1
            keep = False
        else:
            keep = False
            print('> error: cannot identify record type:', obj['uri'])
    
    # iterate over the linked instances to find archival records
    for linked_instance in obj['linked_instances']:
        if linked_instance['ref'][:33] == '/repositories/2/archival_objects/':
            # build dictionary of collections, digital objects, and archival objects
            # dict has the form {collection: {(digital object, archival object, type, keep)}}
            dao_count += 1
            if coll != []:
                if collections_dict.get(coll):
                    # add to existing collection
                    collections_dict[coll].add((obj['uri'], linked_instance['ref'], typ, keep))
                else:
                    # create new collection
                    collections_dict[coll] = {(obj['uri'], linked_instance['ref'], typ, keep)}
                    print('> added', coll, client.get(coll).json()['title'])

print('> summary:')
print('>', dao_count, 'digital objects')
print('>', len(collections), 'collections with digital objects')
print('>', published, 'published')
print('>', notpublished, 'not published')
print('>', suppressed, 'suppressed')
print('>', notsuppressed, 'not suppressed')
print('>', numbresources, 'resources')
print('>', numbaccessions, 'accessions')
print('>', orphandigitalobjects, 'orphan digital objects')
            
# update collections info in database
# updates collno, colltitle, description, eadurl
# does not update docount, incl, carchives clibrary, iarchive, youtube, other, collid
# write time of last update to db
# collectionids = set of collection ids

# read included collections from db
# retrieve included collections from db
# returns dictionary of collection numbers and inclusion status
connection = sq.connect(dbpath)
cursor = connection.cursor()
query = 'SELECT collno,incl FROM collections'
includedcollections = dict()
for row in cursor.execute(query).fetchall():
    includedcollections[row[0]] = row[1]

#temp
#print(includedcollections)

# write ISO last update
now = datetime.now()
last_update = now.isoformat()
    
query = 'UPDATE last_update SET dt=? WHERE fn=?;'
cursor.execute(query, [last_update, 'xml'])
  
# delete all records from db
query = 'DELETE FROM collections;'
cursor.execute(query)

query = 'INSERT INTO collections (collno,eadurl,colltitle,description,collid,docount,incl,caltechlibrary,internetarchive,youtube,other,typ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?);'
for collectionid in collections:
    coll_info = client.get(collectionid).json()
    collid = coll_info['uri']
    if collid[16:25] == 'resources': 
        typ = 'resource'
        collno = collid[26:]
    elif collid[16:26] == 'accessions':
        typ = 'accession'
        collno = collid[27:]
    else:
        typ = 'unknown'
        print('> error: cannot identify record type:', collid)
    # collid is the URI of the collection
    
    eadurl = 'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/'+collno+'&metadataPrefix=oai_ead'
    colltitle = coll_info['title']
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
    # collno text, colltitle text, docount int, incl int, 
    # carchives int, clibrary int, iarchive int, youtube int, other int, 
    # collid text, description text, eadurl text
    cursor.execute(query, [collno, eadurl, colltitle, description, collid, 0, 
            includedcollections.get(collno, 0), 0, 0, 0, 0, typ])
    
    #temp
    #print('temp:', collectionid[26:])

# commit changes to db before reading
connection.commit()

# read collection info from db
# colls is a list of tuples
query = 'SELECT collno,eadurl,colltitle,description,collid,docount,incl,caltechlibrary,internetarchive,youtube,other,typ FROM collections'
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
    oaiset = ET.SubElement(ListSets, 'set')
    setSpec = ET.SubElement(oaiset, 'setSpec')
    setSpec.text = coll[0]
    setName = ET.SubElement(oaiset, 'setName')
    setName.text = coll[2]
    setDescription = ET.SubElement(ET.SubElement(ET.SubElement(
        oaiset, 'setDescription'), 'oai_dc', {'xmlns:oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                                           'xmlns:dc': 'http://purl.org/dc/elements/1.1/'}), 'dc:description')
    setDescription.text = coll[3]

dao_count = 0
dao_skipped = 0
dao_dict = dict()

# build ListRecords segment
ListRecords = ET.SubElement(oaixml, 'ListRecords', {'metadataPrefix': 'oai_dc'})

print('Elapsed time:', round(time.time() - start, 1), 'secs')

print('Building static repository...')

urls = set()

intertime = time.time()

for coll in colls:

    # coll[0] = collno
    # coll[1] = eadurl
    # coll[2] = colltitle
    # coll[3] = description
    # coll[4] = collid
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

    #temp
    #print('>', setid)

    collectiontitle = coll[2]
    dao_dict[setid] = dict() # initialize dictionary for collection's statistics

    #temp
    j=0

    if collections_dict.get(setid):

        print(collectiontitle)
    
        # iterate over collection
        # do = digital object, ao = archival object
        # typ = type of collection resource|accession
        # keep = True if the object is published and not suppressed
        # collections_dict[setid] = {(digital object, archival object, type, keep)}        
        for do, ao, typ, keep in collections_dict[setid]:

            generator = (file_version for file_version in client.get(do).json()['file_versions']
                         if keep
                            and typ == 'resource'
                            #and file_version['publish'] == True
                            and file_version.get('use_statement', 'ok') 
                            not in ['image-thumbnail', 'URL-Redirected'])

            try:
                file_uri = next(generator)['file_uri']
                url = urlparse(file_uri).hostname
                if url == 'resolver.caltech.edu' or url == 'digital.archives.caltech.edu' or url == 'californiarevealed.org':
                    hostcategory = 'caltechlibrary'
                elif url == 'archive.org':
                    hostcategory = 'internetarchive'
                elif url == 'youtube.com' or url == 'youtu.be':
                    hostcategory = 'youtube'
                else:
                    hostcategory = 'other'
                if url not in urls:
                    urls.add(url)
                if dao_dict[setid].get(hostcategory):
                    dao_dict[setid][hostcategory] += 1
                else:
                    dao_dict[setid][hostcategory] = 1
                dao_count += 1

                # record element
                record = ET.SubElement(ListRecords, 'record')

                # header element
                header = ET.SubElement(record, 'header')

                # identifier elements
                identifier = ET.SubElement(header, 'identifier')
                identifier.text = 'collections.archives.caltech.edu' + do
                identifier.attrib = {'type': 'digital'}

                identifier = ET.SubElement(header, 'identifier')
                identifier.text = 'collections.archives.caltech.edu' + ao
                identifier.attrib = {'type': 'archival'}

                identifier = ET.SubElement(header, 'identifier')
                identifier.text = 'collections.archives.caltech.edu' + setid
                identifier.attrib = {'type': 'collection'}

                # datestamp element
                datestamp = ET.SubElement(header, 'datestamp')
                datestamp.text = today

                # setSpec element
                setspec = ET.SubElement(header, 'setSpec')
                setspec.text = coll[0]

                # metadata element
                metadata = ET.SubElement(record, 'metadata')

                # dc element
                dc = ET.SubElement(metadata, 'oai_dc:dc', {'xmlns:oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                                                       'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
                                                       'xmlns:dcterms': 'http://purl.org/dc/terms/'})
                
                # title elements
                title = ET.SubElement(dc, 'dc:title')
                title.text = client.get(do).json()['title']
                title.attrib = {'type': 'digital'}

                title = ET.SubElement(dc, 'dc:title')
                title.text = client.get(ao).json()['title']
                title.attrib = {'type': 'archival'}

                title = ET.SubElement(dc, 'dc:title')
                title.text = client.get(setid).json()['title']
                title.attrib = {'type': 'collection'}

                # ancestor titles
                print('testing:', ao[33:])
                ancestors = get_ancestors('archival_objects', ao[33:])
                print(ancestors)
                for a in ancestors:
                    if a:
                        ancestor = ET.SubElement(dc, 'dc:title')
                        ancestor.text = a[0]
                        if a[1]:
                            ancestor.attrib = {'level': a[1]}

                # relation element
                relation = ET.SubElement(dc, 'dc:relation')
                relation.text = collectiontitle
                relation.attrib = {'label': 'Collection'}

                # description element
                description = ET.SubElement(dc, 'dc:description')
                description.text = 'Digital object in ' + collectiontitle

                # identifier element
                identifier = ET.SubElement(dc, 'dc:identifier')
                identifier.text = file_uri
                identifier.attrib = {'scheme': 'URI', 'type': 'resource'}

                # dates
                dates = get_dates('archival_objects', ao[33:])
                #print(ao[33:])
                #print(dates)
                for d in dates:
                    if d != '':
                        date = ET.SubElement(dc, 'dc:date')
                        date.text = d                

                # extents
                extents = get_extents('archival_objects', ao[33:])
                #print(extents)
                for e in extents:
                    if e != '':
                        extent = ET.SubElement(dc, 'dc:format')
                        extent.text = e

                # subjects
                subjects = get_subjects('archival_objects', ao[33:])
                #print(subjects)
                for s in subjects:
                    if s:
                        subject = ET.SubElement(dc, 'dc:subject')
                        subject.text = s[0]
                        if s[1]:
                            subject.attrib = {'source': s[1]}

                recs_created += 1
                print(recs_created, end='\r')

            except:
                
                recs_skipped += 1
                dao_skipped += 1

            #temp
            if j > 5:
                break
            j += 1

        print('>', recs_created, 'records created')
        print('>', recs_skipped, 'records skipped')
        print('>', round(time.time() - intertime, 1), 'secs', '(' + datetime.now().isoformat() + ')')
        intertime = time.time()

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
fileout = Path(Path(__file__).resolve().parent).joinpath('../xml/caltecharchives.xml')
with open(fileout, 'w') as f:
    f.write(prettify(oaixml))

'''
for collection in dao_dict:
    print(collection)
    for url in dao_dict[collection]:
        print('>', url, dao_dict[collection][url])
'''

print(dao_count, 'total records created')
print(dao_skipped, 'total records skipped')

#print(dao_dict)

#print(urls)

print('Total elapsed time:', round(time.time() - start, 1))

print('Done.')