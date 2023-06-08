from datetime import timedelta

from flask import Flask, redirect, request, url_for, session, render_template
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user, UserMixin,
)
from pathlib import Path, PurePosixPath
from authlib.integrations.flask_client import OAuth
import requests
# mysql
from flaskext.mysql import MySQL
# for image uploading
import os
import base64
import time
import openai
import datetime

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
google_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()

# This will read the secret from file.
# WE SHOULD NOT PUBLISH OUR SECRET
with open("secrets/google_secret") as f:
    google_secret = f.readline()

with open("secrets/chatgpt_api_key") as f:
    openai.api_key = f.readline()

if not os.path.exists("./img"):
    os.mkdir('img')

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


# cursor = conn.cursor()


class User(UserMixin):
    pass


def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email from Users")
    return cursor.fetchall()


def parseImgName(url):
    return url.split('/')[-1]


def getCurrentDate():
    return datetime.datetime.fromtimestamp(
        time.time()).strftime('%Y-%m-%d')


def isRegistered(email):
    c = conn.cursor()
    c.execute(f"SELECT email FROM Users WHERE Users.email='{email}'")
    result = c.fetchone()
    return result is not None


def getImgDataFromName(imgname):
    path = getImgPathFromName(imgname)
    # https://stackoverflow.com/questions/7389567/output-images-to-html-using-python
    data = base64.b64encode(open(f'{path}', 'rb').read()).decode('utf-8')
    return data


def getImgDataFromUrl(image_url):
    img_data = requests.get(image_url).content
    # sometimes open with relative path doesn't work
    img_path = getImgPathFromName(parseImgName(image_url))
    with open(f'{img_path}', 'wb+') as handler:
        handler.write(img_data)
    imgname = parseImgName(image_url)
    return getImgDataFromName(imgname)


def getquote(keyword):
    messages = [{"role": "system",
                 "content": "Generate a quote within 30 words without an author in quotation marks only based solely on a single word that users enter. If the word entered is invalid, just return the string 'idk' and nothing else."}]

    message = keyword

    if len(message.split()) > 1:
        print("Only a single word is allowed!")
        return "Only a single word is allowed!"

    if message:
        messages.append(
            {"role": "user", "content": message},
        )
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages
        )
    reply = chat.choices[0].message.content
    if reply == "idk":
        print("ChatGPT cannot understand your input!")
        return "ChatGPT cannot understand your input!"
    # print(f"ChatGPT: {reply}")
    messages.append({"role": "assistant", "content": reply})

    return reply


def getprompt(quote):
    messages = [{"role": "system",
                 "content": "Create a prompt in 30 words or less that generates an image based on the quote I send you."}]

    message = quote

    if message:
        messages.append(
            {"role": "user", "content": message},
        )
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages
        )
    reply = chat.choices[0].message.content
    # print(f"ChatGPT: {reply}")
    messages.append({"role": "assistant", "content": reply})

    return reply


def getImgPathFromName(imgName):
    """
    Please pass in the name returned by parseImgName
    """
    return str(Path(__file__).parent.as_posix()) + "/img/" + imgName


@login_manager.user_loader
def user_loader(email):
    # print("user_loader")
    users = getUserList()
    if not email or email not in str(users):
        return
    user = User()
    user.id = email
    return user


@app.route('/')
def frontPage():
    if request.args.get('test') == 'True':
        message = request.args.get('message')
        imgname = request.args.get('imgname')
        return render_template('frontend.html', message=message, getdata=getImgDataFromName, imgname=imgname)
    elif not current_user.is_authenticated:
        return f"Hello!"
    return f"Hello, you are logged in as {current_user.id}"


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


@app.route('/login', methods=['GET', 'POST'])
def login():
    method = request.args.get('method')
    if method == 'Google' and request.method == 'GET':
        google = oauth.create_client('google')  # create the google oauth client
        redirect_uri = url_for('authorize_google', _external=True)
        destination = google.authorize_redirect(redirect_uri)
        return destination
    elif method == 'Username' and request.method == 'POST':
        redirect_uri = url_for('frontPage')
        email = request.form.get('email')
        password = request.form.get('password')
        c = conn.cursor()
        c.execute(f"SELECT email FROM Users u WHERE u.email = '{email}' and u.password = '{password}'")
        result = c.fetchone()
        if result is not None:
            user = User()
            user.id = email
            login_user(user)
            return redirect(redirect_uri)
        else:
            c.execute(f"SELECT email FROM Users u WHERE u.email = '{email}'")
            if c.fetchone() is not None:
                return f"Wrong Username or password!"
            return f"Not registered yet!"
    elif method == 'Username' and request.method == 'GET':
        return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        c = conn.cursor()
        email = request.form.get('email')
        password = request.form.get('password')
        if not isRegistered(email):
            c.execute(f"INSERT INTO Users VALUES('{email}','{password}')")
            conn.commit()
            return redirect('login', method='Username', message=f"Successfully registered {email}!")
        else:
            return render_template('register.html', message=f"Email {email} is already registered!")
    elif request.method == 'GET':
        return render_template('register.html')


@app.route('/authorize_google')
def authorize_google():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token()  # Access token from google. Needed though variable not used.
    userinfo = oauth.google.userinfo()
    user = User()
    user.id = userinfo['email']
    c = conn.cursor()
    if not isRegistered(user.id):
        c.execute(f"INSERT INTO Users(email) VALUES ('{user.id}')")
        conn.commit()
    login_user(user)
    # session.permanent = True  # make the session permanent so it keeps existing after browser gets closed
    return redirect(url_for('frontPage'))


@app.route('/testquote')
def testquote():
    keyword = request.args.get('keyword')
    quote = getquote(keyword)
    return quote


@app.route('/testprompt')
def testprompt():
    keyword = request.args.get('keyword')
    quote = getquote(keyword)
    prompt = getprompt(quote)
    return prompt


@app.route('/testimg')
def testimg():
    path = request.args.get('path')
    # https://stackoverflow.com/questions/7389567/output-images-to-html-using-python
    data = base64.b64encode(open(f'{path}', 'rb').read()).decode('utf-8')
    img = f'<img src="data:image/png;base64,{data}">'
    return img


@app.route('/download')
def download():
    image_url = request.args.get('url')
    img_data = requests.get(image_url).content
    # sometimes open with relative path doesn't work
    img_path = getImgPathFromName(parseImgName(image_url))
    with open(f'{img_path}', 'wb+') as handler:
        handler.write(img_data)
    return redirect(url_for('testimg', path=img_path))


@app.route('/history')
@login_required
def load_history():
    email = current_user.id
    c = conn.cursor()
    c.execute(f"SELECT * FROM history WHERE email='{email}'")
    result = c.fetchall()
    final = []
    for t in result:
        d = {'hid': t[0],
             'email': t[1],
             'quote': t[2],
             'imgname': t[3],
             'date': t[4],
             'keyword': t[5],
             }
        final.append(d)
    return render_template('history.html', data=final)


@app.route('/generate', methods=['POST'])
def generate():
    keyword = request.form.get('keyword')
    if current_user.is_authenticated:
        email = current_user.id
        quote = 'This is chatgpt response'
        if not (quote.__contains__('invalid') or quote.__contains__('Sorry') or quote.__contains__("cannot")):
            prompt = 'prompt'
            imgUrl = 'https://cdn-prod.medicalnewstoday.com/content/images/articles/319/319899/glass-half-empty-and-half-full.jpg'
            imgname = parseImgName(imgUrl)
            c = conn.cursor()
            c.execute(
                f"INSERT INTO history(email, quote, imgname,keyword,date) VALUES ('{email}','{quote}','{imgname}','{keyword}','{getCurrentDate()}')")
            conn.commit()
            return redirect(url_for('frontPage', message='Generated!', test=True, imgname=imgname))
    else:
        quote = 'This is chatgpt response'
        if not (quote.__contains__('invalid') or quote.__contains__('Sorry') or quote.__contains__("cannot")):
            prompt = 'prompt'
            imgUrl = 'https://cdn-prod.medicalnewstoday.com/content/images/articles/319/319899/glass-half-empty-and-half-full.jpg'
            imgname = parseImgName(imgUrl)
            return redirect(url_for('frontPage', message='Generated!', test=True, imgname=imgname))
        return redirect(url_for('frontPage', quote=quote, test=True))


@app.route('/view')
def view():
    imgname = request.args.get('imgname')
    message = request.args.get('message')
    return redirect(url_for('frontPage', message=message, imgname=imgname, test=True))


if __name__ == '__main__':
    app.run()
