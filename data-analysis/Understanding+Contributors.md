
## Goal: understanding contributors

The term "community" in this context refers to the group of people contributing to Mozilla projects. Thus, this goal could be summarized as characterizing Mozilla community based on their contributors. A contributor will be understood as a person who performs an action that can be tracked in the set of considered data sources. For example: sending a commit, opening or closing a ticket. As they will be different depending on the data source, particular actions used in each analysis will be detailed within particular goals.

The main objective of this goal is to determine a set of characteristics of contributors:

  * Projects: to which projects they contribute.
  * Organizations: to which organizations they are affiliated
  * Gender: which one is their gender
  * Age: which one is their "age" in the project (time contributing)
  * Geographical origin: where do they come from

Those goals can be refined in the following questions:

**Questions**:

* Which projects can be identified?
* Which contributors have activity related to each project?
* Which organizations can be identified?
* Which contributors are affiliated to each organization?
* Which of those contributors are hired by Mozilla, and which are not?
* Which gender are contributors?
* How long have been contributors contributing?
* Where do contributors come from?

These questions can be answered with the following metrics/data:

**Metrics**:

* List of projects
* Contributors by project
* Number of contributors by project over time
* List of organizations
* Contributors by organization
* Number of contributors by organization over time
* Contributors by groups: hired by Mozilla, the rest
* Contributors by gender
* Number of contributors by gender over time
* Time of first and last commit for each contributor
* Length of period of activity for each contributor
* Contributors by time zone (when possible)
* Contributors by city name (when possible)

All the characeterizations of developers (by project, by organization, by hired by Mozilla/rest, by gender, by period of activity, by time zone, by city name) can be a discriminator / grouping factor for the metrics defined for the next goals. Most of these metrics can be made particular for each of the considered data sources.

### Metric Calculations
First we need to load a connection against the proper ES instance. We use an external module to load credentials from a file that will not be shared. If you want to run this, please use your own credentials, just put them in a file named '.settings' (in the same directory as this notebook) following the example file 'settings.sample'.

**TODO**: Add bot and merges filtering.


```python
import pandas

import plotly as plotly
import plotly.graph_objs as go

from util import ESConnection
from elasticsearch_dsl import Search

es_conn = ESConnection()
```

#### List of Projects

To get the list of projects we will query ES to retrieve the unique count of commits for each project. To do that, we bucketize data based on 'project' field (to a maximum of 100 projects, given by 'size' parameter set below).


```python
s = Search(using=es_conn, index='git')

# Unique count of Commits by Project (max 100 projects)
s.aggs.bucket('projects', 'terms', field='project', size=100)\
    .metric('commits', 'cardinality', field='hash', precision_threshold=100000)
result = s.execute()

# In case you need to check response, uncomment line below
#print(result.to_dict()['aggregations'])

```


```python
df = pandas.DataFrame()

df = df.from_dict(result.to_dict()['aggregations']['projects']['buckets'])
df = df.drop('doc_count', axis=1)
df['commits'] = df['commits'].apply(lambda row: row['value'])
df=df[['key', 'commits']]
df.columns = ['Project', '# Commits']

df
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Project</th>
      <th># Commits</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>mozilla</td>
      <td>1902323</td>
    </tr>
    <tr>
      <th>1</th>
      <td>mozilla-services</td>
      <td>147526</td>
    </tr>
    <tr>
      <th>2</th>
      <td>rust-lang</td>
      <td>135992</td>
    </tr>
    <tr>
      <th>3</th>
      <td>servo</td>
      <td>78163</td>
    </tr>
    <tr>
      <th>4</th>
      <td>mdn</td>
      <td>12750</td>
    </tr>
    <tr>
      <th>5</th>
      <td>moztw</td>
      <td>8618</td>
    </tr>
    <tr>
      <th>6</th>
      <td>mozilla-mobile</td>
      <td>9105</td>
    </tr>
    <tr>
      <th>7</th>
      <td>aframevr</td>
      <td>7160</td>
    </tr>
    <tr>
      <th>8</th>
      <td>mozilla-japan</td>
      <td>5787</td>
    </tr>
    <tr>
      <th>9</th>
      <td>mozmar</td>
      <td>5415</td>
    </tr>
    <tr>
      <th>10</th>
      <td>MozillaCZ</td>
      <td>4433</td>
    </tr>
    <tr>
      <th>11</th>
      <td>mozillascience</td>
      <td>3871</td>
    </tr>
    <tr>
      <th>12</th>
      <td>Mozilla-TWQA</td>
      <td>3748</td>
    </tr>
    <tr>
      <th>13</th>
      <td>mozillach</td>
      <td>3676</td>
    </tr>
    <tr>
      <th>14</th>
      <td>mozillabrasil</td>
      <td>2101</td>
    </tr>
    <tr>
      <th>15</th>
      <td>mozfr</td>
      <td>2059</td>
    </tr>
    <tr>
      <th>16</th>
      <td>browserhtml</td>
      <td>1977</td>
    </tr>
    <tr>
      <th>17</th>
      <td>mozillahispano</td>
      <td>1826</td>
    </tr>
    <tr>
      <th>18</th>
      <td>MozVR</td>
      <td>1532</td>
    </tr>
    <tr>
      <th>19</th>
      <td>MozillaTN</td>
      <td>1191</td>
    </tr>
    <tr>
      <th>20</th>
      <td>MozillaFoundation</td>
      <td>1153</td>
    </tr>
    <tr>
      <th>21</th>
      <td>MozillaKerala</td>
      <td>1007</td>
    </tr>
    <tr>
      <th>22</th>
      <td>mozdevs</td>
      <td>883</td>
    </tr>
    <tr>
      <th>23</th>
      <td>mozillaitalia</td>
      <td>473</td>
    </tr>
    <tr>
      <th>24</th>
      <td>mozillaperu</td>
      <td>141</td>
    </tr>
    <tr>
      <th>25</th>
      <td>mozillavenezuela</td>
      <td>51</td>
    </tr>
    <tr>
      <th>26</th>
      <td>mozillacampusclubs</td>
      <td>36</td>
    </tr>
    <tr>
      <th>27</th>
      <td>mozillaph</td>
      <td>29</td>
    </tr>
  </tbody>
</table>
</div>



#### Contributors by Project


```python
s = Search(using=es_conn, index='git')

# Unique count of Commits by Project (max 100 projects)
s.aggs.bucket('projects', 'terms', field='project', size=100)\
    .metric('contributors', 'cardinality', field='author_uuid', precision_threshold=100000)
result = s.execute()

# In case you need to check response, uncomment line below
#print(result.to_dict()['aggregations'])

```


```python
df = pandas.DataFrame()

df = df.from_dict(result.to_dict()['aggregations']['projects']['buckets'])
df = df.drop('doc_count', axis=1)
df['contributors'] = df['contributors'].apply(lambda row: row['value'])
df=df[['key', 'contributors']]
df.columns = ['Project', '# Contributors']

df
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Project</th>
      <th># Contributors</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>mozilla</td>
      <td>10965</td>
    </tr>
    <tr>
      <th>1</th>
      <td>mozilla-services</td>
      <td>2122</td>
    </tr>
    <tr>
      <th>2</th>
      <td>rust-lang</td>
      <td>2444</td>
    </tr>
    <tr>
      <th>3</th>
      <td>servo</td>
      <td>1384</td>
    </tr>
    <tr>
      <th>4</th>
      <td>mdn</td>
      <td>334</td>
    </tr>
    <tr>
      <th>5</th>
      <td>moztw</td>
      <td>89</td>
    </tr>
    <tr>
      <th>6</th>
      <td>mozilla-mobile</td>
      <td>108</td>
    </tr>
    <tr>
      <th>7</th>
      <td>aframevr</td>
      <td>205</td>
    </tr>
    <tr>
      <th>8</th>
      <td>mozilla-japan</td>
      <td>58</td>
    </tr>
    <tr>
      <th>9</th>
      <td>mozmar</td>
      <td>73</td>
    </tr>
    <tr>
      <th>10</th>
      <td>MozillaCZ</td>
      <td>33</td>
    </tr>
    <tr>
      <th>11</th>
      <td>mozillascience</td>
      <td>109</td>
    </tr>
    <tr>
      <th>12</th>
      <td>Mozilla-TWQA</td>
      <td>49</td>
    </tr>
    <tr>
      <th>13</th>
      <td>mozillach</td>
      <td>66</td>
    </tr>
    <tr>
      <th>14</th>
      <td>mozillabrasil</td>
      <td>181</td>
    </tr>
    <tr>
      <th>15</th>
      <td>mozfr</td>
      <td>60</td>
    </tr>
    <tr>
      <th>16</th>
      <td>browserhtml</td>
      <td>44</td>
    </tr>
    <tr>
      <th>17</th>
      <td>mozillahispano</td>
      <td>68</td>
    </tr>
    <tr>
      <th>18</th>
      <td>MozVR</td>
      <td>26</td>
    </tr>
    <tr>
      <th>19</th>
      <td>MozillaTN</td>
      <td>47</td>
    </tr>
    <tr>
      <th>20</th>
      <td>MozillaFoundation</td>
      <td>112</td>
    </tr>
    <tr>
      <th>21</th>
      <td>MozillaKerala</td>
      <td>35</td>
    </tr>
    <tr>
      <th>22</th>
      <td>mozdevs</td>
      <td>14</td>
    </tr>
    <tr>
      <th>23</th>
      <td>mozillaitalia</td>
      <td>18</td>
    </tr>
    <tr>
      <th>24</th>
      <td>mozillaperu</td>
      <td>8</td>
    </tr>
    <tr>
      <th>25</th>
      <td>mozillavenezuela</td>
      <td>8</td>
    </tr>
    <tr>
      <th>26</th>
      <td>mozillacampusclubs</td>
      <td>4</td>
    </tr>
    <tr>
      <th>27</th>
      <td>mozillaph</td>
      <td>3</td>
    </tr>
  </tbody>
</table>
</div>



#### Number of contributors by project over time
**TODO**: provide a plot similar to https://analytics.mozilla.community:443/goto/9523b9b00de0b35645de488a1a06514e


```python
s = Search(using=es_conn, index='git')
s.params(timeout=30)

# Unique count of Commits by Project (max 100 projects)
s = s.filter('range', grimoire_creation_date={'gt': 'now/M-2y', 'lt': 'now/M'})
s.aggs.bucket('projects', 'terms', field='project', size=10)\
    .bucket('time', 'date_histogram', field='grimoire_creation_date', interval='quarter')\
    .metric('contributors', 'cardinality', field='author_uuid', precision_threshold=100000)

#print(s.to_dict())
result = s.execute()

# In case you need to check response, uncomment line below
#print(result.to_dict()['aggregations'])
```


```python
df = pandas.DataFrame(columns=['Project', 'Time', '# Contributors'])

result.to_dict()['aggregations']['projects']['buckets']
for b in result.to_dict()['aggregations']['projects']['buckets']:
    #print(b['key'])
    for i in b['time']['buckets']:
        #print("\tdate: ", i['key_as_string'], 'value: ',i['contributors']['value'])
        df.loc[len(df)] = [b['key'], i['key_as_string'], i['contributors']['value']]  

#df
```


```python
plotly.offline.init_notebook_mode(connected=True)

# Select rows by unique column value
#for project in df.Project.unique():
#    print(df.loc[df['Project'] == project])

bars = []
for project in df.Project.unique():
    project_df = df.loc[df['Project'] == project]
    bars.append(go.Bar(
        x=project_df['Time'].tolist(),
        y=project_df['# Contributors'].tolist(),
        name=project))

layout = go.Layout(
    barmode='stack'
)

fig = go.Figure(data=bars, layout=layout)
plotly.offline.iplot(fig, filename='stacked-bar')
```


<script>requirejs.config({paths: { 'plotly': ['https://cdn.plot.ly/plotly-latest.min']},});if(!window.Plotly) {{require(['plotly'],function(plotly) {window.Plotly=plotly;});}}</script>



<div id="5c26a655-bf48-416e-94a2-6bd9a4212cb5" style="height: 525px; width: 100%;" class="plotly-graph-div"></div><script type="text/javascript">require(["plotly"], function(Plotly) { window.PLOTLYENV=window.PLOTLYENV || {};window.PLOTLYENV.BASE_URL="https://plot.ly";Plotly.newPlot("5c26a655-bf48-416e-94a2-6bd9a4212cb5", [{"x": ["2015-04-01T00:00:00.000Z", "2015-07-01T00:00:00.000Z", "2015-10-01T00:00:00.000Z", "2016-01-01T00:00:00.000Z", "2016-04-01T00:00:00.000Z", "2016-07-01T00:00:00.000Z", "2016-10-01T00:00:00.000Z", "2017-01-01T00:00:00.000Z"], "name": "mozilla", "type": "bar", "y": [1107.0, 1337.0, 1500.0, 1534.0, 1459.0, 1433.0, 1223.0, 1300.0]}, {"x": ["2015-04-01T00:00:00.000Z", "2015-07-01T00:00:00.000Z", "2015-10-01T00:00:00.000Z", "2016-01-01T00:00:00.000Z", "2016-04-01T00:00:00.000Z", "2016-07-01T00:00:00.000Z", "2016-10-01T00:00:00.000Z", "2017-01-01T00:00:00.000Z"], "name": "rust-lang", "type": "bar", "y": [298.0, 276.0, 305.0, 339.0, 302.0, 361.0, 213.0, 248.0]}, {"x": ["2015-04-01T00:00:00.000Z", "2015-07-01T00:00:00.000Z", "2015-10-01T00:00:00.000Z", "2016-01-01T00:00:00.000Z", "2016-04-01T00:00:00.000Z", "2016-07-01T00:00:00.000Z", "2016-10-01T00:00:00.000Z", "2017-01-01T00:00:00.000Z"], "name": "servo", "type": "bar", "y": [90.0, 122.0, 149.0, 168.0, 176.0, 169.0, 160.0, 172.0]}, {"x": ["2015-04-01T00:00:00.000Z", "2015-07-01T00:00:00.000Z", "2015-10-01T00:00:00.000Z", "2016-01-01T00:00:00.000Z", "2016-04-01T00:00:00.000Z", "2016-07-01T00:00:00.000Z", "2016-10-01T00:00:00.000Z", "2017-01-01T00:00:00.000Z"], "name": "mozilla-services", "type": "bar", "y": [56.0, 87.0, 95.0, 109.0, 84.0, 74.0, 77.0, 111.0]}, {"x": ["2015-04-01T00:00:00.000Z", "2015-07-01T00:00:00.000Z", "2015-10-01T00:00:00.000Z", "2016-01-01T00:00:00.000Z", "2016-04-01T00:00:00.000Z", "2016-07-01T00:00:00.000Z", "2016-10-01T00:00:00.000Z", "2017-01-01T00:00:00.000Z"], "name": "mozilla-mobile", "type": "bar", "y": [21.0, 26.0, 26.0, 24.0, 20.0, 16.0, 23.0, 36.0]}, {"x": ["2015-07-01T00:00:00.000Z", "2015-10-01T00:00:00.000Z", "2016-01-01T00:00:00.000Z", "2016-04-01T00:00:00.000Z", "2016-07-01T00:00:00.000Z", "2016-10-01T00:00:00.000Z", "2017-01-01T00:00:00.000Z"], "name": "aframevr", "type": "bar", "y": [7.0, 20.0, 44.0, 38.0, 42.0, 52.0, 72.0]}, {"x": ["2015-04-01T00:00:00.000Z", "2015-07-01T00:00:00.000Z", "2015-10-01T00:00:00.000Z", "2016-01-01T00:00:00.000Z", "2016-04-01T00:00:00.000Z", "2016-07-01T00:00:00.000Z", "2016-10-01T00:00:00.000Z", "2017-01-01T00:00:00.000Z"], "name": "mdn", "type": "bar", "y": [23.0, 29.0, 36.0, 37.0, 33.0, 39.0, 50.0, 30.0]}, {"x": ["2015-04-01T00:00:00.000Z", "2015-07-01T00:00:00.000Z", "2015-10-01T00:00:00.000Z", "2016-01-01T00:00:00.000Z", "2016-04-01T00:00:00.000Z", "2016-07-01T00:00:00.000Z", "2016-10-01T00:00:00.000Z", "2017-01-01T00:00:00.000Z"], "name": "mozmar", "type": "bar", "y": [7.0, 8.0, 6.0, 11.0, 7.0, 12.0, 11.0, 13.0]}, {"x": ["2015-04-01T00:00:00.000Z", "2015-07-01T00:00:00.000Z", "2015-10-01T00:00:00.000Z", "2016-01-01T00:00:00.000Z", "2016-04-01T00:00:00.000Z", "2016-07-01T00:00:00.000Z", "2016-10-01T00:00:00.000Z", "2017-01-01T00:00:00.000Z"], "name": "mozillascience", "type": "bar", "y": [12.0, 27.0, 25.0, 33.0, 25.0, 13.0, 17.0, 21.0]}, {"x": ["2015-04-01T00:00:00.000Z", "2015-07-01T00:00:00.000Z", "2015-10-01T00:00:00.000Z", "2016-01-01T00:00:00.000Z", "2016-04-01T00:00:00.000Z", "2016-07-01T00:00:00.000Z", "2016-10-01T00:00:00.000Z", "2017-01-01T00:00:00.000Z"], "name": "Mozilla-TWQA", "type": "bar", "y": [8.0, 6.0, 4.0, 6.0, 10.0, 6.0, 6.0, 7.0]}], {"barmode": "stack"}, {"showLink": true, "linkText": "Export to plot.ly"})});</script>


#### List of organizations



```python
s = Search(using=es_conn, index='git')

# Unique count of Commits by Project (max 100 projects)
s.aggs.bucket('organizations', 'terms', field='author_org_name', size=100)\
    .metric('commits', 'cardinality', field='hash', precision_threshold=100000)
result = s.execute()

# In case you need to check response, uncomment line below
#print(result.to_dict()['aggregations'])
```


```python
df = pandas.DataFrame()

df = df.from_dict(result.to_dict()['aggregations']['organizations']['buckets'])
df = df.drop('doc_count', axis=1)
df['commits'] = df['commits'].apply(lambda row: row['value'])
df=df[['key', 'commits']]
df.columns = ['Organization', '# Commits']

df
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Organization</th>
      <th># Commits</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Mozilla Staff</td>
      <td>1371711</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Community</td>
      <td>967091</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Mozilla Reps</td>
      <td>624</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Unknown</td>
      <td>34</td>
    </tr>
  </tbody>
</table>
</div>



#### Contributors by organization


```python
s = Search(using=es_conn, index='git')

# Unique count of Commits by Project (max 100 projects)
s.aggs.bucket('organizations', 'terms', field='author_org_name', size=100).\
    metric('contributors', 'cardinality', field='author_uuid', precision_threshold=100000)
result = s.execute()

# In case you need to check response, uncomment line below
#print(result.to_dict()['aggregations'])
```


```python
df = pandas.DataFrame()

df = df.from_dict(result.to_dict()['aggregations']['organizations']['buckets'])
df = df.drop('doc_count', axis=1)
df['contributors'] = df['contributors'].apply(lambda row: row['value'])
df=df[['key', 'contributors']]
df.columns = ['Organization', '# Contributors']

df
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Organization</th>
      <th># Contributors</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Mozilla Staff</td>
      <td>2084</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Community</td>
      <td>13074</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Mozilla Reps</td>
      <td>2</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Unknown</td>
      <td>20</td>
    </tr>
  </tbody>
</table>
</div>



#### Number of contributors by organization over time
**TODO**: provide a plot similar to https://analytics.mozilla.community:443/goto/5dce2b36ec14405a09827860169ae234

#### Contributors by groups: hired by Mozilla, the rest
**TODO**: needs to know who are hired by Mozilla

#### Contributors by gender
**TODO**: Pending of running gender study over the data.

#### Number of contributors by gender over time
**TODO**: Pending of running gender study over the data.

#### Time of first and last commit for each contributor


#### Length of period of activity for each contributor


#### Contributors by time zone (when possible)

#### Contributors by city name (when possible)
