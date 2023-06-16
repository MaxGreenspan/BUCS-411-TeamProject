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
import json
from util import *

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
google_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()

# This will read the secret from file.
# WE SHOULD NOT PUBLISH OUR SECRET
with open("secrets/google_secret") as f:
    google_secret = f.readline()

with open("secrets/chatgpt_api_key") as f:
    openai.api_key = f.readline()

mysql = MySQL()
app = Flask(__name__, static_url_path="/static")

# These will need to be changed according to your credentials.
# about things that needs to be changed, see comments.
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'BostonU#3087'  # NOTE:change this to your mysql password.
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


def parseOpenAIImgName(url):
    pass


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

    if message:
        messages.append(
            {"role": "user", "content": message},
        )
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages
        )
    reply = chat.choices[0].message.content
    if reply.__contains__("idk") \
            or reply.__contains__('invalid') \
            or reply.__contains__('Sorry') \
            or reply.__contains__("cannot"):
        print("The service cannot understand your input!")
        return "The service cannot understand your input!", False
    # print(f"ChatGPT: {reply}")
    messages.append({"role": "assistant", "content": reply})

    return reply, True


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


def getImgDataFromPath(path):
    data = base64.b64encode(open(f'{path}', 'rb').read()).decode('utf-8')
    return data


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
    message = request.args.get('message')
    imgPath = request.args.get('imgPath')
    imgName = request.args.get('imgName')
    redirectFromSave = request.args.get('redirectFromSave')
    ok = request.args.get('ok')
    if not current_user.is_authenticated:
        email = None
    else:
        email = current_user.id
    return render_template('frontend.html', message=message, imgPath=imgPath,
                           imgName=imgName, redirectFromSave=redirectFromSave,
                           authorized=current_user.is_authenticated, email=email, ok=ok)


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
    return redirect(url_for('frontPage', test=True))


@app.route('/login', methods=['GET', 'POST'])
def login():
    method = request.args.get('method')
    message = request.args.get('message')
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
        return render_template('login.html', message=message)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        c = conn.cursor()
        email = request.form.get('email')
        password = request.form.get('password')
        if not isRegistered(email):
            c.execute(f"INSERT INTO Users VALUES('{email}','{password}')")
            conn.commit()
            return redirect(url_for('login', message=f"Successfully registered {email}!", method="Username"))
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


@app.route('/img/<name>')
def testimg(name):
    # https://stackoverflow.com/questions/7389567/output-images-to-html-using-python
    # img = f'<img src="data:image/png;base64,{data}">'
    return render_template('testimg.html', name=name, getImgDataFromName=getImgDataFromName)


@app.route('/download')
def download():
    image_url = request.args.get('url')
    img_data = requests.get(image_url).content
    # sometimes open with relative path doesn't work
    img_path = getImgPathFromName("test.png")
    with open(f'{img_path}', 'wb+') as handler:
        handler.write(img_data)
    return redirect(url_for('testimg', name="test.png"))


@app.route('/downloadOpenai')
def downloadOpenai():
    image_url = request.args.get('url')


@app.route('/history')
@login_required
def load_history():
    imgname = request.args.get('imgname')
    quote = request.args.get('quote')
    email = current_user.id
    c = conn.cursor()
    c.execute(f"SELECT * FROM history WHERE email='{email}' ORDER BY hid DESC")
    result = c.fetchall()
    final = []
    for t in result:
        d = {
            'quote': t[2],
            'imgname': t[3],
            'date': t[4],
            'description': t[5],
        }
        final.append(d)
    return render_template('history.html', data=final, imgname=imgname, quote=quote)


@app.route('/generate', methods=['POST'])
def generate():
    keyword = request.form.get('keyword')
    quote, ok = getquote(keyword)
    print(quote)
    # quote = "(Test)Even on the darkest days, the sun is just behind the clouds."
    if ok:
        quote = quote[1:-1]
        prompt = getprompt(quote)
        print(prompt)
        imgUrl = 'https://cdn-prod.medicalnewstoday.com/content/images/articles/319/319899/glass-half-empty-and-half-full.jpg'
        imgName = getimage(prompt)
        # imgName = "glass-half-empty-and-half-full.jpg"
        return redirect(url_for('frontPage', message=quote, test=True, imgName=imgName, ok=ok))
    return redirect(url_for('frontPage', message=quote, test=True, ok=ok))


@app.route('/view')
def view():
    imgname = request.args.get('imgname')
    message = request.args.get('message')
    return redirect(url_for('frontPage', message=message, imgname=imgname, test=True))


@app.route('/saveToHistory', methods=['POST'])
@login_required
def saveToHistory():
    description = request.form.get('description')
    quote = request.form.get('quote')
    imgName = request.form.get('imgName')
    c = conn.cursor()
    c.execute(
        "INSERT INTO history(email, quote, imgname, description, date) \
        VALUES(%s,%s,%s,%s,%s)", (current_user.id, quote, imgName, description, getCurrentDate()))
    conn.commit()
    return redirect(url_for("frontPage", imgName=imgName, message=quote, redirectFromSave=True, test=True, ok=True))


def encodeimage(script):
    PROMPT = script
    DATA_DIR = Path.cwd() / "jsons"

    DATA_DIR.mkdir(exist_ok=True)

    response = openai.Image.create(
        prompt=PROMPT,
        n=1,
        size="256x256",
        response_format="b64_json",
    )

    # This is where the filename is generated
    file_name = DATA_DIR / f"{PROMPT[:5]}-{response['created']}.json"

    with open(file_name, mode="w", encoding="utf-8") as file:
        json.dump(response, file)

    return file_name


def getimage(prompt):
    # DATA_DIR stores the image in a file called "responses"
    DATA_DIR = Path.cwd() / "jsons"
    # The filename is "Write-1686233086.json", generated by getimage() function
    JSON_FILE = DATA_DIR / encodeimage(prompt)
    # IMAGE_DIR stores the image in a file called "images" in png format
    IMAGE_DIR = Path.cwd() / "static"

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    with open(JSON_FILE, mode="r", encoding="utf-8") as file:
        response = json.load(file)

    for index, image_dict in enumerate(response["data"]):
        image_data = base64.b64decode(image_dict["b64_json"])
        image_file = IMAGE_DIR / f"{JSON_FILE.stem}-{index}.png"
        with open(image_file, mode="wb") as png:
            png.write(image_data)
    return f"{JSON_FILE.stem}-{index}.png"

if __name__ == '__main__':
    app.run()