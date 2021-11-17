# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json


class Aiqichatest2Pipeline:
    conn = None

    def open_spider(self, spider):
        print('开始爬虫.....')
        try:
            self.browser = spider.browser
        except:
            print("browser为空")

        # self.conn = spider.conn

    def process_item(self, item, spider):
        insertType = item['insertType']
        if insertType == 'stockInfo':
            stockInfo = item['stockInfo']
            print(stockInfo['companyName'])

        # elif insertType == 'invest':
        #     print('***********invest')
        #
        # elif insertType == 'basicHold':
        #     print('***********basicHold')
        #
        # elif insertType == 'equitypledge':
        #     print('***********equitypledge')
        # else:
        #     print('***********other')
        return item

    def close_spider(self, spider):
        print('结束爬虫.....')
        try:
            self.browser.quit()
        except:
            print("browser为空")
