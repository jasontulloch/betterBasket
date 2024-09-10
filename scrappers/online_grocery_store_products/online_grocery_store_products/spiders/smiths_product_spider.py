import scrapy
from time import sleep
import undetected_chromedriver as uc
from scrapy.selector import Selector
from ..items import FoodItem
import json
import os
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

class SmithsProductSpider(scrapy.Spider):
    name = "smiths-products"
    allowed_domains = ["smithsfoodanddrug.com"]

    def __init__(self):
        self.next_page_no = 1
        self.urls_length = 0
        self.current_url_index = 0

        # Get the correct path to walmart_urls.json
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_file_path = os.path.join(base_path, 'urls', 'smiths_urls.json')

        # Load URLs from JSON
        with open(json_file_path, 'r') as file:
            self.urls = json.load(file)  # Assuming it's a list of objects with 'path' key

        with open('control.txt', 'w') as t:
            pass

    def start_requests(self):
        # Loop through the URLs from the JSON file and create requests
        for url_object in self.urls:
            url = url_object['path']  # Extract the 'path' from each object
            category = url_object.get('category', 'No Category')
            categoryId = url_object.get('categoryId', 'No Category ID')
            subcategory = url_object.get('subcategory', 'No Subcategory')
            subcategoryId = url_object.get('subcategoryId', 'No Subcategory ID')
            company = url_object.get('company', 'No Company')
            companyId = url_object.get('companyId', 'No Company ID')
            self.urls_length += 1

            yield scrapy.Request(url=url, callback=self.parse, meta={'category': category, 'categoryId': categoryId, 'subcategory': subcategory, 'subcategoryId': subcategoryId, 'company': company, 'companyId': companyId})

    def get_next_page_link(self, url, next_page_no):

        # Parse the current URL
        parsed_url = urlparse(url)

        # Extract the query parameters
        query_params = parse_qs(parsed_url.query)

        # Update the "page" parameter to the next page number
        query_params['page'] = [str(next_page_no)]

        # Rebuild the query string
        new_query_string = urlencode(query_params, doseq=True)

        # Rebuild the URL with the updated query string
        new_url = urlunparse(parsed_url._replace(query=new_query_string))

        self.current_url_index += 1

        return new_url

    def parse(self, response):

        # Retrieve the category and subcategory from the meta data
        category = response.meta.get('category')
        categoryId = response.meta.get('categoryId')
        subcategory = response.meta.get('subcategory')
        subcategoryId = response.meta.get('subcategoryId')
        company = response.meta.get('company')
        companyId = response.meta.get('companyId')
        city = ''
        zipCode = ''

        while True:
            options = uc.ChromeOptions()
            driver = uc.Chrome(enable_cdp_events=True)
            driver.implicitly_wait(15)
            driver.maximize_window()
            driver.get(response.url)

            sleep(3)

            for _ in range(3):
                page_height = driver.execute_script('return document.body.scrollHeight')
                driver.execute_script(f'window.scrollTo(0, {page_height});')
                sleep(2)

            sleep(3)

            page = driver.page_source
            driver.quit()

            my_response = Selector(text=page)

            # Extract the location info containing city and zip code
            if my_response.xpath("//button[contains(@class, 'PostalCodeSearchBox--drawer') and @data-testid='PostalCodeSearchBox-drawer']//span[@class='kds-Text--s']/text()") is not None:
                zipCode = my_response.xpath(
                    "//button[contains(@class, 'PostalCodeSearchBox--drawer') and @data-testid='PostalCodeSearchBox-drawer']//span[@class='kds-Text--s']/text()"
                ).get()

            if my_response.xpath("//h2[contains(@class, 'SearchGridHeader--products') and @data-testid='SearchGridHeader-products']/text()") is not None:
                items_count = my_response.xpath(
                    "//h2[contains(@class, 'SearchGridHeader--products') and @data-testid='SearchGridHeader-products']/text()"
                ).re_first(r'(\d+)')

                # Convert the result to an integer
                if items_count:
                    items_count = int(items_count)

            food_items = my_response.css('div[data-testid="product-grid-container"]')

            with open('control.txt', 'a') as t:
                t.write(f'{len(food_items)} items for page {self.next_page_no}\n')

            for index, item in food_items:
                food_item = FoodItem()

                if item.xpath("//div[contains(@class, 'ProductCard') and @data-testid='product-card-0']//span[@data-testid='cart-page-item-description']/text()").get() is not None:
                    food_item['label'] = item.xpath("//div[contains(@class, 'ProductCard') and @data-testid='product-card-0']//span[@data-testid='cart-page-item-description']/text()").get()
                else:
                    food_item['label'] = 'No Name Information'

                if item.xpath("//div[contains(@class, 'ProductCard') and @data-testid='product-card-0']//data[@data-testid='cart-page-item-unit-price']/@value").get() is not None:
                    food_item['price'] = float(item.xpath("//div[contains(@class, 'ProductCard') and @data-testid='product-card-0']//data[@data-testid='cart-page-item-unit-price']/@value"))
                else:
                    food_item['price'] = 'No Price Information'

                if item.css("//div[contains(@class, 'ProductCard') and @data-testid='product-card-0']//img[@data-testid='cart-page-item-image-loaded']/@src").attrib['src'] is not None:
                    food_item['image_link'] = item.css("//div[contains(@class, 'ProductCard') and @data-testid='product-card-0']//img[@data-testid='cart-page-item-image-loaded']/@src").attrib['src']
                else:
                    food_item['image_link'] = 'No Image Link Information'

                food_item['category'] = category
                food_item['categoryId'] = categoryId
                food_item['subcategory'] = subcategory
                food_item['subcategoryId'] = subcategoryId
                food_item['company'] = company
                food_item['companyId'] = companyId
                food_item['city'] = city
                food_item['zipCode'] = zipCode

                yield food_item

            self.next_page_no += 1

            next_page_link = self.get_next_page_link(response.url, self.next_page_no)

            if self.next_page_no <= 1:
                yield response.follow(next_page_link, callback=self.parse,
                                      meta={'category': category, 'categoryId': categoryId, 'subcategory': subcategory, 'subcategoryId': subcategoryId, 'company': company, 'companyId': companyId, 'city': city, 'zipCode': zipCode})
            elif self.urls_length != self.current_url_index:
                self.next_page_no = 1

            break
