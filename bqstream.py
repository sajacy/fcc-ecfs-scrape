#!/usr/bin/env python

import json
import argparse
import pprint
import sys
from collections import OrderedDict
from google.cloud import bigquery
from google.cloud.bigquery.schema import SchemaField

def flush(buffer, table):
    errors = table.insert_data(buffer)

    if not errors:
        print('Loaded {} rows'.format(len(buffer)))
    else:
        print('Errors:')
        pprint.pprint(errors)

def parse(schema):
    return [SchemaField(field_type=i.get('type').upper(),
                        fields=parse(i.get('fields', ())),
                        mode=i.get('mode','NULLABLE').upper(),
                        name=i.get('name'))
            for i in schema]


def main(dataset, table, batchsize, schema):

    schemafields = parse(json.load(schema))

    print 'Parsed schema:'
    pprint.pprint(schemafields)

    bigquery_client = bigquery.Client()
    dataset = bigquery_client.dataset(dataset)
    if not dataset.exists():
        dataset.create()

    table = dataset.table(table)
    table.schema = schemafields
    if not table.exists():
        table.create()

    buffer = []
    
    print 'Reading from STDIN...'
    for line in sys.stdin:
        obj = json.loads(line, object_pairs_hook=OrderedDict)
        buffer.append(tuple([v for k,v in obj.items()]))
        if len(buffer) >= batchsize:
            flush(buffer, table)
            buffer = []

    if len(buffer) > 0:
        flush(buffer, table)
        buffer = []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Stream STDIN lines as rows for the given schema into BigQuery')
    parser.add_argument('-d', '--dataset', help='Dataset to load')
    parser.add_argument('-t', '--table', help='Table to load')
    parser.add_argument('-b', '--batchsize', type=int, help='batchsize', default=500)
    parser.add_argument('schemafile', help='A JSON-format BiqQuery schema file')
    args = parser.parse_args()

    main(args.dataset, args.table, args.batchsize, open(args.schemafile, 'r'))
