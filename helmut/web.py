import json
from datetime import datetime

from flask import abort, g, request, url_for, Response
from bson.dbref import DBRef
from bson.objectid import ObjectId

from helmut.core import app, entities, solr, request_format
from helmut.query import query


_recon_type = {
        'id': '/' + app.config['ENTITY_NAME'],
        'name': app.config['ENTITY_NAME'].capitalize()
    }


def default_json(obj):
    '''
    Return a json representations for some custom objects.
    Used for the *default* parameter to json.dump[s](),
    see http://docs.python.org/library/json.html#json.dump

    Raises :exc:`TypeError` if it can't handle the object.
    '''
    if isinstance(obj, DBRef):
        return obj.as_doc()
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("%r is not JSON serializable" % obj)

def jsonify(data):
    data = json.dumps(data, default=default_json)
    if 'callback' in request.args:
        data = '%s(%s)' % (request.args.get('callback'), data)
    return Response(data, mimetype='application/json')


@app.before_request
def before_request():
    # HTTPConnection used by pysolr is not thread-safe.
    g.solr = solr()

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/search')
def search():
    return jsonify({'message': 'not implemented'})

@app.route('/%(ENTITY_NAME)s/<path:path>.<format>' % app.config)
@app.route('/%(ENTITY_NAME)s/<path:path>' % app.config)
def entity(path, format=None):
    entity = entities.find_one({'path': path})
    if entity is None:
        abort(404)
    del entity['_id']
    entity['%(ENTITY_NAME)s_url' % app.config] = \
            url_for('entity', path=path, _external=True)
    format = request_format(format)
    if format == 'json':
        return jsonify(entity)
    return "<h1>%s</h1>" % entity.get('title')


def _query(q):
    if isinstance(q, basestring):
        q = {'query': q}
    try:
        limit = max(1, min(100, int(q.get('limit'))))
    except ValueError: limit = 5
    except TypeError: limit = 5

    filters = [(p.get('p'), p.get('v', '*')) for p in q.get('properties', []) \
            if 'p' in p]
    results = query(g.solr, q.get('query'), kw=filters, limit=limit)
    matches = []
    for result in results.get('docs', []):
        matches.append({
            'name': result.get('title'),
            'score': result.get('score') * 2000,
            'type': [_recon_type],
            'id': '/' + app.config['ENTITY_NAME'] + '/' + result.get('path'),
            'uri': url_for('entity', path=result.get('path'), _external=True),
            'match': False
            })

    return {
        'result': matches, 
        'num': results.get('numFound')
        }


@app.route('/reconcile', methods=['GET', 'POST'])
def reconcile():
    """ 
    Reconciliation API, emulates Google Refine API. See: 
    http://code.google.com/p/google-refine/wiki/ReconciliationServiceApi
    """
    # TODO: Add propert support for types and namespacing.
    data = request.args.copy()
    data.update(request.form.copy())
    if 'query' in data:
        # single 
        q = data.get('query')
        if q.startswith('{'):
            try:
                q = json.loads(q)
            except ValueError:
                abort(400)
        return jsonify(_query(q))
    elif 'queries' in data:
        # multiple requests in one query
        qs = data.get('queries')
        try:
            qs = json.loads(qs)
        except ValueError:
            abort(400)
        queries = {}
        for k, q in qs.items():
            queries[k] = _query(q)
        return jsonify(queries)
    else:
        urlp = url_for('index', _external=True).strip('/') + '{{id}}'
        meta = {
                'name': app.config['TITLE'],
                'identifierSpace': 'http://rdf.freebase.com/ns/type.object.id',
                'schemaSpace': 'http://rdf.freebase.com/ns/type.object.id',
                'view': {'url': urlp},
                'preview': {
                    'url': urlp + '?preview=true', 
                    'width': 400,
                    'height': 300
                    },
                'defaultTypes': [_recon_type]
                }
        return jsonify(meta)

if __name__ == "__main__":
    app.run()

