import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from datetime import date

#FUNCTIONS

#returns a pretty-printed XML string for on-screen display
def prettify(elem):
    xml_string = ET.tostring(elem)
    xml_file = dom.parseString(xml_string)
    pretty_xml = xml_file.toprettyxml(indent="  ")
    return pretty_xml

# builds xml for each record and adds to ListRecords segment
def buildrecordxml(listrecords, c, collectiontitle, inheriteddata):
    global no_records, setid
    #create record element
    record = ET.SubElement(listrecords, 'record')
    header = ET.SubElement(record, 'header')
    identifier = ET.SubElement(header, 'identifier')
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
        text = daoloc.attrib['{http://www.w3.org/1999/xlink}href']
        identifier.text = text
        if 'img.archives.caltech.edu' in text:
            identifier.attrib = {'scheme': 'URI', 'type': 'thumbnail'}
        else:
            identifier.attrib = {'scheme': 'URI', 'type': 'resource'}
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


# string form of date to write to each record
today = date.today().strftime("%Y-%m-%d")


# Collections
colls = list()
# George Ellery Hale Papers
colls.append(['HaleGE',
              'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/124&metadataPrefix=oai_ead',
              'George Ellery Hale Papers',
              "George Ellery Hale(1868-1938) was an influential astrophysicist and science administrator. This collection of Hale's scientific, professional, and personal papers documents his roles in inventing the spectrohelioscope; promoting international cooperation among scientists; and founding major observatories, as well as the California Institute of Technology, Huntington Library, Astrophysical Journal, and National Research Council."])
# Paul B. MacCready Papers
colls.append(['MacCreadyPB',
              'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/197&metadataPrefix=oai_ead',
              'Paul B. MacCready Papers',
              "Arriving on December 30th 2003, the collection documents most aspects of MacCready's career and many features of his individual character. Constituted within the papers is a diverse array of documents, media, objects, manuscripts and printed material; awards; videos and film; photographs and slides, diaries and notebooks; memorabilia, biographical material and ephemera. While the collection spans over seventy years (ca. 1930-2002), the bulk of material dates from the mid 1960s to the mid '90s. Especially prevalent within the collection are papers and ephemera from 1977 to 1985 during which time MacCready was working on his Gossamers and interest in human-powered flight was at its peak"])
# Donald A. Glaser Papers
colls.append(['GlaserDA',
              'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/34&metadataPrefix=oai_ead',
              'Donald A. Glaser Papers',
              "Donald Arthur Glaser (1926-2013) earned his PhD in Physics and Mathematics from the California Institute of Technology in 1950 and won the 1960 Nobel Prize in Physics for his invention of the bubble chamber. He then changed his research focus to molecular biology and went on to co-found Cetus Corporation, the first biotechnology company. In the 1980s he again switched his focus to neurobiology and the visual system. The Donald A. Glaser papers consist of research notes and notebooks, manuscripts and printed papers, correspondence, awards, biographical material, photographs, audio-visual material, and born-digital files. This finding aid is an intellectual arrangement of two collections: first portion originally from the University of California Berkeley, Bancroft Library and the second from the Caltech Archives."])
# Caltech Images Collection
colls.append(['Photographs',
              'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/219&metadataPrefix=oai_ead',
              'Caltech Images Collection',
              "Caltech Images is a collection of over ten thousand images representing Caltech's history and the people who have contributed to the Caltech story. It includes historic and contemporary photographs of people and places, reproductions of historic scientific artifacts and art, and illustrations drawn from Caltech's rare book collection in the history of science and technology."])
# Palomar Observatory Records
colls.append(['Palomar',
              'https://collections.archives.caltech.edu/oai?verb=GetRecord&identifier=/repositories/2/resources/228&metadataPrefix=oai_ead',
              'Palomar Observatory Records',
              'In an ongoing effort led by Jean Mueller, the Caltech Library, and funded by the Riesenfeld family, a collection of telescope logbooks, spanning the years 1936-2012, have been scanned and made available online.'])

print('Building OAI-PMH XML...')

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
#    setdescription = ET.SubElement(set, 'setDescription')
#    oaidcdc = ET.SubElement(setdescription, 'dc')
#    dc = ET.SubElement(oaidcdc, 'description')
#    dc.text = 'some text'

    setDescription = ET.SubElement(ET.SubElement(ET.SubElement(
        set, 'setDescription'), 'oai_dc', {'xmlns:oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                                           'xmlns:dc': 'http://purl.org/dc/elements/1.1/'}), 'dc:description')
    setDescription.text = coll[3]


no_records = 0


for coll in colls:   

    setid = coll[0]

    print('Reading ' + coll[0] + '...')
    response = requests.get(coll[1])
    with open('aspace.xml', 'wb') as file:
        file.write(response.content)

    #read OAI finding aid
    print('Writing ' + coll[0] + '...')
    tree = ET.parse('aspace.xml')
    root = tree.getroot()

    #isolate the EAD portion of the file
    ead = root.find('.//ead', ns)
    #isolate the archdesc portion of the file
    archdesc = ead.find('.//archdesc', ns)
    #isolate the dsc portion of the file
    dsc = archdesc.find('.//dsc', ns)
    #save the collection title
    collectiontitle = archdesc.find('.//did/unittitle', ns).text

    #construct a filename for output
    #try:
    #    fileid = 'caltecharchives'+root.find('.//{*}request', ns).attrib['identifier'].replace('/', '-')
    #except:
    #    try:
    #        fileid = ead.find('.//eadid', ns).text
    #    except:
    #        fileid = 'caltecharchives'
    #fileout = fileid + '.xml'
    fileout = 'caltecharchives.xml'

    #build ListRecords segment
    ListRecords = ET.SubElement(oaixml, 'ListRecords', {'metadataPrefix': 'oai_ead'})
    #iterate over containers to collect inherited data and build records
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


#insert ListSets segment into oaixml
#oaixml.insert(0, ListSets)


#display the output
print(prettify(oaixml))
print()
print('Total records: ' + str(no_records))

#write to disk
with open(fileout, 'w') as f:
    f.write(prettify(oaixml))

#tree = ET.ElementTree(oaixml)
#tree.write('caltecharchives.xml', encoding='utf-8', xml_declaration=True)

#tree = ET.ElementTree(ListSets)
#tree.write('sets.xml', encoding='utf-8', xml_declaration=True)