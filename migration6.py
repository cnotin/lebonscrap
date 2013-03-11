# coding=utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

import config


engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

try:
    engine.connect().execute("ALTER TABLE `lebonscrap`.`appartements` ADD COLUMN `sent_email` TINYINT(1);")
    session.commit()
except OperationalError, e:
    print e

engine.connect().execute("UPDATE appartements SET sent_email = 0")
session.commit()
