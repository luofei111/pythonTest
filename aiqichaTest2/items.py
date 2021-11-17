# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Aiqichatest2Item(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class StockCompanyItem(scrapy.Item):
    stockInfo = scrapy.Field()


# 股权穿透
class StockInfoItem(scrapy.Item):
    stockInfo = scrapy.Field()
    insertType = scrapy.Field()


# 对外投资
class InvestItem(scrapy.Item):
    invest = scrapy.Field()
    insertType = scrapy.Field()


# 控股企业
class HoldItem(scrapy.Item):
    basicHold = scrapy.Field()
    insertType = scrapy.Field()


class ReportItem(scrapy.Item):
    title = scrapy.Field()
    date = scrapy.Field()
    url = scrapy.Field()
    industryCode = scrapy.Field()
