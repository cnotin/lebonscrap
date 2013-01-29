from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Appartement(Base):
    __tablename__ = 'appartements'

    id = Column(Integer, primary_key=True)
    titre = Column(String)
    loyer = Column(Integer)
    ville = Column(String)
    cp = Column(Integer)
    pieces = Column(Integer)
    meuble = Column(Boolean)
    surface = Column(Integer)
    description = Column(String)
    photos = relationship("Photo", order_by="Photo.id", backref="appartements")
    date = Column(String)
    auteur = Column(String)

    def __init__(self, titre, loyer, ville, cp, pieces, meuble, surface, description, photos, date, auteur):
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

        self.date = date#.decode("utf-8")
        self.auteur = unicode(auteur)


class Photo(Base):
    __tablename__ = 'photos'

    id = Column(Integer, primary_key=True)
    file = Column(String, nullable=False)
    appartement_id = Column(Integer, ForeignKey('appartements.id'))

    appartement = relationship("Appartement", backref=backref('appartements', order_by=id))

    def __init__(self, file):
        self.file = file.split('/')[-1]


    def __repr__(self):
        return "<Photo('%s')>" % self.file
