#!/usr/bin/env python3
"""Package initializer"""
from models.user import User
import os
from models.engine.db_storage import DBStorage


storage = DBStorage()
classes = {"User": User}
storage.reload()
