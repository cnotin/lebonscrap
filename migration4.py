# coding=utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from Entities import Appartement

import config


engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

try:
    engine.connect().execute("ALTER TABLE `lebonscrap`.`appartements` ADD COLUMN `url` VARCHAR(200);")
    session.commit()
except OperationalError, e:
    print e

for appart in session.query(Appartement).all():
    if appart.source == "leboncoin":
        appart.url = "http://www.leboncoin.fr/locations/%d.htm" % appart.id
    elif appart.source == "foncia":
        appart.url = "http://fr.foncia.com/annonces-immobilieres/location/detail.php?bien_id=%d&bd_id=FON" % appart.id
session.commit()
