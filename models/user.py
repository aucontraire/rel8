#!/usr/bin/env python3
"""User module"""
from datetime import datetime
from models.base_model import Base, BaseModel
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship


class User(BaseModel, Base):
    """User class"""
    __tablename__ = "users"
    id = Column(String(60), nullable=False, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    username = Column(String(60), nullable=False)
    access_code = Column(String(60), nullable=False)
    phone_number = Column(String(60), nullable=False)
    password = Column(String(128), nullable=True)
    calendars = relationship('Calendar', back_populates='users')
