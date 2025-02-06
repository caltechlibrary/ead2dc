import requests, json
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
    setspec.text = setid
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

#builds inherited data for each record; XML build is triggered if digital object is present
#c is the container object
#n is the level of the container
def inheritdata(c, n):
    e = c.find('./did/unittitle', ns)
    if e is not None:
        title = (c.attrib['level'], e.text)
    else:
        title = ('', '')
    if len(inheriteddata) < n:
        inheriteddata.append(title)
    elif len(inheriteddata) == n:
        inheriteddata[n-1] = title
    else:
        for i in range(len(inheriteddata)):
            if i >= n:
                inheriteddata.pop()
        inheriteddata[n-1] = title
    
    # temp
    if True:
    #if locatedao(c):
        buildrecordxml(ListRecords, c, collectiontitle, inheriteddata)
    return

#loop over c recursively
def containerloop(container):
    global n
    first = True
    for c in container.findall('./c', ns):
        if first:
            first = False
            n += 1
        #print(n, c.attrib['id'], c.attrib['level'])
        inheritdata(c, n)
        containerloop(c)
        if not first:
            n -= 1
            first = True
    return

# checks if digital object is present
# old version: dao are in OAI
'''
def locatedao(c):    
    if c.find('./did/daogrp/daoloc', ns) is not None:
        return True
    elif c.find('./did/dao', ns) is not None:
        return True
    else:
        return False
'''
# new version
def locatedao(c):
    global dao_count
    try:
        id_type = c.find('./did/unitid', ns).attrib['type']
        if id_type == 'aspace_uri':
            print(c.find('./did/unitid', ns).text)
            dao_count += 1
    except:
        print('error: no aspace_uri')
    return True
    
# read collection info from db
def read_colls_from_db():
    connection = sq.connect(dbpath)
    db = connection.cursor()
    query = 'SELECT collno,eadurl,colltitle,description,collid,docount,incl,carchives,clibrary,iarchive,youtube,other FROM collections'
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

    query = 'INSERT INTO collections (collno,eadurl,colltitle,description,collid,docount,incl,carchives,clibrary,iarchive,youtube,other) VALUES (?,?,?,?,?,?,?,?,?,?,?,?);'
    for coll in colls:
        coll_info = client.get(coll).json()
        collid = coll_info['uri']
        collno = collid[:26]
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
        db.execute(query, [collno, eadurl, colltitle, description, collid, coll[5], 
                           coll[6], coll[7], coll[8], coll[9], coll[10], coll[11]])
    
    db.close()
    connection.commit()
    connection.close()
    return

# MAIN

# read config file
print('Reading config file...')
with open(Path(Path(__file__).resolve().parent).joinpath('config.json'), "r") as f:
    config = json.load(f)

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
                        print('> added', coll)

print('Number of digital objects:', dao_count)
print('Number of collections with digital objects:', len(collections))
print('Collections with digital objects...')

for item in collections_dict.items():
    # print title of collection and number of digital objects
    print(client.get(item[0]).json()['title'], ':', len(item[1]), 'digital objects')
    # iterate over digital objects and archival objects

    # temp
    i = 0

    for do, ao in item[1]:

        # temp
        #print(item[0], do, ao)
        i += 1
        if i > 2:
            break

        generator = (file_version for file_version in client.get(do).json()['file_versions']
                     if file_version['publish'] == True
                     and file_version.get('use_statement', 'ok') not in ['image-thumbnail', 'URL-Redirected'])
        try:
            do_title = client.get(ao).json()['title']
        except:
            do_title = 'no title'
            print('no title')
        try:
            file_uri = next(generator)['file_uri']
        except:
            print('no file uri')

# update collections info in database
# updates collno, colltitle, description, eadurl
# does not update docount, incl, carchives clibrary, iarchive, youtube, other, collid
update_db(collections)

# read collections from database
colls = read_colls_from_db()

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
    print(coll)
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
dao_dict = dict()

# build ListRecords segment
ListRecords = ET.SubElement(oaixml, 'ListRecords', {'metadataPrefix': 'oai_dc'})

print('Building static repository...')

for coll in colls: 
    
    setid = coll[0]
    collectiontitle = coll[2]
    dao_dict[setid] = dict() # initialize dictionary for collection's statistics

    urls = set()

    print(collectiontitle)

    # temp
    j=0

    if collections_dict.get(setid):
        print('found setid')
    
        for do, ao in collections_dict[setid]:

            #temp
            j += 1
            if j > 5:
                break

            generator = (file_version for file_version in client.get(do).json()['file_versions']
                         if file_version['publish'] == True
                         and file_version.get('use_statement', 'ok') not in ['image-thumbnail', 'URL-Redirected'])
            try:
                do_title = client.get(ao).json()['title']
            except:
                do_title = 'no title'
                print('no title')
            try:
                file_uri = next(generator)['file_uri']
                url = urlparse(file_uri).hostname
                print(url)
                if url not in urls:
                    urls.add(url)
                    if dao_dict[setid].get(url):
                        dao_dict[setid][url] += 1
                    else:
                        dao_dict[setid][url] = 1
                dao_count += 1

                #create record element
                record = ET.SubElement(ListRecords, 'record')
                header = ET.SubElement(record, 'header')
                identifier = ET.SubElement(header, 'identifier')
                identifier.text = 'collections.archives.caltech.edu' + do
                datestamp = ET.SubElement(header, 'datestamp')
                datestamp.text = today
                setspec = ET.SubElement(header, 'setSpec')
                setspec.text = setid
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
                identifier.text = 'collections.archives.caltech.edu' + file_uri
                identifier.attrib = {'scheme': 'URI', 'type': 'resource'}
            except:
                print('no file uri, record not created')

    else:
        print('no setid')

'''
    # read EAD for collection
    response = requests.get(coll[1])
    root = ET.fromstring(response.content)

    if root.find('.//archdesc', ns) is None:
        continue

    #isolate the EAD portion of the file
    ead = root.find('.//ead', ns)
    #isolate the archdesc portion of the file
    archdesc = ead.find('.//archdesc', ns)
    #isolate the dsc portion of the file
    dsc = archdesc.find('.//dsc', ns)
    #save the collection title & id
    collectiontitle = archdesc.find('.//did/unittitle', ns).text
    collectionid = archdesc.find('.//did/unitid', ns).text

    # build ListRecords segment
    ListRecords = ET.SubElement(oaixml, 'ListRecords', {'metadataPrefix': 'oai_dc'})
    # iterate over containers to collect inherited data and build records
    # iteration over containers

    # version without enumeration of c

    # temp
    k = 0

    for c in dsc.findall('./c', ns):

        # temp
        k += 1
        if k > 2:
            break

        n = 1
        inheriteddata = list()
        inheritdata(c, n)
        #print(n, c.attrib['id'], c.attrib['level'])
        containerloop(c)
'''

#write to disk
fileout = Path(Path(__file__).resolve().parent).joinpath('../xml/caltecharchives.xml')
with open(fileout, 'w') as f:
    f.write(prettify(oaixml))

print(dao_count)

print(dao_dict)
