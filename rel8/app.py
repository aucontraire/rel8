#!/usr/bin/env python3
"""rel8 Flask app"""
import binascii
import datetime
from flask import abort, flash, Flask, jsonify, render_template
from flask import redirect, request, session, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import models
from models.interval import Interval
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
        return redirect('dashboard')
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
                return redirect(url_for('dashboard'))
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


@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    error = None
    responses = []
    current_user.sessions.sort(key=lambda session: session.updated_at, reverse=False)
    for session in current_user.sessions:
        session.responses.sort(key=lambda response: response.updated_at, reverse=False)
        if len(session.responses) == 1:
            responses.append((session.responses[0], ))
        else:
            responses.append((session.responses[0], session.responses[1]))

    return render_template('dashboard.html', error=error, user=current_user, responses=responses)


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
            name=form.predictor.data.strip().lower(),
            user_id=current_user.id
        )
        outcome = Outcome(
            name=form.outcome.data.strip().lower(),
            user_id=current_user.id
        )
        interval = Interval(
            duration=form.duration.data,
            user_id=current_user.id
        )
        models.storage.new(predictor)
        models.storage.new(outcome)
        models.storage.new(interval)
        models.storage.save()
        flash('Variables added')

    return render_template('variables.html', form=form, error=error)


def session_expired(created_at, interval):
    delta = datetime.timedelta(hours=interval)
    now = datetime.datetime.utcnow()
    return now > created_at + delta


def new_session(user, message, response):
    sms_session = Session(
        user_id=user.id,
        interval_id=user.interval.id
    )
    models.storage.new(sms_session)
    models.storage.save()

    if message.strip().lower() == user.predictor.name:
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
            if message.strip().lower() == user.predictor.name:
                if len(user.sessions) == 0 or user.sessions[0].complete is True:
                    new_session(user, message, response)
                elif user.sessions[0].complete is False:
                    if session_expired(user.sessions[0].created_at, user.sessions[0].interval.duration):
                        user.sessions[0].complete = True
                        new_session(user, message, response)
                    else:
                        response.message('We were expecting outcome: {}'.format(user.outcome.name))
            elif message.strip().lower() == user.outcome.name:
                if len(user.sessions) == 0 or user.sessions[0].complete is True:
                    response.message('We were expecting predictor: {}'.format(user.predictor.name))
                elif user.sessions[0].complete is False:
                    if session_expired(user.sessions[0].created_at, user.sessions[0].interval.duration):
                        user.sessions[0].complete = True
                        response.message('We were expecting predictor: {}'.format(user.predictor.name))
                    else:
                        sms_response = Response(
                            session_id=user.sessions[0].id,
                            outcome_id=user.outcome.id,
                            user_id=user.id,
                            message=message,
                            twilio_json="{}"
                        )
                        models.storage.new(sms_response)
                        user.sessions[0].complete = True
                        models.storage.save()
    elif consent is True and name_req is True:
        access_code = binascii.hexlify(os.urandom(8)).decode()
        session['access-code'] = access_code
        user = User()
        user.username = message.strip()
        user.phone_number = phone_number
        user.access_code = access_code
        models.storage.new(user)
        models.storage.save()
        session['user-id'] = user.id
        response.message(
            "Welcome {}! Please go to: {}/register/?access-code={}".format(
                user.username, SITE_URL, access_code
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
