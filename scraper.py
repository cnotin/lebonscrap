# coding=utf-8
import urllib2
from bs4 import BeautifulSoup
import re
from Appartement import Appartement
from queue_tasks import QueueTasks
import time

user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0'
headers = {'User-Agent': user_agent}
id_regexp = re.compile(r"locations/([0-9]*).htm")
jobs = QueueTasks()
jobs.start()

def get_id(url):
    return id_regexp.findall(url)[0]


def download_annonce(id):
    request = urllib2.Request(
        "http://www.leboncoin.fr/locations/" + id + ".htm", None,
        headers)
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
    cp = params.find("th", text=re.compile("Code postal")).parent.td.string
    pieces = params.find("th", text=re.compile(u"Pièces")).parent.td.string
    meuble = (unicode(params.find("th", text=re.compile(u"Meublé")).parent.td.string).strip() == u"Meublé")
    surface = params.find("th", text=re.compile("Surface")).parent.td.contents[0]

    description = unicode(pool.find("div", {"class": "content"}))

    photos = re.findall(r"aImages\[\d\] = \"(http://.*)\";", the_page)

    appart = Appartement(titre, loyer, ville, cp, pieces, meuble, surface, description, photos, date, auteur)
    print titre
    time.sleep(1)


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
    #print id + " = " + annonce["title"] + " - " + url
    jobs.add(download_annonce, id)
    time.sleep(1)

