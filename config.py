# -*- coding: utf-8 -*-
import secret

SQLALCHEMY_DATABASE_URI = u'mysql+mysqldb://%s@localhost/lebonscrap?use_unicode=1&charset=utf8' \
                          % secret.DB_AUTH
PHOTO_DIR = u"/home/clem/PycharmProjects/lebonscrap/photos/"
