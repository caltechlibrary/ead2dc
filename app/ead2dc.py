import requests, json
import sqlite3 as sq
import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from datetime import date, datetime
from pathlib import Path

#FUNCTIONS

#returns a "pretty" XML string
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
    if locatedao(c):
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

#checks if digital object is present
def locatedao(c):
    if c.find('./did/daogrp/daoloc', ns) is not None:
        return True
    elif c.find('./did/dao', ns) is not None:
        return True
    else:
        return False
    
#write time of last update to db
def update_last_update():
    # write ISO last update
    now = datetime.now()
    last_update = now.isoformat()
    connection = sq.connect(dbpath)
    db = connection.cursor()
    query = 'UPDATE last_update SET dt=? WHERE fn=?;'
    db.execute(query, [last_update, 'xml'])
    db.close()
    connection.commit()
    connection.close()
    return

#read collection info from db
def read_colls_from_db():
    connection = sq.connect(dbpath)
    db = connection.cursor()
    query = 'SELECT collno, eadurl, colltitle, description FROM collections'
    colls = db.execute(query).fetchall()
    db.close()
    connection.close()
    return colls

#MAIN PROGRAM

# read config file
with open(Path(Path(__file__).resolve().parent).joinpath('config.json'), "r") as f:
    config = json.load(f)

# db location
dbpath = Path(Path(__file__).resolve().parent).joinpath('../instance/ead2dc.db')

# string form of date to write to each record
today = date.today().strftime("%Y-%m-%d")

# load collection info as list of lists
'''
with open(Path(Path(__file__).resolve().parent).joinpath('collections.json'), 'r') as f:
    # reading from json file
    collection_dict = json.load(f)
colls = list()
for key in collection_dict:
    colls.append([key, 
                  collection_dict[key]['eadurl'], 
                  collection_dict[key]['title'], 
                  collection_dict[key]['description']])
'''
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

for coll in colls: 
    setid = coll[0]
    # read EAD for collection
    response = requests.get(coll[1])
    root = ET.fromstring(response.content)

    #isolate the EAD portion of the file
    ead = root.find('.//ead', ns)
    #isolate the archdesc portion of the file
    archdesc = ead.find('.//archdesc', ns)
    #isolate the dsc portion of the file
    dsc = archdesc.find('.//dsc', ns)
    #save the collection title & id
    collectiontitle = archdesc.find('.//did/unittitle', ns).text
    collectionid = archdesc.find('.//did/unitid', ns).text

    fileout = Path(Path(__file__).resolve().parent).joinpath('../xml/caltecharchives.xml')

    # version without enumeration of c
    for c in dsc.findall('./c', ns):
        n = 1
        inheriteddata = list(tuple())
        inheritdata(c, n)
        #print(n, c.attrib['id'], c.attrib['level'])
        containerloop(c)

    # build ListRecords segment
    # version with enumeration of c
    '''
    ListRecords = ET.SubElement(oaixml, 'ListRecords', {'metadataPrefix': 'oai_dc'}) 
    # iterate over containers to collect inherited data and build records
    for c01 in dsc.findall('.//c01', ns):
        inheriteddata = list(tuple())
        inheritdata(c01, 1)
        for c02 in c01.findall('.//c02', ns):
            inheritdata(c02, 2)
            for c03 in c02.findall('.//c03', ns):
                inheritdata(c03, 3)
                for c04 in c03.findall('.//c04', ns):
                    inheritdata(c04, 4)
                    for c05 in c04.findall('.//c05', ns):
                        inheritdata(c05, 5)
                        for c06 in c05.findall('.//c06', ns):
                            inheritdata(c06, 6)
                            for c07 in c06.findall('.//c07', ns):
                                inheritdata(c07, 7)
                                for c08 in c07.findall('.//c08', ns):
                                    inheritdata(c08, 8)
                                    for c09 in c08.findall('.//c09', ns):
                                        inheritdata(c09, 9)
                                        for c10 in c09.findall('.//c10', ns):
                                            inheritdata(c10, 10)
                                            for c11 in c10.findall('.//c11', ns):
                                                inheritdata(c11, 11)
                                                for c12 in c11.findall('.//c12', ns):
                                                    inheritdata(c12, 12)
    '''
#write to disk
with open(fileout, 'w') as f:
    f.write(prettify(oaixml))

update_last_update()