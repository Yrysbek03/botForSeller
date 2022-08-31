import asyncio
import json
import logging
import os
import pathlib
import math

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asyncpg import UniqueViolationError
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from data.config import *
from loader import dp, db, bot

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 YaBrowser/21.6.1.271 Yowser/2.5 Safari/537.36",
}


def get_browser(r=0):
    if r == 0:
        return webdriver.Chrome('Y:\\Python\\z_own_project\\kaspiparser\\chromedriver_win32\\chromedriver.exe')
    else:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        return webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)


async def parse_goods(browser, pages):
    count = 0
    for i in range(pages):  # pages
        browser.implicitly_wait(10)
        blocks = browser.find_elements(By.CLASS_NAME, "offer-managment__product-cell-inner")
        for block in blocks:
            a_s = block.find_element(By.CLASS_NAME, 'offer-managment__product-cell-link')
            try:
                await db.insert_good(name=a_s.text, link=a_s.get_attribute('href'),
                                     slug=
                                     block.find_elements(By.CLASS_NAME,
                                                         'offer-managment__product-cell-meta-text')
                                     [1].text)
                count += 1
            except UniqueViolationError:
                pass
        await next_page(browser)

    browser.close()
    return count


async def authenticate(browser):
    browser.get('https://kaspi.kz/merchantcabinet/')
    browser.implicitly_wait(2)

    username_input = browser.find_element(By.NAME, 'username')
    username_input.clear()
    username_input.send_keys(username)

    await asyncio.sleep(.3)

    password_input = browser.find_element(By.NAME, 'password')
    password_input.clear()
    password_input.send_keys(password)

    await asyncio.sleep(2)
    password_input.send_keys(Keys.ENTER)
    # await asyncio.sleep(.5)
    # browser.implicitly_wait(2)


async def next_page(browser: webdriver.Chrome):
    button = browser.find_element(By.CSS_SELECTOR, 'img[aria-label="Next page"]')
    browser.set_window_size(width=1366, height=1300)
    browser.implicitly_wait(10)
    ActionChains(browser).move_to_element(button).click(button).perform()


async def parse_all_goods():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    browser = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    # browser = webdriver.Chrome('Y:\\Python\\z_own_project\\kaspiparser\\chromedriver_win32\\chromedriver.exe')
    try:
        await authenticate(browser)
        boolean = await test(browser)
        while not boolean:
            browser.refresh()
            boolean = await test(browser)
        browser.set_window_size(1500, 1400)
        # browser.execute_script('let l = document.querySelector("#jvlabelWrap");l.style.top = "0";')
        await asyncio.sleep(5)
        browser.implicitly_wait(5)
        # Move to goods page
        browser.find_element(by=By.XPATH, value='//*[@id="main-nav-offers"]/a').send_keys(Keys.ENTER)
        await asyncio.sleep(10)
        count = 0
        pages = math.ceil(int(browser.find_element(By.CLASS_NAME, 'gwt-HTML').text[
                              browser.find_element(By.CLASS_NAME, 'gwt-HTML').text.rfind(' '):].strip()) / 10)
        # Start parsing
        for i in range(pages):
            browser.implicitly_wait(10)
            await asyncio.sleep(2)
            blocks = browser.find_elements(By.CLASS_NAME, "offer-managment__product-cell-inner")
            for block in blocks:
                a_s = block.find_element(By.CLASS_NAME, 'offer-managment__product-cell-link')
                try:
                    await db.insert_good(name=a_s.text, link=a_s.get_attribute('href'),
                                         slug=
                                         block.find_elements(By.CLASS_NAME, 'offer-managment__product-cell-meta-text')
                                         [1].text)
                    count += 1
                except UniqueViolationError as ex:
                    print(ex)

            await next_page(browser)

        browser.close()
        return count
    except Exception as ex:
        logging.info(ex)
        browser.close()
        browser.quit()


async def check_good_rating(browser, link):
    try:
        browser.get(link)
        # await asyncio.sleep(2)
        browser.implicitly_wait(100)
        browser.set_window_size(width=1366, height=1300)
        first = browser.find_element(By.TAG_NAME, 'tbody').find_element(By.TAG_NAME, 'tr')
        if first.find_element(By.TAG_NAME, 'td a').text != company:
            price = first.find_element(By.CLASS_NAME, 'sellers-table__price-cell-text').text
            return int(price[:price.find('₸')].strip().replace(' ', ''))
    except Exception as ex:
        logging.info(link)
        logging.info(ex)
        pass


async def test(browser):
    try:
        await asyncio.sleep(5)
        browser.implicitly_wait(5)
        browser.find_element(by=By.XPATH, value='//*[@id="main-nav-offers"]/a').send_keys(Keys.ENTER)
        await asyncio.sleep(5)
        return True
    except Exception:
        return False


async def change_price_of_good(browser, slugs):
    await authenticate(browser)
    browser.set_window_size(1500, 1400)
    boolean = await test(browser)
    while not boolean:
        browser.refresh()
        boolean = await test(browser)

    while True:
        try:
            await asyncio.sleep(5)
            browser.implicitly_wait(10)

            browser.execute_script('let l = document.querySelector("#jvlabelWrap");l.style.top = "0";')

            text_page = browser.find_element(By.CLASS_NAME, 'gwt-HTML').text
            current = int(text_page[text_page.find('-') + 1:text_page.find(' ')])
            pages = int(text_page[text_page.rfind(' '):].strip())
            blocks = browser.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
            have_other = False
            index = -1
            for block in blocks:
                index += 1
                slug = block.find_elements(By.CLASS_NAME, 'offer-managment__product-cell-meta-text')[1].text
                if slug in slugs.keys():
                    buttons = browser.find_elements(By.CSS_SELECTOR, 'a[class="icon _medium _edit"]')
                    element = WebDriverWait(browser, 5).until(EC.element_to_be_clickable(
                        buttons[index]))
                    element.click()
                    browser.implicitly_wait(10)

                    checkbox = browser.find_element(By.ID, 'checkbox-control-price')

                    checkbox.click()
                    await asyncio.sleep(.3)

                    checkbox = browser.find_element(By.ID, 'checkbox-control-pickuppoint')
                    checkbox.click()
                    await asyncio.sleep(.2)

                    textarea = browser.find_element(By.CSS_SELECTOR, 'input[type="text"]')
                    good = await db.select_good(slug=slug)
                    if slugs[slug] >= good[4] + good[5]:  # 4 5
                        new_price = str(slugs[slug] - good[5])  # 5
                    else:
                        new_price = good[4]  # 4

                    textarea.send_keys(new_price)
                    await asyncio.sleep(0.3)

                    browser.find_element(By.CLASS_NAME, 'button').click()
                    slugs.pop(slug)
                    await asyncio.sleep(2)
                    have_other = True
                    break
            if current == pages and index + 1 == len(blocks):
                break

            if not have_other:
                await next_page(browser)

        except Exception as ex:
            logging.info(ex)


async def control_ratings():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    browser = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    # browser = webdriver.Chrome('Y:\\Python\\z_own_project\\kaspiparser\\chromedriver_win32\\chromedriver.exe')
    to_be_change = {}
    try:
        goods = await db.select_goods_active()
        for good in goods:
            first_price = await check_good_rating(browser, good[2])  # 2
            if first_price:
                to_be_change[good[3]] = first_price
            await asyncio.sleep(1.5)
        await change_price_of_good(browser, to_be_change)

        browser.close()

    except Exception as ex:
        logging.info(ex)
        browser.close()
        browser.quit()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(control_ratings())
