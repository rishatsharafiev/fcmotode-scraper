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
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException

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

    def get_category_max_page(self, category_url):
        driver = self.driver
        try:
            driver.get(category_url)

            initial_wait = WebDriverWait(driver, 60*60)
            initial_wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.CategoryList'))
            )

            categories = driver.find_elements_by_css_selector('span[itemprop="itemListElement"] span[itemprop="name"]')
            self.categories = [category.text for category in categories][1:]

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

    def get_product_links(self, category_url):
        driver = self.driver
        end_page_id = self.get_category_max_page(category_url)
        page_size = 60
        links = []

        try:
            time.sleep(0.5)
            for page in range(1, end_page_id + 1):
                page_url = 'https://www.fc-moto.de/epages/fcm.sf/ru_RU/?ViewAction=View&ObjectID=2693575&PageSize={page_size}&Page={page}'.format(page_size=page_size, page=page)
                driver.get(page_url)

                try:
                    initial_wait = WebDriverWait(driver, 3*60)
                    initial_wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.CategoryList'))
                    )

                    products = driver.find_elements_by_css_selector('.InfoArea .Headline a[itemprop="url"]')
                    product_links = [product.get_attribute('href') for product in products]
                    links.extend(product_links)

                    time.sleep(0.5)
                except (NoSuchElementException, TimeoutException):
                    print('--> Page stalled')

        except Exception as e:
            self.logger.exception(str(e))

        return list(set(links))

    def get_element_by_css_selector(self, selector):
        driver = self.driver
        try:
            element = driver.find_element_by_css_selector(selector)
        except (NoSuchElementException, TimeoutException):
            element = None
        return element

    def get_elements_by_css_selector(self, selector):
        driver = self.driver
        try:
            elements = driver.find_elements_by_css_selector(selector)
        except (NoSuchElementException, TimeoutException):
            elements = None
        return elements

    def get_product(self, product_url):
        driver = self.driver
        product = {}
        try:
            driver.get(product_url)
            try:
                initial_wait = WebDriverWait(driver, 3*60)
                initial_wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.ContentAreaWrapper'))
                )

                common_wait = WebDriverWait(driver, 3*60)

                # 'Наименование',
                name = self.get_element_by_css_selector('.ICProductVariationArea [itemprop="name"]')
                name = name.text if name else ''

                # 'Производитель',
                manufacturer = self.get_element_by_css_selector('.ICProductVariationArea [itemprop="manufacturer"]')
                manufacturer = manufacturer.text if manufacturer else ''

                # 'Цвета',
                colors = self.get_element_by_css_selector('.ICVariationSelect .Bold.Value')
                colors = colors.text if colors else ''

                # 'Все размеры',
                all_size = self.get_elements_by_css_selector('.ICVariationSelect li > button')
                all_size = set([size.text for size in all_size] if all_size else [])

                # 'Неактивные размеры',
                disabled_size = self.get_elements_by_css_selector('.ICVariationSelect li.disabled > button')
                disabled_size = set([size.text for size in disabled_size] if disabled_size else [])

                # 'Активные размеры',
                active_size = all_size.difference(disabled_size)

                # 'Цена',
                price = self.get_element_by_css_selector('.PriceArea .Price')
                price = price.text if price else ''
                price_cleaned = price.replace('руб.', '').replace(' ', '').replace(',', '.')

                # 'Фотография'
                front_picture = self.get_element_by_css_selector('#ICImageMediumLarge')
                front_picture = front_picture.get_attribute('src') if front_picture else ''

                activate_second_picture = self.get_element_by_css_selector('#ProductThumbBar > li:nth-child(2) > img')

                if activate_second_picture:
                    activate_second_picture.click()
                    time.sleep(3)
                    back_picture = self.get_element_by_css_selector('#ICImageMediumLarge')
                back_picture = back_picture.get_attribute('src') if activate_second_picture and back_picture else ''

                # 'Описание'
                description = self.get_element_by_css_selector('.description[itemprop="description"]')
                description_text = description.text if description else ''
                description_html = description.get_attribute('innerHTML') if description else ''

                product = {
                    'name': name,
                    'manufacturer': manufacturer,
                    'colors': colors,
                    'all_size': all_size,
                    'disabled_size': disabled_size,
                    'active_size': active_size,
                    'price': price,
                    'price_cleaned': price_cleaned,
                    'front_picture': front_picture,
                    'back_picture': back_picture,
                    'description_text': description_text,
                    'description_html': description_html,

                }

            except (NoSuchElementException, TimeoutException):
                print('--> Product stalled')

        except Exception as e:
            self.logger.exception(str(e))

        return product

    def test_main(self):
        try:
            category_url = 'https://www.fc-moto.de/ru/Mototsikl/Mototsiklitnaya-odizhda/Mototsiklitnyrui-kurtki/Kozhanyrui-mototsiklitnyrui-kurtki'
            product_urls = self.get_product_links(category_url)
            for product_url in product_urls:
                print(self.get_product(product_url))
        finally:
            self.driver.quit()

if __name__ == '__main__':
    unittest.main()
