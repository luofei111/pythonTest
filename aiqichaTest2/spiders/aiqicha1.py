import datetime
import random

import scrapy

import json

from aiqichaTest2.items import ReportItem

from redis import Redis

from aiqichaTest2.DateUtils import DateUtils


class Aiqicha1Spider(scrapy.Spider):
    name = 'aiqicha1'
    # allowed_domains = ['www.baidu.com']

    start_urls = ['http://reportapi.eastmoney.com/report/bk?bkCode=016']

    # 创建redis链接对象
    conn = Redis(host='127.0.0.1', port=6379, decode_responses=True, charset='utf-8')

    # 解析行业列表
    def parse(self, response):
        cat_obj = json.loads(response.text)

        # 行业列表
        industry_list = cat_obj['data']

        # 存储行业列表
        for industry in industry_list:
            ex = self.conn.sadd('industryList', json.dumps(industry))

            # if ex == 1:
            #     print('该行业未保存----------->' + industry['bkCode'])
            # else:
            #     print('该行业已保存----------->' + industry['bkCode'])

        # 查询报告列表
        my_industry = random.choice(industry_list)

        industryCode = my_industry['bkCode']

        beginTime = DateUtils.getlastServenDate(self)

        endTime = datetime.date.today()

        print('industryCode------------>' + industryCode)

        next_url = 'http://reportapi.eastmoney.com/report/list?industryCode=' + industryCode + '&pageSize=50&beginTime=' + str(
            beginTime) + '&endTime=' + str(endTime) + '&pageNo=1&qType=1'

        yield scrapy.Request(url=next_url, meta={"industryCode": industryCode}, callback=self.parser_industry_report)

    # 解析研报列表
    def parser_industry_report(self, response):
        report_obj = json.loads(response.text)

        report_list = report_obj['data']

        if len(report_list) == 0:
            print('暂无研报数据------------>' + response.meta['industryCode'])

        for report in report_list:
            infoCode = report['infoCode']

            industryCode = report['industryCode']

            date = report['publishDate']
            date = date.split(" ")[0]

            # 存储研报的reportCode
            ex = self.conn.sadd('reportCodeList', str(infoCode))

            if ex == 1:
                print('爬取infoCode------------>' + infoCode)
                yield scrapy.Request(
                    'http://data.eastmoney.com/report/zw_industry.jshtml?infocode=' + infoCode,
                    meta={"industryCode": industryCode, "date": date},
                    callback=self.parser_report_details)
            else:
                print('已爬取infoCode------------>' + infoCode)

    # 解析研报详情
    def parser_report_details(self, response):
        url_list = response.xpath('/html/body/div[1]/div[8]/div[3]/div[1]/div[1]/div[3]/div[3]/span[2]')

        url = url_list.xpath('./a/@href').extract_first()
        title = response.xpath('//div[@class="c-title"]/h1/text()').extract_first()

        item = ReportItem()
        item['title'] = title
        item['date'] = response.meta['date']
        item['url'] = url
        item['industryCode'] = response.meta['industryCode']
        yield item
