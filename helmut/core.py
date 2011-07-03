from flask import Flask, request
from pymongo import Connection
from solr import SolrConnection

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
app.config.from_envvar('RECON_SETTINGS', silent=True)

conn = Connection(app.config['MONGO_HOST'])
db = conn[app.config['MONGO_DB']]
entities = db[app.config['MONGO_COLLECTION']]

solr_host = app.config['SOLR_HOST']

def solr():
    return SolrConnection(solr_host)
