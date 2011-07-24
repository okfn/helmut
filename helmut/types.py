from datetime import datetime
#from urllib import quote
from dateutil import tz

from webstore.client import Database

from helmut.core import app, solr
from helmut.text import normalize

def datetime_add_tz(dt):
    """ Solr requires time zone information on all dates. """
    return datetime(dt.year, dt.month, dt.day, dt.hour,
                    dt.minute, dt.second, tzinfo=tz.tzutc())


class Type(object):

    def __init__(self, db_user, db_name, entity_table, entity_key, 
                 alias_table, alias_text, alias_key):
        self.entity_table = entity_table
        self.entity_key = entity_key
        self.alias_text = alias_text
        self.alias_key = alias_key
        self.conn = solr()
        self.database = Database(app.config['WEBSTORE_SERVER'],
                                 db_user, db_name)
        self.alias = self.database[alias_table]
        self.entity = self.database[entity_table]
    
    def index(self, step=500):
        rows = []
        for i, row in enumerate(self.entity.traverse(_step=step)):
            row = self.row_to_index(row)
            rows.append(row)
            if i % step == 0:
                self.conn.add_many(rows, _commit=True)
                rows = []
        if len(rows):
            self.conn.add_many(rows)
        self.finalize()

    def row_to_index(self, row):
        key = row.get(self.entity_key)
        q = {self.alias_key: key}
        aliases = self.alias.traverse(**q)
        aliases = map(lambda a: a.get(self.alias_text), aliases)
        row['alias'] = aliases
        row['title.n'] = normalize(row.get('title'))
        row['alias.n'] = map(normalize, aliases)
        row['__type__'] = self.entity_table
        return row

    def finalize(self):
        """ After loading, run a few optimization operations. """
        self.conn.optimize()
        self.conn.commit()

    def by_key(self, key):
        return self.entity.find_one(**{self.entity_key: key})

    @classmethod
    def config(cls):
        db = Database(app.config['WEBSTORE_SERVER'],
                      app.config['WEBSTORE_USER'],
                      app.config.get('WEBSTORE_DB', 'helmut'))
        return db[app.config.get('WEBSTORE_TABLE', 'types')]

    @classmethod
    def _row_to_type(cls, row):
        return cls(row['db_user'],
                   row['db_name'],
                   row['entity_table'],
                   row['entity_key'],
                   row['alias_table'],
                   row['alias_text'],
                   row['alias_key'])

    @classmethod
    def types(cls):
        _types = []
        for row in cls.config().traverse():
            _types.append(cls._row_to_type(row))
        return _types

    @classmethod
    def by_name(cls, name):
        row = cls.config().find_one(name=name)
        if row is not None:
            row = cls._row_to_type(row)
        return row

