#!/usr/bin/env python3
"""rel8 Flask app"""
import binascii
import csv
import datetime
from dateutil import relativedelta
from flask import abort, flash, Flask, jsonify, render_template
from flask import redirect, request, session, stream_with_context, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from io import StringIO
import models
from models.interval import Interval
from models.outcome import Outcome
from models.predictor import Predictor
from models.response import Response
from models.session import Session
from models.user import User
import os
import phonenumbers
import pytz
from pytz import timezone
from rel8.forms import RegistrationForm, PasswordForm, LoginForm, VariablesForm
from rel8.utils import get_local_dt
from twilio.rest import Client
from werkzeug.datastructures import Headers
from werkzeug import wrappers


TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')


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
    consent_requested = session.get('consent_requested', False)
    name_requested = session.get('name_requested', False)

    return session, counter, consent, consent_requested, name_requested


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
                user.timezone = form.timezone.data
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
        elif len(session.responses) == 2:
            diff = relativedelta.relativedelta(session.responses[1].updated_at, session.responses[0].updated_at)
            responses.append((session.responses[0], session.responses[1], diff.minutes))

    return render_template('dashboard.html', error=error, user=current_user, responses=responses)


@app.route('/csv')
def csv_download():
    now = datetime.datetime.now()
    filename = "{}.csv".format(get_local_dt(now, human=True, format='%Y-%m-%d_%H.%M.%S'))

    def generate():
        data = StringIO()
        writer = csv.writer(data)

        writer.writerow(('predictor dt', 'predictor', 'outcome dt', 'outcome', 'difference (min)'))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        current_user.sessions.sort(key=lambda session: session.updated_at, reverse=False)
        for session in current_user.sessions:
            session.responses.sort(key=lambda response: response.updated_at, reverse=False)
            if len(session.responses) == 1:
                writer.writerow(
                    (
                        get_local_dt(session.responses[0].updated_at),
                        session.responses[0].message,
                        '',
                        '',
                        ''
                    )
                )
            elif len(session.responses) == 2:
                diff = relativedelta.relativedelta(session.responses[1].updated_at, session.responses[0].updated_at)
                writer.writerow(
                    (
                        get_local_dt(session.responses[0].updated_at),
                        session.responses[0].message,
                        get_local_dt(session.responses[1].updated_at),
                        session.responses[1].message,
                        diff.minutes
                    )
                )

            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    headers = Headers()
    headers.set('Content-Disposition', 'attachment', filename=filename)

    return wrappers.Response(
        stream_with_context(generate()),
        mimetype='text/csv', headers=headers
    )


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
    predictor = ''
    outcome = ''
    duration = ''

    if current_user.predictor:
        predictor = current_user.predictor.name
        outcome = current_user.outcome.name
        duration = current_user.interval.duration

    data = {
        'predictor': predictor,
        'outcome': outcome,
        'duration': duration
    }

    form = VariablesForm(data=data)
    if form.validate_on_submit():
        if current_user.predictor:
            current_user.predictor.name = form.predictor.data.strip().lower()
            current_user.outcome.name = form.outcome.data.strip().lower()
            current_user.interval.duration = form.duration.data
            flash('Variables updated')
        else:
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
            flash('Variables added')

        models.storage.save()

    return render_template('variables.html', form=form, error=error)


def session_expired(created_at, interval):
    delta = datetime.timedelta(hours=interval)
    now = datetime.datetime.utcnow()
    return now > created_at + delta


def new_session(user, message):
    sms_session = Session(
        user_id=user.id,
        interval_id=user.interval.id
    )
    models.storage.new(sms_session)
    models.storage.save()

    sms_response = Response(
        session_id=sms_session.id,
        predictor_id=user.predictor.id,
        user_id=user.id,
        message=message,
        twilio_json="{}"
    )
    models.storage.new(sms_response)
    models.storage.save()


@app.route('/sms', methods=['POST'])
def sms():
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    response_body = None
    session, counter, consent, consent_requested, name_requested = get_session()
    phone_number = request.form['From']
    message = request.form['Body']
    user = find_user_by_phone(phone_number)
    if user:
        if not user.predictor or not user.outcome:
            response_body = "Hi {}. You need to set up your variables first: {}".format(user.username, SITE_URL)
        elif message.strip().lower() != user.predictor.name and message.strip().lower() != user.outcome.name:
            response_body = 'That does not match your variables. Try again.'
        else:
            user.sessions.sort(key=lambda sess: sess.updated_at, reverse=True)
            if message.strip().lower() == user.predictor.name:
                if len(user.sessions) == 0 or user.sessions[0].complete is True:
                    new_session(user, message)
                elif user.sessions[0].complete is False:
                    if session_expired(user.sessions[0].created_at, user.sessions[0].interval.duration):
                        user.sessions[0].complete = True
                        new_session(user, message)
                    else:
                        response_body = 'We were expecting outcome: {}'.format(user.outcome.name)
            elif message.strip().lower() == user.outcome.name:
                if len(user.sessions) == 0 or user.sessions[0].complete is True:
                    response_body = 'We were expecting predictor: {}'.format(user.predictor.name)
                elif user.sessions[0].complete is False:
                    if session_expired(user.sessions[0].created_at, user.sessions[0].interval.duration):
                        user.sessions[0].complete = True
                        response_body = 'We were expecting predictor: {}'.format(user.predictor.name)
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
    elif consent is True and consent_requested is True and name_requested is True:
        access_code = binascii.hexlify(os.urandom(8)).decode()
        session['access-code'] = access_code
        user = User()
        user.username = message.strip()
        user.phone_number = phone_number
        user.access_code = access_code
        models.storage.new(user)
        models.storage.save()
        session['user-id'] = user.id
        response_body = "Welcome {}! Please go to: {}/register/?access-code={}".format(user.username, SITE_URL, access_code)
    elif consent_requested is True and name_requested is False:
        session['name_requested'] = True
        if message.strip().lower() == 'yes':
            session['consent'] = True
            response_body = "What's your name?"
        elif message.strip().lower() == 'no':
            response_body = "Sorry to hear that. Bye."
    else:
        response_body = "Would you like to enroll in rel8? [Yes, No]"
        session['consent_requested'] = True

    message = client.messages.create(
        to=phone_number,
        from_=TWILIO_PHONE_NUMBER,
        body=response_body
    )
    return str(message)


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
