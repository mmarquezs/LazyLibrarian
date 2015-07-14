#!/usr/bin/env python

"""A short and sweet script to download books from libgen.in

A short and sweet script to download books from libgen.in."""

import re
import sys
import copy
import math
import urllib2
import argparse
import tabulate
import itertools
import multiprocessing

import json

from bs4 import BeautifulSoup

mirrors = ['libgen.in', 'libgen.org', 'gen.lib.rus.ec']

searchurl = 'http://'+mirrors[2]+'/search.php?&req=%s&view=simple&column=def&sort=title&sortmode=ASC&page=%d'
downloadurl = 'http://'+mirrors[2]+'/get.php?md5='

# make it do parallel multipart download
# http://stackoverflow.com/questions/1798879/download-file-using-partial-download-http

# def _number_of_result_pages(numberofbooks, resultsperpage):
#     return int(math.ceil(numberofbooks / float(resultsperpage)))

# def _next_page(term, numberofbooks):
#     return ((searchurl % (term, n)) for n in range(2, _number_of_result_pages(numberofbooks, 25) + 1))

# def _range(start, stop, step):
#     return [(n, min(n+step, stop)) for n in range(start, stop, step)]

# def _parts(request, ranges):
#     return ((request % (a,b)) for a, b in ranges)

def search(term):
    """
    Yield result pages for a given search term.

    :param term: the search term as a str
    :returns: BeautifulSoup4 object representing a result page
    """
    if len(term) < 4:
        raise ValueError('Your search term must be at least 4 characters long.')
    firstpage = BeautifulSoup(urllib2.urlopen(searchurl % (term, 1)),"lxml")
    nbooksforpage = 25          # By default it shows 25 books per page.
    results={}# Results
    results["books"]=[]
    TableBooks= firstpage.find("table",attrs={"class":"c","rules":"rows","width":"100%","align":"center","cellpadding":"1","cellspacing":"1"}).find_all("tr",recursive=False)
    for x in range(1,nbooksforpage+1):
        row=TableBooks[x].find_all("td",recursive=False)
        authorslist=row[1].find_all("a",recursive=False)
        authors=[]
        for y in range(0,len(authorslist)):
            if authorslist[y].string!=None:
                authors+=[authorslist[y].text+" "]
        title=row[2].find("a",recursive=False).text
        publisher=row[3].text
        year=row[4].text
        language=row[6].text
        size=row[7].text
        extension=row[8].text
        url=row[9].find("a")["href"]
        # books+=[{TableBooks[x]
        book={"authors":authors,"title":title,"publisher":publisher,"year":year,"lang":language,"size":size,"ext":extension,"url":url}
        results["books"]+=[book]

        # print authors,title,publisher,year,language,size,extension,url+"\n"
    print json.dumps(results, sort_keys=True,indent=4, separators=(',', ': '))
    numberofbooks = int(re.search('\d+', firstpage.find(text=re.compile('^\d+ books found'))).group())
    print(('%d books found' % numberofbooks))
    # for page in _next_page(term, numberofbooks):
    #     print BeautifulSoup(urllib2.urlopen(page))

def extract(page):
    """Extract all the books info in a given result page.

    :param page: result page as an BeautifulSoup4 object
    :returns: list of books as a list of dicts
    """
    # data.find_all(href=re.compile("book/index.php\?md5="))
    # for i, data in enumerate():
    # book['id'] = i
    # book['author'] = None
    # book['title'] = None
    # book['publisher'] = None
    # book['year'] = None
    # book['pages'] = None
    # book['lang'] = None
    # book['size'] = None
    # book['extension'] = None
    # book['hash'] = None
    pass

def select(books):
    """
    Print the books info on a single search result page
    and allows the user to choose one to download.

    :param books: list of books
    :returns: a book as a dict or None if not found
    """
    headers = ['ID', 'Author(s)', 'Title', 'Publisher', 'Year', 'Pages', 'Language', 'Size', 'Extension']
    print(tabulate.tabulate([b.values() for b in books], headers))
    # for book in books:
    #    print('ID:{0} {1} - {2} {3}'.format(book['id'], book['author'], book['title'], book['publisher'])),
    #    print('{0} {1} {2} {3} {4}'.format(book['year'], book['pages'], book['lang'], book['size'], book['extension']))
    while True:
        try:
            choice = int(raw_input('Choose book: '))
            if choice <= 0 or choice > 25:
                raise ValueError
        except ValueError: print('Invalid choice. Try again.'); continue
        except (KeyboardInterrupt, EOFError): print(''); sys.exit(0)
        break
    book = next((b for b in books if b['id'] == choice), None)
    if not book:
        print('No book with this ID.')
        sys.exit(1)
    return book

def download(book):
    """
    Download a book from libgen.in to the current directory.

    :param book: md5 hash of a book
    """
    blocksize = 1024 # in bytes
    filename = book['title'] + '.' + book['extension']
    bookurl = downloadurl + book['hash']
    filesize = int(urllib2.urlopen(bookurl).info().getheaders("Content-Length")[0]) # in bytes
    req = urllib2.Request(bookurl)
    parts = _range(0, filesize, blocksize)
    req = urllib2.Request(downloadurl + book['hash'])
    requests = list(itertools.repeat(req, len(parts))) # make len(parts) request copies
    reqs = []
    for r, rng in itertools.izip(requests, parts):
        reqs.append(r.add_header('Range', 'bytes={0}-{1}'.format(rng[0], rng[1])))
    for r in reqs: print(r.headers)
    return
    #requests = [r.add_header('Range', 'bytes={0}-{1}'.format(rng[0], rng[1])) for r, rng in itertools.izip(requests, parts)] # change headers

    def _download_and_save(req):
        with open(filename, 'wb') as f:
            f.seek(byte)
            f.write(req.get_data())

    p = multiprocessing.Pool(processes=3)
    parts = p.map(_download_and_save, requests)

    # filename = re.search('filename=\"(.+)\"', r.info()['Content-Disposition']).group(1)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Read more, kids.')
    parser.add_argument('-s', '--search', dest='search', required=True, help='search term')
    parser.add_argument('-y', '--year', dest='year', type=int, help='year of publication')
    parser.add_argument('-t', '--type', dest='extension', default='pdf', help='file extension')
    args = parser.parse_args()
    #print type(args)
    search(args.search)
    """
    for result_page in search(args.search):
        selected = select(extract(result_page))
        if selected:
            download(selected['hash']
    """

    # download("6738829E0C619C853DFE3507C80BCE98")

    # 'Downloaded X MB in Y seconds.'
