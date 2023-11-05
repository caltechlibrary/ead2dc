import os, json
from pathlib import Path
from flask import Flask

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
