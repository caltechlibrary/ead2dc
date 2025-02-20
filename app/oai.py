import requests, json, time
import sqlite3 as sq
import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from asnake.client import ASnakeClient

# FUNCTIONS

# returns a "pretty" XML string
def prettify(elem):
    xml_string = ET.tostring(elem)
    xml_file = dom.parseString(xml_string)
    pretty_xml = xml_file.toprettyxml(indent="  ")
    return pretty_xml

# builds XML for each record and adds to ListRecords segment
def buildrecordxml(listrecords, c, collectiontitle, inheriteddata):
    global no_records, setid
    #create record element
    record = ET.SubElement(listrecords, 'record')
    header = ET.SubElement(record, 'header')
    identifier = ET.SubElement(header, 'identifier')
    try:
        #construct id from aspace uri
        identifier.text = 'collections.archives.caltech.edu' + c.find('./did/unitid[@type="aspace_uri"]', ns).text
    except:
        #construct id from aspace id
        identifier.text = 'archives.caltech.edu:' + c.attrib['id']

    datestamp = ET.SubElement(header, 'datestamp')
    datestamp.text = today
    setspec = ET.SubElement(header, 'setSpec')
    setspec.text = setid[26:]
    metadata = ET.SubElement(record, 'metadata')
    dc = ET.SubElement(metadata, 'oai_dc:dc', {'xmlns:oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                                           'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
                                           'xmlns:dcterms': 'http://purl.org/dc/terms/'})
    #title = file/item title from current container
    title = ET.SubElement(dc, 'dc:title')
    title.text = inheriteddata[-1][1]
    #collection title
    relation = ET.SubElement(dc, 'dc:relation')
    relation.text = collectiontitle
    relation.attrib = {'label': 'Collection'}
    #inherited titles from parent containers
    for titledata in inheriteddata[:-1]:
        relation = ET.SubElement(dc, 'dc:relation')
        relation.text = titledata[1]
        relation.attrib = {'label': titledata[0].title()}
    #creator (persname) from current container
    for creat in c.findall('.//origination/persname', ns):
        creator = ET.SubElement(dc, 'dc:creator')
        creator.text = creat.text
        if creat.attrib.get('source'):
            creator.attrib = {'scheme': creat.attrib['source']}
    #creator (corpname) from current container
    for creat in c.findall('.//origination/corpname', ns):
        creator = ET.SubElement(dc, 'dc:creator')
        creator.text = creat.text
        if creat.attrib.get('source'):
            creator.attrib = {'scheme': creat.attrib['source']}
    #date from current container
    for unitdate in c.findall('.//unitdate', ns):
        date = ET.SubElement(dc, 'dc:date')
        date.text = unitdate.text
    #format from current container
    for fmt in c.findall('.//physdesc/extent', ns):
        format = ET.SubElement(dc, 'dc:extent')
        format.text = fmt.text
    #description from current container
    for desc in c.findall('.//abstract', ns):
        description = ET.SubElement(dc, 'dc:description')
        description.text = desc.text
    #subjects from current container
    for subj in c.findall('.//controlaccess/subject', ns):
        subject = ET.SubElement(dc, 'dc:subject')
        subject.text = subj.text
        if subj.attrib.get('source'):
            subject.attrib = {'scheme': subj.attrib['source']}
    for geog in c.findall('.//controlaccess/geogname', ns):
        subject = ET.SubElement(dc, 'dc:subject')
        subject.text = geog.text
        if geog.attrib.get('source'):
            subject.attrib = {'scheme': geog.attrib['source']}
    for pers in c.findall('.//controlaccess/persname', ns):
        subject = ET.SubElement(dc, 'dc:subject')
        subject.text = pers.text
        if pers.attrib.get('source'):
            subject.attrib = {'scheme': pers.attrib['source']}
    for corp in c.findall('.//controlaccess/corpname', ns):
        subject = ET.SubElement(dc, 'dc:subject')
        subject.text = corp.text
        if corp.attrib.get('source'):
            subject.attrib = {'scheme': corp.attrib['source']}
    for func in c.findall('.//controlaccess/function', ns):
        subject = ET.SubElement(dc, 'dc:subject')
        subject.text = func.text
        if func.attrib.get('source'):
            subject.attrib = {'scheme': func.attrib['source']}
    #identifiers from current container
    for unitid in c.findall('.//unitid', ns):
        identifier = ET.SubElement(dc, 'dc:identifier')
        text = unitid.text
        if text[:14]=='/repositories/':
            text = 'collections.archives.caltech.edu' + text
        identifier.text = text
    #links from current container
    for daoloc in c.findall('.//daoloc', ns):
        identifier = ET.SubElement(dc, 'dc:identifier')
        text = daoloc.attrib['{http://www.w3.org/1999/xlink}href']
        identifier.text = text
        if 'img.archives.caltech.edu' in text:
            identifier.attrib = {'scheme': 'URI', 'type': 'thumbnail'}
        else:
            identifier.attrib = {'scheme': 'URI', 'type': 'resource'}
    for dao in c.findall('.//dao', ns):
        identifier = ET.SubElement(dc, 'dc:identifier')
        text = dao.attrib['{http://www.w3.org/1999/xlink}href']
        type = dao.attrib['{http://www.w3.org/1999/xlink}type']
        identifier.text = text
        identifier.attrib = {'scheme': 'URI', 'type': type}
    no_records += 1
    return listrecords

# MAIN

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

print('Building collections dictionary...')

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
                        print('> added', coll, client.get(coll).json()['title'])

print('> summary', dao_count, 'digital objects')
print('> summary', len(collections), 'collections with digital objects')
            
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

# write ISO last update
now = datetime.now()
last_update = now.isoformat()
    
query = 'UPDATE last_update SET dt=? WHERE fn=?;'
cursor.execute(query, [last_update, 'xml'])
  
# delete all records from db
query = 'DELETE FROM collections;'
cursor.execute(query)

query = 'INSERT INTO collections (collno,eadurl,colltitle,description,collid,docount,incl,carchives,clibrary,iarchive,youtube,other) VALUES (?,?,?,?,?,?,?,?,?,?,?,?);'
for collectionid in collections:
    coll_info = client.get(collectionid).json()
    collid = coll_info['uri']
    collno = collid[26:]
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
            includedcollections.get(collectionid[:26], 0), 0, 0, 0, 0, 0])

# commit changes to db before reading
connection.commit()

# read collection info from db
# colls is a list of tuples
query = 'SELECT collno,eadurl,colltitle,description,collid,docount,incl,carchives,clibrary,iarchive,youtube,other FROM collections'
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

    recs_created = 0
    recs_skipped = 0

    setid = '/repositories/2/resources/' + coll[0]
    collectiontitle = coll[2]
    dao_dict[setid] = dict() # initialize dictionary for collection's statistics

    print(collectiontitle)

    # temp
    #j=0

    if collections_dict.get(setid):
    
        for do, ao in collections_dict[setid]:

            #temp
            #j += 1
            #if j > 5:
            #    break

            generator = (file_version for file_version in client.get(do).json()['file_versions']
                         if file_version['publish'] == True
                         and file_version.get('use_statement', 'ok') 
                         not in ['image-thumbnail', 'URL-Redirected'])
            try:
                do_title = client.get(ao).json()['title']
            except:
                do_title = 'no title'
                print('> no title')
            try:
                file_uri = next(generator)['file_uri']
                url = urlparse(file_uri).hostname
                if url == 'resolver.caltech.edu' or url == 'www.annualreviews.org':
                    hostcategory = 'clibrary'
                elif url == 'archive.org':
                    hostcategory = 'iarchive'
                elif url == 'digital.archives.caltech.edu' or url == 'californiarevealed.org':
                    hostcategory = 'carchives'
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

                #create record element
                record = ET.SubElement(ListRecords, 'record')
                header = ET.SubElement(record, 'header')
                identifier = ET.SubElement(header, 'identifier')
                identifier.text = 'collections.archives.caltech.edu' + do
                datestamp = ET.SubElement(header, 'datestamp')
                datestamp.text = today
                setspec = ET.SubElement(header, 'setSpec')
                setspec.text = coll[0]
                metadata = ET.SubElement(record, 'metadata')
                dc = ET.SubElement(metadata, 'oai_dc:dc', {'xmlns:oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                                                       'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
                                                       'xmlns:dcterms': 'http://purl.org/dc/terms/'})
                title = ET.SubElement(dc, 'dc:title')
                title.text = do_title
                relation = ET.SubElement(dc, 'dc:relation')
                relation.text = collectiontitle
                relation.attrib = {'label': 'Collection'}
                description = ET.SubElement(dc, 'dc:description')
                description.text = 'Digital object in ' + collectiontitle
                identifier = ET.SubElement(dc, 'dc:identifier')
                identifier.text = file_uri
                identifier.attrib = {'scheme': 'URI', 'type': 'resource'}

                recs_created += 1

            except:
                
                recs_skipped += 1
                dao_skipped += 1

    else:
        print('> no setid')

    print('>', recs_created, 'records created')
    print('>', recs_skipped, 'records skipped')

    print('>', round(time.time() - intertime, 1), 'secs')
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