#import requests
#url = 'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/124&metadataPrefix=oai_ead'
#response = requests.get(url)
#with open('aspace.xml', 'wb') as file:
#   file.write(response.content)

import xml.etree.ElementTree as ET
import xml.dom.minidom

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    xml_string = ET.tostring(elem)
    xml_file = xml.dom.minidom.parseString(xml_string)
    pretty_xml = xml_file.toprettyxml(indent="  ")
    return pretty_xml

ns = {'': 'urn:isbn:1-931666-22-9', 'xlink': 'http://www.w3.org/1999/xlink',
      'xsi': "http://www.w3.org/2001/XMLSchema-instance"}
ET.register_namespace('', 'urn:isbn:1-931666-22-9')
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')

tree = ET.parse('aspace.xml')
root = tree.getroot()

ead = root.findall('.//ead', ns)[0]
archdesc = ead.findall('.//archdesc', ns)[0]
dsc = archdesc.findall('.//dsc', ns)[0]

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

ListRecords = ET.SubElement(oaixml, 'ListRecords', {'metadataPrefix': 'oai_ead'})
for i, did in enumerate(dsc.findall('.//*[@level="file"]/did', ns)):
    record = ET.SubElement(ListRecords, 'oai:record')
    header = ET.SubElement(record, 'oai:header')
    identifier = ET.SubElement(header, 'oai:identifier')
    datestamp = ET.SubElement(header, 'oai:datestamp')
    metadata = ET.SubElement(record, 'oai:metadata')
    dc = ET.SubElement(metadata, 'oai_dc:dc', {'xmlns:oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                                 'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
                                 'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                                 'xsi:schemaLocation': 'http://www.openarchives.org/OAI/2.0/oai_dc/ http:// www.openarchives.org/OAI/2.0/oai_dc.xsd'})
    for unittitle in did.findall('.//unittitle', ns):
        title = ET.SubElement(dc, 'dc:title')
        title.text = unittitle.text
    creator = ET.SubElement(dc, 'dc:creator')
    creator.text = 'creator...'
    for unitdate in did.findall('.//unitdate', ns):
        date = ET.SubElement(dc, 'dc:date')
        date.text = unitdate.text
    type = ET.SubElement(dc, 'dc:type')
    type.text = 'type...'
    subject = ET.SubElement(dc, 'dc:subject')
    subject.text = 'subject...'
    description = ET.SubElement(dc, 'dc:description')
    description.text = 'description...'
    for unitid in did.findall('.//unitid', ns):
        identifier = ET.SubElement(dc, 'dc:identifier')
        identifier.text = unitid.text
    for daoloc in did.findall('.//daoloc', ns):
        relation = ET.SubElement(dc, 'dc:relation')
        #print(daoloc.attrib)
        relation.text = daoloc.attrib['{http://www.w3.org/1999/xlink}href']
    



print(prettify(oaixml))
print('record count:', i+1)
