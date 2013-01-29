import re

page =  open('appart.htm', 'r').read()


# aImages[0] = "http://193.164.196.50/images/746/746230104797309.jpg";
images = re.findall(r"aImages\[\d\] = \"(http://.*)\";", page)
for image in images:
    print image

