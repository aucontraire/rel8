#!/usr/bin/env python3
from flask_wtf import FlaskForm
from wtforms import IntegerField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, NumberRange


class RegistrationForm(FlaskForm):
    phone_number = StringField('Phone number', validators=[
        DataRequired(), Length(min=7, max=20)])
    access_code = StringField('Access code', validators=[
        DataRequired(), Length(min=16, max=16)])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=8, max=20)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), Length(min=8, max=20), EqualTo('password')])
    timezone = SelectField('Timezone', validators=[DataRequired()], choices=[
        ('US/Central', 'Central'),
        ('US/Eastern', 'Eastern'),
        ('US/Mountain', 'Mountain'),
        ('US/Pacific', 'Pacific')
        ]
    )
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


class VariablesForm(FlaskForm):
    predictor = StringField('Predictor', validators=[
        DataRequired(), Length(min=2, max=20)])
    outcome = StringField('Outcome', validators=[
        DataRequired(), Length(min=2, max=20)])
    duration = IntegerField('Duration', validators=[
        DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Submit')
