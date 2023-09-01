#This code block pulls xml from url and save to file; only needed to update the local file; comment out after first run
import requests
#url = 'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/124&metadataPrefix=oai_ead'
#url = 'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/197&metadataPrefix=oai_ead'
url = 'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/34&metadataPrefix=oai_ead'
response = requests.get(url)
with open('aspace.xml', 'wb') as file:
   file.write(response.content)

import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from datetime import date

#string form of date to write to each record
today = date.today().strftime("%Y-%m-%d")

#returns a pretty-printed XML string for on-screen display
def prettify(elem):
    xml_string = ET.tostring(elem)
    xml_file = dom.parseString(xml_string)
    pretty_xml = xml_file.toprettyxml(indent="  ")
    return pretty_xml

#builds xml for each record
def buildrecordxml(listrecords, c, collectiontitle, inheriteddata):
    record = ET.SubElement(listrecords, 'oai:record')
    header = ET.SubElement(record, 'oai:header')
    identifier = ET.SubElement(header, 'oai:identifier')
    identifier.text = 'oai:archives.caltech.edu:' + c.attrib['id']
    datestamp = ET.SubElement(header, 'oai:datestamp')
    datestamp.text = today
    metadata = ET.SubElement(record, 'oai:metadata')
    dc = ET.SubElement(metadata, 'oai_dc:dc', {'xmlns:oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                                           'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
                                           'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                                           'xsi:schemaLocation': 'http://www.openarchives.org/OAI/2.0/oai_dc/ http:// www.openarchives.org/OAI/2.0/oai_dc.xsd'})
    for unittitle in c.findall('.//unittitle', ns):
        title = ET.SubElement(dc, 'dc:title')
        title.text = unittitle.text
    title = ET.SubElement(dc, 'dc:title')
    title.text = collectiontitle
    if inheriteddata['seriestitle'] is not None:
        title = ET.SubElement(dc, 'dc:title')
        title.text = inheriteddata['seriestitle']
    if inheriteddata['subseriestitle'] is not None:
        title = ET.SubElement(dc, 'dc:title')
        title.text = inheriteddata['subseriestitle']
    for creat in c.findall('.//origination/persname', ns):
        creator = ET.SubElement(dc, 'dc:creator')
        creator.text = creat.text
        creator.attrib = {'scheme': creat.attrib['source']}
    for creat in c.findall('.//origination/corpname', ns):
        creator = ET.SubElement(dc, 'dc:creator')
        creator.text = creat.text
        creator.attrib = {'scheme': creat.attrib['source']}
    for unitdate in c.findall('.//unitdate', ns):
        date = ET.SubElement(dc, 'dc:date')
        date.text = unitdate.text
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
    for unitid in c.findall('.//unitid', ns):
        identifier = ET.SubElement(dc, 'dc:identifier')
        identifier.text = unitid.text
    for daoloc in c.findall('.//daoloc', ns):
        identifier = ET.SubElement(dc, 'dc:identifier')
        identifier.text = daoloc.attrib['{http://www.w3.org/1999/xlink}href']
        identifier.attrib = {'scheme': 'URI'}
    return listrecords


ns = {'': 'urn:isbn:1-931666-22-9', 'xlink': 'http://www.w3.org/1999/xlink',
      'xsi': "http://www.w3.org/2001/XMLSchema-instance"}
ET.register_namespace('', 'urn:isbn:1-931666-22-9')
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')

#read OAI finding aid
tree = ET.parse('aspace.xml')
root = tree.getroot()

#isolate the EAD portion of the file
ead = root.findall('.//ead', ns)[0]
#isolate the archdesc portion of the file
archdesc = ead.findall('.//archdesc', ns)[0]
#isolate the dsc portion of the file
dsc = archdesc.findall('.//dsc', ns)[0]
#save the collection title to write to each DV record
collectiontitle = archdesc.findall('.//did/unittitle', ns)[0].text
collectionid = ead.find('.//eadid', ns).text
fileout = collectionid + '.xml'

from xml.dom import minidom

oaixml = ET.Element('Repository', {'xmlns': 'http://www.openarchives.org/OAI/2.0/static-repository',
                    'xmlns:oai': 'http://www.openarchives.org/OAI/2.0/',
                    'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                    'xsi:schemaLocation': 'http://www.openarchives.org/OAI/2.0/static-repository http://www.openarchives.org/OAI/2.0/static-repository.xsd'})
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

ListMetadataFormats = ET.SubElement(oaixml, 'ListMetadataFormats')
metadataFormat = ET.SubElement(ListMetadataFormats, 'oai:metadataFormat')
metadataPrefix = ET.SubElement(metadataFormat, 'oai:metadataPrefix')
metadataPrefix.text = "oai_dc"
schema = ET.SubElement(metadataFormat, 'oai:schema')
schema.text = "http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
metadataNamespace = ET.SubElement(metadataFormat, 'oai:metadataNamespace')
metadataNamespace.text = "http://www.openarchives.org/OAI/2.0/oai_dc/"

ListRecords = ET.SubElement(oaixml, 'ListRecords', {
                            'metadataPrefix': 'oai_ead'})

for c in dsc.findall('.//*[@level="series"]', ns):
    inheriteddata = {'seriestitle': None, 'subseriestitle': None, 'filetitle': None}
    if c.find('.//unittitle', ns) is not None:
        seriestitle = c.find('.//unittitle', ns).text
    else:
        seriestitle = '[Untitled]'
    #print('Series:', seriestitle)
    inheriteddata['seriestitle'] = seriestitle
    if c.findall('.//*[@level="subseries"]', ns):
        for c2 in c.findall('.//*[@level="subseries"]', ns):
            if c2.find('.//unittitle', ns) is not None:
                subseries = c2.find('.//unittitle', ns).text
            else:
                subseries = '[Untitled]'
            #print('--> Subseries:', subseries)
            inheriteddata['subseriestitle'] = subseries
            for c3 in c2.findall('.//*[@level="file"]', ns):
                if c3.find('.//unittitle', ns) is not None:
                    filetitle = c3.find('.//unittitle', ns).text
                else:
                    filetitle = '[Untitled]'
                #print('----> Title:', filetitle)
                inheriteddata['filetitle'] = filetitle
                ListRecords = buildrecordxml(ListRecords, c3, collectiontitle, inheriteddata)
    else:
        for c4 in c.findall('.//*[@level="file"]', ns):
            if c4.find('.//unittitle', ns) is not None:
                filetitle = c4.find('.//unittitle', ns).text
            else:
                filetitle = '[Untitled]'
            #print('----> Title:', filetitle)
            inheriteddata['filetitle'] = filetitle
            ListRecords = buildrecordxml(ListRecords, c4, collectiontitle, inheriteddata)

#display the output
print(prettify(oaixml))

#write to disk
with open(fileout, 'w') as f:
    f.write(prettify(oaixml))