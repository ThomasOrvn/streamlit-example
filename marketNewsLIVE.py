#classics
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

#function to get news from one search
@st.cache(suppress_st_warning=True)
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
  df.head(10)
  return df

#functions to combine newd flow from one or multiple searches
@st.cache(suppress_st_warning=True)
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

#Streamlit app
#initialization, loading of 1st load 
data = comboGets("natural gas europe & Montel TTF prices").to_html(escape=False, index=False)

#app layout
st.title('SEGE LIVE Energy News App')
search_input = st.text_input("Search: ",value="natural gas europe & Montel TTF prices", max_chars=50, placeholder="Insert 1 or multiple searches separated by &")
st.markdown=(f"input is: {search_input}")

status = st.empty()
if search_input=="":
    search_input= "empty search, please add search input"
else:
    data = comboGets(search_input).to_html(escape=False, index=False)

status.text(f"searched news for: {search_input}")
auto_update_checkbox = st.checkbox('10 min auto refresh?')

table = st.empty() #st.container()
table.container().write(data, unsafe_allow_html=True)

while(auto_update_checkbox):
    table.empty()
    status.text("fetching data...")
    data = comboGets('natural gas europe only')
    data = data.to_html(escape=False)
    table.write(data, unsafe_allow_html=True)
    now = now = moment.utcnow().timezone("Europe/Brussels").format('DD MMMM HH:mm:ss')
    status.text(f"Last refresh: {now}")
    time.sleep(600.0)
    


