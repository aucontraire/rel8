#!/usr/bin/env python3
"""User module"""
from datetime import datetime
from flask_login import UserMixin
from models.base_model import Base, BaseModel
from models.interval import Interval
from models.outcome import Outcome
from models.predictor import Predictor
from models.response import Response
from models.session import Session
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship


class User(UserMixin, BaseModel, Base):
    """User class"""
    __tablename__ = "users"
    id = Column(String(60), nullable=False, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    username = Column(String(60), nullable=False)
    access_code = Column(String(60), nullable=False)
    phone_number = Column(String(60), nullable=False)
    password = Column(String(128), nullable=True)
    interval = relationship('Interval', uselist=False, back_populates='user')
    predictor = relationship('Predictor', uselist=False, back_populates='user')
    outcome = relationship('Outcome', uselist=False, back_populates='user')
    sessions = relationship('Session', back_populates='user')
    responses = relationship('Response', back_populates='user')
