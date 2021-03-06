import os
import jinja2
import webapp2
import re
from google.appengine.ext import db

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

import hashlib

def hash_str(s):
        return hashlib.md5(s).hexdigest()

def make_secure_val(s):
        return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
        val = h.split('|')[0]
        if h == make_secure_val(val):
                return val

class MainPage(Handler):
    def markup(self, template, **values):
        self.response.write(JINJA_ENVIRONMENT.get_template(template).render(values))

    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        visits = 0
        visit_cookie_str = self.request.cookies.get('visits')
        if visit_cookie_str:
            cookie_val = check_secure_val(visit_cookie_str)
            if cookie_val:
                visits = int(cookie_val)
        visits += 1
        new_cookie_val = make_secure_val(str(visits))
        self.response.headers.add_header('Set-Cookie', 'visits=%s' % new_cookie_val)
        if visits > 100:
            self.write("You are the best ever!")
        else:
            self.write("You've been here %s times!" % visits)

SECRET = 'imsosecret'
import hmac
def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def valid_user(name, pw):
    user = get_user(name)
    if user and user.password_hash == H(pw):
        return user

import random
from string import letters

def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt=make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
    salt = h.split(',')[1]
    return h == make_pw_hash(name, pw, salt)

h = make_pw_hash('spez', 'hunter2')
print valid_pw('spez', 'hunter2', h)

app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
