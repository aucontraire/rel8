#!/usr/bin/env python3
"""Predictor module"""
from datetime import datetime
from models.base_model import Base, BaseModel
from models.response import Response
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship


class Predictor(BaseModel, Base):
    """Predictor class"""
    __tablename__ = "predictors"
    id = Column(String(60), nullable=False, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    name = Column(String(60), nullable=False)
    user_id = Column(String(60), ForeignKey('users.id'), nullable=False)
    user = relationship('User', back_populates='predictor')
    calendar_id = Column(String(60), ForeignKey('calendars.id'), nullable=False)
    calendar = relationship('Calendar', back_populates='predictor')
    responses = relationship('Response', back_populates='predictor')
