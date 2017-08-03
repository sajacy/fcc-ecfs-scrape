#!/usr/bin/env python

import os
import json
import urllib2
import argparse
import time
import sys
from collections import OrderedDict

APIKEY = os.environ['APIKEY']
TEMPLATEURL = 'https://publicapi.fcc.gov/ecfs/filings?api_key={}&express_comment=1&proceedings.name={}&sort=date_received,ASC&limit={}&offset={}&date_received=%5Bgte%5D{}%5Blte%5D{}'

def fetch(proceeding, limit, paging, offset, datestart, dateend):
    found = paging
    while offset < limit and found == paging:
        url = TEMPLATEURL.format(APIKEY, proceeding, paging, offset, datestart, dateend)
        print >> sys.stderr, "Requesting {}".format(url)
        res = urllib2.urlopen(url)
        found = process(res)
        offset = offset + found
        time.sleep(2)


def process(response):
    payload = json.loads(response.read())
    i = 0
    for f in payload['filings']:
        try:
            # process comments
            if f['submissiontype']['short'] == 'COMMENT':
               print transform(f)
        except Exception as e:
            print >> sys.stderr, e, i, f
            pass
        i = i + 1

    return i


def transform(f):
    ADDRESS_WHITELIST = ['address_line_1', 'address_line_2', 'city', 'state', 'zip4', 'zip_code']

    # The order of fields MUST MATCH the schema JSON
    return json.dumps(OrderedDict([
        ('id', f['id_submission']),
        ('ts', f['date_submission']),
        ('name', ','.join([i.get('name','') for i in f.get('filers')]) if len(f.get('filers',[])) > 0 else ''),
        ('address', {k:v for k,v in f.get('addressentity',{}).items() if k in ADDRESS_WHITELIST}),
        ('email', f.get('contact_email')),
        ('proceeding', f['proceedings'][0]['name']),
        ('comment', f.get('text_data',''))
    ]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape FCC Filings For PII')
    parser.add_argument('proceeding', help='Name of the proceeding e.g. "17-108"')
    parser.add_argument('-l', '--limit', type=int, help='total limit, multiple of --paging', default=1000)
    parser.add_argument('-p', '--paging', type=int, help='results per page', default=100)
    parser.add_argument('-s', '--start', type=int, help='starting offset', default=0)
    parser.add_argument('-ds', '--datestart', help='starting date', default='2017-04-26')
    parser.add_argument('-de', '--dateend', help='ending date', default='2017-08-30')

    args = parser.parse_args()
    fetch(args.proceeding, args.limit, args.paging, args.start, args.datestart, args.dateend)
