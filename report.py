#!/bin/python3
# encoding=utf8
import requests
import json
import re
import argparse
import io
from bs4 import BeautifulSoup
import PIL
import pytesseract
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
CAS_RETURN_URL = "https://weixine.ustc.edu.cn/2020/caslogin"
UPLOAD_PAGE_URL = "https://weixine.ustc.edu.cn/2020/upload/xcm"
UPLOAD_IMAGE_URL = "https://weixine.ustc.edu.cn/2020img/api/upload_for_student"
UPLOAD_INFO = [
    (1, "14-day Big Data Trace Card")
]
DEFAULT_PIC = ['https://raw.githubusercontent.com/pipixia244/South_Seven-AutoReport/master/14day.jpg', 
               'https://raw.githubusercontent.com/pipixia244/South_Seven-AutoReport/master/ankang.jpg']

class Report(object):
    def __init__(self, stuid, password, data_path, emer_person, relation, emer_phone, location, dbca, dl):
        self.stuid = stuid
        self.password = password
        self.data_path = data_path
        self.emer_person = emer_person
        self.relation = relation
        self.emer_phone = emer_phone
        if location == 1 or location == "1": #校外
            self.in_school = 0
            self.city_area = dbca
            self.detailed_location = dl
        else:
            self.in_school = 1
            self.dorm_building = dbca
            self.dorm = dl

    def login_retry(self):
        # 统一验证登录
        loginsuccess = False
        retrycount = 5
        while (not loginsuccess) and retrycount:
            session = self.login()
            cookies = session.cookies
            getform = session.get("https://weixine.ustc.edu.cn/2020")
            retrycount = retrycount - 1
            if getform.url != "https://weixine.ustc.edu.cn/2020/home":
                print("Login Failed! Retrying...")
            else:
                print("Login Successful!")
                loginsuccess = True
        if not loginsuccess:
            return False
        self.session = session
        return True

    def report(self):
        session = self.session
        cookies = session.cookies
        getform = session.get("https://weixine.ustc.edu.cn/2020")
        # 获取基本数据信息
        data = getform.text
        data = data.encode('ascii','ignore').decode('utf-8','ignore')
        soup = BeautifulSoup(data, 'html.parser')
        token = soup.find("input", {"name": "_token"})['value']

        with open(self.data_path, "r+") as f:
            data = f.read()
            data = json.loads(data)
            data["jinji_lxr"]=self.emer_person
            data["jinji_guanxi"]=self.relation
            data["jiji_mobile"]=self.emer_phone
            if not self.in_school:
                data["juzhudi"] = "合肥市内校外"
                data["jutiwz"] = self.detailed_location
                data["city_area"] = self.city_area
            else:
                data["dorm_building"]=self.dorm_building
                data["dorm"]=self.dorm
            data["_token"]=token
        
        #print(data)

        # 自动健康打卡
        headers = {
            'authority': 'weixine.ustc.edu.cn',
            'origin': 'https://weixine.ustc.edu.cn',
            'upgrade-insecure-requests': '1',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.100 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'referer': 'https://weixine.ustc.edu.cn/2020/home',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cookie': "PHPSESSID=" + cookies.get("PHPSESSID") + ";XSRF-TOKEN=" + cookies.get("XSRF-TOKEN") + ";laravel_session="+cookies.get("laravel_session"),
        }

        url = "https://weixine.ustc.edu.cn/2020/daliy_report"
        resp=session.post(url, data=data, headers=headers)
        #print(resp)
        res = session.get("https://weixine.ustc.edu.cn/2020/apply/daliy/i?t=3")
        if(res.status_code < 400 and (res.url == "https://weixine.ustc.edu.cn/2020/upload/xcm" or res.url == "https://weixine.ustc.edu.cn/2020/apply/daliy/i?t=3")):
            print("report success!")
            return True
        elif(res.status_code < 400 and res.url != "https://weixine.ustc.edu.cn/2020/upload/xcm"):
            print(res.url)
            print("report failed")
            return False
        else:
            print("unknown error, code: "+str(res.status_code))
            return False
        
    def report2(self):
        # 自动出校报备
        session = self.session
        ret = session.get("https://weixine.ustc.edu.cn/2020/apply/daliy/i?t=3")
        #print(ret.status_code)
            
        print("开始例行报备.")
        data = ret.text
        data = data.encode('ascii','ignore').decode('utf-8','ignore')
        soup = BeautifulSoup(data, 'html.parser')
        token2 = soup.find("input", {"name": "_token"})['value']
        start_date = soup.find("input", {"id": "start_date"})['value']
        end_date = soup.find("input", {"id": "end_date"})['value']
        
        print("{}---{}".format(start_date, end_date))
        REPORT_URL = "https://weixine.ustc.edu.cn/2020/apply/daliy/ipost"
        RETURN_COLLEGE = {'东校区', '西校区', '中校区', '南校区', '北校区', '高新校区', '先研院', '国金院'}
        REPORT_DATA = {
            '_token': token2,
            'start_date': start_date,
            'end_date': end_date,
            'return_college[]': RETURN_COLLEGE,
            'reason': "校内上课/考试",
            'comment': "上课/自习",
            't': 3,
        }
        ret = session.post(url=REPORT_URL, data=REPORT_DATA)
        
        # #删除占用码(可选功能, 默认关闭, 若想开启请取消注释)
        # if (is_new_upload == 1 and is_user_upload == 0):
        #    print("delete.")
        #    header = session.headers
        #    header['referer'] = "https://weixine.ustc.edu.cn/2020/upload/xcm"
        #    header['X-CSRF-TOKEN'] = token2
        #    ret1 = session.post("https://weixine.ustc.edu.cn/2020/upload/1/delete", headers=header)
        #    ret2 = session.post("https://weixine.ustc.edu.cn/2020/upload/2/delete", headers=header)
        #    if(ret1.status_code < 400 and ret2.status_code < 400):
        #        print("delete success.")
        #    else:
        #        print(f"delete error, error code: {ret1} and {ret2}.") 

        if ret.status_code == 200:
            print("success! code: "+str(ret.status_code))
            return True
        else:
            print("error occured, code: "+str(ret.status_code))
            return False
        



    def login(self):
        retries = Retry(total=5,
                        backoff_factor=0.5,
                        status_forcelist=[500, 502, 503, 504])
        s = requests.Session()
        s.mount("https://", HTTPAdapter(max_retries=retries))
        s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67"
        url = "https://passport.ustc.edu.cn/login?service=http%3A%2F%2Fweixine.ustc.edu.cn%2F2020%2Fcaslogin"
        r = s.get(url, params={"service": CAS_RETURN_URL})
        x = re.search(r"""<input.*?name="CAS_LT".*?>""", r.text).group(0)
        cas_lt = re.search(r'value="(LT-\w*)"', x).group(1)

        CAS_CAPTCHA_URL = "https://passport.ustc.edu.cn/validatecode.jsp?type=login"        
        r = s.get(CAS_CAPTCHA_URL)
        img = PIL.Image.open(io.BytesIO(r.content))
        pix = img.load()
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                r, g, b = pix[i, j]
                if g >= 40 and r < 80:
                    pix[i, j] = (0, 0, 0)
                else:
                    pix[i, j] = (255, 255, 255)
        lt_code = pytesseract.image_to_string(img).strip()
        
        
        data = {
            'model': 'uplogin.jsp',
            'service': 'https://weixine.ustc.edu.cn/2020/caslogin',
            'username': self.stuid,
            'password': str(self.password),
            'warn': '',
            'showCode': '1',
            'button': '',
            'CAS_LT': cas_lt,
            'LT': lt_code
        }
        print("lt-code is {}, login...".format(lt_code))
        s.post(url, data=data)
        self.session = s
        return s


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='URC nCov auto report script.')
    parser.add_argument('--data_path', help='path to your own data used for post method', type=str)
    parser.add_argument('--stuid', help='your student number', type=str)
    parser.add_argument('--password', help='your CAS password', type=str)
    parser.add_argument('--emer_person', help='emergency person', type=str)
    parser.add_argument('--relation', help='relationship between you and he/she', type=str)
    parser.add_argument('--emer_phone', help='phone number', type=str)
    parser.add_argument('--location', help='location, 1 for out of school and other for in school', type=str)
    parser.add_argument('--dormbuildingORcityarea', help='dorm building num or your city area, depending on your location input.', type=str)
    parser.add_argument('--dormORlocation', help='dorm number or detailed location, depending on your location input.', type=str)
    args = parser.parse_args()
    autorepoter = Report(stuid=args.stuid, password=args.password, data_path=args.data_path, emer_person=args.emer_person, 
                         relation=args.relation, emer_phone=args.emer_phone, dbca=args.dormbuildingORcityarea, dl=args.dormORlocation, 
                         location=args.location)
    count = 5
    while count != 0:
        autorepoter.login_retry()
        ret1 = autorepoter.report()
        ret2 = autorepoter.report2()
        if ret1 and ret2 != False:
            break
        print("Report Failed, retry...")
        count = count - 1
    if count != 0:
        exit(0)
    else:
        exit(-1)
