
import certifi
import configparser

import pandas as pd

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

def ESConnection():

    parser = configparser.ConfigParser()
    parser.read('.settings')

    section = parser['ElasticSearch']
    user = section['user']
    password = section['password']
    host = section['host']
    port = section['port']
    path = section['path']

    connection = "https://" + user + ":" + password + "@" + host + ":" + port + "/" + path

    es_read = Elasticsearch([connection], use_ssl=True, verity_certs=True, ca_cert=certifi.where(), scroll='300m',
	timeout=1000)

    return es_read


def to_df_by_time(result, group_column, time_column, value_column,subgroup_column,
		 group_field, time_field, value_field, subgroup_field):
    """Creates a dataframe based on group and time values
    """
    df = pd.DataFrame(columns=[group_column, time_column, value_column, subgroup_column])

    for time in result.to_dict()['aggregations'][time_field]['buckets']:
        for group in time[group_field]['buckets']:
            for subgroup in group[subgroup_field]['buckets']:
                df.loc[len(df)] = [group['key'], time['key_as_string'], subgroup[value_field]['value'], subgroup['key']]

    return df


def read_projects(filepath):
    xl = pd.ExcelFile(filepath)
    project_groups = {}
    for sheet_name in xl.sheet_names:
        project_groups[sheet_name] = xl.parse(sheet_name)

    # FIX GITHUB REPO NAMES BY ADDING .git TO THE END

    project_groups['Github']['Repo'] = project_groups['Github']['Repo'] + '.git'

    return project_groups

def test():
    es_conn = ESConnection()

    s = Search(using=es_conn, index='git')
    s.execute()

    for item in s.scan():
        print(item)
        break

def test_xls():
    pg = read_projects("data/Contributors and Communities Analysis - Project grouping.xlsx")

    for key in pg.keys():
        print(key)

    print(pg['Github'])

if __name__ == "__main__":
    test()
    test_xls()
