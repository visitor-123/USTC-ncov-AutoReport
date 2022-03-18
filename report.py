#import time
import datetime
from datetime import date
import re
import argparse
from bs4 import BeautifulSoup
import json
import pytz
from ustclogin import Login
class Report(object):
    def __init__(self, stuid, password, data_path):
        self.stuid = stuid
        self.password = password
        self.data_path = data_path

    @property
    def report(self):
        login=Login(self.stuid,self.password,'https://weixine.ustc.edu.cn/2020','https://weixine.ustc.edu.cn/2020/caslogin','https://weixine.ustc.edu.cn/2020/home')
        if login.login():
            data = login.result.text
            data = data.encode('ascii','ignore').decode('utf-8','ignore')
            soup = BeautifulSoup(data, 'html.parser')
            token = soup.find("input", {"name": "_token"})['value']
            token1 = token

            with open(self.data_path, "r+", encoding='utf-8') as f:
                data = f.read()
                data = json.loads(data)
                data["_token"]=token
            headers = {
                'authority': 'weixine.ustc.edu.cn',
                'origin': 'https://weixine.ustc.edu.cn',
                'upgrade-insecure-requests': '1',
                'content-type': 'application/x-www-form-urlencoded',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'referer': 'https://weixine.ustc.edu.cn/2020/',
                'accept-language': 'zh-CN,zh;q=0.9',
                'Connection': 'close',
                'cookie': "PHPSESSID=" + login.cookies.get("PHPSESSID") + ";XSRF-TOKEN=" + login.cookies.get("XSRF-TOKEN") + ";laravel_session="+login.cookies.get("laravel_session"),
            }

            url = "https://weixine.ustc.edu.cn/2020/daliy_report"
            resp=login.session.post(url, data=data, headers=headers)

            print(token1)

            #to check if report success

            data = login.session.get("https://weixine.ustc.edu.cn/2020").text
            soup = BeautifulSoup(data, 'html.parser')
            pattern = re.compile("202[0-9]-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}")
            token = soup.find(
                "span", {"style": "position: relative; top: 5px; color: #666;"})
            flag = False
            if pattern.search(token.text) is not None:
                date1 = pattern.search(token.text).group()
                print("Latest report: " + date1)
                date1 = date1 + " +0800"
                reporttime = datetime.datetime.strptime(date1, "%Y-%m-%d %H:%M:%S %z")
                timenow = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
                delta = timenow - reporttime
                print("{} second(s) before.".format(delta.seconds))
                if delta.seconds < 120:
                    flag = True
            if flag == False:
                print("Report FAILED!")
            else:
                print("Report SUCCESSFUL!")

                # apply to go outside

                # start_date = date.today()
                if 1:
                    print("Day to apply to go outside, trying to apply")
                    end_date = start_date + datetime.timedelta(days=6)
                    start_date = start_date.isoformat()
                    end_date = end_date.isoformat()
                    data = login.session.get('https://weixine.ustc.edu.cn/2020/apply/daliy').text
                    data = data.encode('ascii', 'ignore').decode('utf-8', 'ignore')
                    soup = BeautifulSoup(data, 'html.parser')
                    token = soup.find("input", {"name": "_token"})['value']
                    token2 = token
                    data2 = {
                        "_token": token2,
                        "start_date": start_date,
                        "end_date": end_date,
                        "t": 
                    }
                    print(data2)
                    headers2 = {
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36',
                        'cookie': "PHPSESSID=" + login.cookies.get("PHPSESSID") + ";XSRF-TOKEN=" + login.cookies.get(
                            "XSRF-TOKEN") + ";laravel_session=" + login.cookies.get("laravel_session"),
                    }
                    url2 = "https://weixine.ustc.edu.cn/2020/apply/daliy/post"
                    resp2 = login.session.post(url2, data=data2, headers=headers2)

                    # to check if apply success

                    data = login.session.get("https://weixine.ustc.edu.cn/2020/apply_total").text
                    soup = BeautifulSoup(data, 'html.parser')
                    pattern = re.compile("202[0-9]-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}")
                    token = soup.find("table")
                    flag = False
                    if pattern.search(token.text) is not None:
                        date1 = pattern.search(token.text).group()
                        print("Latest apply: " + date1)
                        date1 = date1 + " +0800"
                        reporttime = datetime.datetime.strptime(date1, "%Y-%m-%d %H:%M:%S %z")
                        timenow = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
                        delta = timenow - reporttime
                        print("{} second(s) before.".format(delta.seconds))
                        if delta.seconds < 120:
                            flag = True
                    if flag == False:
                        print("Report FAILED!")
                    else:
                        print("Report SUCCESSFUL!")

            return flag
        else:
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='URC nCov auto report script.')
    parser.add_argument('data_path', help='path to your own data used for post method', type=str)
    parser.add_argument('stuid', help='your student number', type=str)
    parser.add_argument('password', help='your CAS password', type=str)
    args = parser.parse_args()
    autorepoter = Report(stuid=args.stuid, password=args.password, data_path=args.data_path)
    count = 5
    while count != 0:
        ret = autorepoter.report
        if ret != False:
            break
        print("Report Failed, retry...")
        count = count - 1
    if count != 0:
        exit(0)
    else:
        exit(-1)
