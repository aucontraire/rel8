#!/usr/bin/env python3
"""Interval module"""
from datetime import datetime
from models.base_model import Base, BaseModel
from models.session import Session
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class Interval(BaseModel, Base):
    """Interval class"""
    __tablename__ = "intervals"
    id = Column(String(60), nullable=False, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    duration = Column(Integer, nullable=False)
    user_id = Column(String(60), ForeignKey('users.id'), nullable=False)
    user = relationship('User', back_populates='interval')
    sessions = relationship('Session', back_populates='interval')
