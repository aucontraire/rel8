#!/usr/bin/env python3
"""User module"""
from datetime import datetime
from models.base_model import Base, BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship


class Calendar(BaseModel, Base):
    """Calendar class"""
    __tablename__ = "calendars"
    id = Column(String(60), nullable=False, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    name = Column(String(60), nullable=False)
    user_id = Column(String(60), ForeignKey('users.id'), nullable=False)
    user = relationship('User', back_populates='calendars')
