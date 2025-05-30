# local imports
from app.aspace import get_notes, get_last_update, write_last_update, csv_gen
from app.db import get_db
# other imports
from flask import Blueprint, request, Response, render_template, send_file
from datetime import datetime, date
import xml.etree.ElementTree as ET
import xml.dom.minidom as dom
from pathlib import Path
import csv, json, subprocess

# read config file
with open(Path(Path(__file__).resolve().parent).joinpath('config.json'), 'r') as f:
    config = json.load(f)

# max number of records to return
maxrecs = config['MAXIMUM_RECORDS_RETURNED']
# data provider URL
dpurl = config['DATA_PROVIDER_URL']
# base uri
idbase = config['ID_BASE_URI'] 
# public url
pub_url = config['PUBLIC_URL']
# collection base
cbase = config['COLLECTION_BASE_URI']

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

# read static repository file
tree = ET.parse(Path(Path(__file__).resolve().parent).joinpath('../xml/caltecharchives.xml'))
root = tree.getroot()

ids = list()
for node in root.findall('.//record/header/identifier', ns):
    try:
        id = int(node.text[65:])
        ids.append(id)
    except:
        pass
ids = [str(id) for id in sorted(ids)]

# returns a pretty-printed XML string
def prettify(elem):
    xml_string = ET.tostring(elem)
    xml_file = dom.parseString(xml_string)
    pretty_xml = xml_file.toprettyxml(indent="  ")
    return pretty_xml

# build OAI
@bp.route('/build')
def build():
    return render_template('build.html')

# returns a list of IDs
@bp.route('/browse/<page_number>')
def browse(page_number):
    page_number=int(page_number)
    page_size=1000
    items_total=len(ids)
    pages_total=(items_total+page_size-1)//page_size
    ids_display=ids[(page_number-1)*page_size:page_number*page_size]
    return render_template("browse.html", 
                           ids=ids_display, 
                           idbase=idbase, 
                           dpurl=dpurl,
                           page_size=page_size,
                           items_total=items_total,
                           pages_total=pages_total,
                           page_number=page_number)

# returns a record
@bp.route('/search', methods=('GET', 'POST'))
def search():
    if request.method == 'POST':
        ids = [id.text[65:] for id in root.findall('.//record/header/identifier', ns)]
        if request.form['id'] in ids:
            id = request.form['id']
        else:
            id = "id not found"
        return render_template("search.html", 
                               id=id, 
                               idbase=idbase, 
                               dpurl=dpurl)
    else:
        return render_template("search.html")

# read/write collections data to db
# display collections list
@bp.route('/collections')
def collections():
    db = get_db()
    query = 'SELECT sum(docount) as tot_docount, \
                    sum(caltechlibrary) as tot_clibrary, \
                    sum(internetarchive) as tot_iarchive, \
                    sum(youtube) tot_youtube, sum(other) as tot_other \
                FROM collections;'
    totals = db.execute(query).fetchone()
    return render_template('collections.html', 
                           output=read_colls(), 
                           dt_col=get_last_update('col'),
                           dt_xml=get_last_update('xml'),
                           url=pub_url+cbase,
                           totals=totals)

# read/write collections data to db
# display collections list
# download collections data
@bp.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        category = request.form.get('category')
        filename = './' + category + '.csv'
        fieldnames = [  'uri', 
                        'title', 
                        'publish', 
                        'restrictions', 
                        'repository_processing_note', 
                        'ead_id', 
                        'finding_aid_title', 
                        'finding_aid_filing_title', 
                        'finding_aid_date', 
                        'finding_aid_author', 
                        'created_by', 
                        'last_modified_by', 
                        'create_time', 
                        'system_mtime', 
                        'user_mtime', 
                        'suppressed', 
                        'is_slug_auto', 
                        'id_0', 
                        'level', 
                        'resource_type', 
                        'finding_aid_description_rules', 
                        'finding_aid_language', 
                        'finding_aid_script',
                        'finding_aid_status', 
                        'jsonmodel_type'   ]
        rec_count = csv_gen(filename, fieldnames, category)
    return render_template('dashboard2.html',
                           category=category,
                           filename=filename,
                           rec_count=rec_count)

@bp.route('/download')
def download():
    return send_file(path, as_attachment=True)

'''
# return the CSV file as a response
    response = Response(csv_data, mimetype='text/csv')
    response.headers.set('Content-Disposition', 'attachment', filename='collections.csv')
    return response
'''

# refresh collections data from ArchivesSpace
@bp.route('/collections2')
def collections2():
    codepath = Path(Path(__file__).resolve().parent).joinpath('updcollinfo.py')
    output=subprocess.run(['python', codepath], capture_output=True, text=True)
    return render_template('collections.html', 
                           output=read_colls(), 
                           dt=get_last_update('col'),
                           url=pub_url+cbase,
                           digitalobject_count=output,
                           archivalobject_count=output,
                           totals=get_total_counts())

# get total object counts
def get_total_counts():
    db = get_db()
    query = 'SELECT sum(docount) as tot_docount, \
                    sum(caltechlibrary) as tot_clibrary, \
                    sum(internetarchive) as tot_iarchive, \
                    sum(youtube) tot_youtube, sum(other) as tot_other \
                FROM collections;'
    return db.execute(query).fetchone()

# read collections data for display
def read_colls():
    query = "SELECT collno, colltitle, docount, caltechlibrary, \
                    internetarchive, youtube, other, incl \
            FROM collections \
            ORDER BY docount DESC;"
    colls = get_db().execute(query).fetchall()
    n = sum(k for (_,_,k,_,_,_,_,_) in colls)
    return (n, len(colls), colls)

# query db and update collections json file for list of ids
def update_coll_json(ids):
    db = get_db()
    # initialize dict for json output
    coll_dict = dict()
    query = "SELECT colltitle FROM collections WHERE collno=?;"
    for id in ids:
        coll_dict[id] = {'title' : db.execute(query, [id]).fetchone()[0],
                         'description' : get_notes(id),
                         'eadurl' : pub_url+'oai?verb=GetRecord&identifier=/'+cbase+id+'&metadataPrefix=oai_ead'}
    # save included collections to JSON file
    with open(Path(Path(__file__).resolve().parent).joinpath('collections.json'), 'w') as f:
        json.dump(coll_dict, f)
    return

# update selected collections
@bp.route('/collections3', methods=['GET', 'POST'])
def collections3():
    db = get_db()
    if request.method == 'POST':
        db.execute('UPDATE collections SET incl=0;')
        ids = request.form.getlist('include')
        for id in ids:
            db.execute('UPDATE collections SET incl=1 WHERE collno=?;', [id])
        db.commit()
        update_coll_json(ids)
        write_last_update('col')
    totals = db.execute('SELECT total,caltechlibrary,internetarchive,youtube,other FROM totals;').fetchone()
    return render_template('collections.html', 
                           output=read_colls(), 
                           dt_col=get_last_update('col'),
                           dt_xml=get_last_update('xml'),
                           url=pub_url+cbase,
                           totals=totals)

# regenerate info
@bp.route('/regen')
def regen():
    return render_template("regen.html", 
                           done=False, 
                           dt_xml=get_last_update('xml'),
                           dt_col=get_last_update('col'))

# regenerate XML
@bp.route('/regen2')
def regen2():
    codepath = Path(Path(__file__).resolve().parent).joinpath('ead2dc.py')
    subprocess.run(['python', codepath], capture_output=False)
    return render_template("regen.html", 
                           done=True, 
                           dt_xml=get_last_update('xml'),
                           dt_col=get_last_update('col'))

# run both collections (updcollinfo.py) and regen (ead2dc.py) scripts and reload server
@bp.route('/update')
def update():
    codepath = Path(Path(__file__).resolve().parent).joinpath('update.sh')
    subprocess.run(['sh', codepath], capture_output=False)
    return render_template("regen.html", 
                           done=True, 
                           dt_xml=get_last_update('xml'),
                           dt_col=get_last_update('col'))

@bp.route('/search2')
def search2():
    try:
        ids = [root.find('.//record/header/identifier', ns)]
    except:
        ids = ['']
    return render_template("browse.html")

# log requests
def log(rq):
    query = "INSERT INTO logs (date, verb, setname, identifier, datefrom, dateuntil) VALUES (?, ?, ?, ?, ?, ?);"
    db = get_db()
    db.execute(query, rq)
    db.commit()
    return

# OAI data provider
@bp.route('/oai')
def oai():

    # list of collections to include
    db = get_db()
    query = "SELECT collno FROM collections WHERE incl;"
    colls = [collno[0] for collno in db.execute(query).fetchall()]

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
        resumptionToken = request.args.get('resumptionToken').split(':')
        set = resumptionToken[0]
        datefrom = resumptionToken[1]
        dateuntil = resumptionToken[2]
        startrec = int(resumptionToken[3])

    else:

        # iteration flag
        first = True
    
        # get parameters from request
        set =  '000' if request.args.get('set') is None else request.args.get('set')
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
        rquest.text = dpurl
        listmetadataformats = ET.SubElement(oaixml, 'ListMetadataFormats')

        if identifier is None:

            rquest.attrib = {'verb': 'ListMetadataFormats'}
            for node in elem:
                listmetadataformats.append(node)
                count += 1

        else:

            rquest.attrib = {'verb': 'ListMetadataFormats', 'identifier': identifier}
            nodes = root.findall(f'.//identifier[.="{identifier}"]/../../..[@metadataPrefix]', ns)
            for node in nodes:
                prefix = node.attrib['metadataPrefix']
                mf = root.find(f'.//ListMetadataFormats/metadataFormat/metadataPrefix[.="{prefix}"]/..', ns)
                listmetadataformats.append(mf)
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
            if node.find('./setSpec', ns).text in colls:
                listsets.append(node)
                count = 1

    elif verb == 'ListRecords' or verb == 'ListIdentifiers':

        elem = root.find('./ListRecords', ns)
        # create OAI-PMH XML object
        oaixml = ET.Element('OAI-PMH')
        respDate = ET.SubElement(oaixml, 'responseDate')
        respDate.text = today
        rquest = ET.SubElement(oaixml, 'request')
        rquest.attrib = {'verb': 'ListRecords'}
        rquest.text = dpurl
        listrecords = ET.SubElement(oaixml, 'ListRecords')
        listrecords.attrib = {'metadataPrefix': 'oai_dc'}
        recrds = elem.findall('./{http://www.openarchives.org/OAI/2.0/}record')

        for recrd in recrds:

            if (recrd.find('./header/setSpec', ns).text == set or set == '000') and \
                recrd.find('./header/setSpec', ns).text in colls:

                if recrd.find('./header/datestamp', ns).text >= datefrom and \
                   recrd.find('./header/datestamp', ns).text <= dateuntil:

                    cursor += 1

                    if (cursor > startrec) and (cursor <= startrec + maxrecs):

                        count += 1

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

                    if cursor >= startrec + maxrecs:
                        resumptionToken = ET.SubElement(listrecords, '{http://www.openarchives.org/OAI/2.0/}resumptionToken')
                        resumptionToken.attrib = {'cursor': str(cursor)}
                        resumptionToken.text = f'{set}:{datefrom}:{dateuntil}:{cursor}'
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
            if root.find('./ListRecords/record/header/setSpec', ns).text in colls:
                try:
                    record = root.find(f'.//identifier[.="{identifier}"]/../../.', ns)
                    getrecord.append(record)
                    count += 1
                except:
                    pass
            
    else:

        oaixml = ET.Element('OAI-PMH')
        respDate = ET.SubElement(oaixml, 'responseDate')
        respDate.text = today
        error = ET.SubElement(oaixml, 'error')
        error.text = "Missing or invalid verb or key."

    return Response(ET.tostring(oaixml), mimetype='text/xml')

