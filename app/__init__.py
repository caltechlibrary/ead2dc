import os
from flask import Flask

#def create_app(test_config=None):

# create and configure the app
app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(DATABASE=os.path.join(app.instance_path, 'log.db'))

from . import db
db.init_app(app)

from . import oaidp
app.register_blueprint(oaidp.bp)
app.add_url_rule('/', endpoint='index')

#return app

#app = create_app()