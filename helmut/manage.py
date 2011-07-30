from flaskext.script import Manager

from helmut.core import app, solr
from helmut.entity import Type

manager = Manager(app)

@manager.command
@manager.option('-t', '--type', dest='type_name', default=None)
def index(type_name):
    """ Index all entities of a given type. """
    type_ = Type.by_name(type_name)
    if type_ is None:
        print "No such type: %s" % type_name
    else:
        type_.index()

@manager.command
def reset():
    """ Reset the entire search index. """
    conn = solr()
    conn.delete_query('*:*')

if __name__ == "__main__":
    manager.run()

