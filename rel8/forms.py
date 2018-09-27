#!/usr/bin/env python3
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class RegistrationForm(FlaskForm):
    phone_number = StringField('Phone number', validators=[
        DataRequired(), Length(min=7, max=20)])
    access_code = StringField('Access code', validators=[
        DataRequired(), Length(min=16, max=16)])
    submit = SubmitField('Register')


class PasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=8, max=20)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), Length(min=8, max=20), EqualTo('password')])
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    phone_number = StringField('Phone number', validators=[
        DataRequired(), Length(min=7, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
