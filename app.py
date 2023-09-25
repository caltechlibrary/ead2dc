homepg = '''
        <!DOCTYPE html>
        <html>
        <head><title>Caltech Archives Data Provider</title></head>
        <body>
        
        <p>This is the Caltech Archives OAI-PMH data provider.</p>
        
        <p>The base URL is <a href="https://apps.library.caltech.edu/ead2dc/oai">https://apps.library.caltech.edu/ead2dc/oai</a>.</p>
        
        <p>All verbs, and the set argument, are supported, viz.:</p>
        
        <ul>
        <li>Identify
            <ul>
            <li>Example: <a href="https://apps.library.caltech.edu/ead2dc/oai?verb=Identify">Identify</a></li>
            </ul>
        </li>
        <li>ListMetadataFormats
            <ul>
            <li>Example: <a href="https://apps.library.caltech.edu/ead2dc/oai?verb=ListMetadataFormats">ListMetadataFormats</a></li>
            <li>argument not supported: identifier</li>
            </ul>
        </li>
        <li>ListSets
            <ul>
            <li>Example: <a href="https://apps.library.caltech.edu/ead2dc/oai?verb=ListSets">ListSets</a></li>
            <li>argument not supported: resumptionToken</li>
            </ul>
        </li>
        <li>ListIdentifiers
            <ul>
            <li>Example: <a href="https://apps.library.caltech.edu/ead2dc/oai?verb=ListIdentifiers&set=hale">ListIdentifiers&set=hale</a></li>
            <li>argument supported: set</li>
            <li>arguments not supported: from, until, metadataPrefix, resumptionToken</li>
            </ul>
        </li>
        <li>ListRecords
            <ul>
            <li>Example: <a href="https://apps.library.caltech.edu/ead2dc/oai?verb=ListRecords&set=palomar">ListRecords&set=palomar</a></li>
            <li>argument supported: set</li>
            <li>arguments not supported: from, until, metadataPrefix, resumptionToken</li></ul></li>
        <li>GetRecord
            <ul>
            <li>Example: <a href="https://apps.library.caltech.edu/ead2dc/oai?verb=GetRecord&identifier=oai:archives.caltech.edu:aspace_09a14c019ee4a38be8885d5d57cc2d06">GetRecord&identifier=oai:archives.caltech.edu:aspace_09a14c019ee4a38be8885d5d57cc2d06</a></li>
            <li>argument supported: identifier</li>
            <li>argument not supported: metadataPrefix</li>
            </ul>
        </li>
        </ul>

        <p>Notes:</p>
        
        <ul>
        <li>Dublin Core is the only metadata standard supported at this time.</li>
        <li>The set structure is flat, not hierarchical.</li>
        <li>All records belong to one and only one set, so harvesting all sets will capture all records.</li>
        </ul>
        
        <p>For more information visit:</p>
        
        <ul>
        <li><a href="https://www.openarchives.org/OAI/openarchivesprotocol.html">OAI-PMH specification</a></li>
        <li><a href="https://archives.caltech.edu">Caltech Archives website</a></li>
        <li><a href="https://github.com/caltechlibrary/ead2dc">GitHub</a></li>
        </ul>
        '''

# import main Flask class and request object
from flask import Flask, request, Response#, session
#from flask_session import Session
from datetime import date
import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from pathlib import Path
#import secrets

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
#tree = ET.parse("caltecharchives.xml")
root = tree.getroot()

# data provider URL
dpurl = 'https://apps.library.caltech.edu/ead2dc/oai'

# string form of date to write to each record
today = date.today().strftime("%Y-%m-%d")

# create the Flask app
app = Flask(__name__)
#SESSION_TYPE = 'filesystem'
#app.config.from_object(__name__)
#Session(app)


# returns a pretty-printed XML string
def prettify(elem):
    xml_string = ET.tostring(elem)
    xml_file = dom.parseString(xml_string)
    pretty_xml = xml_file.toprettyxml(indent="  ")
    return pretty_xml

'''
@app.route('/set/<string:value>')
def set_session(value):
    session['key'] = value
    return Response(f"Value set to {value}")

@app.route('/get/')
def get_session():
    stored_session = session.get('key', 'None')
    return (Response(f"Value stored in session is {stored_session}"))
'''

@app.route('/')
def index():
    return homepg


@app.route('/oai')
def oai():

    
    #session['verb'] = request.args.get('verb')
    #session['set'] = request.args.get('set')
    
    #print(session['verb'])
    #print(session['set'])
    #print(app.secret_key)
    #token = secrets.token_urlsafe(24)
    #print('secrets token:', token)


    

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
        rquest.text = dpurl
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
        rquest.text = dpurl
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
        rquest.text = dpurl
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
        rquest.text = dpurl
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
            rquest.text = dpurl
            getrecord = ET.SubElement(oaixml, 'GetRecord')
            record = root.find(f'.//oai:identifier[.="{identifier}"]/../../.', ns)
            getrecord.append(record)

    else:

        oaixml = ET.Element('OAI-PMH')
        respDate = ET.SubElement(oaixml, 'responseDate')
        respDate.text = today
        error = ET.SubElement(oaixml, 'error')
        error.text = "Missing or invalid verb or key."


    return Response(ET.tostring(oaixml), mimetype='text/xml')



if __name__ == '__main__':
    app.run(debug=True, port=5000)
else:
    application = app
