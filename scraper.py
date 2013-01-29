# coding=utf-8
import urllib2
from bs4 import BeautifulSoup
import re
from Entities import Appartement
from queue_tasks import QueueTasks
import time

user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0'
headers = {'User-Agent': user_agent}
id_regexp = re.compile(r"locations/([0-9]*).htm")

def get_id(url):
    return int(id_regexp.findall(url)[0])


def download_annonce(id):
    appart_url="http://www.leboncoin.fr/locations/%d.htm" % id

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
        pieces_tag=params.find("th", text=re.compile(r"Pi.ces"))
        if pieces_tag:
            pieces = pieces_tag.parent.td.string
        else:
            pieces=-1

        #meublé/non meublé n'est pas un param obligatoire
        meuble_tag = params.find("th", text=re.compile(r"Meubl."))
        if meuble_tag:
            meuble = (unicode(meuble_tag.parent.td.string.strip()) == u"Meublé")
        else:
            meuble = None

        #la surface n'est pas un param obligatoire
        surface_tag = params.find("th", text=re.compile("Surface"))
        if surface_tag:
            surface=int(re.sub(r'[^\d-]+', '', surface_tag.parent.td.contents[0]))
        else:
            surface=-1
    except AttributeError as e:
        print "Scraping problem"

    description = unicode(pool.find("div", {"class": "content"}))

    # cette méthode choppe les photos dans le code du carrousel (dispo quand ya plusieurs photos)
    photos = re.findall(r"aImages\[\d\] = \"(http://.*)\";", the_page)
    if not photos:
        # si 0 ou 1 photo alors pas de carrousel, essayons autrement
        image_tag=pool.find("a", {"id":"image"})
        if image_tag:
            # ya 1 photo
            photos=re.findall(r"(http://.*\.jpg)" ,image_tag["style"])
    for photo in photos:
        photo_jobs.add((photo, appart_url))

    appart = Appartement(titre, loyer, ville, cp, pieces, meuble, surface, description, photos, date, auteur)
    print titre
    time.sleep(1)


def download_photo(params):
    url=params[0]
    origin=params[1]

    print "I download " + url
    request = urllib2.Request(url, headers=headers)
    try:
        response = urllib2.urlopen(request)
        output = open("photos/" + url.split("/")[-1], 'wb')
        output.write(response.read())
        output.close()
    except urllib2.HTTPError, e:
        print "Photo download problem, got a %d while retrieving %s for appartement %s" % (e.code, url,origin)
    time.sleep(1)

appart_jobs = QueueTasks(download_annonce)
photo_jobs = QueueTasks(download_photo)

request = urllib2.Request(
    "http://www.leboncoin.fr/locations/offres/ile_de_france/?o=1&mrs=600&mre=1200&ret=1&ret=2&location=Paris", None,
    headers)
response = urllib2.urlopen(request)
the_page = response.read()
pool = BeautifulSoup(the_page)

annonces = pool.find("div", {"class": "list-lbc"}).find_all("a")

for annonce in annonces:
    url = annonce["href"]
    id = get_id(url)
    appart_jobs.add(id)

time.sleep(5)
while not appart_jobs.empty():
    print "#####  Waiting for appart jobs"
    time.sleep(5)
while not photo_jobs.empty():
    print "#####  Waiting for photos jobs"
    time.sleep(5)
print "Bye"
