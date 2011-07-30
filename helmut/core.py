from flask import Flask, request
from flaskext.login import LoginManager
from solr import SolrConnection
from webstore.client import Database

from helmut import default_settings

MIME_TYPES = {
        'text/html': 'html',
        'application/xhtml+xml': 'html',
        'application/json': 'json',
        'text/javascript': 'json'
        }

def request_format(fmt):
    best = request.accept_mimetypes \
        .best_match(MIME_TYPES.keys())
    if fmt in MIME_TYPES.values():
        return fmt
    return MIME_TYPES.get(best)


app = Flask(__name__)
app.config.from_object(default_settings)
app.config.from_envvar('HELMUT_SETTINGS', silent=True)

login_manager = LoginManager()
login_manager.setup_app(app)

solr_host = app.config['SOLR_HOST']

def solr():
    return SolrConnection(solr_host)


database = Database(app.config['WEBSTORE_SERVER'],
              app.config['WEBSTORE_USER'],
              app.config.get('WEBSTORE_DB', 'helmut'))
types_table = database[app.config.get('WEBSTORE_TABLE', 'types')]


