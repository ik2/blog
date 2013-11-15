import os
import jinja2
import webapp2
import re
from google.appengine.ext import db

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class MainHandler(webapp2.RequestHandler):
    def markup(self, template, **values):
        self.response.write(JINJA_ENVIRONMENT.get_template(template).render(values))

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

    def newline_replace(self):
        self.content = re.sub(r"[\r\n]+(?=.+)", "</p><p>", self.content)
        return self.content

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
            error = "subject and content, please!"
            self.markup("newpost.html", subject = subject, content = content, error = error)

class PostPage(MainHandler):
    def get(self, post_id):
        posts = Post.get_by_id(int(post_id))
        self.markup("blog.html", posts = [posts])

app = webapp2.WSGIApplication([
    ('/blog', Blog),
    ('/blog/newpost', NewPost),
    ('/blog/([0-9]+)', PostPage),
], debug=True)
