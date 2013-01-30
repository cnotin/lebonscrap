# coding=utf-8

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import time, locale
from datetime import datetime

Base = declarative_base()
locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")

class Appartement(Base):
    __tablename__ = 'appartements'

    id = Column(Integer, primary_key=True)
    titre = Column(String(100))
    loyer = Column(Integer)
    ville = Column(String(50))
    cp = Column(Integer)
    pieces = Column(Integer)
    meuble = Column(Boolean)
    surface = Column(Integer)
    description = Column(String(5000))
    photos = relationship("Photo", order_by="Photo.id", backref="appartements")
    date = Column(DateTime)
    auteur = Column(String(100))

    def __init__(self, id, titre, loyer, ville, cp, pieces, meuble, surface, description, photos, date, auteur):
        self.id = id
        self.titre = unicode(titre)
        self.loyer = loyer
        self.ville = unicode(ville)
        self.cp = cp
        self.pieces = pieces
        self.meuble = meuble
        self.surface = surface
        self.description = unicode(description)

        for photo in photos:
            self.photos.append(Photo(photo))

        self.date = datetime.fromtimestamp(
            time.mktime(time.strptime("2013 " + date.encode("utf-8"), u"%Y le %d %B à %H:%M".encode("utf-8"))))
        self.auteur = unicode(auteur)

    def __repr__(self):
        return u"<Appartement %r>" % self.titre


class Photo(Base):
    __tablename__ = 'photos'

    id = Column(Integer, primary_key=True)
    file = Column(String(40), nullable=False)
    appartement_id = Column(Integer, ForeignKey('appartements.id'))

    appartement = relationship("Appartement", backref=backref('appartements', order_by=id))

    def __init__(self, file):
        self.file = file.split('/')[-1]


    def __repr__(self):
        return "<Photo('%s')>" % self.file
