# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class OnlineGroceryStoreProductsItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class FoodItem(scrapy.Item):
    company = scrapy.Field()
    companyId = scrapy.Field()
    category = scrapy.Field()
    categoryId = scrapy.Field()
    subcategory = scrapy.Field()
    subcategoryId = scrapy.Field()
    label = scrapy.Field()
    price = scrapy.Field()
    image_link = scrapy.Field()
    zipCode = scrapy.Field()
    city = scrapy.Field()
