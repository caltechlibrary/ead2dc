import os, json
from pathlib import Path
from flask import Flask, render_template

from asnake.client import ASnakeClient

# read config file
with open(Path(Path(__file__).resolve().parent).joinpath('config.json'), "r") as f:
    config = json.load(f)

asnake_client = ASnakeClient(
    baseurl=config["ArchivesSpace Credentials"]["ASPACE_API_URL"],
    username=config["ArchivesSpace Credentials"]["ASPACE_USERNAME"],
    password=config["ArchivesSpace Credentials"]["ASPACE_PASSWORD"]
)
asnake_client.authorize()

# create and configure the app
app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = config['Flask Configuration']['SECRET_KEY']
app.config.from_mapping(DATABASE=os.path.join(app.instance_path, 'ead2dc.db'))

from . import db
db.init_app(app)

from . import auth
app.register_blueprint(auth.bp)
    
from . import oaidp
app.register_blueprint(oaidp.bp)
app.add_url_rule('/', endpoint='index')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('auth/login.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/browse')
def browse():
    return render_template('browse.html')
