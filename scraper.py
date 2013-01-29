import urllib2
from bs4 import BeautifulSoup
import re
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
    print "managing id " + id
    time.sleep(5)


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
    print id + " = " + annonce["title"] + " - " + url
    jobs.add(download_annonce, id)
    time.sleep(1)

