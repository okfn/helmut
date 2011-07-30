
from webstore.client import Database, WebstoreClientException

from helmut.core import login_manager, app

@login_manager.user_loader
def load_user(userid):
    username, password = userid.split(':', 1)
    return User(username, password)

class User(object):

    def __init__(self, username, password):
        self.username = username
        self.password = password

    @classmethod
    def check(cls, username, password):
        try:
            db = Database(app.config['WEBSTORE_SERVER'],
                          app.config.get('WEBSTORE_USER'),
                          app.config.get('WEBSTORE_DB', 'helmut'), 
                          http_user=username, 
                          http_password=password)
            db.tables() # request to trigger auth
            return User(username, password)
        except WebstoreClientException:
            return None

    def get_id(self):
        return u'%s:%s' % (self.username, self.password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def __repr__(self):
        return "User<%s>" % self.username
