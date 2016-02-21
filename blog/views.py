from models import User, get_todays_recent_posts
from flask import Flask, request, session, redirect, url_for, render_template, flash

app = Flask(__name__)

@app.route('/')
def index():
    posts = get_todays_recent_posts()
    return render_template('index.html', posts=posts)

@app.route('/profile/<username>')
def profile(username):
    logged_in_username = session.get('username')
    user_being_viewed_username = username

    user_being_viewed = User(user_being_viewed_username)
    posts = user_being_viewed.get_recent_posts()

    similar = []
    common = []
    kids = []

    if logged_in_username:
        logged_in_user = User(logged_in_username)

        if logged_in_user.username == user_being_viewed.username:
            similar = logged_in_user.get_similar_users()
            kids = logged_in_user.get_kids()
        else:
            common = logged_in_user.get_commonality_of_user(user_being_viewed)

    return render_template(
        'profile.html',
        username=username,
        posts=posts,
        similar=similar,
        kids=kids,
        common=common
    )

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(username) < 1:
            flash('Your username must be at least one character.')
        elif len(password) < 5:
            flash('Your password must be at least 5 characters.')
        elif not User(username).register(password):
            flash('A user with that username already exists.')
        else:
            session['username'] = username
            flash('Logged in.')
            return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not User(username).verify_password(password):
            flash('Invalid login.')
        else:
            session['username'] = username
            flash('Logged in.')
            return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out.')
    return redirect(url_for('index'))

@app.route('/add_kid', methods=['POST'])
def add_kid():
    name = request.form['name']

    if not name:
        flash('You must give your kid a name.')
    else:
        User(session['username']).add_kid(name)
        flash('adding kid')

    return redirect(url_for('index'))

@app.route('/add_post', methods=['POST'])
def add_post():
    title = request.form['title']
    tags = request.form['tags']
    text = request.form['text']

    if not title or not tags or not text:
        if not title:
            flash('You must give your post a title.')
        if not tags:
            flash('You must give your post at least one tag.')
        if not text:
            flash('You must give your post a text body.')
    else:
        User(session['username']).add_post(title, tags, text)

    return redirect(url_for('index'))

@app.route('/add_goal', methods=['POST'])
def add_goal():
    goalName = request.form['goalName']
    kidName = request.form['kidName']
    amount = request.form['amount']
    carrot = request.form['carrot']
    stick = request.form['stick']

    if not goalName or not kidName or not amount:
        if not goalName:
            flash('You must give your goal a goalName.')
        if not kidName:
            flash('You must give your goal at least one kid.')
        if not amount:
            flash('You must give your goal an amount.')
    else:
        User(session['username']).add_goal(goalName, kidName, amount, carrot, stick)

    return redirect(url_for('index'))


@app.route('/like_post/<post_id>')
def like_post(post_id):
    username = session.get('username')

    if not username:
        flash('You must be logged in to like a post.')
        return redirect(url_for('login'))

    User(username).like_post(post_id)

    flash('Liked post.')
    return redirect(request.referrer)

# @app.route('/profile/<username>')
# def profile(username):
#     logged_in_username = session.get('username')
#     user_being_viewed_username = username

#     user_being_viewed = User(user_being_viewed_username)
#     posts = user_being_viewed.get_recent_posts()

#     similar = []
#     common = []

#     if logged_in_username:
#         logged_in_user = User(logged_in_username)

#         if logged_in_user.username == user_being_viewed.username:
#             similar = logged_in_user.get_similar_users()
#         else:
#             common = logged_in_user.get_commonality_of_user(user_being_viewed)

#     return render_template(
#         'profile.html',
#         username=username,
#         posts=posts,
#         similar=similar,
#         common=common
#     )