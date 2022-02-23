#classics
from multiprocessing.sharedctypes import Value
from re import L
import pandas as pd
import moment
import time
#necessary for data scraping
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
#streamlit
import streamlit as st

#make clickable links in data df
def make_clickable(link):
    # target _blank to open new window
    title_link = link.split('::')
    print(title_link)
    return f'<a target="_blank" href="{title_link[1]}">{title_link[0]}</a>'


def getNews(keyword_input):
  #dynamic keyword to fetch any G news with dyn url
  keyword = keyword_input.split(" ")
  search = '+'.join(keyword)
  url = f"https://www.google.com/search?q={search}&source=lnms&tbm=nws&sa=X&ved=2ahUKEwiN0rOIwt71AhVIzIUKHXh4Cd8Q_AUoAnoECAEQBA&biw=1920&bih=937&dpr=1&safe=active&ssui=on"
  obj_arr = []
  root = "https://www.google.com/"
  for i in range(1,3):#scrape the 1st 3 pages of Gnews
    headers = {'User-agent':'Mozilla/5.0',
            'Accept-Language': 'en-US,en;q=0.5'
            }
    req = Request(url,headers=headers)
    resp = urlopen(req).read()
    #print(resp)
    soup = BeautifulSoup(resp,'html.parser')
    #print(soup.prettify())
    for element in soup.find_all('div', attrs={'class':'ZINbbc luh4tb xpd O9g5cc uUPGi'}):
      try:
        link = element.find('a',href=True)['href'].split('/url?q=')[1]
        #remove part of string in link '/&sa...'
        link = link.split('&sa')[0]
        link = link.split('%')[0]
        title = element.find('div', attrs={'class':'BNeawe vvjwJb AP7Wnd'}).text
        source = element.find('div', attrs={'class':'BNeawe UPmit AP7Wnd'}).text
        date_and_Descrip = element.find('div', attrs={'class':'BNeawe s3v9rd AP7Wnd'}).text
        index_split = date_and_Descrip.index(" · ")
        date_str = date_and_Descrip[0:index_split].strip()
        description = date_and_Descrip[index_split+2:].strip()
        obj = {
            'title': title,
            'description': description,
            'date': date_str,
            'datetimePosted': moment.date(date_str).timezone("Europe/Brussels").format("DD-MM-YYYY HH:MM"),
            'source': source,
            'link': link,
            'search': keyword_input,
            'API_call_datetime': moment.utcnow().timezone("Europe/Brussels").format('DD MMMM HH:mm')
        }
        obj_arr.append(obj)
      except(TypeError, KeyError) as e:
        # Token not found. Replace 'pass' with additional logic.
        pass
    #in case the number of pages is lower than 5, the "next page" button won't be available so we do not want the code to break, so we implemente a try .. except logic
    try:
      next = soup.find('a',attrs={'class':'nBDE1b G5eFlf'})['href']
      url = root + next
    except:
        pass

    df = pd.DataFrame(obj_arr)
    #embed urls into clickable titles
    df['title'] = df['title'] + '::' + df['link']
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

  #sort values by datetime column values
  data['datetimePosted'] = pd.to_datetime(data['datetimePosted'], dayfirst= True )
  # test_comboGets.info(verbose=True)
  data = data.sort_values(by='datetimePosted', ascending=False)
  data['datetimePosted'] = data['datetimePosted'].astype(str)

  #re arrange column order
  data = data[['date','title','description','source','search']]
  data = data.drop_duplicates(subset='title')
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
    session.search = "Natural Gas Europe & TTF Natural Gas prices & Europe Electricity Prices"
if 'news_data' not in session:
    session.news_data = comboGets(session.search).to_html(escape=False, index=False)

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
news_table.write(session.news_data, unsafe_allow_html=True)

while (checkbox):
    with st.spinner("Auto refresh..."):
        session.news_data = comboGets(session.search).to_html(escape=False, index=False)
    session.auto_refresh_count += 1
    countAutoRefresh.write(f'Count of Auto Refresh: {session.auto_refresh_count}')
    news_table.empty()
    news_table.write(session.news_data, unsafe_allow_html=True)
    time.sleep(600)
    



