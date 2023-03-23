import random
from time import time, localtime
import cityinfo
from requests import get, post
from datetime import datetime, date
import sys
import os
import http.client, urllib
from zhdate import ZhDate
import json
from warnings import warn


class DailyLovePush:
    def __init__(self, cfg_path="./config.json"):
        self.cfg_path = cfg_path
        self.config = {}
        self.init_file()

    def init_file(self):
        with open(self.cfg_path, encoding="utf-8") as f:
            self.config = json.load(f)

    def get_color(self, obj):
        color_dict = {
            "date": "#238E23",
            "city": "#3F3E3F",
            "weather": "#5B8982",
            "min_temperature": "#007FFF",
            "max_temperature": "#FF2400",
            "love_day": "#FF7F00",
            "birthday1": "#F5D040",
            "birthday2": "#F5D040",
            "note_en": "#38B0DE",
        }
        if obj not in color_dict:
            return self.gen_random_color()
        else:
            return color_dict.get(obj)

    @staticmethod
    def gen_random_color():
        # 获取随机颜色
        get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
        color_list = get_colors(100)
        return random.choice(color_list)

    def get_access_token(self):
        # appId
        app_id = self.config["app_id"]
        # appSecret
        app_secret = self.config["app_secret"]
        post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                    .format(app_id, app_secret))
        try:
            access_token = get(post_url).json()['access_token']
        except KeyError:
            print("获取access_token失败，请检查app_id和app_secret是否正确")
            os.system("pause")
            sys.exit(1)
        # print(access_token)
        return access_token

    def get_birthday(self, birthday, year, today):
        birthday_year = birthday.split("-")[0]
        # 判断是否为农历生日
        if birthday_year[0] == "r":
            r_mouth = int(birthday.split("-")[1])
            r_day = int(birthday.split("-")[2])
            # 今年生日
            birthday = ZhDate(year, r_mouth, r_day).to_datetime().date()
            year_date = birthday

        else:
            # 获取国历生日的今年对应月和日
            birthday_month = int(birthday.split("-")[1])
            birthday_day = int(birthday.split("-")[2])
            # 今年生日
            year_date = date(year, birthday_month, birthday_day)
        # 计算生日年份，如果还没过，按当年减，如果过了需要+1
        if today > year_date:
            if birthday_year[0] == "r":
                # 获取农历明年生日的月和日
                r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
                birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
            else:
                birth_date = date((year + 1), birthday_month, birthday_day)
            birth_day = str(birth_date.__sub__(today)).split(" ")[0]
        elif today == year_date:
            birth_day = 0
        else:
            birth_date = year_date
            birth_day = str(birth_date.__sub__(today)).split(" ")[0]
        return birth_day

    def get_weather(self, province, city):
        # 城市id
        try:
            city_id = cityinfo.cityInfo[province][city]["AREAID"]
        except KeyError:
            print("推送消息失败，请检查省份或城市是否正确")
            os.system("pause")
            sys.exit(1)
        # city_id = 101280101
        # 毫秒级时间戳
        t = (int(round(time() * 1000)))
        headers = {
            "Referer": "http://www.weather.com.cn/weather1d/{}.shtml".format(city_id),
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        }
        url = "http://d1.weather.com.cn/dingzhi/{}.html?_={}".format(city_id, t)
        response = get(url, headers=headers)
        response.encoding = "utf-8"
        response_data = response.text.split(";")[0].split("=")[-1]
        response_json = eval(response_data)
        # print(response_json)
        weatherinfo = response_json["weatherinfo"]
        # 天气
        weather = weatherinfo["weather"]
        # 最高气温
        temp = weatherinfo["temp"]
        # 最低气温
        tempn = weatherinfo["tempn"]
        return weather, temp, tempn

    # 词霸每日一句
    def get_ciba(self):
        if self.config["Whether_Eng"]:
            try:
                url = "http://open.iciba.com/dsapi/"
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
                }
                r = get(url, headers=headers)
                note_en = r.json()["content"]
                note_ch = r.json()["note"]
                return note_ch, note_en
            except:
                raise Exception("词霸API调取错误")

    def caihongpi(self):
        if self.config["Whether_caihongpi"]:
            try:
                conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
                params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                conn.request('POST', '/caihongpi/index', params, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.loads(data)
                data = data["newslist"][0]["content"]
                if ("XXX" in data):
                    data.replace("XXX", "蒋蒋")
                return data
            except:
                raise Exception("彩虹屁API调取错误，请检查API是否正确申请或是否填写正确")

    # 健康小提示API
    def get_health(self):
        if self.config["Whether_health"]:
            try:
                conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
                params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                conn.request('POST', '/healthtip/index', params, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.loads(data)
                data = data["newslist"][0]["content"]
                return data
            except:
                raise Exception("健康小提示API调取错误，请检查API是否正确申请或是否填写正确")

    # 星座运势
    def lucky(self):
        if self.config["Whether_lucky"]:
            try:
                conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
                params = urllib.parse.urlencode({'key': self.config["tianxing_API"],
                                                 'astro': self.config["astro"]})
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                conn.request('POST', '/star/index', params, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.loads(data)
                data = "爱情指数：" + str(data["newslist"][1]["content"]) + "   工作指数：" + str(
                    data["newslist"][2]["content"]) + "\n今日概述：" + str(data["newslist"][8]["content"])
                return data
            except Exception:
                warn("星座运势API调取错误，请检查API是否正确申请或是否填写正确")
                return ""

    # 励志名言
    def lizhi(self):
        if self.config["Whether_lizhi"]:
            try:
                conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
                params = urllib.parse.urlencode({'key': self.config["tianxing_API"]})
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                conn.request('POST', '/lzmy/index', params, headers)
                res = conn.getresponse()
                data = res.read()
                data = json.loads(data)
                return data["newslist"][0]["saying"]
            except:
                raise Exception("励志古言API调取错误，请检查API是否正确申请或是否填写正确")

    # 下雨概率和建议
    def tip(self):
        pop, tips = "", ""
        if not self.config["Whether_tip"]:
            return pop, tips
        try:
            conn = http.client.HTTPSConnection('api.tianapi.com')  # 接口域名
            params = urllib.parse.urlencode({'key': self.config["tianxing_API"],
                                             'city': self.config["city"]})
            headers = {'Content-type': 'application/x-www-form-urlencoded'}
            conn.request('POST', '/tianqi/index', params, headers)
            res = conn.getresponse()
            data = res.read()
            data = json.loads(data)
            pop_chance = int(float(data["newslist"][0]["pcpn"])) * 100
            if pop_chance > 70:
                pop = "%s%% (最好带伞哦~ )" % pop_chance
            tips = data["newslist"][0]["tips"]
            return pop, tips
        except Exception as ex:
            warn(f"天气预报API调取错误: {ex}")
            return pop, tips

    # 推送信息
    def send_message(self, to_user, access_token,
                     city_name, weather, max_temperature,
                     min_temperature, pipi, lizhi, pop, tips,
                     note_en, note_ch, health_tip, lucky_):
        # TODO: data字典的组装要根据实际情况,自动跳过未正确获取的字段
        url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
        week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
        year = localtime().tm_year
        month = localtime().tm_mon
        day = localtime().tm_mday
        today = datetime.date(datetime(year=year, month=month, day=day))
        week = week_list[today.isoweekday() % 7]
        # 获取在一起的日子的日期格式
        love_year = int(self.config["love_date"].split("-")[0])
        love_month = int(self.config["love_date"].split("-")[1])
        love_day = int(self.config["love_date"].split("-")[2])
        love_date = date(love_year, love_month, love_day)
        # 获取在一起的日期差
        love_days = str(today.__sub__(love_date)).split(" ")[0]
        # 获取所有生日数据
        birthdays = {}
        for k, v in self.config.items():
            if k[0:5] == "birth":
                birthdays[k] = v
        data = {
            "touser": to_user,
            "template_id": self.config["template_id"],
            "url": "http://weixin.qq.com/download",
            "topcolor": "#FF0000",
            "data": {
                "date": {
                    "value": "{} {}".format(today, week),
                    "color": self.get_color("date")
                },
                "city": {
                    "value": city_name,
                    "color": self.get_color("city")
                },
                "weather": {
                    "value": weather,
                    "color": self.get_color("weather")
                },
                "min_temperature": {
                    "value": min_temperature,
                    "color": self.get_color("min_temperature")
                },
                "max_temperature": {
                    "value": max_temperature,
                    "color": self.get_color("max_temperature")
                },
                "love_day": {
                    "value": love_days,
                    "color": self.get_color("love_day")
                },
                "note_en": {
                    "value": note_en,
                    "color": self.get_color("note_en")
                },
                "note_ch": {
                    "value": note_ch,
                    "color": self.get_color("note_ch")
                },

                "pipi": {
                    "value": pipi,
                    "color": self.get_color("pipi")
                },

                "lucky": {
                    "value": lucky_,
                    "color": self.get_color("lucky")
                },

                "lizhi": {
                    "value": lizhi,
                    "color": self.get_color("lizhi")
                },

                "pop": {
                    "value": pop,
                    "color": self.get_color("weather")
                },
                "health": {
                    "value": health_tip,
                    "color": self.get_color("health")
                },

                "tips": {
                    "value": tips,
                    "color": self.get_color("tips")
                }
            }
        }
        print(data['data']['pop'])
        for i, (key, value) in enumerate(birthdays.items()):
            # 获取距离下次生日的时间
            birth_day = self.get_birthday(value, year, today)
            # 将生日数据插入data
            data["data"][key] = {"value": birth_day, "color": self.get_color(f'birthday{i + 1}')}
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        }
        res= post(url, headers=headers, json=data)
        response = res.json()
        if response["errcode"] == 40037:
            print("推送消息失败，请检查模板id是否正确")
        elif response["errcode"] == 40036:
            print("推送消息失败，请检查模板id是否为空")
        elif response["errcode"] == 40003:
            print("推送消息失败，请检查微信号是否正确")
        elif response["errcode"] == 0:
            print("推送消息成功")
        else:
            print(response)

    def start(self):
        # 获取accessToken
        accessToken = self.get_access_token()
        # 接收的用户
        users = self.config["user"]
        # 传入省份和市获取天气信息
        province, city = self.config["province"], self.config["city"]
        weather, max_temperature, min_temperature = self.get_weather(province, city)
        # 获取词霸每日金句
        note_ch, note_en = self.get_ciba()
        # 彩虹屁
        pipi = self.caihongpi()
        # 健康小提示
        health_tip = self.get_health()
        # 下雨概率和建议
        pop, tips = self.tip()
        # 励志名言
        lizhi = self.lizhi()
        # 星座运势
        lucky_ = self.lucky()
        # 公众号推送消息
        for user in users:
            self.send_message(user, accessToken, city, weather, max_temperature, min_temperature, pipi, lizhi, pop, tips,
                         note_en, note_ch, health_tip, lucky_)

if __name__ == "__main__":
    love_push = DailyLovePush()
    love_push.start()
