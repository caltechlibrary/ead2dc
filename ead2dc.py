#This code block pulls xml from url and save to file; only needed to update the local file; comment out after first run
#George Ellery Hale Papers
#url = 'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/124&metadataPrefix=oai_ead'
#Paul B. MacCready Papers
url = 'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/197&metadataPrefix=oai_ead'
#Donald A. Glaser Papers
#url = 'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/34&metadataPrefix=oai_ead'
#Caltech Images Collection
#url = 'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/219&metadataPrefix=oai_ead'
import requests
response = requests.get(url)
with open('aspace.xml', 'wb') as file:
   file.write(response.content)

import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from datetime import date

#string form of date to write to each record
today = date.today().strftime("%Y-%m-%d")

#FUNCTIONS

#returns a pretty-printed XML string for on-screen display
def prettify(elem):
    xml_string = ET.tostring(elem)
    xml_file = dom.parseString(xml_string)
    pretty_xml = xml_file.toprettyxml(indent="  ")
    return pretty_xml

# builds xml for each record and adds to ListRecords segment
def buildrecordxml(listrecords, c, collectiontitle, inheriteddata):
    #create record element
    record = ET.SubElement(listrecords, 'oai:record')
    header = ET.SubElement(record, 'oai:header')
    identifier = ET.SubElement(header, 'oai:identifier')
    #construct id from aspace id
    identifier.text = 'oai:archives.caltech.edu:' + c.attrib['id']
    datestamp = ET.SubElement(header, 'oai:datestamp')
    datestamp.text = today
    metadata = ET.SubElement(record, 'oai:metadata')
    dc = ET.SubElement(metadata, 'oai_dc:dc', {'xmlns:oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                                           'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
                                           'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                                           'xsi:schemaLocation': 'http://www.openarchives.org/OAI/2.0/oai_dc/ http:// www.openarchives.org/OAI/2.0/oai_dc.xsd'})
    #title = file/item title from current container
    title = ET.SubElement(dc, 'dc:title')
    title.text = inheriteddata[-1]
    #collection title
    title = ET.SubElement(dc, 'dc:title')
    title.text = collectiontitle
    #inherited titles from parent containers
    for titledata in inheriteddata[:-1]:
        title = ET.SubElement(dc, 'dc:title')
        title.text = titledata
    #creator (persname) from current container
    for creat in c.findall('.//origination/persname', ns):
        creator = ET.SubElement(dc, 'dc:creator')
        creator.text = creat.text
        creator.attrib = {'scheme': creat.attrib['source']}
    #creator (corpname) from current container
    for creat in c.findall('.//origination/corpname', ns):
        creator = ET.SubElement(dc, 'dc:creator')
        creator.text = creat.text
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
        subject.attrib = {'scheme': subj.attrib['source']}
    for geog in c.findall('.//controlaccess/geogname', ns):
        subject = ET.SubElement(dc, 'dc:subject')
        subject.text = geog.text
        subject.attrib = {'scheme': geog.attrib['source']}
    for pers in c.findall('.//controlaccess/persname', ns):
        subject = ET.SubElement(dc, 'dc:subject')
        subject.text = pers.text
        subject.attrib = {'scheme': pers.attrib['source']}
    for corp in c.findall('.//controlaccess/corpname', ns):
        subject = ET.SubElement(dc, 'dc:subject')
        subject.text = corp.text
        subject.attrib = {'scheme': corp.attrib['source']}
    for func in c.findall('.//controlaccess/function', ns):
        subject = ET.SubElement(dc, 'dc:subject')
        subject.text = func.text
        subject.attrib = {'scheme': func.attrib['source']}
    #identifiers from current container
    for unitid in c.findall('.//unitid', ns):
        identifier = ET.SubElement(dc, 'dc:identifier')
        identifier.text = unitid.text
    #links from current container
    for daoloc in c.findall('.//daoloc', ns):
        identifier = ET.SubElement(dc, 'dc:identifier')
        identifier.text = daoloc.attrib['{http://www.w3.org/1999/xlink}href']
        identifier.attrib = {'scheme': 'URI'}
    return listrecords

#builds inherited data for each record; XML build is triggered if digital object is present
#c is the container object
#n is the level of the container
def inheritdata(c, n):
    e = c.find('./did/unittitle', ns)
    if e is not None:
        title = e.text
    else:
        title = '[no title]'
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

#checks if digital object is present
def locatedao(c):
    if c.find('./did/daogrp/daoloc', ns) is not None:
        for daoloc in c.findall('./did/daogrp/daoloc', ns):
            if 'datastream' in daoloc.attrib['{http://www.w3.org/1999/xlink}href']:
                return False
        return True
    else:
        return False

#MAIN PROGRAM

#namespace dictionary
ns = {'': 'urn:isbn:1-931666-22-9', 'xlink': 'http://www.w3.org/1999/xlink',
      'xsi': "http://www.w3.org/2001/XMLSchema-instance"}
ET.register_namespace('', 'urn:isbn:1-931666-22-9')
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')

#read OAI finding aid
tree = ET.parse('aspace.xml')
root = tree.getroot()

#isolate the EAD portion of the file
ead = root.find('.//ead', ns)
#isolate the archdesc portion of the file
archdesc = ead.find('.//archdesc', ns)
#isolate the dsc portion of the file
dsc = archdesc.find('.//dsc', ns)
#save the collection title to write to each DC record
collectiontitle = archdesc.find('.//did/unittitle', ns).text
#construct a filename for output
try:
    fileid = 'caltecharchives'+root.find('.//{*}request', ns).attrib['identifier'].replace('/', '-')
except:
    try:
        fileid = ead.find('.//eadid', ns).text
    except:
        fileid = 'caltecharchives'
fileout = fileid + '.xml'

#create OAI-PMH XML object
oaixml = ET.Element('Repository', {'xmlns': 'http://www.openarchives.org/OAI/2.0/static-repository',
                    'xmlns:oai': 'http://www.openarchives.org/OAI/2.0/',
                    'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                    'xsi:schemaLocation': 'http://www.openarchives.org/OAI/2.0/static-repository http://www.openarchives.org/OAI/2.0/static-repository.xsd'})

#build Identify segment
Identify = ET.SubElement(oaixml, 'Identify')
repositoryName = ET.SubElement(Identify, 'oai:repositoryName')
repositoryName.text = 'Caltech Archives Digital Collections'
baseURL = ET.SubElement(Identify, 'oai:baseURL')
baseURL.text = 'http://gateway.institution.org/oai/an.oai.org/ma/mini.xml'
protocolVersion = ET.SubElement(Identify, 'oai:protocolVersion')
protocolVersion.text = '2.0'
adminEmail = ET.SubElement(Identify, 'oai:adminEmail')
adminEmail.text = 'archives@caltech.edu'
deletedRecord = ET.SubElement(Identify, 'oai:deletedRecord')
deletedRecord.text = 'no'
granularity = ET.SubElement(Identify, 'oai:granularity')
granularity.text = 'YYYY-MM-DD'

#build ListMetadataFormats segment
ListMetadataFormats = ET.SubElement(oaixml, 'ListMetadataFormats')
metadataFormat = ET.SubElement(ListMetadataFormats, 'oai:metadataFormat')
metadataPrefix = ET.SubElement(metadataFormat, 'oai:metadataPrefix')
metadataPrefix.text = "oai_dc"
schema = ET.SubElement(metadataFormat, 'oai:schema')
schema.text = "http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
metadataNamespace = ET.SubElement(metadataFormat, 'oai:metadataNamespace')
metadataNamespace.text = "http://www.openarchives.org/OAI/2.0/oai_dc/"

#build ListRecords segment
ListRecords = ET.SubElement(oaixml, 'ListRecords', {'metadataPrefix': 'oai_ead'})
#iterate over containers to collect inherited data and build records
for c01 in dsc.findall('.//c01', ns):
    inheriteddata = list()
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
                        for c07 in c05.findall('.//c07', ns):
                            inheritdata(c07, 7)
                            for c08 in c05.findall('.//c08', ns):
                                inheritdata(c08, 8)
                                for c09 in c05.findall('.//c09', ns):
                                    inheritdata(c09, 9)
                                    for c10 in c05.findall('.//c10', ns):
                                        inheritdata(c10, 10)
                                        for c11 in c05.findall('.//c11', ns):
                                            inheritdata(c11, 11)
                                            for c12 in c05.findall('.//c12', ns):
                                                inheritdata(c12, 12)


#display the output
print(prettify(oaixml))

#write to disk
with open(fileout, 'w') as f:
    f.write(prettify(oaixml))