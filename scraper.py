# -*- coding: utf-8 -*-
import os
import re
import datetime
import scraperwiki
import urllib2
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# Set up variables
entity_id = "E5043_KUTCRBO_gov"
url = "http://data.kingston.gov.uk/Kingston_Open_Data/"
errors = 0

# Set up functions
def convert_mth_strings ( mth_string ):
    month_numbers = {'JAN': '01', 'FEB': '02', 'MAR':'03', 'APR':'04', 'MAY':'05', 'JUN':'06', 'JUL':'07', 'AUG':'08', 'SEP':'09','OCT':'10','NOV':'11','DEC':'12' }
    #loop through the months in our dictionary
    for k, v in month_numbers.items():
        #then replace the word with the number
        mth_string = mth_string.replace(k, v)
    return mth_string

def validateFilename(filename):
    filenameregex = '^[a-zA-Z0-9]+_[a-zA-Z0-9]+_[a-zA-Z0-9]+_[0-9][0-9][0-9][0-9]_[0-9][0-9]$'
    dateregex = '[0-9][0-9][0-9][0-9]_[0-9][0-9]'
    validName = (re.search(filenameregex, filename) != None)
    found = re.search(dateregex, filename)
    if not found:
        return False
    date = found.group(0)
    year, month = int(date[:4]), int(date[5:7])
    now = datetime.now()
    validYear = (2000 <= year <= now.year)
    validMonth = (1 <= month <= 12)
    if all([validName, validYear, validMonth]):
        return True

def validateURL(url):
    try:
        r = requests.get(url, allow_redirects=True)
        return r.status_code == 200
    except:
        raise

def validateFiletype(url):
    try:
        r = requests.head(url, allow_redirects=True)
        sourceFilename = r.headers.get('Content-Disposition')
        if sourceFilename:
            ext = os.path.splitext(sourceFilename)[1].replace('"', '').replace(';', '').replace(' ', '')
        else:
            ext = os.path.splitext(url)[1]
        if ext in ['.csv', '.xls', '.xlsx']:
            return True
    except:
        raise


# pull down the content from the webpage
html = urllib2.urlopen(url)
soup = BeautifulSoup(html)

# find all entries with the required class
text_link = soup.find('h4', text=re.compile(u'Items of spend over £500'))

links = text_link.find_all_next('a', href=True)

for link in links:
    url = link['href']
    if 'https://drive.google.com/file/d/' in url:
        title = link.contents[0]
        # create the right strings for the new filename
        csvYr = title.split(' ')[-1]
        csvMth = title.split(' ')[-2][:3]
        csvMth = csvMth.upper()
        csvMth = convert_mth_strings(csvMth);
        filename = entity_id + "_" + csvYr + "_" + csvMth
        todays_date = str(datetime.now())

        fileUrl = url.strip()
        if not validateFilename(filename):
            print filename, "*Error: Invalid filename*"
            errors += 1
            continue
        if not validateURL(fileUrl):
            print filename, "*Error: Invalid URL*"
            print fileUrl
            errors += 1
            continue
        # Commenting out the file type test because the CMS uses a crumby dynamic url which doesn't link to a file, so we can't test for file type
        # if not validateFiletype(fileUrl):
            # print filename, "*Error: Invalid filetype*"
            # errors += 1
            # continue

        scraperwiki.sqlite.save(unique_keys=['l'], data={"l": fileUrl, "f": filename, "d": todays_date })
        print filename
if errors > 0:
    raise Exception("%d errors occurred during scrape." % errors)
