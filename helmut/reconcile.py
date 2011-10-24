from flask import url_for

from helmut.entity import Type

def match(q):
    if isinstance(q, basestring):
        q = {'query': q}
    try:
        limit = max(1, min(100, int(q.get('limit'))))
    except ValueError: limit = 5
    except TypeError: limit = 5
    filters = [(p.get('pid'), p.get('v', '*')) for p in \
               q.get('properties', []) if 'pid' in p]
    type_ = q.get('type')
    if type_ is not None:
        if isinstance(type_, basestring):
            type_ = [type_]
        types = map(lambda t: t.strip().lstrip('/'), type_)
        filters.extend([('__type__', t) for t in types])
        # todo: implement types_strict
    results = Type.find_fuzzy(q.get('query'), filters=filters, rows=limit)
    matches = []
    for result in results.get('response', {}).get('docs', []):
        id = url_for('entity', type=result.get('__type__'),
                key=result.get('__key__'))
        uri = url_for('entity', type=result.get('__type__'),
                key=result.get('__key__'), _external=True)
        matches.append({
            'name': result.get('title'),
            'score': result.get('score') * 10,
            'type': [{
                'id': '/' + result.get('__type__'),
                'name': result.get('__type__')
                }],
            'id': id,
            'uri': uri,
            'match': result.get('title') == q.get('query')
            })

    return {
        'result': matches, 
        'num': results.get('response').get('numFound')
        }

def prefix_search(args):
    start = int(args.get('start', 0))
    limit = int(args.get('limit', 20))
    
    fq = []
    if 'type' in args:
        type_ = args.get('type').strip().lstrip('/')
        fq.append('+__type__:"%s"' % type_)
    
    qs = args.get('prefix', '').strip()
    qs = qs + "^%d" % (len(qs)/2)
    results = Type.find(qs, fq, start=start, rows=limit)
    matches = []
    for result in results.get('response', {}).get('docs', []):
        id = url_for('entity', type=result.get('__type__'),
                key=result.get('__key__'))
        matches.append({
            'name': result.get('title'),
            'n:type': {
                'id': '/' + result.get('__type__'),
                'name': result.get('__type__')
                },
            'r:score': result.get('score'),
            'id': id,
            'type': ['foo']
            })
    return {
        "code" : "/api/status/ok",
        "status" : "200 OK",
        "prefix" : args.get('prefix'),
        "result" : matches
        }
