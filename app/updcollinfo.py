from aspace import update_collections, get_notes
from oaidp import write_last_update
from db import get_db

from pathlib import Path
import json


# FUNCTIONS

# read collections data for display
def read_colls():
    query = "SELECT collno, colltitle, docount, carchives, clibrary, \
            iarchive, youtube, other, incl FROM collections ORDER BY docount DESC;"
    colls = get_db().execute(query).fetchall()
    n = sum(k for (_,_,k,_,_,_,_,_,_) in colls)
    return (n, len(colls), colls)

# update collections json
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

# MAIN PROGRAM

db = get_db()

# list of collections to include in OAI DP
# this is used to update incl field after update
incl = list() 
for e in db.execute('SELECT collno FROM collections WHERE incl=1;'):
    incl.append(e[0])

update_coll_json(incl)

# get data from ArchivesSpace as list
# output[0] = total number of do's
# output[1] = number of collections
# output[2] = a list of collections [coll id, title, stats(dict), incl]
# output[3] = elapsed time
output, digitalobject_count, archivalobject_count, totals = update_collections(incl) 

# update totals in db
#totals = {'total'           : , 
#          'caltecharchives' : , 
#          'caltechlibrary'  : , 
#          'internetarchive' : , 
#          'youtube'         : , 
#          'other'           : }
db.execute('DELETE FROM totals')
query='INSERT INTO totals(total,caltecharchives,caltechlibrary,internetarchive,youtube,other) \
        VALUES (?,?,?,?,?,?)'
db.execute(query, list(totals.values()))

# isolate collections info
colls=output[2]
    
# delete collections (easiest way to refresh data)
db.execute('DELETE FROM collections')

# insert updated data from ArchivesSpace into db
query = 'INSERT INTO collections(collno,colltitle,docount,carchives,clibrary,\
                    iarchive,youtube,other,incl) \
                    VALUES (?,?,?,?,?,?,?,?,?);'
for coll in colls:
    db.execute(query, [coll[0], coll[1], \
                coll[2]['docount'], coll[2]['caltecharchives'], coll[2]['caltechlibrary'], \
                coll[2]['internetarchive'], coll[2]['youtube'], coll[2]['other'], \
                coll[3]])
    
# update incl field
query = 'UPDATE collections SET incl=1 WHERE collno=?;'
for id in incl:
    db.execute(query, [id])

# commit changes
db.commit()
    
# record time of update
dt=write_last_update('col')