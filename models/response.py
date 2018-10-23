#!/usr/bin/env python3
"""Response module"""
from datetime import datetime
from flask_login import current_user
from models.base_model import Base, BaseModel
from rel8.utils import get_local_dt
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import relationship


class Response(BaseModel, Base):
    """Response class"""
    __tablename__ = "responses"
    id = Column(String(60), nullable=False, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    session_id = Column(String(60), ForeignKey('sessions.id'), nullable=False)
    session = relationship('Session', back_populates='responses')
    predictor_id = Column(String(60), ForeignKey('predictors.id'), nullable=True)
    predictor = relationship('Predictor', back_populates='responses')
    outcome_id = Column(String(60), ForeignKey('outcomes.id'), nullable=True)
    outcome = relationship('Outcome', back_populates='responses')
    user_id = Column(String(60), ForeignKey('users.id'), nullable=False)
    user = relationship('User', back_populates='responses')
    message = Column(String(128), nullable=False)
    twilio_json = Column(JSON, nullable=False, default=[])
    error = Column(Boolean, default=False)

    def human_created_at(self):
        return get_local_dt(self.created_at, human=True)

    def human_updated_at(self):
        return get_local_dt(self.updated_at, human=True)
