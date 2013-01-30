# coding=utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Entities import  Appartement
import  locale

locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")

engine = create_engine('mysql+mysqldb://root@localhost/lebonscrap?use_unicode=1', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

print "loop"
for appart in session.query(Appartement).all():
    if not appart.datetime.month == 1:
        appart.datetime = appart.datetime.replace(year=2012)
        print appart.datetime

session.commit()

