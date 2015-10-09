#!/usr/bin/env python

import os, requests, itertools

yearlist = [str(entry) for entry in range(1988, 2016)]
monthlist = [str(entry) for entry in range(1, 13)]
daylist = [str(entry) for entry in range(1, 32)]
urlbase = 'http://www.publications.parliament.uk/pa/cm%s/cmhansrd/cm%s/debtext/%s-%s.htm'

def create_url(years, date, number):
    url = urlbase % (years, date, date, number)
    return url

def increment_pagenum(pagenum):
    return n_digit(str(int(pagenum) + 1), 4)

def n_digit(numstr, n):
    length = n - len(numstr)
    result = ''.join([str(0)]*length) + numstr
    return result

def generate_datelist():
    datelist = []
    for year, month, day in itertools.product(yearlist, monthlist, daylist):
        years = year + str(int(year) + 1)[-2:]
        longdate = year[-2:] + n_digit(month, 2) + n_digit(day, 2)
        if longdate[0] == '0':
            shortdate = longdate[1:]
        else:
            shortdate = longdate
        datelist.append((years, longdate, shortdate))
    return datelist

def download_urls():
    filebase = '/mnt/ssd0/ukhansard/pages/%s'
    datelist = generate_datelist()
    urlfilepath = '/mnt/ssd0/ukhansard/pages/urls.txt'
    with open(urlfilepath, 'w') as g:
        for years, longdate, shortdate in datelist:
            pagenum = '0001'
            while True:
                filesuffix = longdate + '-' + pagenum
                filename = filebase % filesuffix
                url = urlbase % (years, longdate, shortdate, pagenum)
                g.write(url + '\n')
                r = requests.get(url)
                if r.status_code == 404:
                    break
                with open(filename, 'w') as f:
                    f.write(r.text.encode('utf-8'))
                pagenum = increment_pagenum(pagenum)

download_urls()
