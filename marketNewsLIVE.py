#classics
import json
import pandas as pd
import time


#necessary for data scraping
from urllib.request import Request, urlopen
#streamlit
import streamlit as st

#make clickable links in data df
def make_clickable(link):
    # target _blank to open new window
    title_link = link.split('::')
    return f'<a target="_blank" href="{title_link[1]}">{title_link[0]}</a>'


def getNews(keyword_input):
  #dynamic keyword to fetch any G news with dyn url
  apiKey = "bb387d5cf17b423194e93dc774363333"
  keywords = keyword_input.split(" ")
  keyword_split = '+'.join(keywords)
  print(keyword_split)
  url = f"https://newsapi.org/v2/everything?q={keyword_split}&apiKey={apiKey}"
  request = Request(url)
  resp = urlopen(request).read()
  resp_json = json.loads(resp.decode('utf-8'))
  df = pd.DataFrame.from_dict(resp_json['articles'])
  #retrive the name of the source via the apply method
  df['source'] = df['source'].apply(lambda x: x['name'])
  #replace the "na" by "unknown"
  df = df.fillna("Unknown")
  #convert published datetime to UTC
  df['publishedAt'] = pd.to_datetime(df['publishedAt'], utc= True)
  #compare the published datetime with current datetime
  df['publishedWhen'] = pd.to_datetime('today', utc= True) - df['publishedAt']
  #convert timedelta into hours, but not working
  df['publishedWhen'] = pd.to_timedelta(df['publishedWhen'], unit= 'hours')
  #reformat published datetime Day Month Year Hour:Min
  df['publishedAt'] = df['publishedAt'].dt.strftime('%m/%d/%Y %H:%m')
  df['keyword'] = keyword_input
  df['title'] = df['title'] + '::' + df['url']
  #embed urls into clickable titles
  df['title'] = df['title'].apply(make_clickable)
#return news df as function output
  return df

#functions to combine newd flow from one or multiple searches
def comboGets(search):
  searchList = [word.strip() for word in search.split("&")]
  for i, word in enumerate(searchList):
    #initialization with 1st word of the search list
    if(i==0):
      data = getNews(word)
    print('Fetching news for word: {}'.format(word))
    data2 = getNews(word)
    data= data.append(data2, ignore_index=True)
    #print('length of final Dataset {}'.format(len(data)))


  # test_comboGets.info(verbose=True)
  data = data.sort_values(by='publishedAt', ascending=False)
  data['publishedWhen'] = data['publishedWhen'].astype(str)

 
  #re arrange column order
  data = data[['title','description','source','publishedAt','keyword']]
  data = data.drop_duplicates(subset='title')
  #reset index on 'date' column 
  #data = data.set_index('date')
  return data


####################STREAMLIT APP###################
#set the full page mode
st.set_page_config(layout="wide")

#init session
session = st.session_state

if 'status' not in session:
    session.status = 'State 0'
if 'auto_refresh_count' not in session:
    session.auto_refresh_count = 0
if 'search' not in session:
    session.search = "Natural Gas Europe"
if 'news_data' not in session:
    session.news_data = comboGets("Natural Gas Europe").to_html(escape=False, index=False)

def f_update() :
    with st.spinner("Refreshing page... please hold a sec"):
        session.news_data = comboGets(session.search).to_html(escape=False, index=False)
        session.status = "updated"

#App layout
st.title('SEGE ENERGY NEWS LIVE')
st.text_input(label='Input Searched Keyword(s)',key='search', on_change=f_update)

st.write('Search entered: ',session.search)
checkbox = st.checkbox(label='10 mins auto refresh', key='auto_update')

#st.write(session)

countAutoRefresh = st.empty()
countAutoRefresh.write(f'Count of Auto Refresh: {session.auto_refresh_count}')

news_table = st.empty()
time.sleep(3)
news_table.write(session.news_data, unsafe_allow_html=True)

while (checkbox):
    with st.spinner("Auto refresh..."):
        session.news_data = comboGets(session.search).to_html(escape=False, index=False)
    session.auto_refresh_count += 1
    countAutoRefresh.write(f'Count of Auto Refresh: {session.auto_refresh_count}')
    news_table.empty()
    news_table.write(session.news_data, unsafe_allow_html=True)
    time.sleep(5)
    



