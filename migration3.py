# coding=utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
from sqlalchemy.exc import OperationalError

engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

try:
    engine.connect().execute("ALTER TABLE appartements ADD COLUMN source ENUM('leboncoin', 'foncia')")
    session.commit()
except OperationalError, e:
    print e

engine.connect().execute("UPDATE appartements SET source = 'leboncoin'")
session.commit()
