from flask import escape, flash, Flask, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy

import re

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:wordpass@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(127), unique=True, nullable=False)
    password = db.Column(db.String(127))
    blogs = db.relationship('BlogPost', backref='author', lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return "<User={id={self.id}, username='{username}'}>"

class BlogPost(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    body = db.Column(db.String(4095))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'),
        nullable=False)

    def __init__(self, title, body, author_id):
        self.title = title
        self.body = body
        self.author_id = author_id

def is_invalid_username(username_attempt):
    """returns False if username_attempt is a valid username,
        otherwise returns a helpful error message"""
    return (False if re.match("^[a-zA-Z][a-zA-Z0-9_]{2,19}$",
            username_attempt) else
            """username must be 3-20 characters in length, first character in
            [a-zA-Z], remaining characters in [a-zA-Z0-9_]""")

def is_invalid_password(password_attempt):
    """returns False if password_attempt is a valid password,
        otherwise returns a helpful error message"""
    return (False if re.match("^\S{3,20}$", password_attempt) else
        "password must be 3-20 characters in length, with no whitespace")

@app.route('/')
def index():
    return redirect('/blog')


@app.route('/blog')
def display_all_posts():
    post_id = request.args.get('id')
    print("post id {0!r}".format(post_id))
    if post_id:
        post = BlogPost.query.filter_by(id=post_id).first()
        return render_template('post.html', title=post.title, body=post.body)

    posts = BlogPost.query.all()
    return render_template('blog.html',title="It's Alive!",
                            posts=posts)


@app.route('/signup', methods=['GET', 'POST'])
def new_user():
    # User enters new, valid username, a valid password, and verifies password correctly and is redirected to the '/newpost' page with their username being stored in a session.
    # User leaves any of the username, password, or verify fields blank and gets an error message that one or more fields are invalid.
    # User enters a username that already exists and gets an error message that username already exists.
    # User enters different strings into the password and verify fields and gets an error message that the passwords do not match.
    # User enters a password or username less than 3 characters long and gets either an invalid username or an invalid password message.

    if request.method == 'GET':
        return render_template('signup.html')

    validated = True

    #
    # username validation
    #
    username_attempt = request.form.get('username', '').strip()
    username_errmsg = is_invalid_username(username_attempt)
    if username_errmsg: # username is empty or no good
        validated = False
    if User.query.filter_by(username=username_attempt).first() is not None:
        validated = False
        username_errmsg = "username already exists"
    valid_username = username_attempt if validated else None
    
    #
    # password validation
    #
    password_errmsg = ''
    password2_errmsg = ''
    password_attempt = request.form.get('password', '').strip()
    password2_attempt = request.form.get('password2', '').strip()
    password_error = is_invalid_password(password_attempt)
    if password_error:
        validated = False
        password_errmsg = password_error
    elif password_attempt != password2_attempt:
        validated = False
        password_errmsg = "good password ..."
        password2_errmsg = "but they don't match!"
    valid_password = password_attempt if validated else None
    
    if not validated:
        return render_template('signup.html',
                    username_invalid=username_errmsg,
                    password_invalid=password_errmsg,
                    password2_invalid=password2_errmsg)
    elif valid_username and valid_password:
        new_user = User(valid_username, valid_password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = valid_username
        return redirect('/newpost')
    else:
        return 


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username_attempt = request.form.get('username')
    if not username_attempt:
        return render_template('login.html')

    username_attempt = username_attempt.strip()
    username_error = is_invalid_username(username_attempt)
    if username_error:
        return render_template('login.html', errmsg=username_error)
    valid_user = User.query.filter_by(username=username_attempt).first()
    if valid_user:
        valid_password = False
        password_attempt = request.form.get('password')
        if password_attempt and password_attempt == valid_user.password:
            # User enters a username that is stored in the database with the correct password and is redirected to the /newpost page with their username being stored in a session.
            session['username'] = valid_user.username
            return redirect('/newpost')
        else:
            # User enters a username that is stored in the database with an incorrect password and is redirected to the /login page with a message that their password is incorrect.
            return render_template('login.html',
                                    username=valid_user.username,
                                    errmsg="invalid password")
    else:
        # User tries to login with a username that is not stored in the database and is redirected to the /login page with a message that this username does not exist.
        return render_template('login.html', errmsg="no such username")
    # User does not have an account and clicks "Create Account" and is directed to the /signup page.

@app.route('/checklogin')
def checklogin():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return 'You are not logged in'

@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
    return redirect('/blog')

@app.route('/newpost', methods=['GET', 'POST'])
def publish():
    if 'username' not in session:
        flash("please log in to create a new blog post")
        return redirect('/login')

    if request.method == 'POST':
        post_title = request.form['title']
        post_body = request.form['body']
        new_post = BlogPost(post_title, post_body)
        db.session.add(new_post)
        db.session.commit()
        return redirect('blog?id={0}'.format(new_post.id))
    else:
        return render_template('newpost.html')


#
# FOR DEVELOPMENT/DEMONSTRATION ONLY
#
# how-to get your secret key
# >>> import secrets
# >>> secrets.token_urlsafe(24)
# ...
# more info
# >>> help(secrets)
#
# NEVER MAKE YOUR SECRET KEY PUBLIC LIKE I HAVE HERE!!!
#
app.secret_key =  'mxLDMoEHmbuewIWDQmOl1oFgpALUScrb'

if __name__ == "__main__":
    app.run()