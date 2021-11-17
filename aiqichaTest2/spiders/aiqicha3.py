import scrapy

from time import sleep

from scrapy.http import HtmlResponse

from selenium import webdriver

from selenium.webdriver.chrome.options import Options

from selenium.webdriver import ChromeOptions

from redis import Redis


class Aiqicha3Spider(scrapy.Spider):
    name = 'aiqicha3'
    # allowed_domains = ['https://aiqicha.baidu.com/']
    start_urls = ['https://aiqicha.baidu.com/']

    # 创建redis链接对象
    conn = Redis(host='127.0.0.1', port=6379, decode_responses=True, charset='utf-8')
    companyCode = ''

    def __init__(self):
        # 实现无可视化界面的操作
        chrome_options = Options()
        chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')

        # 实现规避检测
        option = ChromeOptions()
        option.add_experimental_option('excludeSwitches', ['enable-automation'])

        # 实例化一个浏览器对象
        self.browser = webdriver.Chrome(executable_path='../chromedriver', chrome_options=chrome_options,
                                        options=option)

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

