#!/usr/bin/python3
"""DBStorage class that sets up SQLAlchemy and connects with database"""
from models.base_model import Base
from models.user import User
import os
from sqlalchemy import (create_engine)
from sqlalchemy.orm import sessionmaker, scoped_session


class DBStorage:
    """
    DBStorage class
    """
    __engine = None
    __session = None

    def __init__(self):
        """
        Initializes database connection
        """
        user_name = os.getenv("REL8_MYSQL_USER")
        pwd = os.getenv("REL8_MYSQL_PWD")
        host = os.getenv("REL8_MYSQL_HOST")
        db = os.getenv("REL8_MYSQL_DB")

        self.__engine = create_engine(
            'mysql+mysqldb://{}:{}@{}/{}'.format(
                user_name, pwd, host, db), pool_pre_ping=True)

        if os.getenv("HBNB_ENV") == 'test':
            Base.metadata.drop_all(bind=self.__engine)

    def all(self, cls=None):
        """
        Retrieves dictionary of objects in database
        Args:
            cls (obj): class of objects to be queried
        Returns:
            dictionary of objects
        """
        objs_dict = {}
        objs = None
        """
        if cls:
            if cls in classes:
                cls = classes[cls]
                objs = self.__session.query(cls).all()
        else:
            objs = self.__session.query(State, City).all()
        for obj in objs:
            key = "{}.{}".format(type(obj).__name__, obj.id)
            objs_dict[key] = obj
        """
        if cls:
            objs = self.__session.query(cls).all()
            for obj in objs:
                objs_dict[obj.phone_number] = obj

        return (objs_dict)

    def new(self, obj):
        """
        Creates a query on current db session depending on class name
        """
        self.__session.add(obj)

    def save(self):
        """
        commit all changes of the current db session
        """
        self.__session.commit()

    def delete(self, obj=None):
        """
        delete from current db session obj if not none
        """
        if obj:
            self.__session.delete(obj)
            self.save()

    def reload(self):
        """
        create all tb in db
        create current db session and is thread safe
        """
        Base.metadata.create_all(self.__engine)
        session_factory = sessionmaker(bind=self.__engine,
                                       expire_on_commit=False)
        Session = scoped_session(session_factory)
        self.__session = Session()
