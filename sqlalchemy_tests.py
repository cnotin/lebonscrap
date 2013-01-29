# coding=utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Entities import Base, Appartement

engine = create_engine('sqlite:///:memory:', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)


appart1 = Appartement("Appart super", 900, "Paris", 75008, 2, True, 25, "blah blah <br /> suite",
    ["http://193.164.196.50/images/746/746230104797309.jpg", "http://193.164.196.50/images/746/42.jpg"],
    "le 29 janvier à 19:33", "Michel")
session.add(appart1)
session.commit()
