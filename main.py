from flask import Flask, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:beproductive@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

class BlogPost(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    body = db.Column(db.String(4095))

    def __init__(self, title, body):
        self.title = title
        self.body = body

@app.route('/')
def index():
    return redirect('/blog')

@app.route('/blog')
def display_all_posts():

    posts = BlogPost.query.all()
    return render_template('blog.html',title="It's Alive!",
                            posts=posts)

@app.route('/newpost', methods=['GET', 'POST'])
def publish():

    if request.method == 'POST':
        post_title = request.form['title']
        post_body = request.form['body']
        new_post = BlogPost(post_title, post_body)
        db.session.add(new_post)
        db.session.commit()
        return redirect('blog')
    else:
        return render_template('newpost.html')


if __name__ == "__main__":
    app.run()