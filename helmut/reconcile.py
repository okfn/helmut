from flask import url_for

from helmut.entity import Type

def match(q):
    if isinstance(q, basestring):
        q = {'query': q}
    try:
        limit = max(1, min(100, int(q.get('limit'))))
    except ValueError: limit = 5
    except TypeError: limit = 5

    filters = [(p.get('p'), p.get('v', '*')) for p in \
               q.get('properties', []) if 'p' in p]
    types = q.get('types')
    if types is not None:
        if isinstance(types, basestring):
            types = [types]
        types = map(lambda t: t.strip().lstrip('/'), types)
        filters.extend([('__type__', t) for t in types])
        # todo: implement types_strict
    results = Type.find(q.get('query'), filters=filters, rows=limit)
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
            'match': False
            })

    return {
        'result': matches, 
        'num': results.get('response').get('numFound')
        }
