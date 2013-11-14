#!/usr/bin/env python

import os
import jinja2
import webapp2
import re
import string

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def cypher(content):
    alphabet = string.lowercase
    ALPHABET = string.uppercase
    cyphered = ''
    for letter in content:
        if re.match(r"[a-z]", letter):
            shift = alphabet.index(letter) + 13
            if shift > 26:
                shift += -26
            cyphered += alphabet[shift]
        elif re.match(r"[A-Z]", letter):
            shift = ALPHABET.index(letter) + 13
            if shift > 26:
                shift += -26
            cyphered += ALPHABET[shift]
        else:
            cyphered += letter
    return cyphered

class MainHandler(webapp2.RequestHandler):
    def markup(self, template, **values):
        self.response.write(JINJA_ENVIRONMENT.get_template(template).render(values))

class ROT13(MainHandler):
    def get(self):
        self.markup('rot13.html')
        
    def post(self):
        text = self.request.get('text')
        self.markup('rot13.html', result = cypher(text))

username_re = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
password_re = re.compile(r"^.{3,20}$")
email_re = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def valid_username(username):
    return username_re.match(username)

def valid_password(password):
    return password_re.match(password)

def valid_email(email):
    return not email or email_re.match(email)

class Signup(MainHandler):
    def get(self):
        self.markup('signup.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        values = {}

        if not valid_username(username):
            values['error_username'] = "That's not a valid username."
        if not valid_password(password):
            values['error_password'] = "That wasn't a valid password."
        if password != verify:
            values['error_verify'] = "Your passwords didn't match."
        if not valid_email(email):
            values['error_email'] = "That's not a valid email."

        if values != {}:
            values.update({'username' : username, 'email' : email})
            self.markup('signup.html', **values)
        else:
            self.redirect("/welcome?username=" + username)

class Welcome(MainHandler):
    def get(self):
        username = self.request.get('username')
        self.markup('welcome.html', username = username)

app = webapp2.WSGIApplication([
    ('/rot13', ROT13),
    ('/signup', Signup),
    ('/welcome', Welcome),
], debug=True)
