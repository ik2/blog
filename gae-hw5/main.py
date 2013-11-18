import jinja2
import os
import webapp2
import re
import json
from databases import *
from security import *

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class BlogHandler(webapp2.RequestHandler):
    def markup(self, template, **values):
        self.response.write(JINJA_ENVIRONMENT.get_template(template).render(values))

    def set_cookie(self, name, value):
        self.response.headers.add_header('Set-Cookie', name + '=' + make_secure_value(value) + '; Path=/')

    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.response.write(json_txt)

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        if self.request.url.endswith('.json'):
            self.format = 'json'
        else:
            self.format = 'html'

class Signup(BlogHandler):
    def get(self):
        self.markup('signup.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')
        user = User.by_name(username)
        values = {}
        if not valid_username(username):
            values['error_username'] = "That's not a valid username."
        if user:
            values['error_username2'] = "Username already exists."
        if not valid_password(password):
            values['error_password'] = "That wasn't a valid password."
        if password != verify:
            values['error_verify'] = "Your passwords didn't match."
        if not valid_email(email):
            values['error_email'] = "That's not a valid email."
        if values:
            values.update({'username' : username, 'email' : email})
            self.markup('signup.html', **values)
        else:
            password_hashed = make_password_hash(username, password)
            user = User(username = username, password_hashed = password_hashed, email = email)
            user.put()
            self.set_cookie("user_id", str(user.key().id()))
            self.redirect("/welcome")

class Welcome(BlogHandler):
    def get(self):
        cookie_str = self.request.cookies.get('user_id')
        if cookie_str and check_secure_value(cookie_str):
            uid = cookie_str.split('|')[0]
            user = User.get_by_id(int(uid))
            self.markup('welcome.html', username = user.username)
        else:
            self.redirect("/signup")

class Login(BlogHandler):
    def get(self):
        self.markup('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        user = User.by_name(username)
        if user and valid_password_hash(username, password, user.password_hashed):
            self.set_cookie("user_id", str(user.key().id()))
            self.redirect("/welcome")
        else:
            msg = "Invalid login"
            self.markup('login.html', username = username, error = msg)

class Logout(BlogHandler):
    def get(self):
        self.response.delete_cookie('user_id')
        self.redirect("/signup")

class Blog(BlogHandler):
    def get(self):
        posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC")
        if self.format == 'html':
            self.markup("blog.html", posts = posts)
        elif self.format == 'json':
            self.render_json(post.as_dict() for post in posts)

class NewPost(BlogHandler):
    def get(self):
        self.markup("newpost.html")

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")
        if subject and content:
            b = Post(subject = subject, content = content)
            b.put()
            permalink = str(b.key().id())
            self.redirect("/blog/" + permalink)
        else:
            msg = "subject and content, please!"
            self.markup("newpost.html", subject = subject, content = content, error = msg)

class PostPage(BlogHandler):
    def get(self, post_id):
        post = Post.get_by_id(int(post_id))
        if self.format == 'html':
            self.markup("blog.html", posts = [post])
        elif self.format == 'json':
            self.render_json(post.as_dict())

app = webapp2.WSGIApplication([
    ('/signup', Signup),
    ('/welcome', Welcome),
    ('/login', Login),
    ('/logout', Logout),
    ('/blog/?(?:\.json)?', Blog),
    ('/blog/newpost', NewPost),
    ('/blog/([0-9]+)(?:\.json)?', PostPage),
], debug=True)
