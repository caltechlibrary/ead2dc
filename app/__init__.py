import os, json
from pathlib import Path
from flask import Flask, render_template

# read config file
with open(Path(Path(__file__).resolve().parent).joinpath('config.json'), "r") as f:
    config = json.load(f)

# create and configure the app
app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = config['Flask Configuration']['SECRET_KEY']
app.config.from_mapping(DATABASE=os.path.join(app.instance_path, 'log.db'))

from . import db
db.init_app(app)

from . import oaidp
app.register_blueprint(oaidp.bp)
app.add_url_rule('/', endpoint='index')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ead2dc')
def ead2dc():
    return render_template('ead2dc.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/oaidp')
def oaidp():
    return render_template('oaidp.html')

