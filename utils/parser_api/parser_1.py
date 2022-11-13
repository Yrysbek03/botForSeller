import asyncio
import logging
import os
import math

from asyncpg import UniqueViolationError
from selenium import webdriver
from selenium.webdriver import Keys

from data.config import *
from loader import db, bot

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 YaBrowser/21.6.1.271 Yowser/2.5 Safari/537.36",
}


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
    # browser = webdriver.Chrome('Y:\\Python\\chromedriver\\chromedriver.exe')
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
        await asyncio.sleep(60)
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


async def check_good_rating(browser, link, first: bool):
    try:
        browser.get(link)
        await asyncio.sleep(10)  # 5
        browser.implicitly_wait(15)  # 15
        browser.set_window_size(width=1366, height=1300)
        if first:
            browser.find_element(By.XPATH, '/html/body/div[4]/div[1]/div/div[1]/div[1]/div/ul[1]/li[16]/a').click()
            browser.implicitly_wait(15)  # 15
        first = browser.find_element(By.TAG_NAME, 'tbody').find_element(By.TAG_NAME, 'tr')
        if first.find_element(By.TAG_NAME, 'td').find_element(By.TAG_NAME, 'a').text != company:
            price = first.find_element(By.CLASS_NAME, 'sellers-table__price-cell-text').text
            return int(price[:price.find('₸')].strip().replace(' ', ''))
        else:
            try:
                price = first.find_element(By.CLASS_NAME, 'sellers-table__price-cell-text').text
                price = int(price[:price.find('₸')].strip().replace(' ', ''))
                second = browser.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')[1]
                s_price = second.find_element(By.CLASS_NAME, 'sellers-table__price-cell-text').text
                s_price = int(s_price[:s_price.find('₸')].strip().replace(' ', ''))
                if s_price > price + 1000:
                    return s_price
            except Exception as ex:
                pass

    except Exception as ex:
        if 'no such element: Unable to locate element: {"method":"css selector","selector":"tbody"}' in ex.args[
            0] or 'no such element: Unable to locate element: {"method":"tag name","selector":"tbody"}' in ex.args[0]:
            pass
        else:
            try:
                if browser.find_element(By.CLASS_NAME, 'layout').get_attribute(
                        'class') == 'layout _desktop':
                    return -1
            except Exception as ex1:
                if 'Unable to locate element: {"method":"css selector","selector":".layout"}' in ex1.args[0]:
                    return -3
                logging.info(ex)
                logging.info(ex1)
                await bot.send_photo(ADMINS[0], browser.get_screenshot_as_png(),
                                     caption=f'check_good_rating: {browser.current_url}'
                                             f'\nlink: {link}'
                                             f'\n{ex.args[0]}')
            boolean = 0
            try:
                if browser.find_element(By.CLASS_NAME, 'dialogTop'):
                    boolean = -2
            except Exception:
                pass
            if boolean == -2:
                return boolean
            else:
                if 'Timed out receiving message from renderer' in ex.args[0]:
                    return -5
                else:
                    logging.info(ex)
                    await bot.send_photo(ADMINS[0], browser.get_screenshot_as_png(),
                                         caption=f'check_good_rating: {browser.current_url}'
                                                 f'\nlink: {link}'
                                                 f'\n{ex.args[0]}')


async def test(browser):
    try:
        await asyncio.sleep(5)  # 5
        browser.implicitly_wait(5)
        browser.find_element(by=By.XPATH, value='//*[@id="main-nav-offers"]/a').send_keys(Keys.ENTER)
        await asyncio.sleep(5)
        return True
    except Exception:
        return False


async def change_price_of_good(browser, slugs):
    try:
        try:
            await authenticate(browser)
            browser.set_window_size(1500, 1400)
            boolean = await test(browser)
            while not boolean:
                browser.refresh()
                boolean = await test(browser)
        except Exception as e:
            logging.info(e.args)
            return None

        previous_link = ''

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
                    try:
                        current_price = int(
                            block.find_element(By.CLASS_NAME, 'offer-managment__price-cell-price').text.replace(' ', ''))
                    except Exception as ex:
                        current_price = int(
                            block.find_element(By.CLASS_NAME, 'offer-managment__price-cell-price').text.replace(' ', '')[
                            :block.find_element(By.CLASS_NAME, 'offer-managment__price-cell-price').text.replace(' ',
                                                                                                                 '').find(
                                '...')])
                    if slug in slugs.keys():
                        good = await db.select_good(slug=slug)
                        if current_price == good[4]:
                            continue
                        elif slugs[slug] >= good[4] + good[5]:  # 4 5
                            new_price = str(slugs[slug] - good[5])  # 5
                        else:
                            new_price = good[4]  # 4

                        buttons = browser.find_elements(By.CSS_SELECTOR, 'a[class="icon _medium _edit"]')
                        element = WebDriverWait(browser, 5).until(EC.element_to_be_clickable(
                            buttons[index]))
                        element.click()
                        browser.implicitly_wait(10)

                        checkbox = browser.find_element(By.ID, 'checkbox-control-price')

                        checkbox.click()
                        await asyncio.sleep(.3)

                        # checkbox = browser.find_element(By.ID, 'checkbox-control-pickuppoint')
                        # checkbox.click()
                        # await asyncio.sleep(.2)

                        textarea = browser.find_element(By.CSS_SELECTOR, 'input[type="text"]')

                        textarea.send_keys(new_price)
                        await asyncio.sleep(0.3)

                        previous_link = browser.current_url

                        browser.find_element(By.CLASS_NAME, 'button').click()
                        slugs.pop(slug)
                        await asyncio.sleep(2)  # 2

                        browser.implicitly_wait(2)
                        try:
                            if previous_link == browser.current_url and browser.find_element(By.CSS_SELECTOR, 'div[class="ks-gwt-dialog _small g-ta-c"]'):
                                browser.find_element(By.CLASS_NAME, 'button[class="gwt-Button button"]').click()
                        except Exception as e:
                            logging.info(e.args)
                        await asyncio.sleep(2)

                        have_other = True
                        break
                if current == pages and index + 1 == len(blocks):
                    break

                if not have_other:
                    await next_page(browser)

            except Exception as ex:
                if (ex.args[0] == "invalid literal for int() with base 10: ''"):
                    pass
                else:
                    await bot.send_photo(ADMINS[0], browser.get_screenshot_as_png(),
                                         caption=f'{ex.args}')
                    logging.info(ex.args[0])  # invalid literal for int() with base 10: ''
    except Exception as ex5:
        await bot.send_photo(ADMINS[0], browser.get_screenshot_as_png(),
                             caption=f'{ex5.args}')
        logging.info(ex5.args)


async def control_ratings(goods):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    browser = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    # browser = webdriver.Chrome('Y:\\Python\\chromedriver\\chromedriver.exe')
    to_be_change = {}

    try:
        first = True
        finished = True
        for index, good in enumerate(goods):
            try:
                first_price = await check_good_rating(browser, good[2], first)  # 2
            except Exception as e:
                logging.info(e.args)
                logging.info("111")
            if index == 0:
                first = False
            if first_price:
                try:
                    if first_price == -5 or first_price == -1 or first_price == -2 or first_price == -3:
                        await bot.send_message(ADMINS[0], f'returned {first_price}')
                        finished = False
                        break
                    to_be_change[good[3]] = first_price
                except Exception as e:
                    logging.info(e.args)
                    logging.info("222")
            await asyncio.sleep(2)
        if len(to_be_change) > 0:
            try:
                await change_price_of_good(browser, to_be_change)
            except Exception as e:
                logging.info(e.args)
                logging.info("333")
        if finished:
            await bot.send_message(ADMINS[0], 'Control rating was finished')
        else:
            await bot.send_message(ADMINS[0], 'Control rating was finished with Timeout')

    except Exception as ex:
        if 'Message: unknown error: session deleted because of page crash' in ex.args[0]:
            logging.info(ex)
            return None
        else:
            if 'invalid session id' in ex.args[0] or 'Can\'t parse entities: unsupported start tag' in ex.args[0]:
                await bot.send_message(ADMINS[0], 'Перезапустите бота')
                await bot.send_message(889962936, 'Перезапустите бота')
            logging.info(ex.args)
            return None
    # finally:
    #     try:
    #         browser.close()
    #         browser.quit()
    #     except Exception as ex:
    #         pass
