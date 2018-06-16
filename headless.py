import os
import sys
import requests
import pprint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

chrome_options = Options()
#chrome_options.add_argument("--headless")

driver = webdriver.Chrome(executable_path=os.path.abspath("../chromedriver"), chrome_options=chrome_options)
driver.implicitly_wait(5)
driver.get("https://www.advisorservices.com/")
driver.find_element_by_name('USERID').clear()
driver.find_element_by_name('USERID').send_keys('smarek')
driver.find_element_by_id('password').clear()
driver.find_element_by_id('password').send_keys('2$M@QMyDi!Z6Z5')
driver.find_element_by_id('loginBtn').send_keys(Keys.ENTER)
driver.switch_to.frame(0)
driver.find_element(By.XPATH, '//*[@id="pageContainer"]/div[1]/table/tbody/tr/td[2]/table/tbody/tr/td[1]/a[7]').click()
WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
driver.switch_to.window('irebal')
print('Looking for loading overlay')
WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, 'loading')))
WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'CreateAndConfigure_text')))
print('Overlay finished')
#driver.get('https://irebal-ct.advisorservices.com/irebal/model/inventory')
#driver.find_element_by_id('btnImportModel_label').click()
cookies = driver.get_cookies()
pprint.pprint(cookies)
headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundaryH1tyvhqnxXElLQ0Z',
        'Cookie': '; '.join([f'{x["name"]}={x["value"]}' for x in cookies]),
        'Host': 'irebal-ct.advisorservices.com',
        'Origin': 'https://irebal-ct.advisorservices.com',
        'Referer': 'https://irebal-ct.advisorservices.com/irebal/model/inventory',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36',
}
print('Making request')
pprint.pprint(headers)
resp = requests.request('POST', 'https://irebal-ct.advisorservices.com/irebal/model/import=model', headers=headers, data='blah')
print(resp.text)
print(resp)
sys.exit()
