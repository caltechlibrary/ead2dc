from flask import Flask, Blueprint, request, Response, render_template#, g
from datetime import datetime, date
import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from pathlib import Path

from app.db import get_db

bp = Blueprint('oaidp', __name__)

# namespace dictionary
ns = {'': 'http://www.openarchives.org/OAI/2.0/',
      'xlink': 'http://www.w3.org/1999/xlink',
      'dc': 'http://purl.org/dc/elements/1.1/',
      'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/'}

# register namespaces
ET.register_namespace('', 'http://www.openarchives.org/OAI/2.0/')
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
ET.register_namespace('oai_dc', 'http://www.openarchives.org/OAI/2.0/oai_dc/')
ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')

# read OAI finding aid
#tree = ET.parse('xml/caltecharchives.xml')
tree = ET.parse(Path(Path(__file__).resolve().parent).joinpath('caltecharchives.xml'))
root = tree.getroot()

# data provider URL
dpurl = 'https://apps.library.caltech.edu/ead2dc/oai'

# create the Flask app
#app = Flask(__name__)


# returns a pretty-printed XML string
def prettify(elem):
    xml_string = ET.tostring(elem)
    xml_file = dom.parseString(xml_string)
    pretty_xml = xml_file.toprettyxml(indent="  ")
    return pretty_xml


# log requests
def log(now, verb, set=None, identifier=None):

    query = "INSERT INTO logs (date, verb, setname, identifier) VALUES (?, ?, ?, ?);"

    db = get_db()
    db.execute(query, [now, verb, set, identifier])
    db.commit()

    return


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/oai')
def oai():

#    token = secrets.token_urlsafe(64)
#    print('secrets token:', token)

    # string form of date to write to each record
    today = date.today().strftime("%Y-%m-%d")

# log request
    verb = request.args.get('verb')
    set = request.args.get('set')
    identifier = request.args.get('identifier')
    now = datetime.now().isoformat()
    log(now, verb, set, identifier)

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

            if recrd.find('.//setSpec', ns).text == set or set is None:

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
            record = root.find(f'.//identifier[.="{identifier}"]/../../.', ns)
            getrecord.append(record)

    else:

        oaixml = ET.Element('OAI-PMH')
        respDate = ET.SubElement(oaixml, 'responseDate')
        respDate.text = today
        error = ET.SubElement(oaixml, 'error')
        error.text = "Missing or invalid verb or key."


    return Response(ET.tostring(oaixml), mimetype='text/xml')


'''
if __name__ == '__main__':
    app.run(debug=True, port=5000)
else:
    application = app
'''