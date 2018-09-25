#!/usr/bin/env python3
"""Package initializer"""
from models.user import User
import os


if os.getenv('REL8_TYPE_STORAGE') == 'db':
    print('using database')
    from models.engine.db_storage import DBStorage
    storage = DBStorage()
else:
    print('using something else')
storage.reload()
