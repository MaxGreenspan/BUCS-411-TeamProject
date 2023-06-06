from datetime import timedelta

from flask import Flask, redirect, request, url_for, session
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user, UserMixin,
)
from authlib.integrations.flask_client import OAuth
import requests
# mysql
from flaskext.mysql import MySQL
# for image uploading
import os
import base64
import time

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
google_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()

# This will read the secret from file.
# WE SHOULD NOT PUBLISH OUR SECRET
with open('./secrets/google_secret') as f:
    google_secret = f.readline()

mysql = MySQL()
app = Flask(__name__)

# These will need to be changed according to your credentials.
# about things that needs to be changed, see comments.
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'zhuceyezi'  # NOTE:change this to your mysql password.
app.config['MYSQL_DATABASE_DB'] = 'CS411'  # Also change this if your database name is not CS411.
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# session config

# We need to decide on a app secret key. Probably someone should generate a random string. But it should be fine for
# now.
app.secret_key = "My key"
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)  # A permanent session lasts for 5 minutes.

# oauth setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='194531708522-ie050jd5vov5teo3a22e54pon6ct6286.apps.googleusercontent.com',
    client_secret=google_secret,
    access_token_url=google_cfg["token_endpoint"],
    authorize_url=google_cfg["authorization_endpoint"],
    client_kwargs={'scope': 'openid email profile'},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
)

login_manager = LoginManager()
login_manager.init_app(app)

# Mysql cursor.
conn = mysql.connect()
cursor = conn.cursor()


class User(UserMixin):
    pass


def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email from Users")
    return cursor.fetchall()


def isRegistered(email):
    c = conn.cursor()
    c.execute(f"SELECT email FROM Users WHERE Users.email='{email}'")
    result = c.fetchone()
    return result is not None


@login_manager.user_loader
def user_loader(email):
    # print("user_loader")
    users = getUserList()
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user


@app.route('/')
def hello_world():
    if request.args.get('test') == 'True':
        return "Hello testing!"
    elif not current_user.is_authenticated:
        return "Hello!"
    return f'Hello,you are logged in as {current_user.id}'


@app.route('/testLog')
@login_required
def testLog():
    return f"You are logged in!"


@login_manager.unauthorized_handler
def unauthorized_handler():
    return f"You are not logged in!"


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('hello_world'))


@app.route('/login/<method>', methods=['GET', 'POST'])
def login(method):
    if method == 'Google':
        google = oauth.create_client('google')  # create the google oauth client
        redirect_uri = url_for('authorize_google', _external=True)
        return google.authorize_redirect(redirect_uri)
    elif method == 'Username':
        redirect_uri = url_for('hello_world')
        session['email'] = 'test_Username_method'
        return redirect(redirect_uri)


@app.route('/register', methods=['POST'])
def register():
    c = conn.cursor()
    email = request.form.get('email')
    password = request.form.get('password')
    if not isRegistered(email):
        c.execute(f"INSERT INTO Users VALUES('{email}','{password}')")
        conn.commit()
        return f"Successfully registered {email} with pw:{password}"
    else:
        return f"Email {email} is already registered!"


@app.route('/authorize_google')
def authorize_google():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token()  # Access token from google. Needed though variable not used.
    userinfo = oauth.google.userinfo()
    user = User()
    user.id = userinfo['email']
    c = conn.cursor()
    if not isRegistered(user.id):
        c.execute(f"INSERT INTO Users(email) VALUES ({user.id})")
        conn.commit()
    login_user(user)
    # session.permanent = True  # make the session permanent so it keeps existing after browser gets closed
    return redirect(url_for('hello_world'))


if __name__ == '__main__':
    app.run()
