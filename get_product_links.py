# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
DOTENV_PATH = os.path.join(BASE_PATH, '.env')
load_dotenv(DOTENV_PATH)

import logging, time
import unittest, json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display
from selenium.common.exceptions import WebDriverException, NoSuchElementException

class TestFCMotoDESite(unittest.TestCase):

    def setUp(self):
        # initialize logget
        self.logger = logging.getLogger(__name__)
        logger_handler = logging.FileHandler(os.path.join(BASE_PATH, '{}.log'.format(__file__)))
        logger_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        logger_handler.setFormatter(logger_formatter)
        self.logger.addHandler(logger_handler)
        self.logger.setLevel(logging.WARNING)
        self.logger.propagate = False

        # self.display = Display(visible=0, size=(1024,800))
        # self.display.start()

        self.current_path = os.path.dirname(os.path.realpath(__file__))
        self.chromedriver_path = os.path.join(self.current_path, 'chromedriver')
        self.driver = webdriver.Chrome(self.chromedriver_path)

    def get_page_max(self):
        driver = self.driver
        try:
            page_url = 'https://www.fc-moto.de/ru/Mototsikl/Mototsiklitnaya-odizhda/Mototsiklitnyrui-kurtki/Kozhanyrui-mototsiklitnyrui-kurtki'
            driver.get(page_url)

            initial_wait = WebDriverWait(driver, 60*60)
            initial_wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.CategoryList'))
            )

            categories = driver.find_elements_by_css_selector('span[itemprop="itemListElement"] span[itemprop="name"]')
            categories = [category.text for category in categories][1:]

            pages = driver.find_elements_by_css_selector('li > a[rel="next"]')
            pages = [page.text for page in pages]
            if len(pages) > 1:
                end_page_id = pages[-2]
            else:
                end_page_id = 1
        except Exception as e:
            self.logger.exception(str(e))
            end_page_id = 0
        return int(end_page_id)

    def test_get_offers_list(self):
        driver = self.driver
        end_page_id = self.get_page_max()
        page_size = 60
        links = []

        try:
            time.sleep(1)
            for page in range(1, end_page_id + 1):
                page_url = 'https://www.fc-moto.de/epages/fcm.sf/ru_RU/?ViewAction=View&ObjectID=2693575&PageSize={page_size}&page={page}'.format(page_size=page_size, page=page)

                print('page: ', page)
                driver.get(page_url)

                initial_wait = WebDriverWait(driver, 60*60)
                initial_wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.CategoryList'))
                )

                products = driver.find_elements_by_css_selector('.InfoArea .Headline a[itemprop="url"]')
                product_links = [product.get_attribute('href') for product in products]
                links.append(product_links)
                time.sleep(1)

            with open('links.json', 'w+') as write_file:
                write_file.write(json.dumps(product_links))

        except Exception as e:
            self.logger.exception(str(e))
        finally:
            driver.quit()


if __name__ == '__main__':
    unittest.main()

### links parser
# page_url = 'https://www.fc-moto.de/ru/Mototsikl/Mototsiklitnaya-odizhda/Mototsiklitnyrui-kurtki/Kozhanyrui-mototsiklitnyrui-kurtki'
# driver.get(page_url)

# initial_wait = WebDriverWait(driver, 60*60)
# initial_wait.until(
#     EC.presence_of_element_located((By.CSS_SELECTOR, '.CategoryList'))
# )

# categories = driver.find_elements_by_css_selector('span[itemprop="itemListElement"] span[itemprop="name"]')
# categories = [category.text for category in categories][1:]

# pages = driver.find_elements_by_css_selector('li > a[rel="next"]')
# pages = [page.text for page in pages]
# if len(pages) > 1:
#     end_page_id = pages[-2]
# else:
#     end_page_id = 1
