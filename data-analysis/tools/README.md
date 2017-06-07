# Some tools used in producing indexes for this analysis

All of these tools have a --help option for learning about their command line interface.

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
