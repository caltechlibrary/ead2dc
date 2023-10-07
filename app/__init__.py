import os
from flask import Flask

# create and configure the app
app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = '8DufQgMGhDb5vKFJc_LQ6KZEcaTaJn8lyZ3hhrYjvHAK7Hch08xtM1xiTaSTJ4Oc3ZxseAZQ6RAmd9KtQuiBLA'
app.config.from_mapping(DATABASE=os.path.join(app.instance_path, 'log.db'))

from . import db
db.init_app(app)

from . import oaidp
app.register_blueprint(oaidp.bp)
app.add_url_rule('/', endpoint='index')
