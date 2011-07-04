import json

from helmut.core import entities
from helmut.text import normalize

def field(k, v, boost=None):
    v = v.replace('"', '\\"')
    fld = '%s:"%s"' % (k, v)
    if boost is not None:
        fld += '^%d' % boost
    return fld

def query(solr, q, filters=(), **kw):
    fq = ['+' + field(k, v) for k, v in filters]
    fq.append('_collection:%s' % entities.name)
    if len(q) and q != '*:*':
        nq = normalize(q)
        _q = [
             field('title', q, boost=10),
             field('title.n', nq, boost=7),
             field('alias', q, boost=8),
             field('alias.n', nq, boost=5),
             field('text', q, boost=2),
             field('text', nq)
             ]
        q = ' OR '.join(_q)
    result = solr.raw_query(q=q, fq=fq, wt='json',
            sort='score desc, title desc', fl='*,score', **kw)
    result = json.loads(result)
    return result

