import datetime as datetime
import time  # 引入time模块


class DateUtils:

    def getMonDayDate(self):
        today = datetime.date.today()  # 获取当前日期, 因为要求时分秒为0, 所以不要求时间

        weekday = today.weekday()  # 获取当前周的排序, 周一为0, 周日为6

        monday_delta = datetime.timedelta(weekday)  # 当前日期距离周一的时间差

        monday = today - monday_delta  # 获取这周一日期

        return monday

    def getlastServenDate(self):
        curticks = time.time()

        lastTicks = curticks - 7 * 86400000

        date = time.strftime("%Y-%m-%d %H:%M:%S", lastTicks)

        print(date)

        return date

    def getlastServenDate(self):
        curticks = time.time()

        lastTicks = curticks - 7 * 86400

        date = time.strftime("%Y-%m-%d", time.localtime(lastTicks))

        print(date)

        return date

    pass
