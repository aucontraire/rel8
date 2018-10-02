#!/usr/bin/env python3
"""ReL8 Flask app"""
import binascii
from flask import abort, flash, Flask, jsonify, render_template
from flask import redirect, request, session, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import models
from models.outcome import Outcome
from models.predictor import Predictor
from models.response import Response
from models.session import Session
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
    if current_user:
        return redirect('account')
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
                return redirect(url_for('account'))
            else:
                error = 'Check your password'
        else:
            error = 'Account does not exist'

    return render_template('login.html', form=form, error=error)


@app.route('/logout')
@login_required
def logout():
    session.pop('user-id')
    logout_user()
    return redirect(url_for('index'))


@app.route('/account', methods=['GET'])
@login_required
def account():
    error = None
    current_user.responses.sort(key=lambda resp: resp.updated_at, reverse=False)
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
    form = VariablesForm()

    if form.validate_on_submit():
        predictor = Predictor(
            name=form.predictor.data,
            user_id=current_user.id
        )
        outcome = Outcome(
            name=form.outcome.data,
            user_id=current_user.id
        )
        models.storage.new(predictor)
        models.storage.new(outcome)
        models.storage.save()
        flash('Variables added')

    return render_template('variables.html', form=form, error=error)


@app.route('/sms', methods=['POST'])
def sms():
    session, counter, consent, name_req = get_session()
    response = MessagingResponse()
    phone_number = request.form['From']
    message = request.form['Body']

    user = find_user_by_phone(phone_number)
    if user:
        if not user.predictor and not user.outcome:
            response.message(
                "Hi {}. You need to set up your variables first: {}".format(
                    user.username, SITE_URL
                )
            )
        elif message.strip().lower() != user.predictor.name and message.strip().lower() != user.outcome.name:
            response.message('That does not match your variables. Try again.')
        else:
            user.sessions.sort(key=lambda sess: sess.updated_at, reverse=True)
            if len(user.sessions) == 0 or user.sessions[0].complete is True:
                print('0 sessions or last session complete is True')
                sms_session = Session(user_id=user.id)
                models.storage.new(sms_session)
                models.storage.save()
                if message.strip().lower() == user.predictor.name:
                    print('matched predictor name')
                    sms_response = Response(
                        session_id=sms_session.id,
                        predictor_id=user.predictor.id,
                        user_id=user.id,
                        message=message,
                        twilio_json="{}"
                    )
                    models.storage.new(sms_response)
                    models.storage.save()
                else:
                    response.message('This should be the predictor.')
            elif user.sessions[0].complete is False:
                print('last session complete is False')
                print(message, user.outcome.name)
                print(len(message), len(user.outcome.name))
                if message.strip().lower() == user.outcome.name:
                    print('matched outcome name')
                    sms_session = user.sessions[0]
                    sms_response = Response(
                        session_id=sms_session.id,
                        outcome_id=user.outcome.id,
                        user_id=user.id,
                        message=message,
                        twilio_json="{}"
                    )
                    models.storage.new(sms_response)
                    sms_session.complete = True
                    models.storage.save()

        if message.strip().lower() == "clear":
            session.clear()
            response.message("Session cleared")

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


@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(
        host=os.getenv('REL8_HOST', default='0.0.0.0'),
        port=int(os.getenv('REL8_PORT', default=5000))
    )
