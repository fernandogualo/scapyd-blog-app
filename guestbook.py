import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


DEFAULT_GUESTBOOK_NAME = 'invitado'


#tema por defecto
def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    return ndb.Key('Guestbook', guestbook_name)

"""
Para almacenar los mensajes y los usuarios que mandan los mensajes,
se hace uso de NDB --> Datastore de Google
"""

#Persona que escribe. Comprueba si esta logueado y su username
class Author(ndb.Model):
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)

#Contenido del mensaje, autor, fecha y hora
class Greeting(ndb.Model):
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


#Pagina principal
class MainPage(webapp2.RequestHandler):

    def get(self):
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

#redirige a un nuevo tema en el foro
class Guestbook(webapp2.RequestHandler):

    def post(self):
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        greeting.content = self.request.get('content')
        greeting.put()
#Construye la nueva URL con los nuevos mensajes
        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))


# Definición de las distintas vistas o servicios
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', Guestbook),
], debug=True)
