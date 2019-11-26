#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TODO：仓储项目接口全部通过token绕过登陆，cookie使用方法已编写完成，待验证

# cookie_config01相关引包
import urllib.request, urllib.parse, urllib.error
import http.cookiejar


def login_cookie(login_url,username,password):
    '''
    headers在函数内写死，切换环境时可验证，此处为500 headers
    :param login_url: 登陆接口地址
    :param username: 登录名
    :param password: 登陆密码
    :return:
    '''
    LOGIN_URL = login_url
    values = {"login":username,
              "pwd":password}
    postdata = urllib.parse.urlencode(values).encode()
    user_agent = r'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
    headers = {'User-Agent': user_agent, 'Connection': 'keep-alive'}

    # 设置保存cookie的文件，同级目录下的cookie.txt
    cookie_filename = 'cookie.txt'
    # 声明一个MozillaCookieJar对象实例来保存cookie，之后写入文件
    cookie = http.cookiejar.MozillaCookieJar(cookie_filename)
    # 利用urllib.request库的HTTPCookieProcessor对象来创建cookie处理器,也就CookieHandler
    handler = urllib.request.HTTPCookieProcessor(cookie)
    # 通过CookieHandler创建opener
    opener = urllib.request.build_opener(handler)

    request = urllib.request.Request(LOGIN_URL, data=postdata, headers=headers)
    try:
        # 此处的open方法打开网页
        response = opener.open(request)
        page = response.read().decode()
        # print(page)
    except urllib.error.URLError as e:
        print(e.code, ':', e.reason)

    cookie.save(ignore_discard=True, ignore_expires=True)  # 保存cookie到cookie.txt中
    # print("获取登陆cookie 的值为：",cookie)

    """
    for item in cookie:
        print('😎 Name = ' + item.name)
        print('😎 Value = ' + item.value)


    data = {"doc":{"supplier":{"order":"cz-18062601","id":"1000006800","name":"测试","org":["1000","2000"]},"purchaser":{"vendee":"1000","group":"110","org":"1000","division":"01","employee":"李直"},"product_line":"F6","payments":[{"cate":"预付","percent":100,"days":3,"mode":"现金","cond":"合同生效之日起"}],"pay":{},"money":{"service":0,"device":1000,"amount":1000},"transport_type":"自提-陆运","rebate":{"percent":0,"device_percent":0,"service_percent":0,"amount":0,"device_amount":0,"service_amount":0,"items":[]},"addition":{"contacts":{},"attachment":{}},"items":[{"code":"00000002-F990","mater_type":"ZCP1","item_type":"ZCP1","group":"F99","origin_code":"00000002","model":"AR0MSDME2A00","factory":"1000","description":"2端口 通道化E1/PRI/VE1/T1 多功能接口卡","tax_rate":"J5","unit":"ST","unitname":"件","price":188.13,"pstat":"ELBSVG","checked":False,"count":20,"sum":1000}],"currency_type":"CNY","type":"NB","project_name":"自动化"}}
    data = urllib.parse.urlencode(data)
    binary_data = data.encode('utf-8')

    '''测试登陆接口'''
    get_url = 'http://kdevelop.chinacloudapp.cn:9002/login' # 验证该cookie能否通过登陆接口
    get_request = urllib.request.Request(get_url)
    get_response = opener.open(get_request)
    print("登陆响应为：",get_response.read().decode())

    '''测试其他接口'''
    # get_url = 'http://kintergration.chinacloudapp.cn:9002/purchase-contract/createProcess'  # 利用cookie请求访问另一个网址
    # get_request = urllib.request.Request(get_url, data=binary_data, headers=headers)
    # get_response = opener.open(get_request)
    # print("登陆响应为：",get_response.read().decode())
    """
    return cookie

def get_cookie_and_request(new_url, binary_data, headers):
    # 设置保存cookie的文件，同级目录下的cookie.txt
    cookie_filename = 'cookie.txt'
    # 声明一个MozillaCookieJar对象实例来保存cookie，之后写入文件
    cookie = http.cookiejar.MozillaCookieJar(cookie_filename)
    # 从文件中读取cookie内容到变量
    cookie.load(cookie_filename, ignore_discard=True, ignore_expires=True)
    print("使用登陆cookie 的值为：",cookie)

    # 利用urllib.request库的HTTPCookieProcessor对象来创建cookie处理器,也就CookieHandler
    handler = urllib.request.HTTPCookieProcessor(cookie)
    # 通过CookieHandler创建opener
    opener = urllib.request.build_opener(handler)

    # get_url = 'http://kdevelop.chinacloudapp.cn:9002/login'  # 利用cookie请求访问另一个网址
    get_url = new_url  # 利用cookie请求访问另一个网址
    get_request = urllib.request.Request(get_url, data=binary_data, headers=headers)
    # get_request = urllib.request.Request(get_url)
    get_response = opener.open(get_request)
    print("登陆响应为：",get_response.read().decode())


def get_cookie(url_login, username, password):
    import requests, urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    # url_login = "http://127.0.0.1:9009/login_action/"
    userdata = {'username': username, 'password': password}
    s = requests.session()
    rs = s.post(url_login, data=userdata)
    cookie = s.cookies.get_dict()
    return cookie
    # ev_url = "http://127.0.0.1:9009/api/add_event/"
    # payload = {'eid': '', 'limit': '', 'address': '', 'start_time': ''}
    # api = requests.post(ev_url, cookies=cookie, data=payload)
    # print(api.json())



if __name__ == '__main__':
    get_cookie("http://kintergration01.chinacloudapp.cn:9540/login","wangqiaochen","kuser540")

    # login_cookie("http://kintergration01.chinacloudapp.cn:9540/login","wangqiaochen","kuser540")
    #
    # header = \
    #     {
    #         "Content-Type": "application/json",
    #     }
    #
    # data = \
    #     {
    #         "doc": {
    #             "model": {
    #                 "department": {
    #                     "_id": "5742a607779ec2cb7405180c",
    #                     "name": "软件及应用事业部"
    #                 },
    #                 "isintegration": "0",
    #                 "cost": {
    #                     "jtjehz": 0,
    #                     "fromdate": "2019-03",
    #                     "haszzs": "否",
    #                     "typestr": "间接运营费用-仓储物流费",
    #                     "citytranscost": 0,
    #                     "enddate": "2019-03",
    #                     "invoicetypestr": "考试费",
    #                     "invoicetype": "1856067",
    #                     "othercost": 0,
    #                     "tripcost": [],
    #                     "category": "18",
    #                     "amount": "10",
    #                     "accomcost": 0,
    #                     "attanum": "3",
    #                     "costtype": "56",
    #                     "tax": ""
    #                 },
    #                 "profit_center": "8100A29001",
    #                 "limit": [
    #                     {
    #                         "virtual": "1",
    #                         "month": 3,
    #                         "using": 0,
    #                         "year": 2019
    #                     }
    #                 ],
    #                 "hasfysqd": "0",
    #                 "finance": {
    #                     "costcenterstr": "软件事业部公共成本中心",
    #                     "returnmoney": "0",
    #                     "due": 10,
    #                     "costcenter": "9100A21999",
    #                     "loan": 0
    #                 },
    #                 "extra": {
    #                     "note": "自动化"
    #                 },
    #                 "division": "4000",
    #                 "user": {
    #                     "_id": "5742a607779ec2cb74051a5d",
    #                     "code": "00001853",
    #                     "login": "wangqiaochen",
    #                     "name": "王乔晨",
    #                     "costype": "9100A21999"
    #                 },
    #                 "jcfwxm": {},
    #                 "amount": "10",
    #                 "fysqd": [],
    #                 "corp": "1000",
    #                 "applydate": "2019-03-26"
    #             }
    #         }
    #     }
    #
    # get_cookie_and_request("http://kintergration01.chinacloudapp.cn:9540/reimburse/createprocess", data, header)