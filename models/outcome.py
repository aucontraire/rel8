#!/usr/bin/env python3
"""Outcome module"""
from datetime import datetime
from models.base_model import Base, BaseModel
from models.response import Response
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship


class Outcome(BaseModel, Base):
    """Outcome class"""
    __tablename__ = "outcomes"
    id = Column(String(60), nullable=False, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    name = Column(String(60), nullable=False)
    user_id = Column(String(60), ForeignKey('users.id'), nullable=False)
    user = relationship('User', back_populates='outcome')
    responses = relationship('Response', back_populates='outcome')
