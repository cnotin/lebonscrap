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


user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0'
headers = {'User-Agent': user_agent}


def normalize_ville(ville):
    if u"paris" in ville:
        ville = u"Paris"
    elif u"billancourt" in ville:
        ville = u"Boulogne-Billancourt"
    elif u"issy" in ville:
        ville = u"Issy-les-Moulineaux"
    elif u"neuilly" in ville:
        ville = u"Neuilly-sur-Seine"
    elif u"vanves" in ville:
        ville = u"Vanves"

    return ville


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
    try:
        date = datetime.fromtimestamp(
            time.mktime(time.strptime("2013 " +
                                      date.encode("utf-8"),
                                      u"%Y le %d %B à %H:%M".encode("utf-8"))))
    except AttributeError:
        date = datetime.now()

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
        else:
            surface = None
    except AttributeError:
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

    appart = Appartement(id, titre, loyer, ville, cp, pieces, meuble, surface, description, photos, date, auteur,
                         "leboncoin", appart_url)
    try:
        Session.add(appart)
        Session.commit()
    except IntegrityError:
        print "Got integrity error while trying to add %d %s" % (id, appart)

    time.sleep(1)


def download_annonce_foncia(id):
    print "Download annonce %d" % id
    appart_url = "http://fr.foncia.com/annonces-immobilieres/location/detail.php?bien_id=%d&bd_id=FON" % id

    request = urllib2.Request(
        appart_url, headers=headers)
    response = urllib2.urlopen(request)
    the_page = response.read()
    pool = BeautifulSoup(the_page)

    titre = pool.find("h2").string

    auteur = pool.find("div", {"class": "post-it-bottom-agence-titre"}).a.string.strip()
    date = datetime.now()

    loyer = int(re.sub(r'[^\d-]+', '', pool.find("div", {"class": "foncia_prix_details_loc_texte"}).string[:-10]))

    titre_exploded = titre.split("-")
    cp = int(titre_exploded[-1])

    ville = normalize_ville(titre_exploded[-2].strip().lower())

    desc_tag = pool.find("div", {"class": "foncia_textepub_detail_loc"})
    txt = ""
    for p in desc_tag.find_all("p", recursive=False):
        txt += p.text + "<br/>"
    adresse = desc_tag.div.div.div.p.text
    try:
        etage = desc_tag.div.div.find("p", recursive=False).text
    except AttributeError:
        etage = u"Etage N/A"
    try:
        dispo = desc_tag.div.ul.text.strip()
    except AttributeError:
        dispo = u"Disponibilité N/A"
    description = u"<div><p>%s</p><p>Adresse : %s</p><p>%s</p><p>%s</p></div>" % (
        txt, adresse, etage, dispo)

    params = list(desc_tag.find("span", {"class": "foncia_mini"}).children)[2]
    try:
        pieces = int(re.findall(r"(\d)", params)[0])
    except IndexError:
        pieces = None
    meuble = params.find("meubl") != -1

    surface = int(pool.find("p", {"class": "foncia_surface_loc"}).text[:-6])

    # cette méthode choppe les photos du carrousel
    photos = re.findall(r'(http://photos.fr.foncia.com/.*/640/480/.*)"', the_page)
    for photo in photos:
        photo_jobs.add(download_photo, (photo, appart_url))

    appart = Appartement(id, titre, loyer, ville, cp, pieces, meuble, surface, description, photos, date, auteur,
                         "foncia", appart_url)
    try:
        Session.add(appart)
        Session.commit()
    except IntegrityError:
        print "Got integrity error while trying to add %d %s" % (id, appart)

    time.sleep(1)


def download_annonce_seloger((id, appart_url)):
    print "Download annonce %d" % id

    request = urllib2.Request(appart_url, headers=headers)
    response = urllib2.urlopen(request)
    the_page = response.read()
    pool = BeautifulSoup(the_page)

    titre = pool.find("title").string.replace("Location", "")[:-13]

    auteur = pool.find("div", {"id": "infos_agence"}).h3.string.replace("Informations sur l'agence", "")

    date = unicode(pool.select(".maj_ref span.maj b")[0].string)
    try:
        date = datetime.fromtimestamp(
            time.mktime(time.strptime(date.encode("utf-8"), u"%d / %m / %Y".encode("utf-8"))))
    except (AttributeError, ValueError), e:
        print "Exception --%s--, use current date instead of %s" % (e, date)
        date = datetime.now()

    loyer = int(re.sub(r'[^\d-]+', '', pool.find("b", {"class": "prix_brut"}).text))

    cp = int(re.findall(r"\(([0-9]*)\)", titre)[0])

    ville = normalize_ville(titre.strip().lower())

    txt = pool.find_all("p", {"class": "textdesc"})[0].string
    desc_tag = pool.find("div", {"class": "infos_ann_light"})

    try:
        etage = desc_tag.find_all("li")[2].find_next().text.strip()
    except AttributeError:
        etage = u"N/A"

    misc = ""
    try:
        misc_li = pool.find("ol", {"id": "mentions_ann"}).find_all("li")
        for m in misc_li:
            t = m.text
            if u"Disponible" in t or u"Meublé" in t:
                misc += u"<li>%s</li>" % t
    except AttributeError:
        pass
    if misc != "":
        misc = "<p>Divers :<ul>%s</ul></p>" % misc
    description = u"<div><p>%s</p><p>Etage : %s</p>%s</div>" % (txt, etage, misc)

    try:
        pieces = int(desc_tag.find_all("li")[0].find_next().text.strip())
    except IndexError:
        pieces = None

    try:
        surface = int(desc_tag.find_all("li")[1].find_next().text.strip()[:-4].strip().split(",")[0])
    except (IndexError, ValueError):
        surface = None

    meuble = None

    # cette méthode choppe les photos du carrousel. Avec potentiellement des photos big et small mélangées.
    gallerie = re.findall(r"""(tabGalerie.*?)</script>""", the_page, re.DOTALL)[0]
    photos = re.findall(r"'(http://..visuels.poliris.com/.*?)'", gallerie, re.DOTALL)
    for photo in photos:
        photo_jobs.add(download_photo, (photo, appart_url))

    appart = Appartement(id, titre, loyer, ville, cp, pieces, meuble, surface, description, photos, date, auteur,
                         "seloger", appart_url)
    try:
        Session.add(appart)
        Session.commit()
    except IntegrityError:
        print "Got integrity error while trying to add %d %s" % (id, appart)

    time.sleep(2)


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
    villes = ("Paris%2075007", "Paris%2075008", "Paris%2075009", "Paris%2075015", "Paris%2075016", "Paris%2075017",
              "Boulogne-Billancourt", "Issy-Les-Moulineaux", "Neuilly-sur-Seine%2092200")
    villes_seloger = ("750107", "750108", "750109", "750115", "750116", "750117", "920012", "920040", "920051")

    nouveautes = 0

    print "Début scraping leboncoin"
    id_regexp = re.compile(r"locations/([0-9]*).htm")

    for ville in villes:
        print "Passage à la ville %s" % ville
        for page_num in range(1, 41):
            request = urllib2.Request(
                "http://www.leboncoin.fr/locations/offres/ile_de_france/"
                "?o=%d&mrs=600&mre=1200&ret=1&ret=2&sqs=1&location=%s" % (page_num, ville), headers=headers)
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
                id = int(id_regexp.findall(url)[0])
                if Session.query(Appartement).filter_by(id=id).first():
                    print "Already seen appart %d trouvé à %s" % (id, ville)
                    nb_already_seen += 1
                else:
                    nouveautes += 1
                    print "Ajout job appart %d trouvé à %s" % (id, ville)
                    appart_jobs.add(download_annonce_leboncoin, id)

            if nb_already_seen == nb_annonces:
                break

    print "Fin scraping leboncoin, nouveautés %d" % nouveautes

    print "\nDébut scraping foncia"
    id_regexp = re.compile(r"bien_id=([0-9]*)&")

    for ville in villes:
        print "Passage à la ville %s" % ville
        for page_num in range(1, 41):

            request = urllib2.Request(
                "http://fr.foncia.com/annonces-immobilieres/location/resultat.php?metier=location"
                "&origine_donnees=interne&formRecherche=true&typesDeBien[1]=on&typesDeBien[2]=on"
                "&typesDeBien[5]=on&nbPieces[0]=on&surfaceMin=20&surfaceMax=&localisation=%s"
                "&loyerMin=600&loyerMax=1200&page=%d" % (ville, page_num), headers=headers)
            response = urllib2.urlopen(request)
            the_page = response.read()
            pool = BeautifulSoup(the_page)

            annonces = pool.select("div.foncia_titre_bien a")

            # empty page
            if len(annonces) == 0:
                break

            # quand qqn ajoute une annonce, il se peut que l'on ait déjà vu le première annonce de la page dans
            # la page précédente. Ce n'est donc pas un moyen sûr pour détecter la fin des nouveautés. On vérifie donc
            # plutôt qu'on a déjà vu tous les appart de la page.
            nb_already_seen = 0
            nb_annonces = 0
            for annonce in annonces:
                nb_annonces += 1

                url = annonce["href"]

                id = int(id_regexp.findall(url)[0])
                if Session.query(Appartement).filter_by(id=id).first():
                    print "Already seen appart %d trouvé à %s" % (id, ville)
                    nb_already_seen += 1
                else:
                    nouveautes += 1
                    print "Ajout job appart %d trouvé à %s" % (id, ville)
                    appart_jobs.add(download_annonce_foncia, id)

            if nb_already_seen == nb_annonces:
                break
            
    print "Fin scraping foncia, nouveautés %d" % nouveautes

    print "\nDébut scraping seloger"
    id_regexp = re.compile(r"/([0-9]*).htm")

    for ville in villes_seloger:
        print "Passage à la ville %s" % ville
        for page_num in range(1, 10):

            request = urllib2.Request(
                "http://www.seloger.com/recherche.htm?ci=%s&idqfix=1&idtt=1&idtypebien=1,2&org=engine"
                "&px_loyerbtw=600/1200&surfacebtw=20/NAN&BCLANNpg=%d" % (ville, page_num), headers=headers)
            response = urllib2.urlopen(request)
            the_page = response.read()
            pool = BeautifulSoup(the_page)

            annonces = pool.select("div#results_container div.rech_libinfo a")

            # empty page
            if len(annonces) == 0:
                break

            # quand qqn ajoute une annonce, il se peut que l'on ait déjà vu le première annonce de la page dans
            # la page précédente. Ce n'est donc pas un moyen sûr pour détecter la fin des nouveautés. On vérifie donc
            # plutôt qu'on a déjà vu tous les appart de la page.
            nb_already_seen = 0
            nb_annonces = 0
            for annonce in annonces:
                nb_annonces += 1

                url = annonce["href"].split("?")[0]

                id = int(id_regexp.findall(url)[0])
                if Session.query(Appartement).filter_by(id=id).first():
                    print "Already seen appart %d trouvé à %s" % (id, ville)
                    nb_already_seen += 1
                else:
                    nouveautes += 1
                    print "Ajout job appart %d trouvé à %s" % (id, ville)
                    appart_jobs.add(download_annonce_seloger, (id, url))

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

    appart_jobs = QueueTasks(nb_threads=2)
    photo_jobs = QueueTasks()

    print "Hello @ %s" % datetime.now()
    main()
