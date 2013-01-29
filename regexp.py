import re

urls = ["http://www.leboncoin.fr/locations/426547326.htm?ca=12_s",
        "http://www.leboncoin.fr/locations/1.htm?ca=12_s",
        "http://www.leboncoin.fr/locations/b.htm?ca=12_s",
        "http://www.leboncoin.fr/locations/b45.htm?ca=12_s",
        "http://www.leboncoin.fr/locations/45b.htm?ca=12_s"]

id_regexp = re.compile(r"locations/([0-9]*).htm")

for url in urls:
    result = id_regexp.findall(url)
    print result
