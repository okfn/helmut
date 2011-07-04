from datetime import datetime
#from urllib import quote
from dateutil import tz

from pymongo import ASCENDING

from helmut.core import entities, solr
from helmut.text import normalize

def datetime_add_tz(dt):
    """ Solr requires time zone information on all dates. """
    return datetime(dt.year, dt.month, dt.day, dt.hour,
                    dt.minute, dt.second, tzinfo=tz.tzutc())

def save_entity(path, title, alias=[], description=None, **kwargs):
    """ Save an entity to the database and to solr.

    Each entity is uniquely described by its path, which will be the last 
    aspect of its URL.
    """
    entity = kwargs.copy()

    assert not '.' in path, "Full stop in path is invalid: %s" % path
    #assert quote(path)==path, "Path changes when URL quoted: %s" % path
    entity['path'] = path

    assert len(title), "Title has no length: %s" % title
    entity['title'] = title
    entity['alias'] = alias

    if description is not None:
        entity['description'] = description

    entity['updated_at'] = datetime.utcnow()

    existing = entities.find_one({'path': path})
    if existing is not None:
        existing.update(entity)
        entity = existing
    else:
        entity['created_at'] = entity['updated_at']
    entities.update({'path': path}, entity, upsert=True)

    entity['_collection'] = entities.name
    entity['title.n'] = normalize(title)
    entity['alias.n'] = map(normalize, alias)
    conn = solr()
    _entity = {}
    for k, v in entity.items():
        if isinstance(v, datetime):
            v = datetime_add_tz(v)
        _entity[str(k)] = v
    conn.add(**_entity)
    conn.commit()

def finalize():
    """ After loading, run a few optimization operations. """
    entities.ensure_index([('path', ASCENDING)])
    conn = solr() 
    conn.optimize()
    conn.commit()
