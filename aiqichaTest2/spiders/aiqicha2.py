from mimetypes import init

import scrapy

from time import sleep

from scrapy.http import HtmlResponse

from selenium import webdriver

from selenium.webdriver.chrome.options import Options

from selenium.webdriver import ChromeOptions

from redis import Redis

from pymongo import MongoClient

# import json
#
# from aiqichaTest2.items import StockCompanyItem
#
# from aiqichaTest2.items import HoldItem
#
# from selenium.webdriver.common.action_chains import ActionChains


from aiqichaTest2.items import StockInfoItem
from aiqichaTest2.items import InvestItem
from aiqichaTest2.items import HoldItem


class Aiqicha2Spider(scrapy.Spider):
    name = 'aiqicha2'
    # allowed_domains = ['https://aiqicha.baidu.com/']
    start_urls = ['https://aiqicha.baidu.com/']

    # 创建redis链接对象
    conn = Redis(host='127.0.0.1', port=6379, decode_responses=True, charset='utf-8')
    companyCode = ''

    # 创建MongoDB连接
    # client = MongoClient('localhost', '27017')
    # 选择一个数据库
    # db = client['test']
    # 选择集合
    # col = client['test', 'runoob']

    def __init__(self):
        # 实现无可视化界面的操作
        chrome_options = Options()
        # chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--disable-gpu')

        # 实现规避检测
        option = ChromeOptions()
        option.add_experimental_option('excludeSwitches', ['enable-automation'])

        # 实例化一个浏览器对象
        self.browser = webdriver.Chrome(executable_path='../chromedriver', chrome_options=chrome_options,
                                        options=option)
        self.browser.implicitly_wait(5)
        self.browser.maximize_window()

        super().__init__()

    def parse(self, response):
        # 29453261288626(小米)  33837380082581(广景) 83351913819305(税务违法) 30049224537125(乐视-司法拍卖)
        # 52324620492621(动产抵押) 17868162152899(清算组信息) 30853655356312(严重违法) 30427578312050(环保处罚) 95592326348232(土地抵押)
        self.companyCode = '33837380082581'

        url = 'https://aiqicha.baidu.com/company_detail_' + self.companyCode + '?tab=basic'

        yield scrapy.Request(url=url,
                             meta={'companyCode': self.companyCode},
                             callback=self.paser_quity_info)

    # 股权穿透
    def paser_quity_info(self, response):
        print("股权穿透---->")

        g_list = response.xpath('//*[@id="stock-chart"]/svg/g/g')

        for index in range(len(g_list)):
            g = g_list[index]
            companyInfoDic = {}
            # 公司名字
            companyName = g.xpath('./text[1]/text()').extract()[0]
            companyInfoDic['companyName'] = companyName
            # 认缴金额
            amount = g.xpath('./text[3]/text()').extract()
            if len(amount) > 0:
                amount = amount[0]
                companyInfoDic['amount'] = amount
            # 认缴占比
            persent = g.xpath('./text[4]/text()').extract()
            if len(persent) > 0:
                persent = persent[0]
                companyInfoDic['persent'] = persent
            # 上/下游
            shareholders = g.xpath('@class').extract()
            if len(shareholders) > 0:
                shareholders = shareholders[0]
                companyInfoDic['shareholders'] = shareholders

            # companyInfoDic['rootCompanyCode'] = self.companyCode
            # companyInfoDic['insertType'] = 'stockInfo'
            # yield companyInfoDic

            # item = StockInfoItem()
            # item['insertType'] = 'stockInfo'
            # item['stockInfo'] = companyInfoDic
            # yield item

        sleep(1)
        # ========>对外投资
        self.parse_basic_invest(response)

        # 可扩展
        # isExpand = g.xpath('./text[@class="isExpand"]/text()').extract()
        #
        # if len(isExpand) > 0:
        #     if "+" == isExpand[0]:
        #         # 节点点击
        #         isExpand_click = self.browser.find_element_by_xpath(
        #             '//*[@id="stock-chart"]/*[name()="svg"]/*[name()="g"]/*[name()="g"][' + str(
        #                 index + 1) + ']/*[name()="text"][@class="isExpand"]')
        #         try:
        #             ActionChains(self.browser).move_to_element(isExpand_click).click(isExpand_click).perform()
        #         except:
        #             print(name + "-------------------->节点超出屏幕" + str(index + 1))
        #         else:
        #             print(name + "---->有节点")
        #             sleep(2)
        #     else:
        #         print(name + "---->无节点")
        # else:
        #     print(name + "---->无节点")

        # print("---->结束解析")
        # sleep(60)

    # 对外投资
    def parse_basic_invest(self, response):
        print("对外投资---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))

        tbody_tr = response.xpath('//div[@id="basic-invest"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无对外投资')

            # ========>控股企业
            self.parse_basic_hold(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                investDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        investDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/div[2]/a[1]/text()').extract()
                        investDic['investCompany'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/div[2]/a[1]/text()').extract()
                        if len(td_info) > 0:
                            investDic['legalperson'] = self.strFormatting(td_info[0])
                        else:
                            td_info = td.xpath('./div/div[2]/p/text()').extract()
                            investDic['legalperson'] = self.strFormatting(td_info[0])
                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        investDic['createTime'] = self.strFormatting(td_info[0])
                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        investDic['investpercent'] = self.strFormatting(td_info[0])
                    if index == 5:
                        td_info = td.xpath('./div/span/text()').extract()
                        investDic['subscribedAmount'] = self.strFormatting(td_info[0])
                    if index == 6:
                        td_info = td.xpath('.//span/text()').extract()
                        investDic['state'] = self.strFormatting(td_info[0])
                # 存储对外投资
                # ex = self.conn.sadd('investList_' + self.companyCode, json.dumps(investDic))
                # if ex == 1:
                #     print('---->已爬取' + investDic['number'])
                # else:
                #     print('---->已存在' + investDic['number'])

                # investDic['insertType'] = 'invest'
                # yield investDic

                # item = InvestItem()
                # item['insertType'] = 'invest'
                # item['invest'] = investDic
                # yield item

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="basic-invest"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>控股企业
                self.parse_basic_hold(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_basic_invest(myResponse)

    # 控股企业
    def parse_basic_hold(self, response):
        print("控股企业---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))

        tbody_tr = response.xpath('//div[@id="basic-hold"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无控股企业')

            # 模拟点击-重点关注
            risk_tab = self.browser.find_element_by_xpath(
                '/html/body/div[1]/div[1]/div/div[6]/div/div/div[3]/a')
            self.browser.execute_script("arguments[0].click();", risk_tab)
            sleep(2)
            response_data = self.browser.page_source
            myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')

            # ========>股权出质
            self.parse_risk_equitypledge(myResponse)

        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                basicHoldDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./text()').extract()
                        basicHoldDic['number'] = self.strFormatting(td_info[0])

                    if index == 1:
                        td_info = td.xpath('./div/div[2]/a[1]/text()').extract()
                        if len(td_info) == 0:
                            td_info = td.xpath('./div/div[2]/p/text()').extract()
                        basicHoldDic['legalPerson'] = self.strFormatting(td_info[0])

                    if index == 2:
                        td_info = td.xpath('./text()').extract()
                        basicHoldDic['holdCompany'] = self.strFormatting(td_info[0])

                    if index == 3:

                        # investmentPathList[investmentPathDic = {'':'',List[]}]
                        investmentPathList = []
                        divList = td.xpath('./div')
                        for div in divList:
                            investmentPathDic = {}
                            # 路径名称
                            pathName = div.xpath('./h5/text()').extract()
                            childCompanyList = []
                            lis = div.xpath('.//li')
                            for index in range(len(lis)):
                                li = lis[index]
                                childCompanyDic = {}
                                if index == 0:
                                    companyName = li.xpath('./text()').extract()
                                    # 母公司
                                    childCompanyDic['childCompany'] = companyName[0]
                                    # 占比
                                    childCompanyDic['present'] = '1'
                                else:
                                    # 子公司
                                    companyName = li.xpath('./a/text()').extract()
                                    childCompanyDic['childCompany'] = companyName[0]
                                    # 占比
                                    present = li.xpath('./span/em/text()').extract()
                                    childCompanyDic['present'] = present[0]

                                childCompanyList.append(childCompanyDic)

                            investmentPathDic['pathName'] = pathName[0]
                            investmentPathDic['pathInfo'] = childCompanyList
                            investmentPathList.append(investmentPathDic)

                        basicHoldDic['investmentPath'] = investmentPathList

                # 存储控股企业
                # ex = self.conn.sadd('basicHold_' + self.companyCode, json.dumps(basicHoldDic))
                # if ex == 1:
                #     print('---->已爬取' + basicHoldDic['number'])
                # else:
                #     print('---->已存在' + basicHoldDic['number'])

                # item = HoldItem()
                # item['insertType'] = 'basicHold'
                # item['basicHoldDic'] = basicHoldDic

                # basicHoldDic['insertType'] = 'basicHold'
                # yield basicHoldDic

            # item = HoldItem()
            # item['insertType'] = 'basicHold'
            # item['basicHold'] = basicHoldDic
            # yield item

            sleep(1)

            next_page = response.xpath('//*[@id="basic-hold"]/div/ul/li[@class="ivu-page-next"]').extract()

            if len(next_page) > 0:
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="basic-hold"]/div/ul/li[@class="ivu-page-next"]')

                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')

                self.parse_basic_hold(myResponse)
            else:
                print('============================>已到最后一页')
                sleep(2)

                # 模拟点击-重点关注
                risk_tab = self.browser.find_element_by_xpath(
                    '/html/body/div[1]/div[1]/div/div[6]/div/div/div[2]/a')
                self.browser.execute_script("arguments[0].click();", risk_tab)
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')

                # ========>股权出质
                self.parse_risk_equitypledge(myResponse)

    # 股权出质
    def parse_risk_equitypledge(self, response):
        print("股权出质---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))

        tbody_tr = response.xpath('//div[@id="risk-equitypledge"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无股权出质')

            # ========>开庭公告
            self.parse_risk_opennotice(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                equitypledgeDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        equitypledgeDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        equitypledgeDic['openDate'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        equitypledgeDic['pledgor'] = self.strFormatting(td_info[0])
                    if index == 3:
                        td_info = td.xpath('./div/a/@href').extract()
                        if len(td_info) > 0:
                            equitypledgeDic['pledge'] = self.strFormatting(td_info[0])
                        else:
                            equitypledgeDic['pledge'] = '暂无数据'
                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        equitypledgeDic['state'] = self.strFormatting(td_info[0])
                    if index == 5:
                        td_info = td.xpath('./div/a/@href').extract()
                        equitypledgeDic['details'] = self.strFormatting(td_info[0])
                # 存储开庭公告
                # ex = self.conn.sadd('equitypledgeList_' + self.companyCode, json.dumps(equitypledgeDic))
                # if ex == 1:
                #     print('---->已爬取' + equitypledgeDic['number'])
                # else:
                #     print('---->已存在' + equitypledgeDic['number'])

                equitypledgeDic['insertType'] = 'equitypledge'
                # yield equitypledgeDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="risk-equitypledge"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>开庭公告
                self.parse_risk_opennotice(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_equitypledge(myResponse)

    # 开庭公告
    def parse_risk_opennotice(self, response):
        print("开庭公告---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))

        tbody_tr = response.xpath('//div[@id="risk-opennotice"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无开庭公告')

            # ========>法院公告
            self.parse_risk_courtnoticed(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                opennoticeDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        opennoticeDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        opennoticeDic['openDate'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        opennoticeDic['code'] = self.strFormatting(td_info[0])
                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        opennoticeDic['cause'] = self.strFormatting(td_info[0])
                    if index == 4:
                        plaintiff = td.xpath('./div/span/p[1]/text()').extract()
                        defendant = td.xpath('./div/span/p[2]/text()').extract()
                        if len(defendant) == 0:
                            opennoticeDic['parties'] = self.strFormatting(plaintiff[0])
                        else:
                            opennoticeDic['parties'] = self.strFormatting(plaintiff[0] + defendant[0])
                    if index == 5:
                        td_info = td.xpath('./div/a/@href').extract()
                        opennoticeDic['details'] = self.strFormatting(td_info[0])
                # 存储开庭公告
                # ex = self.conn.sadd('opennoticeList_' + self.companyCode, json.dumps(opennoticedic))
                # if ex == 1:
                #     print('---->已爬取' + opennoticedic['number'])
                # else:
                #     print('---->已存在' + opennoticedic['number'])

                opennoticeDic['insertType'] = 'opennotice'
                # yield opennoticeDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="risk-opennotice"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>法院公告
                self.parse_risk_courtnoticed(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_opennotice(myResponse)

    # 法院公告
    def parse_risk_courtnoticed(self, response):
        print("法院公告---->")
        tbody_tr = response.xpath('//div[@id="risk-courtnoticed"]/table/tbody/tr')

        if len(tbody_tr) == 0:
            print('---->暂无法院公告')

            # ========>立案信息
            self.parse_risk_filinginfo(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                courtnoticedDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        courtnoticedDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        courtnoticedDic['openDate'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        courtnoticedDic['type'] = self.strFormatting(td_info[0])
                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        courtnoticedDic['reason'] = self.strFormatting(td_info[0])
                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        courtnoticedDic['parties'] = self.strFormatting(td_info[0])
                    if index == 5:
                        td_info = td.xpath('./div/span/text()').extract()
                        courtnoticedDic['court'] = self.strFormatting(td_info[0])
                    if index == 6:
                        td_info = td.xpath('./div/a/@href').extract()
                        courtnoticedDic['details'] = self.strFormatting(td_info[0])
                # 存储立案信息
                # ex = self.conn.sadd('courtnoticed_' + self.companyCode, json.dumps(courtnoticedDic))
                # if ex == 1:
                #     print('---->已爬取' + courtnoticedDic['number'])
                # else:
                #     print('---->已存在' + courtnoticedDic['number'])

                courtnoticedDic['insertType'] = 'courtnoticed'
                # yield courtnoticedDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="risk-courtnoticed"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>立案信息
                self.parse_risk_filinginfo(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_courtnoticed(myResponse)

    # 立案信息
    def parse_risk_filinginfo(self, response):
        print("立案信息---->")

        tbody_tr = response.xpath('//div[@id="risk-filinginfo"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无立案信息')

            # ========>终本案件
            self.parse_risk_terminationcase(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                filinginfoDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        filinginfoDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        filinginfoDic['openDate'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        filinginfoDic['code'] = self.strFormatting(td_info[0])
                    if index == 3:
                        plaintiff = td.xpath('./div/span/p[1]/text()').extract()
                        defendant = td.xpath('./div/span/p[2]/text()').extract()
                        if len(defendant) == 0:
                            filinginfoDic['parties'] = self.strFormatting(plaintiff[0])
                        else:
                            filinginfoDic['parties'] = self.strFormatting(plaintiff[0] + defendant[0])
                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        filinginfoDic['court'] = self.strFormatting(td_info[0])
                    if index == 5:
                        td_info = td.xpath('./div/a/@href').extract()
                        filinginfoDic['details'] = self.strFormatting(td_info[0])
                # 存储立案信息
                # ex = self.conn.sadd('filinginfoList_' + self.companyCode, json.dumps(filinginfo))
                # if ex == 1:
                #     print('---->已爬取' + filinginfo['number'])
                # else:
                #     print('---->已存在' + filinginfo['number'])

                filinginfoDic['insertType'] = 'filinginfo'
                # yield filinginfoDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="risk-filinginfo"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>终本案件
                self.parse_risk_terminationcase(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_filinginfo(myResponse)

    # 终本案件
    def parse_risk_terminationcase(self, response):
        print("终本案件---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))

        tbody_tr = response.xpath('//div[@id="risk-terminationcase"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无终本案件')

            # ========>环保处罚
            self.parse_risk_envpunishment(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                terminationcaseDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        terminationcaseDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        terminationcaseDic['date'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        terminationcaseDic['code'] = self.strFormatting(td_info[0])
                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        terminationcaseDic['object'] = self.strFormatting(td_info[0])
                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        terminationcaseDic['court'] = self.strFormatting(td_info[0])
                    if index == 5:
                        td_info = td.xpath('./div/span/text()').extract()
                        terminationcaseDic['end_date'] = self.strFormatting(td_info[0])
                    if index == 6:
                        td_info = td.xpath('./div/a/@href').extract()
                        terminationcaseDic['details'] = self.strFormatting(td_info[0])

                # 存储终本案件
                # ex = self.conn.sadd('terminationcaseList_' + self.companyCode, json.dumps(terminationcaseDic))
                # if ex == 1:
                #     print('---->已爬取' + terminationcaseDic['number'])
                # else:
                #     print('---->已存在' + terminationcaseDic['number'])

                terminationcaseDic['insertType'] = 'terminationcase'
                # yield terminationcaseDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="risk-terminationcase"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>环保处罚
                self.parse_risk_envpunishment(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_terminationcase(myResponse)

    # 环保处罚
    def parse_risk_envpunishment(self, response):
        print("环保处罚---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))
        tbody_tr = response.xpath('//div[@id="operatingCondition-enterprisejob"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无环保处罚')

            # ========>债券违约
            self.parse_risk_bondbreach(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                envpunishmentDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        envpunishmentDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        envpunishmentDic['code'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        envpunishmentDic['type'] = self.strFormatting(td_info[0])

                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        envpunishmentDic['categary'] = self.strFormatting(td_info[0])

                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        envpunishmentDic['unit'] = self.strFormatting(td_info[0])

                    if index == 5:
                        td_info = td.xpath('./div/span/text()').extract()
                        envpunishmentDic['date'] = self.strFormatting(td_info[0])

                    if index == 6:
                        td_info = td.xpath('./div/a/@href').extract()
                        envpunishmentDic['details'] = self.strFormatting(td_info[0])

                # 存储环保处罚
                # ex = self.conn.sadd('envpunishmentList_' + self.companyCode, json.dumps(envpunishmentDic))
                # if ex == 1:
                #     print('---->已爬取' + envpunishmentDic['number'])
                # else:
                #     print('---->已存在' + envpunishmentDic['number'])

                envpunishmentDic['insertType'] = 'envpunishment'
                # yield envpunishmentDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="operatingCondition-enterprisejob"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>债券违约
                self.parse_risk_bondbreach(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_envpunishment(myResponse)

    # 债券违约
    def parse_risk_bondbreach(self, response):
        print("债券违约---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))

        tbody_tr = response.xpath('//div[@id="risk-bondbreach"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无债券违约')

            # ========>土地抵押
            self.parse_risk_landmortgage(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                bondbreachDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        bondbreachDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        bondbreachDic['code'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        bondbreachDic['intro'] = self.strFormatting(td_info[0])
                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        bondbreachDic['dynamic'] = self.strFormatting(td_info[0])
                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        bondbreachDic['date'] = self.strFormatting(td_info[0])
                    if index == 5:
                        td_info = td.xpath('./div/a/@href').extract()
                        bondbreachDic['details'] = self.strFormatting(td_info[0])

                # 存储债券违约
                # ex = self.conn.sadd('bondbreachList_' + self.companyCode, json.dumps(bondbreachDic))
                # if ex == 1:
                #     print('---->已爬取' + bondbreachDic['number'])
                # else:
                #     print('---->已存在' + bondbreachDic['number'])

                bondbreachDic['insertType'] = 'bondbreach'
                # yield bondbreachDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="risk-bondbreach"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>土地抵押
                self.parse_risk_landmortgage(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_bondbreach(myResponse)

    # 土地抵押
    def parse_risk_landmortgage(self, response):
        print("土地抵押---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))
        tbody_tr = response.xpath('//div[@id="risk-landmortgage"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无土地抵押')

            # ========>严重违法
            self.parse_risk_illegal(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                landmortgageDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        landmortgageDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        landmortgageDic['location'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/a/@href').extract()
                        if len(td_info) < 1:
                            td_info = td.xpath('./div/span/text()').extract()
                        landmortgageDic['mortgagor'] = self.strFormatting(td_info[0])
                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        landmortgageDic['mortgagee'] = self.strFormatting(td_info[0])
                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        landmortgageDic['date'] = self.strFormatting(td_info[0])
                    if index == 5:
                        td_info = td.xpath('./div/a/@href').extract()
                        landmortgageDic['details'] = self.strFormatting(td_info[0])

                # 存储土地抵押
                # ex = self.conn.sadd('landmortgageList_' + self.companyCode, json.dumps(landmortgageDic))
                # if ex == 1:
                #     print('---->已爬取' + landmortgageDic['number'])
                # else:
                #     print('---->已存在' + landmortgageDic['number'])

                landmortgageDic['insertType'] = 'landmortgage'
                # yield landmortgageDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="risk-landmortgage"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>严重违法
                self.parse_risk_illegal(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_landmortgage(myResponse)

    # 严重违法
    def parse_risk_illegal(self, response):
        print("严重违法---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))
        tbody_tr = response.xpath('//div[@id="risk-illegal"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无严重违法')

            # ========>清算组信息
            self.parse_risk_clearaccount(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                illegalDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        illegalDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        illegalDic['person'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        illegalDic['reason'] = self.strFormatting(td_info[0])

                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        illegalDic['authority'] = self.strFormatting(td_info[0])

                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        illegalDic['outOfDate'] = self.strFormatting(td_info[0])

                    if index == 5:
                        td_info = td.xpath('./div/span/text()').extract()
                        illegalDic['outOfReason'] = self.strFormatting(td_info[0])

                    if index == 6:
                        td_info = td.xpath('./div/span/text()').extract()
                        illegalDic['outOfAuthority'] = self.strFormatting(td_info[0])

                # 存储严重违法
                # ex = self.conn.sadd('illegalList_' + self.companyCode, json.dumps(illegalDic))
                # if ex == 1:
                #     print('---->已爬取' + illegalDic['number'])
                # else:
                #     print('---->已存在' + illegalDic['number'])

                illegalDic['insertType'] = 'illegal'
                # yield illegalDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="risk-illegal"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>清算组信息
                self.parse_risk_clearaccount(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_illegal(myResponse)

    # 清算组信息
    def parse_risk_clearaccount(self, response):
        print("清算组信息---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))
        tbody_tr = response.xpath('//div[@id="risk-clearaccount"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无清算组信息')

            # ========>动产抵押
            self.parse_risk_chattelmortgage(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                clearaccountDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        clearaccountDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        clearaccountDic['person'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        clearaccountDic['members'] = self.strFormatting(td_info[0])

                # 存储清算组信息
                # ex = self.conn.sadd('clearaccountList_' + self.companyCode, json.dumps(clearaccountDic))
                # if ex == 1:
                #     print('---->已爬取' + clearaccountDic['number'])
                # else:
                #     print('---->已存在' + clearaccountDic['number'])

                clearaccountDic['insertType'] = 'clearaccount'
                # yield clearaccountDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="risk-clearaccount"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>动产抵押
                self.parse_risk_chattelmortgage(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_clearaccount(myResponse)

    # 动产抵押
    def parse_risk_chattelmortgage(self, response):
        print("动产抵押---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))
        tbody_tr = response.xpath('//div[@id="risk-chattelmortgage"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无动产抵押')

            # ========>司法拍卖
            self.parse_risk_judicialauction(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                chattelmortgageDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        chattelmortgageDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        chattelmortgageDic['date'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        chattelmortgageDic['amount'] = self.strFormatting(td_info[0])
                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        chattelmortgageDic['authority'] = self.strFormatting(td_info[0])
                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        chattelmortgageDic['state'] = self.strFormatting(td_info[0])
                    if index == 5:
                        td_info = td.xpath('./div/a/@href').extract()
                        chattelmortgageDic['details'] = self.strFormatting(td_info[0])

                # 存储动产抵押
                # ex = self.conn.sadd('chattelmortgageList_' + self.companyCode, json.dumps(chattelmortgageDic))
                # if ex == 1:
                #     print('---->已爬取' + chattelmortgageDic['number'])
                # else:
                # print('---->已存在' + chattelmortgageDic['number'])

                chattelmortgageDic['insertType'] = 'chattelmortgage'
                # yield chattelmortgageDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="risk-chattelmortgage"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>司法拍卖
                self.parse_risk_judicialauction(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_chattelmortgage(myResponse)

    # 司法拍卖
    def parse_risk_judicialauction(self, response):
        print("司法拍卖---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))

        tbody_tr = response.xpath('//div[@id="risk-judicialauction"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无司法拍卖')

            # ========>税务违法
            self.parse_risk_taxviolation(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                judicialauctionDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        judicialauctionDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        date_start = td.xpath('./div/span/div[1]/text()').extract()
                        date_end = td.xpath('./div/span/div[2]/text()').extract()
                        judicialauctionDic['date'] = self.strFormatting(date_start[0] + date_end[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        judicialauctionDic['auctionName'] = self.strFormatting(td_info[0])
                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        judicialauctionDic['openingBid'] = self.strFormatting(td_info[0])
                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        judicialauctionDic['court'] = self.strFormatting(td_info[0])
                    if index == 5:
                        td_info = td.xpath('./div/a/@href').extract()
                        judicialauctionDic['details'] = self.strFormatting(td_info[0])

                # 存储税务违法
                # ex = self.conn.sadd('judicialauctionList_' + self.companyCode, json.dumps(judicialauctionDic))
                # if ex == 1:
                #     print('---->已爬取' + judicialauctionDic['number'])
                # else:
                #     print('---->已存在' + judicialauctionDic['number'])

                judicialauctionDic['insertType'] = 'judicialauction'
                # yield judicialauctionDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="risk-taxviolation"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>税务违法
                self.parse_risk_taxviolation(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_judicialauction(myResponse)

    # 税务违法
    def parse_risk_taxviolation(self, response):
        print("税务违法---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))

        tbody_tr = response.xpath('//div[@id="risk-taxviolation"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无税务违法')

            # ========>经营异常
            self.parse_risk_abnormal(response)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                taxviolationDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        taxviolationDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        taxviolationDic['companyName'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/div/text()').extract()
                        taxviolationDic['nature'] = self.strFormatting(td_info[0])
                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        taxviolationDic['date'] = self.strFormatting(td_info[0])
                    if index == 4:
                        td_info = td.xpath('./div/a/@href').extract()
                        taxviolationDic['details'] = self.strFormatting(td_info[0])

                # 存储税务违法
                # ex = self.conn.sadd('taxviolationList_' + self.companyCode, json.dumps(taxviolationDic))
                # if ex == 1:
                #     print('---->已爬取' + taxviolationDic['number'])
                # else:
                #     print('---->已存在' + taxviolationDic['number'])

                taxviolationDic['insertType'] = 'taxviolation'
                # yield taxviolationDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="risk-taxviolation"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # ========>经营异常
                self.parse_risk_abnormal(response)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_taxviolation(myResponse)

    # 经营异常
    def parse_risk_abnormal(self, response):
        print("经营异常---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))

        tbody_tr = response.xpath('//div[@id="risk-abnormal"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无经营异常')

            # 模拟点击 经营状况
            business_tab = self.browser.find_element_by_xpath(
                '/html/body/div[1]/div[1]/div/div[6]/div/div/div[5]/a')
            self.browser.execute_script("arguments[0].click();", business_tab)
            sleep(2)
            response_data = self.browser.page_source
            myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')

            # ========>招聘信息
            self.parse_enterprisejob(myResponse)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                abnormalDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        abnormalDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        abnormalDic['date'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        abnormalDic['reason'] = self.strFormatting(td_info[0])
                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        abnormalDic['organ'] = self.strFormatting(td_info[0])
                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        abnormalDic['outOfDate'] = self.strFormatting(td_info[0])
                    if index == 5:
                        td_info = td.xpath('./div/span/text()').extract()
                        abnormalDic['outOfReason'] = self.strFormatting(td_info[0])
                    if index == 6:
                        td_info = td.xpath('./div/span/text()').extract()
                        abnormalDic['outOfOrgan'] = self.strFormatting(td_info[0])
                # 存储经营异常
                # ex = self.conn.sadd('abnormalList_' + self.companyCode, json.dumps(abnormalDic))
                # if ex == 1:
                #     print('---->已爬取' + abnormalDic['number'])
                # else:
                #     print('---->已存在' + abnormalDic['number'])

                abnormalDic['insertType'] = 'abnormal'
                # yield abnormalDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="risk-abnormal"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # 模拟点击 经营状况
                business_tab = self.browser.find_element_by_xpath(
                    '/html/body/div[1]/div[1]/div/div[6]/div/div/div[5]/a')
                self.browser.execute_script("arguments[0].click();", business_tab)
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')

                # ========>招聘信息
                self.parse_enterprisejob(myResponse)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_risk_abnormal(myResponse)

    # 招聘信息
    def parse_enterprisejob(self, response):
        print("招聘信息---->")

        # thead_tr = response.xpath('//div[@id="risk-opennotice"]/table/thead/tr/td')
        # for td in thead_tr:
        #     thead_str = td.xpath('./text()').extract()
        #     print("开庭公告---->" + thead_str[0].strip().replace('\n', '').replace('\r', ''))
        tbody_tr = response.xpath('//div[@id="operatingCondition-enterprisejob"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无招聘信息')

            # 模拟点击 知识产权
            certRecord_tab = self.browser.find_element_by_xpath(
                '/html/body/div[1]/div[1]/div/div[6]/div/div/div[3]/a')
            self.browser.execute_script("arguments[0].click();", certRecord_tab)
            sleep(2)
            response_data = self.browser.page_source
            myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')

            # ========>知识产权
            self.paser_certRecord_copyright(myResponse)
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                envpunishmentDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    if index == 0:
                        td_info = td.xpath('./div/text()').extract()
                        envpunishmentDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        envpunishmentDic['date'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        envpunishmentDic['position'] = self.strFormatting(td_info[0])

                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        envpunishmentDic['salary'] = self.strFormatting(td_info[0])

                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        envpunishmentDic['address'] = self.strFormatting(td_info[0])

                    if index == 5:
                        td_info = td.xpath('./div/span/text()').extract()
                        envpunishmentDic['education'] = self.strFormatting(td_info[0])

                    if index == 6:
                        td_info = td.xpath('./div/a/@href').extract()
                        envpunishmentDic['details'] = self.strFormatting(td_info[0])

                # 存储招聘信息
                # ex = self.conn.sadd('enterprisejobList_' + self.companyCode, json.dumps(envpunishmentDic))
                # if ex == 1:
                #     print('---->已爬取' + envpunishmentDic['number'])
                # else:
                #     print('---->已存在' + envpunishmentDic['number'])

                envpunishmentDic['insertType'] = 'envpunishment'
                # yield envpunishmentDic

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="operatingCondition-enterprisejob"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)

                # 模拟点击 知识产权
                certRecord_tab = self.browser.find_element_by_xpath(
                    '/html/body/div[1]/div[1]/div/div[6]/div/div/div[3]/a')
                self.browser.execute_script("arguments[0].click();", certRecord_tab)
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')

                # ========>知识产权
                self.paser_certRecord_copyright(myResponse)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.parse_enterprisejob(myResponse)

    # 软件著作权信息
    def paser_certRecord_copyright(self, response):
        print("软件著作权信息---->")

        tbody_tr = response.xpath('//div[@id="certRecord-copyright"]/table/tbody/tr')
        if len(tbody_tr) == 0:
            print('---->暂无软件著作权信息')
        else:
            for tr in tbody_tr:
                tds = tr.xpath('./td')
                # 数据字典
                certRecordCopyrightDic = {}
                for index in range(len(tds)):
                    td = tds[index]
                    # if index == 0:
                    #     td_info = td.xpath('./div/text()').extract()
                    #     certRecordCopyrightDic['number'] = self.strFormatting(td_info[0])
                    if index == 1:
                        td_info = td.xpath('./div/span/text()').extract()
                        certRecordCopyrightDic['name'] = self.strFormatting(td_info[0])
                    if index == 2:
                        td_info = td.xpath('./div/span/text()').extract()
                        certRecordCopyrightDic['intro'] = self.strFormatting(td_info[0])

                    if index == 3:
                        td_info = td.xpath('./div/span/text()').extract()
                        certRecordCopyrightDic['vision'] = self.strFormatting(td_info[0])

                    if index == 4:
                        td_info = td.xpath('./div/span/text()').extract()
                        certRecordCopyrightDic['copyright_categary'] = self.strFormatting(td_info[0])

                    if index == 5:
                        td_info = td.xpath('./div/span/text()').extract()
                        certRecordCopyrightDic['industry_categary'] = self.strFormatting(td_info[0])

                    if index == 6:
                        td_info = td.xpath('./div/span/text()').extract()
                        certRecordCopyrightDic['date'] = self.strFormatting(td_info[0])

                    if index == 7:
                        td_info = td.xpath('./div/a/@href').extract()
                        certRecordCopyrightDic['details'] = self.strFormatting(td_info[0])

                certRecordCopyrightDic['insertType'] = 'certRecordCopyright'

                print(certRecordCopyrightDic)

            sleep(1)
            try:
                # selenuim模拟点击下一页
                # 如果点击到最后一页 就停止
                next_page_li = self.browser.find_element_by_xpath(
                    '//*[@id="operatingCondition-enterprisejob"]/div/ul/li[@class="ivu-page-next"]')
            except Exception:
                print('============================>已到最后一页')
                sleep(2)
            else:
                self.browser.execute_script("arguments[0].click();", next_page_li)
                print('====》点击下一页')
                sleep(2)
                response_data = self.browser.page_source
                myResponse = HtmlResponse(url=response.url, body=response_data, encoding='utf-8')
                self.paser_certRecord_copyright(myResponse)

    def strFormatting(self, str):
        return str.strip().replace('\n', '').replace('\r', '')
