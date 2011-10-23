import json
from datetime import datetime

from flask import abort, g, request, url_for, Response
from flask import render_template, redirect, flash
from flaskext.login import login_user, logout_user
from flaskext.login import current_user, login_required
from jinja2 import evalcontextfilter

from helmut.core import app, solr, request_format
from helmut.reconcile import match
from helmut.entity import Type
from helmut.pager import Pager
from helmut.auth import User


@app.template_filter()
@evalcontextfilter
def date(eval_ctx, value):
    return value.strftime("%d.%m.%Y")


def default_json(obj):
    '''
    Return a json representations for some custom objects.
    Used for the *default* parameter to json.dump[s](),
    see http://docs.python.org/library/json.html#json.dump

    Raises :exc:`TypeError` if it can't handle the object.
    '''
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("%r is not JSON serializable" % obj)

def jsonify(data):
    data = json.dumps(data, default=default_json)
    if 'callback' in request.args:
        data = '%s(%s)' % (request.args.get('callback'), data)
    return Response(data, mimetype='application/json')

@app.context_processor
def set_current_user():
    """ Set some template context globals. """
    return dict(current_user=current_user)

@app.before_request
def before_request():
    # HTTPConnection used by pysolr is not thread-safe.
    g.solr = solr()

@app.route('/')
def index():
    pager = Pager(request.args)
    return render_template('index.tmpl', pager=pager)

@app.route('/search')
def search():
    pager = Pager(request.args)
    return render_template('search.tmpl', pager=pager)

@app.route('/<type>/<path:key>.<any(json,html,rdf):format>')
@app.route('/<type>/<path:key>')
def entity(type, key, format=None):
    type_ = Type.by_name(type)
    if type_ is None:
        abort(404)
    entity = type_.by_key(key)
    if entity is None:
        abort(404)
    if '__id__' in entity:
        del entity['__id__']
    url = url_for('entity', type=type, key=key, _external=True)
    format = request_format(format)
    if format == 'json':
        entity['_url'] = url
        return jsonify(entity)
    #if 'redirect_url' in entity:
    #    return redirect(entity.get('redirect_url'),
    #                    code=303)
    return render_template('view.tmpl', entity=entity, url=url)

@app.route('/manager/login', methods=['GET'])
def login():
    return render_template('login.tmpl')

@app.route('/manager/login', methods=['POST'])
def login_save():
    user = User.check(request.form['login'],
                     request.form['password'])
    if user is None:
        flash('Invalid username or password.', 'warning')
        return render_template('login.tmpl')
    else:
        login_user(user)
        return redirect(url_for('manager'))

@app.route('/manager/logout', methods=['GET'])
def logout():
    logout_user()
    flash('See you soon.', 'success')
    return redirect(url_for('index'))

@app.route('/manager', methods=['GET'])
@login_required
def manager():
    types = Type.types()
    return render_template('manager.tmpl', types=types)

@app.route('/manager/<type>', methods=['GET'])
@login_required
def manage(type):
    type_ = Type.by_name(type)
    return render_template('manage.tmpl', type=type_)

@app.route('/manager/new', methods=['GET'])
@login_required
def manager_new():
    return render_template('create.tmpl')

@app.route('/manager/new', methods=['POST'])
@login_required
def manager_new_save():
    type_ = Type.create(request.form)
    return render_template('manage.tmpl', type=type_)

@app.route('/manager/<type>/edit', methods=['GET'])
@login_required
def manager_edit(type):
    type_ = Type.by_name(type)
    return render_template('edit.tmpl', type=type_)

@app.route('/manager/<type>/edit', methods=['POST'])
@login_required
def manager_edit_save(type):
    type_ = Type.update(type, request.form)
    return render_template('manage.tmpl', type=type_)

@app.route('/reconcile', methods=['GET', 'POST'])
def reconcile():
    """ 
    Reconciliation API, emulates Google Refine API. See: 
    http://code.google.com/p/google-refine/wiki/ReconciliationServiceApi
    """
    # TODO: Add proper support for types and namespacing.
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
        return jsonify(match(q))
    elif 'queries' in data:
        # multiple requests in one query
        qs = data.get('queries')
        try:
            qs = json.loads(qs)
        except ValueError:
            abort(400)
        queries = {}
        for k, q in qs.items():
            queries[k] = match(q)
        return jsonify(queries)
    else:
        urlp = url_for('index', _external=True).strip('/') + '{{id}}'
        types = [{'name': t.name, 'id': '/' + t.name} for t in Type.types()]
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
                'defaultTypes': types
                }
        return jsonify(meta)

if __name__ == "__main__":
    app.run(port=5005)

