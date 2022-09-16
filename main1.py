# ライブラリの設定
from selenium import webdriver
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, ElementNotInteractableException
import pandas as pd
import tqdm
from bs4 import BeautifulSoup
import time
# ドライバーのパスを通す
import chromedriver_binary


class Main:
    def __init__(self, word, url):
        self.ave = None
        self.coincident_number = None
        self.word = word
        self.url = url
        self.url_af = None
        self.driver = None
        self.item_names = []
        self.prices = []

    def driver_set(self):
        option = Options()  # オプションを用意
        option.add_argument('--headless')  # ヘッドレスモードの設定を付与
        self.driver = webdriver.Chrome('chromedriver', options=option)
        self.driver.implicitly_wait(5)

    def into_web(self):
        self.driver.get(self.url)
        self.driver.implicitly_wait(5)
        self.driver.set_window_size('1200', '1000')
        self.driver.implicitly_wait(5)

    def search_web(self):
        try:
            search_bar_xpath = '//*[@id="gatsby-focus-wrapper"]/div/div/header/mer-navigation-top/mer-autocomplete/div[1]/mer-search-input'
            # 検索フォームxpathを格納する
            search_bar = self.driver.find_element(By.XPATH, search_bar_xpath)
            self.driver.implicitly_wait(5)
            # 検索ボックスにキーワードを格納する
            search_key = self.word
            search_bar.send_keys(search_key)
            self.driver.implicitly_wait(5)
            search_bar.send_keys(Keys.ENTER)
            self.driver.implicitly_wait(5)
            self.get_data()
        except:
            search_bar_xpath = '//*[@id="gatsby-focus-wrapper"]/div/div/header/mer-navigation-top/mer-autocomplete/div[1]/mer-search-input'
            # 検索フォームxpathを格納する
            search_bar = self.driver.find_element(By.XPATH, search_bar_xpath)
            self.driver.implicitly_wait(5)
            # 検索ボックスにキーワードを格納する
            search_key = self.word
            search_bar.send_keys(search_key)
            self.driver.implicitly_wait(5)
            sleep(5)
            search_bar.send_keys(Keys.ENTER)
            self.driver.implicitly_wait(5)
            self.get_data()


    def next_page(self, i):
        try:
            if i == 0:
                self.url_af = self.driver.current_url
                self.driver.implicitly_wait(5)
                next_page_xpath = '//*[@id="search-result"]/div/div/div/div[1]/mer-button/button'
            else:
                next_page_xpath = '//*[@id="search-result"]/div/div/div/div[1]/mer-button[2]/button'
            elem = self.driver.find_element(By.XPATH, next_page_xpath)
            self.driver.implicitly_wait(5)
            elem.click()
            self.driver.implicitly_wait(5)
            sleep(1)
            return True
        except :
            return False

    def get_data(self):
        sleep(1)
        html = self.driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, "html.parser")
        items_list = soup.find_all("li", attrs={'data-testid': 'item-cell'})

        for item in items_list:
            self.item_names.append(item.find("mer-item-thumbnail").get('item-name'))
            self.prices.append(item.find("mer-item-thumbnail").get('price'))

    def match_counts(self):
        self.coincident_number = 0
        new_search_key = self.word.lower()

        if len(self.item_names) >= 120:
            for name in self.item_names[:120]:
                new_name = name.lower()
                if new_search_key in new_name:
                    self.coincident_number += 1
        else:
            for name in self.item_names:
                new_name = name.lower()
                if new_search_key in new_name:
                    self.coincident_number += 1

    def total_price(self):
        try:
            total_price = 0
            for price in self.prices:
                new_price = int(price)
                total_price += new_price
            self.ave = total_price / len(self.prices)
        except ZeroDivisionError:
            self.ave = 0

    def store_data(self):
        if len(self.item_names) > 999:
            return [self.word, self.url, '999+', self.coincident_number, round(self.ave, 2), self.url_af]
        else:
            return [self.word, self.url, len(self.item_names), self.coincident_number, round(self.ave, 2), self.url_af]

    def pull_data(self):
        return self.item_names


def main(word, url, csv_out):
    test = Main(word, url)
    test.driver_set()
    test.into_web()
    test.search_web()
    i = 0
    while test.next_page(i) and len(test.pull_data()) < 999:
        test.get_data()
        i += 1
    test.match_counts()
    test.total_price()
    data = pd.DataFrame(test.store_data())
    csv_out = pd.concat([csv_out, data.T])
    return csv_out


if __name__ == '__main__':
    start = time.time()
    print('csvへのパスを入力してください：', end='')
    csv_path = input()
    csv_in = pd.read_csv(csv_path)
    csv_out = pd.DataFrame()
    for word, url in zip(tqdm.tqdm(csv_in['キーワード'].tolist()), csv_in['URL'].tolist()):
        csv_out = main(word, url, csv_out)
    data_csv = csv_out.rename(
        columns={0: 'キーワード', 1: 'URL', 2: '検索数', 3: '一致数', 4: '平均価格', 5: 'URL'})
    data_csv.to_csv(csv_path, index=False)
    print(f'実行時間：{round(time.time()-start, 1)}s')
