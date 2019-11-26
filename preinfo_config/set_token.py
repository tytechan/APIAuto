#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import urllib.request, urllib.parse, urllib.error
from .interface_config import *

def initial_json(data):
    # 按照标准格式格式化json数据
    return json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

def get_token(url, username, password, errInfo=True):

    header = \
        {
            "Content-Type": "application/json"
        }
    # header = json.dumps(header)

    body = {"login": username, "pwd": password}
    # body = initial_json(body)
    body = json.dumps(body)
    # print(body)


    # 方法一：requests.session
    login_ret = myRequest(url, data=body, headers=header)
    # print("登陆响应：",login_ret)

    if errInfo:
        login_code = combineJson(login_ret,"code")
        try:
            assert login_code == "200", \
            "😭 用户登陆失败，响应码为： '%s'" %login_code
            try:
                token = login_ret["rst"]["data"]["token"]
                # print("🙊 你要的token： ",token)
                return token
            except Exception as e:
                raise e
        except AssertionError as e:
            raise AssertionError(e)
        except Exception as e:
            raise e
    else:
        if login_ret is None \
                or login_ret.get("code") != 200:
        # if login_ret is None:
            return ""
        else:
            return login_ret["rst"]["data"]["token"]



    # 方法二：urllib.request
    '''
    # header = urllib.parse.urlencode(header).encode('utf-8')
    # body = urllib.parse.urlencode(body).encode('utf-8')
    request = urllib.request.Request(url=url, data=body, headers=header, method='POST')

    response = urllib.request.urlopen(request)
    print("登陆响应为：",response.read().decode('utf-8'))
    token = response.json()["rst"]["data"]["token"]
    return token
    '''


    # 方法三：requests.post
    '''
    login_url = url
    r = requests.post(login_url, data=body,headers=header)
    print("登陆响应为：",r.json()['code'])
    token = r.json()["rst"]["data"]["token"]
    return token
    '''


if __name__ == '__main__':
    token = get_token("http://kintergration.chinacloudapp.cn:9002/login","zhangwenshu","123sap")
    print("🙊 你要的token： ",token)

    post_url = "http://kintergration.chinacloudapp.cn:9002/purchase-contract/createProcess"

    # 添加token到请求头
    header = \
    {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    }

    print("headers :",header)

    data = \
    {
        "doc": {
            "supplier": {
                "order": "cz-18062702",
                "id": "1000006800",
                "name": "测试",
                "org": [
                    "1000",
                    "2000"
                ]
            },
            "purchaser": {
                "vendee": "1000",
                "org": "1000",
                "group": "110",
                "division": "01",
                "employee": "李直"
            },
            "product_line": "F6",
            "payments": [
                {
                    "cate": "预付",
                    "percent": 100,
                    "days": 3,
                    "mode": "现金",
                    "cond": "合同生效之日起"
                }
            ],
            "pay": {

            },
            "money": {
                "service": 0,
                "device": 1000,
                "amount": 1000
            },
            "transport_type": "自提-陆运",
            "rebate": {
                "percent": 0,
                "device_percent": 0,
                "service_percent": 0,
                "amount": 0,
                "device_amount": 0,
                "service_amount": 0,
                "items": [

                ]
            },
            "addition": {
                "contacts": {

                },
                "attachment": {

                }
            },
            "items": [
                {
                    "code": "00000002-F990",
                    "mater_type": "ZCP1",
                    "item_type": "ZCP1",
                    "group": "F99",
                    "origin_code": "00000002",
                    "model": "AR0MSDME2A00",
                    "factory": "1000",
                    "description": "2端口 通道化E1/PRI/VE1/T1 多功能接口卡",
                    "tax_rate": "J5",
                    "unit": "ST",
                    "unitname": "件",
                    "price": 188.13,
                    "pstat": "ELBSVG",
                    "count": 20,
                    "sum": 1000
                }
            ],
            "currency_type": "CNY",
            "type": "NB",
            "project_name": "自动化"
        }
    }

    s = requests.session()
    data = json.dumps(data)
    # post_ret = s.post(post_url, data=data)
    post_ret = s.post(post_url, headers=header,data=data)
    # print(post_ret.json())
    print(initial_json(post_ret.json()))