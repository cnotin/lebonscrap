# coding=utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Entities import  Appartement
import time, locale
from datetime import datetime

locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")

engine = create_engine('mysql+mysqldb://root@localhost/lebonscrap?use_unicode=1', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

print "loop"
for appart in session.query(Appartement).all():
    if not appart.datetime:
        appart.date = "2013 " + appart.date
        appart.datetime = datetime.fromtimestamp(
            time.mktime(time.strptime(appart.date.encode("utf-8"), u"%Y le %d %B à %H:%M".encode("utf-8"))))
        print appart.date
        print repr(appart.datetime)
        session.commit()

