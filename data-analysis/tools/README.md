# Some tools used in producing indexes for this analysis

All of these scripts have a --help option for learning about their command line interface.

Before running the scripts, install the `elasticsearch` Python package in a Python3 environment. Ensure you run them with python3. For example:

```
% python3 -m venv ~/venvs/elastic-env
% source ~/venvs/elastic-env/bin/activate
(elastic-env) % pip install elasticsearch
(elastic-env) % python elastic_cp.py ...
```

## elastic_cp.py

For copying indexes from one ElasticSearch instance to another one. Has some fitlering capabilities (eg, filter all documents in which some field has some value).

Example: produce a file with a list of JSON documents (one per item) for all commits in an index, as long as they match a certain value for a field. The produced file is `mozilla_git_gecko-dev.json`, the index is `git`, the file to match is `origin`, the value to match is `https://github.com/mozilla/gecko-dev.git`.

```
python elastic_cp.py \
  --src https://user:passwd@analytics.mozilla.community/data --src_index git \
  --dest mozilla_git_gecko-dev.json --with_mapping \
  --match origin https://github.com/mozilla/gecko-dev.git
```

## elastic_projects.py

Annotate the `project` field in enriched indexes for some data sources (git, GitHub, Bugzilla, mailing lists, Discourse), using the information in a spreadsheet that has the correspondence of repositories to projects. That spreadsheet has one sheet per data source, in shich some columns specify the repo, and the last one the project.

Example: annotate the field `project` in the `bugzilla` Bugzilla enriched index, according to the data in the `projects.xlsx` spreadsheet, showing the list of projects identified, logging at the `info` level, writting logging output in `/tmp/log`.

```
python elastic_projects.py \\
  --es https://user:passw@mozilla-test.biterg.io/data \
  --index_bugzilla bugzilla --projects projects.xlsx --show_projects \
  -l info --logfile /tmp/log
```

## elastic_split.py

Very specific tool that uses a raw git index with documents corresponding to all commits in the gecko-dev fir repository, and annotates an enriched index, in which all of these commits are assigned to project `Gecko`, assigning some of them to `Firefox` if they are in some directories (`browser`, `toolkit`, `chrome`).

Example: annotate with `Firefox` as project the enriched index `git` in `mozilla-test.biterg.io/data`, based on the information in the raw index `git_raw_gecko_dev` in `mozilla-test.biterg.io/data`.

```
python elastic_split_repo.py \
  --es_raw https://user:pass@mozilla-test.biterg.io/data \
  --index_raw git_raw_gecko_dev \
  --es_enriched https://user:pass@mozilla-test.biterg.io/data \
  --index_enriched git
```

## Complete process

This is intended to represent the complete process of producing the indexes needed for the analysis (but it is still work in progress):

```
# Copy enriched indexes from production to mozilla-test
#
# Git
time python elastic_cp.py \
  --src https://user:passwd@analytics.mozilla.community/data \
  --src_index git \
  --dest https://user:passw@mozilla-test.biterg.io/data
  --dest_index git --with_mapping \
# GitHub
time python elastic_cp.py \
  --src https://user:passwd@analytics.mozilla.community/data \
  --src_index github_issues \
  --dest https://user:passw@mozilla-test.biterg.io/data
  --dest_index github_issues --with_mapping \
# Bugzilla
time python elastic_cp.py \
  --src https://user:passwd@analytics.mozilla.community/data \
  --src_index bugzilla \
  --dest https://user:passw@mozilla-test.biterg.io/data
  --dest_index bugzilla --with_mapping \
# Mailing lists
time python elastic_cp.py \
  --src https://user:passwd@analytics.mozilla.community/data \
  --src_index mbox \
  --dest https://user:passw@mozilla-test.biterg.io/data
  --dest_index mbox --with_mapping \
# Discourse
time python elastic_cp.py \
  --src https://user:passwd@analytics.mozilla.community/data \
  --src_index discourse \
  --dest https://user:passw@mozilla-test.biterg.io/data
  --dest_index discourse --with_mapping \

# Produce project fields for enriched indexes according to spreadsheet
# (maybe all the following commands could be run in one, but that has
# not been tested).
#
# Git
time python elastic_projects.py \\
  --es https://user:passw@mozilla-test.biterg.io/data \
  --index_git git --projects projects.xlsx --show_projects \
  -l info --logfile /tmp/log
# GitHub
time python elastic_projects.py \\
  --es https://user:passw@mozilla-test.biterg.io/data \
  --index_github github_issues --projects projects.xlsx --show_projects \
  -l info --logfile /tmp/log
# Bugzilla
time python elastic_projects.py \\
  --es https://user:passw@mozilla-test.biterg.io/data \
  --index_bugzilla bugzilla --projects projects.xlsx --show_projects \
  -l info --logfile /tmp/log
# Mailing lists
time python elastic_projects.py \\
  --es https://user:passw@mozilla-test.biterg.io/data \
  --index_email mbox --projects projects.xlsx --show_projects \
  -l info --logfile /tmp/log
# Discourse
time python elastic_projects.py \\
  --es https://user:passw@mozilla-test.biterg.io/data \
  --index_discourse discourse --projects projects.xlsx --show_projects \
  -l info --logfile /tmp/log

# Now, let's split gecko-dev annotating some of its commmits as Firefox
#
# Get a file with the raw index for gecko-dev
time python elastic_cp.py \
  --src https://user:passwd@analytics.mozilla.community/data \
  --src_index git_gecko_dev_and_projects_170520  \
  --dest mozilla_git_raw_gecko-dev.json --with_mapping \
  --match origin https://github.com/mozilla/gecko-dev.git
# Delete the raw index in mozilla-test before uploading (just in case)
curl -XDELETE https://user:passwd@mozilla-test.biterg.io/data/git_raw_gecko_dev
# Upload that file to a raw index in mozilla-test
time python elastic_cp.py \
  --dest https://user:passwd@mozilla-test.biterg.io/data \
  --dest_index git_raw_gecko_dev  \
  --src mozilla_git_raw_gecko-dev.json --with_mapping
# Annotate some commits in gecko-dev repo as Firefox
python elastic_split_repo.py \
  --es_raw https://user:pass@mozilla-test.biterg.io/data \
  --index_raw git_raw_gecko_dev \
  --es_enriched https://user:pass@mozilla-test.biterg.io/data \
  --index_enriched git
```
