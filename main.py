from scrapy.cmdline import execute
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

execute(['scrapy', 'crawl', 'aiqicha2'])  # 你需要将此处的spider_name替换为你自己的爬虫名称

# while True:
#     os.system("scrapy crawl aiqicha1")
#     time.sleep(86400)
    # 每隔一天运行一次就是 24*60*60=86400s，我这里是60s,自己根据需要选择时间
