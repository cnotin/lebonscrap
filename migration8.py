# coding=utf-8

import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Entities import Appartement
import config


engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

for appart in session.query(Appartement).filter_by(source="pap"):
    print appart

    surface = None
    surface_tmp = re.search(u"(\d+)\xa0m", appart.titre)
    if surface_tmp:
        surface = int(surface_tmp.group(1))
    else:
        surface_tmp = re.search(u"(\d+)\xa0m", appart.description)
        if surface_tmp:
            surface = int(surface_tmp.group(1))

    pieces = None
    pieces_tmp = re.search(u"(\d+).pi.ce", appart.titre, re.IGNORECASE)
    if pieces_tmp:
        pieces = int(pieces_tmp.group(1))
    else:
        pieces_tmp = re.search(u"(\d+).pi.ce", appart.description, re.IGNORECASE)
        if pieces_tmp:
            pieces = int(pieces_tmp.group(1))
        else:
            if re.search("studio", appart.titre, re.IGNORECASE):
                pieces = 1

    if re.search("meubl", appart.titre, re.IGNORECASE):
        meuble = True
    else:
        meuble = None

    if surface != appart.surface:
        print "surface before %s, after %s" % (appart.surface, surface)
        appart.surface = surface
    if pieces != appart.pieces:
        print "pieces before %s, after %s" % (appart.pieces, pieces)
        appart.pieces = pieces
    if meuble != appart.meuble:
        print "meuble before %s, after %s" % (appart.meuble, meuble)
        appart.meuble = meuble

    session.commit()
