#!/usr/bin/env python3
"""ReL8 Flask app"""
import binascii
from flask import abort, flash, Flask, jsonify, render_template
from flask import redirect, request, session, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import models
from models.user import User
import os
import phonenumbers
from rel8.forms import RegistrationForm, PasswordForm, LoginForm, VariablesForm
from twilio.twiml.messaging_response import MessagingResponse


TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

app = Flask(__name__)
app.url_map.strict_slashes = False
app.secret_key = os.getenv('SECRET_KEY')

bcrypt = Bcrypt(app)

SITE_URL = os.getenv('SITE_URL')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return models.storage.get(User, user_id)


def get_session():
    counter = session.get('counter', 0)
    counter += 1
    session['counter'] = counter
    consent = session.get('consent', False)
    name_req = session.get('name_req', False)

    return session, counter, consent, name_req


def standardize_phone(phone_number):
    phone_number = phonenumbers.parse(phone_number, "US")
    phone_number_formatted = phonenumbers.format_number(
                phone_number, phonenumbers.PhoneNumberFormat.E164)
    return phone_number_formatted


def find_user_by_phone(phone_number):
    phone_number_formatted = standardize_phone(phone_number)
    users = models.storage.all(User)
    for user in users.values():
        if user.phone_number == phone_number_formatted:
            return user
    return None


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user:
        return redirect(url_for('account'))
    error = None
    form = RegistrationForm()
    if form.validate_on_submit():
        user = find_user_by_phone(form.phone_number.data)
        if user:
            if user.access_code == form.access_code.data:
                user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                user.save()
                return redirect(url_for('login'))
            else:
                error = 'Check access code or follow link in text'
        else:
            error = 'Account does not exist'

    return render_template('register.html', form=form, error=error)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    form = LoginForm()
    if form.validate_on_submit():
        user = find_user_by_phone(form.phone_number.data)
        if user:
            if not user.password:
                error = 'Set up a password first'
                form = RegistrationForm()
                return render_template('register.html', form=form, error=error)
            elif bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                session['user-id'] = user.id #TODO: keep?
                session['logged_in'] = True #TODO: keep?
                #TODO: check if variables are set up
                return redirect(url_for('account'))
            else:
                error = 'Check your password'
        else:
            error = 'Account does not exist'

    return render_template('login.html', form=form, error=error)


@app.route('/logout')
@login_required
def logout():
    session['logged_in'] = False
    session.pop('user-id')
    logout_user()
    return redirect(url_for('index'))


@app.route('/account', methods=['GET'])
@login_required
def account():
    error = None
    return render_template('account.html', error=error, user=current_user)


@app.route('/password', methods=['GET', 'POST'])
@login_required
def password(user=None):
    form = PasswordForm()
    if form.validate_on_submit():
        current_user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        current_user.save()
        flash('Updated password')

    return render_template('password.html', form=form)


@app.route('/variables', methods=['GET', 'POST'])
@login_required
def variables():
    error = None
    user = None
    form = VariablesForm()
    print(type(form))

    user_id = session.get('user-id', None)
    if session.get('logged_in') and user_id:
        user = models.storage.get(User, user_id)
    else:
        return redirect(url_for('password'))

    if request.method == 'POST' and form.validate_on_submit():
        return redirect(url_for('account'))
    return render_template('variables.html', form=form, error=error)



@app.route('/sms/<test>', methods=['POST'])
def sms(test=None):
    session, counter, consent, name_req = get_session()
    response = MessagingResponse()

    json = request.get_json()
    phone_number = json['From']
    message = json['Body']

    users = models.storage.all(User)
    user = users.get(phone_number, None)
    if user:
        response.message(
            "Hi {}, welcome. This is visit #{}.".format(
                user.username, counter
            )
        )
        # TODO: determine predictor/symptom, save message, create  gcal entry

    elif consent is True and name_req is True:
        access_code = binascii.hexlify(os.urandom(8)).decode()
        session['access-code'] = access_code
        user = User()
        user.username = message
        user.phone_number = phone_number
        user.access_code = access_code
        models.storage.new(user)
        models.storage.save()
        session['user-id'] = user.id
        response.message(
            "Welcome {}! Please go to {}/register/?access-code={}".format(
                message, SITE_URL, access_code
            )
        )

    elif consent is True and name_req is False:
        session['name_req'] = True
        if message.strip().lower() == 'yes':
            session['consent'] = True
            response.message("What's your name?")
        elif message.strip().lower() == 'no':
            response.message("Sorry to hear that. Bye.")

    else:
        response.message("Would you like to enroll in rel8? [Yes, No]")
        session['consent'] = True

    return str(response)



if __name__ == '__main__':
    app.run(
        host=os.getenv('REL8_HOST', default='0.0.0.0'),
        port=int(os.getenv('REL8_PORT', default=5000))
    )
