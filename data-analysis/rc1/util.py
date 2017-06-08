
import certifi
import csv
import configparser
from datetime import datetime

import pandas as pd

import plotly as plotly
import plotly.figure_factory as ff
import plotly.graph_objs as go

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

GITHUB_HANDLE = 'github_handle'
EMAIL = 'email'
BUGZILLA_EMAIL = 'bugzilla_email'
UUID = 'uuid'

def read_projects(filepath):
    xl = pd.ExcelFile(filepath)
    project_groups = {}
    for sheet_name in xl.sheet_names:
        project_groups[sheet_name] = xl.parse(sheet_name)

    # FIX GITHUB REPO NAMES BY ADDING .git TO THE END

    project_groups['Github']['Repo'] = project_groups['Github']['Repo'] + '.git'

    return project_groups

def normalize_github_handle(handle):
    github_handle = handle.replace('https://github.com/', '')
    github_handle = github_handle.replace('/', '')
    github_handle = github_handle.replace('@', '')

    return github_handle

def ESConnection():

    parser = configparser.ConfigParser()
    parser.read('.settings')

    section = parser['ElasticSearch']
    user = section['user']
    password = section['password']
    host = section['host']
    port = section['port']
    path = section['path']

    connection = "https://" + user + ":" + password + "@" + host + ":" + port \
                + "/" + path

    es_read = Elasticsearch([connection], use_ssl=True, verity_certs=True,
    ca_cert=certifi.where(), scroll='300m', timeout=1000)

    return es_read

def get_projects():
    return read_projects("../data/Contributors and Communities Analysis - Project grouping.xlsx")

def parse_csv(filepath):
    """Parse CSV files.
    The method parses the CSV file and returns an iterator of
    dictionaries. Each one of this, contains the summary of a response.
    :param raw_csv: CSV string to parse
    :returns: a generator of parsed responses
    """
    with open(filepath) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            yield row

def add_general_date_filters(s):
    # 01/01/1998
    initial_ts = '883609200000'
    return s.filter('range', grimoire_creation_date={'gt': initial_ts})

def add_bot_filter(s):
    return s.filter('term', author_bot='false')

def add_merges_filter(s):
    return s.filter('range', files={'gt': 0})

def add_project_filter(s, project_name):

    # Let's load projects from the REVIEWED SPREADSHEET
    projects = get_projects()

    if project_name.lower() != 'all':
        github = projects['Github']
        repos = github[github['Project'] == project_name]['Repo'].tolist()
        #print(repos)
        s = s.filter('terms', repo_name=repos)
    return s

def create_search(es_conn, source):
    """ Standard function to create an ES search for a
    given data source using a given connection
    """

    # Let's load projects from the REVIEWED SPREADSHEET
    projects = get_projects()

    s = Search(using=es_conn, index=source)

    if source == 'git' or source == 'github':
        github = projects['Github']
        repos = github['Repo'].tolist()
        #print (repos)
        s = s.filter('terms', repo_name=repos)

        # Add bot, merges and date filtering.
        s = add_general_date_filters(s)
        s = add_bot_filter(s)
        s = add_merges_filter(s)

    return s

def print_result(result):
    """In case you need to check query response, call this function
    """
    print(result.to_dict()['aggregations'])


############################
# PANDAS RELATED FUNCTIONS #
############################

def load_survey_df(survey_filepath, uuids_filepath):

    # Get UUIDS from correspondences file
    email_uuid = {}
    github_uuid = {}
    bugzilla_uuid = {}
    for row in parse_csv(uuids_filepath):
        row_uuid = row[UUID]
        if row[EMAIL] is not None and row[EMAIL] != '':
            email_uuid[row[EMAIL]] = row_uuid
        if row[GITHUB_HANDLE] is not None and row[GITHUB_HANDLE] != '':
            github_uuid[row[GITHUB_HANDLE]] = row_uuid
        if row[BUGZILLA_EMAIL] is not None and row[BUGZILLA_EMAIL] != '':
            bugzilla_uuid[row[BUGZILLA_EMAIL]] = row_uuid

    # Read survey and add corresponding UUIDs
    survey_df = pd.DataFrame(columns=['uuid', 'active', 'age', 'country', 'gender', 'disability',
                                      'education level', 'language', 'english proficiency',
                                      'coding'])

    for row in parse_csv(survey_filepath):
        github_handle = row['Please provide us with your GitHub handle']
        github_handle = normalize_github_handle(github_handle)
        email = row['Please provide us with your email']
        bugzilla_email = row['Please provide us with your Bugzilla email']

        uuid = None
        if email in email_uuid:
            uuid = email_uuid[email]
        elif github_handle in github_uuid:
            uuid = github_uuid[github_handle]
        elif bugzilla_email in bugzilla_uuid:
            uuid = bugzilla_uuid[bugzilla_email]

        if uuid is not None:
            active = row['Have you contributed to a Mozilla or related project within the past year? ']
            age = row['How old are you? ']
            country = row['In which country are you currently based?']
            gender = row['With which gender do you identify? ']
            disability = row['Do you identify with any of the below statements']
            education_level = row['What is your current level of education?']
            language = row['Which language do you speak most often? ']
            english_prof = row['How would you rate your proficiency in English?']
            coding = row['Coding:Please select all the ways in which you have contributed to Mozilla or related projects in the past year (Select all that apply.)']
            survey_df.loc[len(survey_df)] = [uuid, active, age, country, gender, disability,
                                             education_level, language, english_prof, coding]
        #else:
        #    print('Not found: ', email, github_handle, bugzilla_email)

    return survey_df

def to_simple_df(result, group_field, value_field, group_column, value_column):
    """Create a DataFrame from an ES result with 1 BUCKET and 1 METRIC.
    """
    df = pd.DataFrame()

    df = df.from_dict(result.to_dict()['aggregations'][group_field]['buckets'])
    df = df.drop('doc_count', axis=1)
    df[value_field] = df[value_field].apply(lambda row: row['value'])
    df=df[['key', value_field]]
    df.columns = [group_column, value_column]

    return df

def stack_by(result, group_column, subgroup_column, value_column,
             group_field, subgroup_field, value_field = None):
    """Creates a dataframe based on group and subgroup values.
    If value_field is provided, then a metric is expected, if not,
    use doc_count as value.
    """
    df = pd.DataFrame(columns=[group_column, subgroup_column, value_column])

    for group in result.to_dict()['aggregations'][group_field]['buckets']:
        for subgroup in group[subgroup_field]['buckets']:
            group_key = group['key']
            if 'key_as_string' in subgroup:
                subgroup_key = subgroup['key_as_string']
            else:
                subgroup_key = subgroup['key']

            if value_field is not None:
                value = subgroup[value_field]['value']
            else:
                value = subgroup['doc_count']

            df.loc[len(df)] = [group_key,
                               subgroup_key,
                               value]

    return df

def stack_by_cusum(result, group_column, subgroup_column, value_column,
                   group_field, subgroup_field,
                   staff_org_names, staff_org,
                   metric_field=None):

    df = pd.DataFrame(columns=[group_column, subgroup_column, value_column])

    for group in result.to_dict()['aggregations'][group_field]['buckets']:
        group_key = group['key']
        if group_key in staff_org_names:
            group_key = staff_org
        else:
            group_key = 'Non-Employees'

        print(group['key'], '->', group_key)

        for subgroup in group[subgroup_field]['buckets']:

            if 'key_as_string' in subgroup:
                subgroup_key = subgroup['key_as_string']
            else:
                subgroup_key = subgroup['key']

            if metric_field is not None:
                value = subgroup[metric_field]['value']
            else:
                value = subgroup['doc_count']

            subgroup_key_list = df[df[group_column] == group_key][subgroup_column]\
                        .tolist()
            if group_key in df[group_column].unique() \
                and subgroup_key in subgroup_key_list:

                df.loc[(df[group_column] == group_key) \
                        & (df[subgroup_column] == subgroup_key),
                       value_column] += value

            else:
                df.loc[len(df)] = [group_key, subgroup_key, value]

    return df

def get_authors_df(result, author_bucket_field):

    # Get a dataframe with each author and their first commit
    buckets_result = result['aggregations'][author_bucket_field]['buckets']

    buckets = []
    for bucket_author in buckets_result:
        author = bucket_author['key']

        first = bucket_author['first']['hits']['hits'][0]
        first_commit = first['sort'][0]/1000
        last_commit = bucket_author['last_commit']['value']/1000
        org_name = first['_source']['author_org_name']
        project = first['_source']['project']
        #uuid = first['_source']['author_uuid']
        buckets.append({
                'first_commit': datetime.utcfromtimestamp(first_commit),
                'last_commit': datetime.utcfromtimestamp(last_commit),
                'author': author,
                #'uuid': uuid,
                'org': org_name,
                'project': project
        })
    authors_df = pd.DataFrame.from_records(buckets)
    authors_df.sort_values(by='first_commit', ascending=False,
                            inplace=True)
    return authors_df

def get_active_authors_df(result, author_bucket_field, year):
    """Returns a dataframe with first and last commit of those authors
    whose last commit was made within a given year"""

    # Get a dataframe with each author and their first commit
    buckets_result = result['aggregations'][author_bucket_field]['buckets']

    buckets = []
    for bucket_author in buckets_result:
        author = bucket_author['key']

        first = bucket_author['first']['hits']['hits'][0]
        first_commit = first['sort'][0]/1000
        last_commit = bucket_author['last_commit']['value']/1000
        org_name = first['_source']['author_org_name']
        project = first['_source']['project']
        #uuid = first['_source']['author_uuid']
        if datetime.utcfromtimestamp(last_commit).year == year:
            buckets.append({
                    'first_commit': datetime.utcfromtimestamp(first_commit),
                    'last_commit': datetime.utcfromtimestamp(last_commit),
                    'author': author,
                    #'uuid': uuid,
                    'org': org_name,
                    'project': project
            })
    authors_df = pd.DataFrame.from_records(buckets)
    authors_df.sort_values(by='first_commit', ascending=False,
                            inplace=True)
    return authors_df


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

def to_simple_df_by_time(result, group_column, time_column, value_column,
		 group_field, time_field, value_field):
    """Creates a dataframe based on group and time values
    """
    df = pd.DataFrame(columns=[group_column, time_column, value_column])

    for time in result.to_dict()['aggregations'][time_field]['buckets']:
        for group in time[group_field]['buckets']:
            df.loc[len(df)] = [group['key'], time['key_as_string'],
                group[value_field]['value']]

    return df


############################
# PLOTLY RELATED FUNCTIONS #
############################

def print_table(df, filename='table.html'):
    plotly.offline.init_notebook_mode(connected=True)
    table = ff.create_table(df)
    plotly.offline.iplot(table, filename=filename)

def print_stacked_bar(df, time_column, value_column, group_column):
    """Print stacked bar chart from dataframe based on time_field,
    grouped by group field.
    """
    plotly.offline.init_notebook_mode(connected=True)

    bars = []
    for group in df[group_column].unique():
        group_slice_df = df.loc[df[group_column] == group]
        bars.append(go.Bar(
            x=group_slice_df[time_column].tolist(),
            y=group_slice_df[value_column].tolist(),
            name=group))

    layout = go.Layout(
        barmode='stack'
    )

    fig = go.Figure(data=bars, layout=layout)
    plotly.offline.iplot(fig, filename='stacked-bar')

def print_grouped_bar(df, time_column, value_column, group_column):
    """Print grouped bar chart from dataframe based on time_field,
    grouped by group field.
    """
    plotly.offline.init_notebook_mode(connected=True)

    bars = []
    for group in df[group_column].unique():
        group_slice_df = df.loc[df[group_column] == group]
        bars.append(go.Bar(
            x=group_slice_df[time_column].tolist(),
            y=group_slice_df[value_column].tolist(),
            name=group))

    layout = go.Layout(
        barmode='group'
    )

    fig = go.Figure(data=bars, layout=layout)
    plotly.offline.iplot(fig, filename='grouped-bar')

def print_horizontal_bar_chart(df, experience_field, title, min_range = 0):

    plotly.offline.init_notebook_mode(connected=True)

    experience = list(range(min_range, int(df[experience_field].max()) + 1))

    people_count = []
    for exp in experience:
        people_count.append(len(df.loc[df[experience_field] == exp]))

    data = [go.Bar(
            x=people_count,
            y=experience,
            orientation = 'h'
    )]

    layout = go.Layout(
        barmode='group',
        title= title
    )

    fig = go.Figure(data=data, layout=layout)
    plotly.offline.iplot(fig, filename='horizontal-bar')


########
# TEST #
########

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
