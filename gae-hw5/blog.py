import os
import jinja2
import webapp2
import re
import hashlib
import hmac
import random
from string import letters
from google.appengine.ext import db

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

SECRET = 'secret'

username_re = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username_re.match(username)

password_re = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password_re.match(password)

email_re = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(email):
    return not email or email_re.match(email)

def make_secure_value(s):
    return s + "|" + hmac.new(SECRET, s).hexdigest()

def check_secure_value(h):
    val = h.split('|')[0]
    if h == make_secure_value(val):
        return val

def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_password_hash(name, pw, salt=None):
    if not salt:
        salt=make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return h + "|" + salt

def valid_password_hash(name, pw, h):
    salt = h.split('|')[1]
    return h == make_password_hash(name, pw, salt)

class User(db.Model):
    username = db.StringProperty(required = True)
    password_hashed = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def by_name(cls, username):
        user = cls.all().filter('username =', username).get()
        return user

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

    def newline_replace(self):
        self.content = re.sub(r"[\r\n]+(?=.+)", "</p><p>", self.content)
        return self.content

class MainHandler(webapp2.RequestHandler):
    def markup(self, template, **values):
        self.response.write(JINJA_ENVIRONMENT.get_template(template).render(values))

    def set_cookie(self, name, value):
        self.response.headers.add_header('Set-Cookie', name + '=' + make_secure_value(value) + '; Path=/')

class Signup(MainHandler):
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
        if values != {}:
            values.update({'username' : username, 'email' : email})
            self.markup('signup.html', **values)
        else:
            password_hashed = make_password_hash(username, password)
            user = User(username = username, password_hashed = password_hashed, email = email)
            user.put()
            self.set_cookie("user_id", str(user.key().id()))
            self.redirect("/welcome")

class Welcome(MainHandler):
    def get(self):
        cookie_str = self.request.cookies.get('user_id')
        if cookie_str and check_secure_value(cookie_str):
            uid = cookie_str.split('|')[0]
            user = User.get_by_id(int(uid))
            self.markup('welcome.html', username = user.username)
        else:
            self.redirect("/signup")

class Login(MainHandler):
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

class Logout(MainHandler):
    def get(self):
        self.response.delete_cookie('user_id')
        self.redirect("/signup")

class Blog(MainHandler):
    def get(self):
        posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC")
        self.markup("blog.html", posts = posts)

class NewPost(MainHandler):
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

class PostPage(MainHandler):
    def get(self, post_id):
        posts = Post.get_by_id(int(post_id))
        self.markup("blog.html", posts = [posts])

app = webapp2.WSGIApplication([
    ('/signup', Signup),
    ('/welcome', Welcome),
    ('/login', Login),
    ('/logout', Logout),
    ('/blog', Blog),
    ('/blog/newpost', NewPost),
    ('/blog/([0-9]+)', PostPage),
], debug=True)
