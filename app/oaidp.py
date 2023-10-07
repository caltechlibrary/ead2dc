from flask import Blueprint, request, Response, render_template
from datetime import datetime, date
import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from pathlib import Path
from urllib.parse import quote, unquote

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
#tree = ET.parse('../xml/caltecharchives.xml')
tree = ET.parse(Path(Path(__file__).resolve().parent).joinpath('../xml/caltecharchives.xml'))
root = tree.getroot()


# encode and decode URL parameters
def urlencode(str):
  return quote(str)
def urldecode(str):
  return unquote(str)


# returns a pretty-printed XML string
def prettify(elem):
    xml_string = ET.tostring(elem)
    xml_file = dom.parseString(xml_string)
    pretty_xml = xml_file.toprettyxml(indent="  ")
    return pretty_xml


# log requests
def log(rq):

    query = "INSERT INTO logs (date, verb, setname, identifier, datefrom, dateuntil) VALUES (?, ?, ?, ?, ?, ?);"

    db = get_db()
    db.execute(query, rq)
    db.commit()

    return


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/oai')
def oai():

    # data provider URL
    dpurl = 'https://apps.library.caltech.edu/ead2dc/oai'

    # number of records per request
    maxrecs = 500

    # empty list for errors
    errors = list()

    # string form of date to write to each record
    today = date.today().strftime("%Y-%m-%d")

    # get verb from request
    verb = request.args.get('verb')
    identifier = request.args.get('identifier')
 
    # resumption token flag
    rToken = False

    if request.args.get('resumptionToken'):

        # iteration flag
        first = False

        # get resumptionToken from request and decode
        resumptionToken = urldecode(request.args.get('resumptionToken')).split('|')
        set = resumptionToken[0]
        datefrom = resumptionToken[1]
        dateuntil = resumptionToken[2]
        startrec = int(resumptionToken[3])
        print(f'startrec: {startrec}')

    else:

        # iteration flag
        first = True
    
        # get parameters from request
        set =  request.args.get('set')
        datefrom = '000-00-00' if request.args.get('from') is None else request.args.get('from')
        dateuntil = '999-99-99' if request.args.get('until') is None else request.args.get('until')
        startrec = 0

    
    now = datetime.now().isoformat()

    # log request
    try:
        id = identifier[identifier.rfind('/')+1:]
    except:
        id = identifier
    rq = [now, verb, set, id, datefrom, dateuntil]
    log(rq)


    # position for ListRecords/ListIdentifiers
    cursor = 0

    # records written
    count = 0


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
        count += 1

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
            count += 1

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
            count = 1

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

                if recrd.find('.//datestamp', ns).text >= datefrom and recrd.find('.//datestamp', ns).text <= dateuntil:

                    if (cursor >= startrec) and (cursor < startrec + maxrecs):

                        record = ET.SubElement(listrecords, '{http://www.openarchives.org/OAI/2.0/}record')
                        header = ET.SubElement(record, '{http://www.openarchives.org/OAI/2.0/}header')
                        hdr = recrd.find('.//{http://www.openarchives.org/OAI/2.0/}header')
                        for node in hdr:
                            header.append(node)
                        
                        count += 1

                        if verb == 'ListRecords':

                            metadata = ET.SubElement(record, '{http://www.openarchives.org/OAI/2.0/}metadata')
                            dc = ET.SubElement(metadata, '{http://www.openarchives.org/OAI/2.0/oai_dc/}dc')
                            metad = recrd.find('.//{http://www.openarchives.org/OAI/2.0/oai_dc/}dc')
                            for node in metad:
                                dc.append(node)

                    cursor += 1

                    if cursor >= startrec + maxrecs:
                        resumptionToken = ET.SubElement(listrecords, '{http://www.openarchives.org/OAI/2.0/}resumptionToken')
                        resumptionToken.attrib = {'cursor': str(cursor)}
                        resumptionToken.text = urlencode(f'{set}|{datefrom}|{dateuntil}|{cursor}')
                        rToken = True
                        break


        if not rToken and not first:
            resumptionToken = ET.SubElement(listrecords, '{http://www.openarchives.org/OAI/2.0/}resumptionToken')
            resumptionToken.attrib = {'cursor': str(cursor)}
                                  

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
            count += 1

    else:

        oaixml = ET.Element('OAI-PMH')
        respDate = ET.SubElement(oaixml, 'responseDate')
        respDate.text = today
        error = ET.SubElement(oaixml, 'error')
        error.text = "Missing or invalid verb or key."

    print(f'{count} records returned')
    print(f'cursor position: {cursor}')

    return Response(ET.tostring(oaixml), mimetype='text/xml')


