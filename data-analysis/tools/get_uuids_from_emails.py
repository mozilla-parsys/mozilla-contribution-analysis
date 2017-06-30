import certifi
import configparser
import csv

import argparse

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q
from elasticsearch_dsl import Search

import pandas as pd

import sys

import sortinghat.api
from sortinghat.db.database import Database
from sortinghat.db.model import Identity, UniqueIdentity
from sortinghat.exceptions import NotFoundError

sys.path.insert(0, '../rc1/')

import util as ut

description = """Look for UUIDS in SortingHat from a list of emails.

Reads a CSV file containing emails (one per row in a column titled email)
and returns another CSV with emails and their associated UUID (if found).

DB configuration should be stored in '.settings' file with following format:

--------
[SortingHat]

db_user=<database_user>
password=<database_password>
db_name=<database_name>
host=<host_name>
port=<port_number>
--------

Example:
    get_uuids_from_emails --input path_to_input_emails_csv \
    --output path_to_output_csv

"""

EMAIL = 'email'
UUID = 'uuid'

def parse_csv(filepath):
    """Parse a CSV email list.
    The method parses the CSV file and returns an iterator of
    dictionaries.
    :param raw_csv: CSV string to parse
    :returns: a generator of parsed entries
    """
    with open(filepath) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            yield row

def read_emails(emails_filepath):
    """Read emails CSV file.
    :param emails_filepath: path to CSV to read
    :returns: a list of emails from CSV.
    """
    email_list = []
    for row in parse_csv(emails_filepath):
        email = row['email']
        email_list.append(email)

    return email_list

def parse_args():
    """Parse command line args
    """
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("-i", "--input", type=str, required=True,
                        help="path to emails CSV to read")

    parser.add_argument("-o", "--output", type=str, required=True,
                        help="path to output CSV to write UUIDs\
                                associated to emails")

    args = parser.parse_args()
    return args

def main():
    """ Read emails and look for uuids.
    """

    # Parse args
    args = parse_args()

    # Read config file
    parser = configparser.ConfigParser()
    parser.read('.settings')
    section = parser['SortingHat']
    db_user = section['db_user']
    db_password = section['password']
    db_name = section['db_name']
    db_host = section['host']
    db_port = section['port']

    db = Database(db_user, db_password, db_name, db_host, db_port)

    # Get email blacklist from SH
    print('Reading email blacklist from SH')
    blacklist = sortinghat.api.blacklist(db)
    email_blacklist = []
    for identity in blacklist:
        email_blacklist.append(identity.excluded)

    with db.connect() as session:
        print('Searching for E-Mails in SH...')
        query = session.query(UniqueIdentity)
        query = query.filter(Identity.source == 'git',
                             UniqueIdentity.uuid == Identity.uuid)
        uidentities = query.order_by(UniqueIdentity.uuid).all()

        print(len(uidentities), ' entities read from SH')

        print('Creating E-Mails dict...')
        email_dict = {}
        dups = 0
        for uidentity in uidentities:

            for identity in uidentity.identities:

                if identity.email is None or identity.email == 'none@none' \
                    or identity.email == '' or identity.email == 'unknown' \
                    or identity.email in email_blacklist:
                    continue
                if identity.email in email_dict:
                    if identity.uuid != email_dict[identity.email]:
                        dups += 1

                email_dict[identity.email] = identity.uuid

        print('Done! Entities in emails dict: ', len(email_dict), ' Dups: ', dups)

    email_list = read_emails(args.input)
    print(len(email_dict), ' emails read from file')

    # Find UUIDS
    matches = {}
    uuids = set()
    dups_in_csv = 0
    not_found_count = 0
    for email in email_list:

        if email in matches:
            dups_in_csv += 1
            #print("Duplicated email in list:", email)

        elif email in email_dict:
            matches[email] = email_dict[email]
            uuids.add(email_dict[email])

        else:
            #print('Not Found: E-Mail:', email)
            not_found_count += 1

    print('dups in csv:', dups_in_csv)
    print('Not found:', not_found_count)
    print('Found         : ', len(matches))
    print('Found (unique): ', len(uuids))

    # Export results
    print('Writing results...')
    csv_array = []
    for email, uuid in matches.items():
        csv_array.append({'email': email, 'uuid': uuid})

    fieldnames = ['email', 'uuid']
    with open(args.output, 'w') as csv_out:
        csvwriter = csv.DictWriter(csv_out, delimiter=',', fieldnames=fieldnames)
        csvwriter.writeheader()
        for row in csv_array:
            csvwriter.writerow(row)

    print('Results wrote to file ', args.output)



if __name__ == "__main__":
    main()
    print('This is the End.')
