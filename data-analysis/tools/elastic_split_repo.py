#!/usr/bin/env python3
# -*- coding: utf-8 -*-

## Copyright (C) 2016 Bitergia
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
## Authors:
##   Jesus M. Gonzalez-Barahona <jgb@bitergia.com>
##

import argparse
import json
import logging
from pprint import pprint
import urllib3

import elasticsearch
import elasticsearch.helpers

from xlrd import open_workbook

description = """Split commits in an enriched index according to directory.

Reads a git raw index to find out which files are touched by a commit.
Given the files touched, and according to a list of included / excluded
directories, annotate an enriched index with the right project.

Example:
    elastic_split_repo --es_raw http://elasctic.instance.xxx \
    --index_raw git_raw --es_enriched http://elasctic.instance2.xxx \\
    --index_enriched git

"""

# Disable warning about not verifying certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def parse_args ():

    parser = argparse.ArgumentParser(description = description)
    parser.add_argument("-l", "--logging", type=str, choices=["info", "debug"],
                        help = "Logging level for output")
    parser.add_argument("--logfile", type=str,
                            help = "Log file")
    parser.add_argument("--es_raw", type=str, required=True,
                        help = "ElasticSearch url for raw index")
    parser.add_argument("--index_raw", type=str,
                        help = "Raw index")
    parser.add_argument("--es_enriched", type=str, required=True,
                        help = "ElasticSearch url for enriched index")
    parser.add_argument("--index_enriched", type=str,
                        help = "Enriched index")
    parser.add_argument("--verify_certs", dest="verify_certs",
                        action="store_true",
                        help = "Verify ssl certificates")
    parser.add_argument("--no_verify_certs", dest="verify_certs",
                        action="store_false",
                        help = "Do not verify ssl certificates")
    parser.add_argument("--scroll_period", default=u'5m',
                        help = "Period to maintain the scroll object in ES")
    parser.add_argument("--max_chunk", default=104857600, type=int,
                        help = "Max chunk size for data upload (default: 100MB)")
    parser.set_defaults(verify_certs=True)

    args = parser.parse_args()
    return args

class Index():
    """Class to interact with an ElasticSearch index.

    This class provides the means for reading from it, and writing to it.

    """

    def __init__(self, instance, index,
                scroll_period, max_chunk, verify_certs=True):
        """Constructor for ElasticSearch indexes.

        change_ops is a dictionary which encodes the change operation
        to perform on the index. It includes several fields:
          - index: the index name
          - to_check: the fields to check in the index
          - to_change: the fields to change in the index

        :param      str instance: url of the ElasticSearch instance
        :param         str index: index in ElasticSearch
        :param scroll_period:     period for scroll object (eg: u'5m')
        :param max_chunk:         max chunk size for bulk upload (bytes)
        :param bool verify_certs: don't verify SSL certificate

        """

        self.instance = instance
        self.index = index
        self.scroll_period = scroll_period
        self.max_chunk = max_chunk
        logging.debug("ElasticSearch instance: " + self.instance)
        try:
            self.es = elasticsearch.Elasticsearch([self.instance],
                                                verify_certs=verify_certs)
        except elasticsearch.exceptions.ImproperlyConfigured as exception:
            if exception.args[0].startswith("Root certificates are missing"):
                print("Error validating SSL certificate for {}.".format(self.instance))
                print("Use --no_verify_certs to avoid validation.")
                exit()
            else:
                raise

class RawIndex(Index):

    def get_reader(self):
        """Generator to get the items from the raw index.

        """

        fields=['ocean-unique-id','data.files']
        # _source parameter to get only the fields we need
        reader = elasticsearch.helpers.scan(client=self.es,
                                index=self.index,
                                scroll=self.scroll_period,
                                request_timeout=30,
                                _source=fields)
        return reader

    def classify(self):
        """Read from the index, classifying (generator).

        :return: Python generator returning classified items

        """

        self.retrieved = 0
        for item in self.get_reader():
            self.retrieved += 1
            files = [d['file'] for d in
                item['_source']['data']['files']]
            num_in_dirs = 0
            for file in files:
                if file.startswith(('browser','toolkit','chrome')):
                    num_in_dirs += 1
            if num_in_dirs == 0:
                project = 'Gecko'
            elif num_in_dirs == len(files):
                project = 'Firefox'
            else:
                if num_in_dirs <= len(files) // 2:
                    project = 'Gecko'
                else:
                    project = 'Firefox'
            # print(project, len(files), num_in_dirs)
            # pprint(item)
            yield (item['_source']['ocean-unique-id'], project)
        print()
        print("Items retrieved:", self.retrieved)

class EnrichedIndex(Index):

    def update(self, items):
        """Generator which updates project field in items.

        :param items: generator producing items to wrap

        """

        self.updated = 0
        for item in items:
#            pprint(item)
            (id, project) = item
            logging.info("Id to update: " + id)
            if project == 'Firefox':
                to_write = {
                    '_op_type': 'update',
                    '_index': self.index,
                    '_type': 'items',
                    '_id': id,
                    'doc': {'project': project}
                    }
                logging.debug("Actions: {}".format(to_write))
                self.updated += 1
                yield to_write
            if (self.updated % 1000) == 0:
                print("Items to update: {}".format(self.updated),
                        end='\r')
        print()

    def write(self, items):
        """Write project field in items to ElasticSearch index.

        :param items:    generator with items to write (_id, project)
        """

        actions = self.update(items)
        result = elasticsearch.helpers.bulk(self.es, actions,
            max_chunk_bytes=self.max_chunk,
            raise_on_error=True,
            stats_only=True)
        print("Bulk result (succesful / errors): ", result)
        print("Items updated:", self.updated)

def main():
    args = parse_args()
    if args.logging:
        log_format = '%(levelname)s:%(message)s'
        if args.logging == "info":
            level = logging.INFO
        elif args.logging == "debug":
            level = logging.DEBUG
        if args.logfile:
            logging.basicConfig(format=log_format, level=level,
                                filename = args.logfile, filemode = "w")
        else:
            logging.basicConfig(format=log_format, level=level)

    index_args = {'scroll_period': args.scroll_period,
                'max_chunk': args.max_chunk,
                'verify_certs': args.verify_certs}

    index_raw = RawIndex(instance=args.es_raw,
                        index=args.index_raw,
                        **index_args)
    index_enriched = EnrichedIndex(instance=args.es_enriched,
                                index=args.index_enriched,
                                **index_args)
    index_enriched.write(index_raw.classify())
#    for item in index_raw.classify():
#        print(item)

if __name__ == "__main__":
    main()
