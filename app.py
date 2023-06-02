from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user, LoginManager, login_user, logout_user
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit

from models import Comment, db, Post, MyUser
import requests
from peewee import DoesNotExist
import pyttsx3 
from bs4 import BeautifulSoup


app = Flask(__name__, static_url_path='/static/')
app.config['SECRET_KEY'] = os.urandom(24)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

socketio = SocketIO(app)

@login_manager.user_loader
def load_user(user_id):
    return MyUser.select().where(MyUser.id == int(user_id)).first()

@app.before_request
def before_request():
    db.connect()

@app.after_request
def after_request(response):
    db.close()
    return response

@app.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))  # Redirect to the login page
    all_posts = Post.select()
    return render_template("index.html", page='home', posts=all_posts, news=[])

@app.route('/search')
def search():
    query = request.args.get('query', '')
    if query:
        all_posts = Post.select().where(Post.title.contains(query))
    else:
        all_posts = Post.select()
    return render_template('search.html', posts=all_posts, query=query)


# @app.route('/profile/<int:id>/')
# @login_required
# def profile(id):
#     user = MyUser.select().where(MyUser.id == id).first()
#     posts = Post.select().where(Post.author_id == id)
#     return render_template('profile.html', user=user, posts=posts)

@app.route('/create/', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        image = request.files['image']

        # Create the 'uploads' directory if it doesn't exist
        uploads_dir = os.path.join(app.static_folder, 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)

        # Save the image to the 'uploads' directory
        image.save(os.path.join(uploads_dir, image.filename))

        post = Post.create(
            title=title,
            description=description,
            image_path='static/uploads/' + image.filename,
            author=current_user
        )

        flash('Post created successfully.')
        return redirect('/')
    return render_template('create.html')

@app.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = Post.select().where(Post.id == id).first()
    if request.method == 'POST':
        if current_user == post.author:
            if post:
                title = request.form['title']
                description = request.form['description']
                post.title = title
                post.description = description
                post.save()
                return redirect(f'/{id}/')
            return f'Post with id = {id} does not exist'
        return f'You dont have permission to update this post'
    return render_template('update.html', post=post)

def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search("[a-z]", password):
        return False
    if not re.search("[A-Z]", password):
        return False
    if not re.search("[0-9]", password):
        return False
    return True

@app.route('/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_post(id):
    try:
        post = Post.get(Post.id == id, Post.author == current_user)
        Comment.delete().where(Comment.post == post).execute()
        post.delete_instance()
        flash('Post deleted successfully.')
        return redirect("/")
    except DoesNotExist:
        return f"Post with id = {id} does not exist"

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        second_name = request.form['second_name']
        password = request.form['password']
        age = request.form['age']
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$'
        user = MyUser.select().where(MyUser.email == email).first()
        if user:
            flash('Email address already exists')
            return redirect('/register/')
        else:
            t1 = len(email)
            t2 = len(name)
            t3 = len(second_name)
            t4 = len(password)
            t5 = len(age)
            if t4 < 8:
                flash('Password should be at least 8 characters long')
                return redirect('/register/')  # Redirect back to the registration page
            elif re.match(pattern, password) is None:
                MyUser.create(
                    email=email,
                    name=name,
                    second_name=second_name,
                    password=generate_password_hash(password, method='scrypt'),
                    age=age
                )
                flash('Registration successful. Please login to continue.')
                return redirect('/login/')  # Redirect to the login page
            return render_template('register.html')
    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = MyUser.select().where(MyUser.email == email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect('/login/')
        else:
            login_user(user)
            return redirect('/')  # Redirect to the main page
    return render_template('login.html')

@app.route('/current_profile/')
@login_required
def current_profile():
    posts = Post.select().where(Post.author_id == current_user.id)
    return render_template('profile.html', user=current_user, posts=posts)

@app.route('/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    post = Post.select().where(Post.id == id).first()
    if post:
        content = request.form['content']
        comment = Comment.create(
            post=post,
            author=current_user,
            content=content
        )
        flash('Comment added successfully.')
        return redirect('/')
    return f'Post with id = {id} does not exist'

@app.route('/logout/')
def logout():
    logout_user()
    return redirect('/login/')

@app.route('/get_latest/')
def get_latest_news():
    # if request.method == 'POST':
    # Send a GET request to the website
    url = 'https://akipress.org/'
    response = requests.get(url)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the news headlines
    news_headlines = soup.find_all('h2', class_='news-title')

    # Extract the text content from the headlines
    news_text = [headline.text.strip() for headline in news_headlines]

    # Convert the news text to audio messages
    engine = pyttsx3.init()
    audio_messages = []
    for text in news_text:
        audio_path = f'audio/{text[:10]}.mp3'
        engine.save_to_file(text, audio_path)
        engine.runAndWait()
        audio_messages.append(audio_path)

    return render_template('get_latest_news.html', audio_messages=audio_messages)

    # return render_template('base.html', audio_messages=[])

@app.route('/video')
@login_required
def video_chat():
    return render_template('video.html')

@socketio.on('message')
def handle_message(message):
    emit('message', message, broadcast=True)

@socketio.on('chat_message')
def handle_chat_message(message):
    emit('chat_message', message, broadcast=True)

# Добавленная функция
@app.route('/example')
def example():
    return "This is an example route."

if __name__ == "__main__":
    socketio.run(app, debug=True)
