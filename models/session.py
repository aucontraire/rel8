#!/usr/bin/env python3
"""Session module"""
from datetime import datetime
from models.base_model import Base, BaseModel
from models.response import Response
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship


class Session(BaseModel, Base):
    """Session class"""
    __tablename__ = "sessions"
    id = Column(String(60), nullable=False, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    user_id = Column(String(60), ForeignKey('users.id'), nullable=False)
    user = relationship('User', back_populates='sessions')
    responses = relationship('Response', back_populates='session')
    complete = Column(Boolean, default=False)
