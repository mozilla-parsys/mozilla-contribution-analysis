# mozilla-contribution-analysis

Notebooks and other data to reproduce the Mozilla Contributions Analysis, performed by Bitergia during May, June 2018.

## Configuration

* Create and activate a Python3 virtual environment:

```bash
% python3 -m venv moz-contrib
% bash moz-contrib/bin/activate
```

* Install Pypi packages for jupyter, pandas (needed) and jupyter-runner (convenient). Install some auxiliary packages as well. The easies way of doing this is by running the requirements.txt file (remember to do that in the activated environment, see above):

```bash
(moz-contrib) % pip install -r requirements.txt
```

* Copy file `data-analysis/settings.sample` to `data-analysis/.settings`, and edit it to match your settings (mainly, where your indexes are, and the credentials to access them). The file should look something like:

```
[ElasticSearch]

user=XXX
password=YYY
host=localhost
port=443
path=data
```

This would mean to use user XXX, passwd YYY to access indexes provided by an ElasticSearch instance located in https://localhost:443/data ()

* Run jupyter, to access the notebooks from the browser:

```
(moz-contrib) % jupyter-notebook
```

Notebooks are in the `data-analysis` directory.
