import requests
import csv
import json
import pprint
import string
import random
from uuid import uuid4
import pandas as pd
import robobrowser
import re
import os
import sys
import time
import requests
import pprint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from io import StringIO


def download_hare_file():
    # curl -X POST --header 'X-OpenAM-Username: scott@maiawealth.com' --header 'X-OpenAM-Password: <password>'
    # https://sso.morningstar.com/sso/json/msusers/authenticate?rme=true -v
    browser = robobrowser.RoboBrowser()
    browser.open('https://msi.morningstar.com/Login.aspx')
    form = browser.get_forms()[0]
    form.fields['email_addr'].value = 'scott@maiawealth.com'
    form.fields['password'].value = 'DoWork2511'
    browser.submit_form(form)

    browser.open('https://msi.morningstar.com/Export.aspx?type=HarePort')
    return browser.response.text


def prepare_upload_file(hare_file):
    f = StringIO(hare_file)
    reader = csv.reader(f, delimiter=',')
    df = pd.DataFrame(data=[row for row in reader])
    new_header = df.iloc[0] #grab the first row for the header
    df = df[1:] #take the data less the header row
    df.columns = new_header #set the header row as the df header

    #print(df)
    df = df.ix[:, ['Ticker', '% of Portfolio']]
    df.insert(0, 'Model Name', 'Hare')
    df.insert(1, 'Model Description', '')
    df.rename(columns={'Ticker': 'Security Symbol',
                       '% of Portfolio': 'Target Percent'}, copy=False, inplace=True)
    df.insert(4, 'Minimum Percent', 'global')
    df.insert(5, 'Maximum Percent', 'global')

    df['Target Percent'] = df['Target Percent'].apply(lambda x: round(float(x), 1))
    total = sum(df['Target Percent'])

    modelmap = {}
    target_sum = 0
    cash_index = None
    for index, row in df.iterrows():
        symbol = row['Security Symbol']
        target_pct = row['Target Percent']
        if not row['Security Symbol']:
            symbol = '$CASH'
            cash_index = index
            df.at[index, 'Security Symbol'] = symbol
        else:
            target_sum += target_pct

        modelmap[symbol] = {'targetPercent': target_pct,
                            'minPercent': 'global', 'maxPercent': 'global', 'isValidRebalBand': True}

    cash_pct = round(100.0 - target_sum, 1)
    assert target_sum + cash_pct == 100.0, f'Target percents total {target_sum + cash_pct}'
    modelmap['$CASH']['targetPercent'] = cash_pct
    df.at[cash_index, 'Target Percent'] = cash_pct
    model = {
        "modelsToAdd": [
            {
                "modelId": 12842995,
                "modelName": "Hare",
                "versionId": 1,
                "securityWithTargetPerc": {},
                "secRebalBandsMap": modelmap,
                "isBlendedModel": False,
                "isExistingModel": True,
                "isUnderAllocatedModel": False,
                "modelTargetPerc": 100,
                "decimalImportAllowed": True,
                "duplicateSecurity": False,
                "isTargetNegative": False,
                "isDraft": False,
                "isSubscribedModel": False
    }]}

    return df.to_csv(index=False), json.dumps(model)


def get_upload_cookies():
    username = 'smarek'
    password = '2$M@QMyDi!Z6Z5'
    chrome_options = Options()
    #chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(executable_path=os.path.abspath("../chromedriver"), chrome_options=chrome_options)
    driver.implicitly_wait(5)
    driver.get("https://www.advisorservices.com/")
    driver.find_element_by_name('USERID').clear()
    driver.find_element_by_name('USERID').send_keys(username)
    driver.find_element_by_id('password').clear()
    driver.find_element_by_id('password').send_keys(password)
    driver.find_element_by_id('loginBtn').send_keys(Keys.ENTER)
    driver.switch_to.frame(0)
    driver.find_element(By.XPATH, '//*[@id="pageContainer"]/div[1]/table/tbody/tr/td[2]/table/tbody/tr/td[1]/a[7]').click()
    WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
    while True:
        try:
            driver.switch_to.window('irebal')
            break
        except:
            time.sleep(0.1)

    print('Looking for loading overlay')
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, 'loading')))
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'CreateAndConfigure_text')))
    print('Overlay finished')
    #driver.get('https://irebal-ct.advisorservices.com/irebal/model/inventory')
    #driver.find_element_by_id('btnImportModel_label').click()
    cookies = driver.get_cookies()
    #time.sleep(1000000)
    driver.close()
    pprint.pprint(cookies)
    cookie_string = '; '.join([f'{x["name"]}={x["value"]}' for x in cookies])
    return cookie_string


def upload_csv(cookie_string, csv_data):
    boundary = '---------------------------' + ''.join(random.choice(string.digits) for _ in range(27))
    payload = f"""--{boundary}
Content-Disposition: form-data; name="securityMdlDt"

on
--{boundary}
Content-Disposition: form-data; name="modelFileUpload"

upload.csv
--{boundary}
Content-Disposition: form-data; name="ImportModel"; filename="upload.csv"
Content-Type: text/csv

{csv_data}
--{boundary}--
"""
    headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Length': str(len(payload)),
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Cookie': cookie_string,
            'Host': 'irebal-ct.advisorservices.com',
            'Origin': 'https://irebal-ct.advisorservices.com',
            'Referer': 'https://irebal-ct.advisorservices.com/irebal/model/inventory',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36',
    }
    print('Making request')

    for k, v in headers.items():
        print(f'{k}:{v}')
    print(f'Payload:\n{payload}')
    resp = requests.request('POST', 'https://irebal-ct.advisorservices.com/irebal/model/import=model', headers=headers,
                            data=payload)
    print(resp.text)
    print(resp)


def upload_json(cookie_string, json_data):
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json; charset=UTF-8',
        'Cookie': cookie_string,
        'Host': 'irebal-ct.advisorservices.com',
        'Origin': 'https://irebal-ct.advisorservices.com',
        'Referer': 'https://irebal-ct.advisorservices.com/irebal/model/inventory',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    print('Making request')
    for k, v in headers.items():
        print(f'{k}:{v}')
    resp = requests.request('POST', 'https://irebal-ct.advisorservices.com/irebal/model/saveimport', headers=headers,
                            data=json_data)
    print(resp.text)
    print(resp)


hare_file = download_hare_file()
csv_data, json_data = prepare_upload_file(hare_file)
cookie_data = get_upload_cookies()
upload_csv(cookie_data, csv_data)
upload_json(cookie_data, json_data)
