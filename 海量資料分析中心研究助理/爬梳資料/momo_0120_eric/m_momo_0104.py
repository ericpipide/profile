import time,threading,csv,requests,random,sys
import pandas as pd
import multiprocessing as mp
from queue import Queue
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter

chrome_options = webdriver.ChromeOptions()
user_agent = 'XXX'
chrome_options.add_argument('--headless')
chrome_options.add_argument('--incognito')
chrome_options.add_argument('--disable-plugins')
chrome_options.add_argument('--user-agent=%s' % user_agent)
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_options.add_experimental_option("prefs",{"profile.managed_default_content_settings.images":2})

def pages_scratch(url,q):
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    first_page = bs(driver.page_source,'lxml')
    try:
        pages = first_page.find_all('li', class_ = 'pageval')[0].text
        pages = int(pages[pages.find('/')+1:])
        for j in range(1, pages+1):
            page_url = str(url) + '&p_pageNum='+ str(j)
            q.put(page_url)
        driver.quit()
    except IndexError:
        driver.quit()
        pass

def item_url_scartch(url,q2):
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=3))
    s.mount('https://', HTTPAdapter(max_retries=3))
    ua = UserAgent()
    user_agent = ua.chrome
    header = {'user-agent':user_agent}
    try:
        res = requests.get(url,headers=header,timeout=8)
        page_data = bs(res.text,'lxml')
        page_data = page_data.find_all('a', class_='productInfo')
        for i in page_data:
            m_item_url = 'https://m.momoshop.com.tw' + i['href']
            q2.put(m_item_url)
    except requests.exceptions.RequestException as e:
        pass

def prd_scratch(url,temp_timeout_list,temp_list):
    #requests過久的重複請求
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=3))
    s.mount('https://', HTTPAdapter(max_retries=3))

    #fakeuseragent
    ua = UserAgent()
    user_agent = ua.chrome
    header = {'user-agent':user_agent}
    
    enter = ' 、'
    try:
        res = requests.get(url,headers=header,timeout=8)
        soup = bs(res.text,'lxml')
        momo_dict = {}

        #當遇到商品售完時結束程式
        try:
            osmGoodsName = soup.find('p',id = 'osmGoodsName')
            momo_dict['商品名稱'] = osmGoodsName.text
        except:
            print("此商品銷售一空",url)
            sys.exit(0)
        
        #價格
        price = soup.find('p','priceTxtArea').text
        price = price.replace('\n','')
        momo_dict['價格'] = price

        #表格內容 ，有些商品沒有表格，用except略過
        attributesArea = soup.find('div','attributesArea')
        try:
            attributesArea_tr = attributesArea.find_all('tr')
            prd_Spec_name = []
            prd_Spec_info = []
            for  a in attributesArea_tr:
                temp = []
                vendordetail_title = a.find('th')
                prd_Spec_name.append(vendordetail_title)
                vendordetail_content = a.find_all('li')
                for content in vendordetail_content:
                    prd_str = content.text.strip()
                    temp.append(prd_str)
                    comma = " 、"
                    prd_content = comma.join(temp)
                prd_Spec_info.append(prd_content)

            #處理沒有欄位名稱的問題
            for i in range(len(prd_Spec_name)):
                try:
                    prd_Spec_name[i].text
                except AttributeError:
                    prd_Spec_info[i-1] = prd_Spec_info[i-1] + ' 、' +prd_Spec_info[i]
                    prd_Spec_name.pop(i)
                    prd_Spec_info.pop(i)

            for i in range(len(prd_Spec_name)):
                momo_dict[prd_Spec_name[i].text] = prd_Spec_info[i]
        except:
            temp_timeout_list.put(url)
            pass
        
        #Area302區
        try:
            Area302 = soup.find_all('div','Area302')[1]
            Area302_content = []
            Area302_text = Area302.find_all('li')
            for i in Area302_text:
                Area302_content.append(i.text)
            Area302_content = enter.join(Area302_content)
            momo_dict['規格'] = Area302_content
        except IndexError:
            pass

        #Area101區以及廠商資訊處理
        Area101 = soup.find('div','Area101')
        firm = str(Area101)
        #沒有這個區域的網頁，直接pass此步驟
        try:
            Area101 = Area101.text
            Area101 = Area101.strip()
            momo_dict['詳細內容'] = Area101
        except AttributeError:
            pass

        firm_information = firm.split('<br/>')
        firm_name_list = []
        firm_address_list = []
        firm_tel_list = []
        phr_name_list = []
        phr_address_list = []
        phr_tel_list = []
        for i in firm_information:
            if "廠商名稱" in i:
                firm_name = i[i.find('：')+1:len(i)]
                firm_name_list.append(firm_name)
            elif "廠商地址" in i:
                firm_address = i[i.find('：')+1:len(i)]
                firm_address_list.append(firm_address)
            elif "廠商電話" in i:
                firm_tel = i[i.find('：')+1:len(i)]
                firm_tel_list.append(firm_tel)
            elif "製造廠名稱" in i:
                firm_name = i[i.find('：')+1:len(i)]
                firm_name_list.append(firm_name)
            elif "製造商" in i:
                firm_name = i[i.find('：')+1:len(i)]
                firm_name_list.append(firm_name)   
            elif "製造廠地址" in i:
                firm_address = i[i.find('：')+1:len(i)]
                firm_address_list.append(firm_address)
            elif "製造廠址" in i:
                firm_address = i[i.find('：')+1:len(i)]
                firm_address_list.append(firm_address)
            elif "藥商名稱" in i:
                phr_name = i[i.find('：')+1:len(i)]
                phr_name_list.append(phr_name)
            elif "藥商地址" in i:
                phr_address = i[i.find('：')+1:len(i)]
                phr_address_list.append(phr_address)
            elif "藥商諮詢專線電話" in i:
                phr_tel = i[i.find('：')+1:len(i)]
                phr_tel_list.append(phr_tel)
            elif "藥商諮詢專線" in i:
                phr_tel = i[i.find('：')+1:len(i)]
                phr_tel_list.append(phr_tel)
        
        firm_name_list = enter.join(firm_name_list)
        momo_dict['廠商名稱'] = firm_name_list

        firm_address_list = enter.join(firm_address_list)
        momo_dict['廠商地址'] = firm_address_list

        firm_tel_list = enter.join(firm_tel_list)
        momo_dict['廠商電話'] = firm_tel_list

        phr_name_list = enter.join(phr_name_list)
        momo_dict['藥商名稱'] = phr_name_list

        phr_address_list = enter.join(phr_address_list)
        momo_dict['藥商地址'] = phr_address_list
        phr_tel_list = enter.join(phr_tel_list)
        momo_dict['藥商電話'] = phr_tel_list

        temp_list.put(momo_dict)
    except requests.exceptions.RequestException:
        temp_timeout_list.put(url)
        pass

    
if __name__ == '__main__':
    driver = webdriver.Chrome(options = chrome_options)
    url = r'https://www.momoshop.com.tw/category/LgrpCategory.jsp?l_code=1299900000&mdiv=1099700000-bt_0_957_01-&ctype=B'
    driver.get(url)
    data = bs(driver.page_source,'lxml')
    driver.quit()
    Momo_URL = 'https://www.momoshop.com.tw'
    Menu_list = ['館長推薦', '新上市', '銷量排行']
    url_queue = []
    Item_url_list = []
    Item_num_list = []
    
    q_page_scratch = Queue()

    f1 = data.find_all('div', id='bt_0_996_13')[0]
    f2 = f1.find_all('tr', id='groupTr')[0]
    open_num = 1
    try:
        for index in [0,2]:  # 0:養生保健 / 3:醫材藥品
            c = f2.find_all('td')[index] 
            for y in c.find_all('li'):
                print('============= ' + y.find_all('a')[0].text + ' ============')
                tmp = y.find_all('a')[0]['href']
                category_c_url = tmp.replace('LgrpCategory', 'DgrpCategory').replace('l_code', 'd_code').replace('MgrpCategory', 'DgrpCategory').replace('m_code', 'd_code')
                item_num=0
                for index2, menu_class in enumerate(Menu_list, start=4): # 4:館長推薦 / 5:新上市 / 6:銷量排行
                    print(menu_class)
                    menu_url = category_c_url[:category_c_url.find('&')+1]+'p_orderType='+str(index2)+'&showType=chessboardType'
                    print(menu_url)
                    t1= threading.Thread(target=pages_scratch,args=(menu_url,q_page_scratch))        #開啟多線程
                    t1.start()
                t1.join()
        for i in range(q_page_scratch.qsize()):
            url_queue.append(q_page_scratch.get())

        m_page_url = []
        for cn_code in url_queue:
            category_code = cn_code.split('&')[0]
            category_code = category_code[category_code.find('='):]
            sortType = cn_code.split('&')[1]
            sortType = sortType[sortType.find('='):]
            pageNum = cn_code.split('&')[3]
            pageNum = pageNum[pageNum.find('='):]
            page_url = 'https://m.momoshop.com.tw/category.momo?cn'+category_code+'&page'+pageNum+'&sortType'+sortType+'&imgSH=fourCardType'
            m_page_url.append(page_url)
        df = pd.DataFrame(m_page_url)
        df.to_csv('url_queue.csv',index = None)

        df1 = pd.read_csv('url_queue.csv',chunksize=15)
        num = 0
        Thread_Group = []
        q_item_url = Queue()
        for chunk in df1:
            num = len(chunk)+num
            for chunk_number in range(len(chunk)):
                item_url = chunk['0'].to_list()[chunk_number]
                print(item_url)
                t2 = threading.Thread(target = item_url_scartch,args=(item_url,q_item_url))
                t2.start()
                Thread_Group.append(t2)
            for t2 in Thread_Group:
                t2.join()
            Thread_Group.clear()
            delay_choices = [2,3,4]  #延遲的秒數
            delay = random.choice(delay_choices)  #隨機選取秒數
            time.sleep(delay)  #延遲
        
        Item_url_list = []
        for i in range(q_item_url.qsize()):
            Item_url_list.append(q_item_url.get())
        
        Item_url_list_check = []
        for i in Item_url_list:
            if i not in Item_url_list_check:
                Item_url_list_check.append(i)
        
        df2 = pd.DataFrame(Item_url_list_check)
        df2.to_csv("Item_url_list.csv",index = None)

    except Exception as e:
        print('Mission Failed', str(e))
        driver.quit()
    
    Momo_item = r'C:\Users\eric0\OneDrive\桌面\實驗室相關\Item_url_list.csv'
    item_df = pd.read_csv(Momo_item,chunksize=15)
    processing = []
    all_prd_dict = Queue()
    timeout_list = Queue()
    for chunk in item_df:
        num = len(chunk) + num
        print(num)
        for i in range(len(chunk)):
            url = chunk['0'].to_list()[i]
            processing.append(threading.Thread(target = prd_scratch , args = (url,timeout_list,all_prd_dict)))
            processing[i].start()
        for i in range(len(chunk)):
            processing[i].join()
        processing.clear()
        delay_choices = [2,3,4]  #延遲的秒數
        delay = random.choice(delay_choices)  #隨機選取秒數
        time.sleep(delay)  #延遲

    product_list = []
    for i in range(all_prd_dict.qsize()):
        product_list.append(all_prd_dict.get())
    product = pd.DataFrame(list(product_list))
    product.to_csv("product.csv", index = None)

    error_prd = []
    for i in range(timeout_list.qsize()):
        error_prd.append(timeout_list.get())
    error_prd = pd.DataFrame(list(error_prd))