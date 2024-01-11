from flask_login import login_user, login_required, logout_user, current_user
import pathlib
import requests
from flask import Blueprint, render_template, flash, url_for, session, abort, redirect, request,Flask,render_template_string
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import random
import string
from pip._vendor import cachecontrol
from flask_migrate import Migrate
import os
from werkzeug.security import generate_password_hash, check_password_hash
from __init__ import db   
from models import User
import urllib.parse
from urllib.parse import quote_plus

app = Flask(__name__)

routing = Blueprint('routing', __name__)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
migrate = Migrate(app, db)


client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret_610011968325-45c7qseggh3ie6oqsh7u975q8vikoprr.apps.googleusercontent.com.json")

from config import GOOGLE_CLIENT_ID

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback",
)

@routing.route('/', methods=['GET', 'POST'])
@login_required

def home():

  return render_template('home.html',user=current_user)
   
@routing.route('/login')
def login_page():

  return render_template('login.html')


@routing.route('/loginbygoogle')
def login_bygoogle():

    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)



@routing.route('/callback')
def callback():


    flow.fetch_token(authorization_response=request.url)


    if not session["state"] == request.args["state"]:
        abort(500)  


    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    
    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
        
    )
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    user = User.query.filter_by(email=session["email"]).first()
    if not user:
        plain_password = ''.join(random.choice(string.ascii_letters) for i in range(10))
        hashed_password = generate_password_hash(plain_password, method='pbkdf2:sha256')



        new_user = User(
            email=session["email"],
            first_name=session["name"],
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        user = new_user
    flash('Logged in successfully!', category='success')
    login_user(user, remember=True)
    return redirect(url_for('routing.home'))



@routing.route('/logout')
@login_required
def logout():
    logout_user()
   
    return redirect(url_for('routing.login_page'))

@routing.route('/share_on_telegram')
@login_required
def share_on_telegram():
    message = f"نام صاحب اکانت : {current_user.first_name}\nایمیل: {current_user.email}\nمی توانید در این قسمت اطلاعات ورود کننده به حساب را مشاهده کنید و این اطلاعات را به اشتراک بگذارید."
    encoded_message = quote_plus(message)
    
    url_to_share = url_for('routing.home', _external=True)
    
    telegram_url = f"https://t.me/share/url?url={quote_plus(url_to_share)}&text={encoded_message}"
    
    return redirect(telegram_url)

@routing.route('/share_on_whatsapp')
def share_on_whatsapp():
   
    message = f"می توانید اطلاعات مربوط به ورود و نام کاربری را در این لینک مشاهده کنید \n نام صاحب اکانت : {current_user.first_name}\nایمیل: {current_user.email}"
    encoded_message = quote_plus(message)
    url_to_share = url_for('routing.home', _external=True)

    url_to_share = request.args.get('url', 'http://127.0.0.1:5000')
    whatsapp_url = f"https://wa.me/?text={quote_plus(url_to_share)}&text={encoded_message}"
    return redirect(whatsapp_url)
