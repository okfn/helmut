import math
from flask import url_for, g

from helmut.query import query

FILTER_PREFIX = "filter-"

class Pager(object):

    def __init__(self, args):
        self.args = args
        self.page = 1
        try:
            self.page = int(args.get('p'))
        except: pass
        self.limit = 20
        self._results = None
        self.facets = []

    @property
    def offset(self):
        return (self.page-1)*self.limit
    
    @property
    def pages(self):
        return int(math.ceil(len(self)/float(self.limit)))
    
    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def has_prev(self):
        return self.page > 1
    
    @property
    def next_url(self):
        return self.page_url(self.page + 1) if self.has_next \
               else self.page_url(self.page)

    @property
    def prev_url(self):
        return self.page_url(self.page - 1) if self.has_prev \
               else self.page_url(self.page)

    @property
    def params(self):
        return [(k, v.encode('utf-8')) for k, v in self.args.items() \
                if k != 'p']


    def page_url(self, page):
        return url_for('search', p=page, **dict(self.params))


    @property
    def filters(self):
        filters = []
        for k, v in self.args.items():
            if k.startswith(FILTER_PREFIX):
                k = k[len(FILTER_PREFIX):]
                filters.append((k, v))
        return filters


    def filter_url(self, key, value):
        params = self.params
        tp = (FILTER_PREFIX + key, value.encode('utf-8'))
        if tp not in params:
            params.append(tp)
        return url_for('search', **dict(params))


    def unfilter_url(self, key, value):
        p = (FILTER_PREFIX + key, value.encode('utf-8'))
        params = [e for e in self.params if e != p]
        return url_for('search', **dict(params))


    def facet_by(self, *facets):
        self.facets.extend(facets)


    @property
    def q(self): 
        return self.args.get('q', '') 


    @property
    def results(self):
        if self._results is None:
            self._results = self.query() 
        return self._results


    def __iter__(self):
        return iter(self.results.get('response', {}).get('docs'))


    def __len__(self):
        return self.results.get('response', {}).get('numFound')


    def facet_values(self, key):
        facets = self.results.get('facet_counts').get('facet_fields')
        _facets = []
        values = facets.get(key)
        for value in values[::2]:
            count = values[values.index(value)+1]
            _facets.append((value, count))
        return sorted(_facets, key=lambda (a, b): b, reverse=True)


    def query(self, **kwargs):
        if len(self.facets):
            kwargs['facet'] = 'true'
            if not 'facet_limit' in kwargs:
                kwargs['facet_limit'] = 20
            kwargs['facet_field'] = self.facets
        return query(g.solr, self.q or '*:*',
                     filters=self.filters,
                     start=self.offset,
                     rows=self.limit,
                     **kwargs)


