#!/usr/bin/env python3
"""ReL8 Flask app"""
import binascii
from flask import abort, flash, Flask, jsonify, render_template
from flask import redirect, request, session, url_for
from flask_bcrypt import Bcrypt
import models
from models.user import User
import os
import phonenumbers
from rel8.forms import RegistrationForm, PasswordForm
from twilio.twiml.messaging_response import MessagingResponse


TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

app = Flask(__name__)
app.url_map.strict_slashes = False
app.secret_key = os.getenv('SECRET_KEY')

bcrypt = Bcrypt(app)

SITE_URL = os.getenv('SITE_URL')


def get_session():
    counter = session.get('counter', 0)
    counter += 1
    session['counter'] = counter
    consent = session.get('consent', False)
    name_req = session.get('name_req', False)

    return session, counter, consent, name_req


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        print('validated register!')
        session['logged_in'] = True
        return redirect(url_for('password'))
    else:
        print('not validated')
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    access_code = request.form['access-code']
    phone_number = phonenumbers.parse(request.form['phone-number'], "US")
    phone_number_formatted = phonenumbers.format_number(
        phone_number, phonenumbers.PhoneNumberFormat.E164)

    user = models.storage.get(User, session['user-id'])
    if not user:
        error = 'No account'
    elif user and user.access_code == access_code:
        session['logged_in'] = True
        session['phone-number'] = phone_number_formatted
        flash('Successfully logged in')
        return render_template('password.html')
    else:
        error = 'Wrong access code'
    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    session['logged_in'] = False
    return index()


@app.route('/password', methods=['GET', 'POST'])
def password(user=None):
    error = None
    form = PasswordForm()
    user = models.storage.get(User, session['user-id'])
    if request.method == 'POST':
        print('errors:', form.errors)
        if form.validate_on_submit():
            print('validated password submission')
            pw_raw = request.form['password']
            user.password = bcrypt.generate_password_hash(pw_raw).decode('utf-8')
            user.save()
            flash('Updated password')
        else:
            print('password submission not valid')
            error = 'Error in submission'

    return render_template('password.html', form=form, error=error)


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
