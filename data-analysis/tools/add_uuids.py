import configparser
import csv
import pandas as pd

import sortinghat.api
from sortinghat.db.database import Database
from sortinghat.db.model import Identity, UniqueIdentity
from sortinghat.exceptions import NotFoundError

import sys

sys.path.insert(0, '../rc1/')

import util as ut


GITHUB_HANDLE = 'github_handle'
EMAIL = 'email'
BUGZILLA_EMAIL = 'bugzilla_email'
UUID = 'uuid'
FAKE_ID = 'fake_id'

IDENTITIES_CSV_FILE = '../data/identities.csv'
#IDENTITIES_CSV_FILE = '../data/survey-fake.csv'
OUT_FILEPATH = 'output.csv'

def parse_survey(filepath):
    """Parse a Bugzilla CSV bug list.
    The method parses the CSV file and returns an iterator of
    dictionaries. Each one of this, contains the summary of a bug.
    :param raw_csv: CSV string to parse
    :returns: a generator of parsed bugs
    """
    with open(filepath) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            yield row

def read_survey(survey_filepath):
    """Read survey CSV file.
    :param survey_filepath: path to CSV to read
    :returns: a dictionary. Response Ids are keys. each
    dict entry is another dict containing email, github handle
    and bugzilla email.
    """
    survey_dict = {}
    fake_id = 0
    for row in parse_survey(survey_filepath):
        github_handle = row['Please provide us with your GitHub handle']
        github_handle = ut.normalize_github_handle(github_handle)
        email = row['Please provide us with your email']
        bugzilla_email = row['Please provide us with your Bugzilla email']

        survey_dict[fake_id] = {GITHUB_HANDLE: github_handle,
                                EMAIL: email,
                                BUGZILLA_EMAIL: bugzilla_email}
        fake_id += 1

    return survey_dict

def main():
    """ Read survey results and look for uuids.
    Output: csv file with uuids asociated to the tuple
    [response id, email, github handle, bugzilla email]

    Reads DB configuration from '.settings' file with following format:

    [SortingHat]

    db_user=<database_user>
    password=<database_password>
    db_name=<database_name>
    host=<host_name>
    port=<port_number>
    """

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
        query = session.query(Identity)
        query = query.filter((Identity.source == 'github') |
                             (Identity.source == 'bugzillarest') |
                             (Identity.source == 'git') |
                             (Identity.source == 'discourse') |
                             (Identity.source == 'mbox'))
        uidentities = query.order_by(Identity.uuid).all()

        print(len(uidentities), ' entities read from SH')

        print('Creating E-Mails dict...')
        email_dict = {}
        dups = 0
        for identity in uidentities:
            if identity.email is None or identity.email == 'none@none' \
                or identity.email == '' or identity.email == 'unknown' \
                or identity.email in email_blacklist:
                continue
            if identity.email in email_dict:
                if identity.uuid != email_dict[identity.email]:
                    dups += 1

            email_dict[identity.email] = identity.uuid
        print('Done! Entities in emails dict: ', len(email_dict), ' Dups: ', dups)

        print('Searching for GitHub handles in SH...')
        query = session.query(Identity)
        query = query.filter(Identity.source == 'github')
        uidentities = query.order_by(Identity.uuid).all()

        print(len(uidentities), ' entities read from SH')

        print('Creating GitHub dict...')
        github_dict = {}
        dups = 0
        for identity in uidentities:
            if identity.username is None or identity.username == '' \
                or identity.username == 'unknown':
                continue
            if identity.username in github_dict:
                if identity.uuid != github_dict[identity.username]:
                    dups += 1

            github_dict[identity.username] = identity.uuid

        print('Done! Entities in GitHub dict: ', len(github_dict), ' Dups: ', dups)

        print('Searching for Bugzilla emails in SH...')
        query = session.query(Identity)
        query = query.filter(Identity.source == 'bugzillarest')
        uidentities = query.order_by(Identity.uuid).all()

        print(len(uidentities), ' entities read from SH')

        print('Creating Bugzilla E-Mails dict...')
        bugzilla_email_dict = {}
        dups = 0
        for identity in uidentities:
            if identity.email is None or identity.email == 'none@none' \
                or identity.email == '' or identity.email == 'unknown' \
                or identity.email in email_blacklist:
                continue
            if identity.email in bugzilla_email_dict:
                if identity.uuid != bugzilla_email_dict[identity.email]:
                    dups += 1

            bugzilla_email_dict[identity.email] = identity.uuid
        print('Done! Entities in Bugzilla emails dict: ', len(bugzilla_email_dict), ' Dups: ', dups)


    survey_dict = read_survey(IDENTITIES_CSV_FILE)
    print(len(survey_dict), ' entries read from survey')

    # Find UUIDS for survey responses
    matches = {}
    for fake_id, survey_entry in survey_dict.items():
        email = survey_entry[EMAIL]
        handle = survey_entry[GITHUB_HANDLE]
        bugzilla_email = survey_entry[BUGZILLA_EMAIL]
        if fake_id not in matches and email in email_dict:
            matches[fake_id] = survey_entry
            matches[fake_id][UUID] = email_dict[email]
        elif fake_id not in matches and handle in github_dict:
            matches[fake_id] = survey_entry
            matches[fake_id][UUID] = github_dict[handle]
        elif fake_id not in matches and bugzilla_email in bugzilla_email_dict:
            matches[fake_id] = survey_entry
            matches[fake_id][UUID] = bugzilla_email_dict[bugzilla_email]
        else:
            print('Not Found: E-Mail:', survey_entry[EMAIL],
            'Github:', survey_entry[GITHUB_HANDLE],
            'Bugzilla:', survey_entry[BUGZILLA_EMAIL])

    print('Found: ', len(matches))

    # Export results
    print('Writing results...')
    csv_array = []
    for fake_id, entry in matches.items():
        row_dict = entry
        csv_array.append(row_dict)

    fieldnames = [UUID, EMAIL, GITHUB_HANDLE, BUGZILLA_EMAIL]
    with open(OUT_FILEPATH, 'w') as csv_out:
        csvwriter = csv.DictWriter(csv_out, delimiter=',', fieldnames=fieldnames)
        csvwriter.writeheader()
        for row in csv_array:
            csvwriter.writerow(row)

    print('Results wrote to file ', OUT_FILEPATH)

if __name__ == "__main__":
    main()
    print('This is the End.')
