import pandas as pd
from bs4 import BeautifulSoup as bs
import urllib.request as ur
import numpy as np
from telegram_bot.config import api_key,chat_id
from database.stock import StockModel
from pymongo import MongoClient
from database.config import MONGO_DB_NAME
from glob import glob

un_search = []

# 새로운 공모주 크롤링한 파일 저장할 경로(38_add_variable)
DIR = '/Users/dy/데청캠/Prediction-of-IPO-stock-price-using-Telegram-chatbot/Data_Preprocessing/'

df_dic = {'기업명': [], '매출액': [], '순이익': [], '구주매출':[], '희망공모가액':[], '청약경쟁률':[], '확정공모가':[]}


for p in range(1,70+1): # page num
    base_url = 'http://www.38.co.kr/html/fund/'
    page = f'index.htm?o=r1&page={p}'
    html = ur.urlopen(base_url+page)
    soup = bs(html.read(), "html.parser")

    for menu in soup.find_all('a','menu'):
        
        cor_url = base_url + menu['href'][2:]
        #print(cor_url)
        cor_html = ur.urlopen(cor_url)
        cor_soup = bs(cor_html.read(), "html.parser")
        
        info_table = cor_soup.find('table',summary='기업개요')
        if info_table is None:
            un_search.append(cor_url)
            continue
        bids_table = cor_soup.find('table',summary='공모정보')
        table = cor_soup.find('table',summary='공모청약일정')
        sub_table = table.find_all('tr')
        
        # 기업개요
        기업명 = info_table.find('td',bgcolor='#FFFFFF').text.split()[0]

        # 크롤링한 정보가 db에 이미 존재한다면, 크롤링 멈추기
        # 70page를 새롭게 크롤링하면 시간이 오래 걸림
        # 따라서 새로운 정보만 크롤링한다!!
        client = MongoClient('localhost', 27017)
        db = client['Ipo']
        print("=====================db======================",db)

        if db.inform.find_one({'기업명': 기업명}):
          break

        trs = info_table.find_all('tr')

        for tr in trs:
            if tr==trs[7]:
                tds = tr.find_all('td')
                for td in tds:
                    매출액=tds[1].text.replace(u'\xa0',u'')
            elif tr==trs[8]:
                tds=tr.find_all('td')
                for td in tds:
                    순이익 = tds[1].text.replace(u'\xa0',u'')
        # 공모 정보
        trs = bids_table.find_all('tr')

        for tr in trs:
            if tr==trs[1]:
                tds=tr.find_all('td')
                for td in tds:
                    구주매출=tds[1].text.replace(u'\xa0',u'')

            if tr==trs[2]:
                tds=tr.find_all('td')
                for td in tds:
                    희망공모가액=tds[1].text.replace(u'\xa0',u'')
                    청약경쟁률 = tds[3].text.replace(u'\xa0',u'')

        확정공모가 = ''.join(sub_table[6].find('td', bgcolor='#FFFFFF').text.split())


        df_dic['기업명'].append(기업명)
        df_dic['매출액'].append(매출액)
        df_dic['순이익'].append(순이익)
        df_dic['구주매출'].append(구주매출)
        df_dic['희망공모가액'].append(희망공모가액)
        df_dic['청약경쟁률'].append(청약경쟁률)
        df_dic['확정공모가'].append(확정공모가)          

        
df=pd.DataFrame(df_dic, columns=('기업명','매출액','순이익','구주매출','희망공모가액','청약경쟁률','확정공모가'))
# csv로 떨구지 말고 df 상태에서 바로 전처리..?

print(df)

df.to_csv(DIR+'38_add_variable.csv', encoding='cp949', mode='a')
# mode=a로 지정할 경우 기존 파일 아래에 값을 추가하여 입력하게됩니다. 
print('Add new data to 38_add_variable is finished!')


data1 = pd.read_csv('/Users/dy/데청캠/Prediction-of-IPO-stock-price-using-Telegram-chatbot/Data_Preprocessing/data.csv',encoding='euc-kr')
data = pd.read_csv('/Users/dy/데청캠/Prediction-of-IPO-stock-price-using-Telegram-chatbot/Data_Preprocessing/38com_benefit.csv')
data_added = pd.read_csv('/Users/dy/데청캠/Prediction-of-IPO-stock-price-using-Telegram-chatbot/Data_Preprocessing/38_add_variable.csv', encoding = 'euc-kr')


from Data_Preprocessing.preprocessing import total_preprocessing
new_df = total_preprocessing(data1,data,data_added)
print('크롤링한 데이터를 추가한 new_df: \n',new_df)

# new_df 저장할 경로 설정
DIR = '/Users/dy/데청캠_2조/Prediction-of-IPO-stock-price-using-chatbot/'

try:
  df = new_df.to_csv(DIR+'raw data/new_data.csv')
  from database.df_to_database import dataframe_to_db
  dataframe_to_db(df)
 
except:
  print('Oops new_data csv 파일로 변환하는 도중에 에러가 났어요')
