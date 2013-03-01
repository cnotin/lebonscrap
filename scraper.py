# coding=utf-8
import urllib2
import re
import time
from datetime import datetime

from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError

from Entities import Appartement
from queue_tasks import QueueTasks
import config


user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0'
headers = {'User-Agent': user_agent}
id_regexp = re.compile(r"locations/([0-9]*).htm")


def get_id(url):
    return int(id_regexp.findall(url)[0])


def download_annonce_leboncoin(id):
    print "Download annonce %d" % id
    appart_url = "http://www.leboncoin.fr/locations/%d.htm" % id

    request = urllib2.Request(
        appart_url, headers=headers)
    response = urllib2.urlopen(request)
    the_page = response.read()
    pool = BeautifulSoup(the_page)

    titre = pool.find("div", {"class": "header_adview"}).find("h2").string

    upload_by = pool.find("div", {"class": "upload_by"})
    auteur = upload_by.find("a").string
    date = unicode(upload_by.contents[2].string).strip()[:-1]

    params = pool.find("div", {"class": "lbcParams"})
    loyer = int(re.sub(r'[^\d-]+', '', params.find("span", {"class": "price"}).string[:-2]))
    ville = params.find("th", text=re.compile("Ville")).parent.td.string
    cp = int(re.sub(r'[^\d-]+', '', params.find("th", text=re.compile("Code postal")).parent.td.string))

    try:
        #piece n'est pas un param obligatoire
        pieces_tag = params.find("th", text=re.compile(r"Pi.ces"))
        if pieces_tag:
            pieces = pieces_tag.parent.td.string
        else:
            pieces = None

        #meublé/non meublé n'est pas un param obligatoire
        meuble_tag = params.find("th", text=re.compile(r"Meubl."))
        if meuble_tag:
            meuble = (unicode(meuble_tag.parent.td.string.strip()) == u"Meublé")
        else:
            meuble = None

        #la surface n'est pas un param obligatoire
        surface_tag = params.find("th", text=re.compile("Surface"))
        if surface_tag:
            surface = int(re.sub(r'[^\d-]+', '', surface_tag.parent.td.contents[0]))
            if surface < 15:
                print "Annulation appart %d car surface %d" % (id, surface)
                return
        else:
            surface = None
    except AttributeError as e:
        print "Scraping problem"

    description = unicode(pool.find("div", {"class": "content"}))

    # cette méthode choppe les photos dans le code du carrousel (dispo quand ya plusieurs photos)
    photos = re.findall(r"aImages\[\d\] = \"(http://.*)\";", the_page)
    if not photos:
        # si 0 ou 1 photo alors pas de carrousel, essayons autrement
        image_tag = pool.find("a", {"id": "image"})
        if image_tag:
            # ya 1 photo
            photos = re.findall(r"(http://.*\.jpg)", image_tag["style"])
    for photo in photos:
        photo_jobs.add(download_photo, (photo, appart_url))

    appart = Appartement(id, titre, loyer, ville, cp, pieces, meuble, surface, description, photos, date, auteur)
    try:
        Session.add(appart)
        Session.commit()
    except IntegrityError:
        print "Got integrity error while trying to add %d %s" % (id, appart)

    time.sleep(1)


def download_photo(params):
    url = params[0]
    origin = params[1]

    print "I download " + url
    request = urllib2.Request(url, headers=headers)
    try:
        response = urllib2.urlopen(request)
        output = open(config.PHOTO_DIR + url.split("/")[-1], 'wb')
        output.write(response.read())
        output.close()
    except urllib2.HTTPError, e:
        print "Photo download problem, got a %d while retrieving %s for appartement %s" % (e.code, url, origin)
    time.sleep(0.5)


def main():
    nouveautes = 0

    for ville in ("Paris%2075007", "Paris%2075008", "Paris%2075009",
                  "Paris%2075015", "Paris%2075016", "Paris%2075017", "Vanves",
                  "Boulogne-Billancourt", "Issy-Les-Moulineaux", "Neuilly-sur-Seine"):
        print "Passage à la ville %s" % ville
        for page_num in range(1, 41):
            request = urllib2.Request(
                "http://www.leboncoin.fr/locations/offres/ile_de_france/?o=%d&mrs=600&mre=1200&ret=1&ret=2&location=%s" % (
                    page_num, ville), headers=headers)
            response = urllib2.urlopen(request)
            the_page = response.read()
            pool = BeautifulSoup(the_page)

            annonces = pool.find("div", {"class": "list-lbc"}).find_all("a")

            # quand qqn ajoute une annonce, il se peut que l'on ait déjà vu le première annonce de la page dans
            # la page précédente. Ce n'est donc pas un moyen sûr pour détecter la fin des nouveautés. On vérifie donc
            # plutôt qu'on a déjà vu tous les appart de la page.
            nb_already_seen = 0
            nb_annonces = 0
            for annonce in annonces:
                nb_annonces += 1

                url = annonce["href"]

                #détecte page où il n'y a pas d'annonce
                if url == u"http://www.leboncoin.fr//.htm?ca=12_s":
                    break
                id = get_id(url)
                if Session.query(Appartement).filter_by(id=id).first():
                    print "Already seen appart %d trouvé à %s" % (id, ville)
                    nb_already_seen += 1
                else:
                    nouveautes += 1
                    print "Ajout job appart %d trouvé à %s" % (id, ville)
                    appart_jobs.add(download_annonce_leboncoin, id)

            if nb_already_seen == nb_annonces:
                break

    print "Fin des villes, sleeping"
    time.sleep(5)
    while not appart_jobs.empty():
        print "Waiting for appart jobs, still %d items" % appart_jobs.size()
        time.sleep(5)
    while not photo_jobs.empty():
        print "Waiting for photos jobs, still %d items" % photo_jobs.size()
        time.sleep(5)
    print "Bye, nouveautes %d\n-----------------------------\n\n\n\n\n\n" % nouveautes


if __name__ == "__main__":
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
    Session = scoped_session(sessionmaker(bind=engine))

    appart_jobs = QueueTasks()
    photo_jobs = QueueTasks(nb_threads=5)

    print "Hello @ %s" % datetime.now()
    main()
