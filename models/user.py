#!/usr/bin/env python3
"""User module"""
from datetime import datetime
from models.base_model import Base, BaseModel
from os import getenv
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import uuid


class User(BaseModel, Base):
    """User class"""
    __tablename__ = "users"
    id = Column(String(60), nullable=False, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    username = Column(String(60), nullable=False)
    access_code = Column(String(60), nullable=False)
    phone_number = Column(String(60), nullable=False)
