# import main Flask class and request object
from flask import Flask, request, Response
from datetime import date
import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from pathlib import Path

# namespace dictionary
ns = {'': 'http://www.openarchives.org/OAI/2.0/static-repository', 'oai': 'http://www.openarchives.org/OAI/2.0/',
      'xsi': "http://www.w3.org/2001/XMLSchema-instance", 'dc': 'http://purl.org/dc/elements/1.1/',
      'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/'
      }
ET.register_namespace('', 'http://www.openarchives.org/OAI/2.0/static-repository')
ET.register_namespace('oai', 'http://www.openarchives.org/OAI/2.0/')
ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
ET.register_namespace('oai_dc', 'http://www.openarchives.org/OAI/2.0/oai_dc/')

# read OAI finding aid
tree = ET.parse(Path(Path(__file__).resolve().parent).joinpath("caltecharchives.xml"))
root = tree.getroot()

# string form of date to write to each record
today = date.today().strftime("%Y-%m-%d")

# create the Flask app
app = Flask(__name__)

# returns a pretty-printed XML string
def prettify(elem):
    xml_string = ET.tostring(elem)
    xml_file = dom.parseString(xml_string)
    pretty_xml = xml_file.toprettyxml(indent="  ")
    return pretty_xml


@app.route('/')
def index():
    return 'Visit /OAI for something useful.'

@app.route('/oai')
def oai():
 
    verb = request.args.get('verb')
    set = request.args.get('set')


    if verb == 'Identify':

        elem = root.find('.//Identify', ns)
        # create OAI-PMH XML object
        oaixml = ET.Element('OAI-PMH')
        respDate = ET.SubElement(oaixml, 'responseDate')
        respDate.text = today
        rquest = ET.SubElement(oaixml, 'request')
        rquest.attrib = {'verb': 'Identify'}
        rquest.text = 'https://apps.library.caltech.edu/oai'
        identify = ET.SubElement(oaixml, 'Identify')
        for node in elem:
            identify.append(node)

    elif verb == 'ListMetadataFormats':

        elem = root.find('.//ListMetadataFormats', ns)
        # create OAI-PMH XML object
        oaixml = ET.Element('OAI-PMH')
        respDate = ET.SubElement(oaixml, 'responseDate')
        respDate.text = today
        rquest = ET.SubElement(oaixml, 'request')
        rquest.attrib = {'verb': 'ListMetadataFormats'}
        rquest.text = 'https://apps.library.caltech.edu/oai'
        listmetadataformats = ET.SubElement(oaixml, 'ListMetadataFormats')
        for node in elem:
            listmetadataformats.append(node)

    elif verb == 'ListSets':

        elem = root.find('.//ListSets', ns)
        # create OAI-PMH XML object
        oaixml = ET.Element('OAI-PMH')
        respDate = ET.SubElement(oaixml, 'responseDate')
        respDate.text = today
        rquest = ET.SubElement(oaixml, 'request')
        rquest.attrib = {'verb': 'ListSets'}
        rquest.text = 'https://apps.library.caltech.edu/oai'
        listsets = ET.SubElement(oaixml, 'ListSets')
        for node in elem:
            listsets.append(node)

    elif verb == 'ListRecords' or verb == 'ListIdentifiers':

        elem = root.find('.//ListRecords', ns)
        # create OAI-PMH XML object
        oaixml = ET.Element('OAI-PMH')
        respDate = ET.SubElement(oaixml, 'responseDate')
        respDate.text = today
        rquest = ET.SubElement(oaixml, 'request')
        rquest.attrib = {'verb': 'ListRecords'}
        rquest.text = 'https://apps.library.caltech.edu/oai'
        listrecords = ET.SubElement(oaixml, 'ListRecords')
        listrecords.attrib = {'metadataPrefix': 'oai_dc'}
        recrds = root.findall('.//{http://www.openarchives.org/OAI/2.0/}record')
        for recrd in recrds:

            if recrd.find('.//oai:setSpec', ns).text == set or set is None:

                record = ET.SubElement(listrecords, '{http://www.openarchives.org/OAI/2.0/}record')
                header = ET.SubElement(record, '{http://www.openarchives.org/OAI/2.0/}header')
                hdr = recrd.find('.//{http://www.openarchives.org/OAI/2.0/}header')
                for node in hdr:
                    header.append(node)

                if verb == 'ListRecords':

                    metadata = ET.SubElement(record, '{http://www.openarchives.org/OAI/2.0/}metadata')
                    dc = ET.SubElement(metadata, '{http://www.openarchives.org/OAI/2.0/oai_dc/}dc')
                    metad = recrd.find('.//{http://www.openarchives.org/OAI/2.0/oai_dc/}dc')
                    for node in metad:
                        dc.append(node)


    elif verb == 'GetRecord':

        identifier = request.args.get('identifier')
        if identifier is None:
            oaixml = ET.Element('noThing',)
            oaixml.text = "No identifier specified."
        else:
            # create OAI-PMH XML object
            oaixml = ET.Element('OAI-PMH')
            respDate = ET.SubElement(oaixml, 'responseDate')
            respDate.text = today
            rquest = ET.SubElement(oaixml, 'request')
            rquest.attrib = {'verb': 'GetRecord', 'identifier': identifier, 'metaDataPrefix': 'oai_dc'}
            rquest.text = 'https://apps.library.caltech.edu/oai'
            getrecord = ET.SubElement(oaixml, 'GetRecord')
            record = root.find(f'.//oai:identifier[.="{identifier}"]/../../.', ns)
            getrecord.append(record)

    else:

        oaixml = ET.Element('noThing',)
        oaixml.text = "Invalid key or verb, or verb not yet supported."


    return Response(ET.tostring(oaixml), mimetype='text/xml')



if __name__ == '__main__':
    app.run()
else:
    application = app
