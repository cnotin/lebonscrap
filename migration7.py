# coding=utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

import config


engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

try:
    engine.connect().execute(
        "ALTER TABLE `lebonscrap`.`appartements` CHANGE COLUMN `source` `source` ENUM('leboncoin','foncia','seloger','pap');")
    session.commit()
except OperationalError, e:
    print e
