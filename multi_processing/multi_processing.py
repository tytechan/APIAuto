#!/usr/bin/env python
# -*- coding: utf_8 -*-

import multiprocessing,threading
import requests
import time
import re
import json
from time import sleep


# -------接口性能测试配置-------
method = "post"
# 接口类型
url = "http://kintergration.chinacloudapp.cn:9002/login"
# 接口地址
header = \
    {
        "Content-Type": "application/json"
    }
data = {"login": "yanyongfeng", "pwd": "123sap"}
data = json.dumps(data).replace("'","\"")
# 接口参数
multi_num = 4
# 线程数
one_work_num = 1
# 每个线程循环次数
loop_sleep = 5
# 每次请求时间间隔
response_time = []
# 平均响应时间列表
error = []
# 错误信息列表
maxNum = 2


class CreateMultiprocesses:
    def __init__(self):
        pass

    @classmethod
    def multi_api(cls, header, data):
        global results
        try:
            s = requests.session()
            data = json.dumps(data).replace("'","\"")
            if method == "post":
                results = s.post(url, headers=header, data=data)
            if method == "get":
                results = s.get(url)
            return results
        except requests.ConnectionError:
            return results
    # 接口函数

    @classmethod
    def multi_response(cls):
        responsetime = float(CreateMultiprocesses.multi_api(data, header).elapsed.microseconds) / 1000
        return responsetime
    # 获取响应时间 单位ms

    @classmethod
    def multi_response_avg(cls):
        avg = 0.000
        l = len(response_time)
        for num in response_time:
            avg += 1.000 * num / l
        return avg
    # 获取平均相应时间 单位ms

    @classmethod
    def multi_time(cls):
        return time.asctime(time.localtime(time.time()))
    # 获取当前时间格式

    @classmethod
    def multi_error(cls):
        try:
            pa = u"个人信息"
            pattern = re.compile(pa)
            match = pattern.search(CreateMultiprocesses.multi_api(header, data).text)
            if CreateMultiprocesses.multi_api(header, data).status_code == 200:
                pass
                if match.group() == pa:
                    pass
            else:
                error.append(CreateMultiprocesses.multi_api().status_code)
        except AttributeError:
            error.append("登录失败")
    # 获取错误的返回状态码

    # @classmethod
    # def multi_work(cls,msg):
    #     multiname = threading.currentThread().getName()
    #     print("[", multiname, "] Sub Multi Begin")
    #     for i in range(one_work_num):
    #         print(msg)
    #         CreateMultiprocesses.multi_api()
    #         print("接口请求时间： ", CreateMultiprocesses.multi_time())
    #         response_time.append(CreateMultiprocesses.multi_response())
    #         CreateMultiprocesses.multi_error()
    #         sleep(loop_sleep)
    #     print("[", multiname, "] Sub Multi End")
    # # 工作线程循环

    @classmethod
    def multi_work(cls,msg):
        multiname = threading.currentThread().getName()
        print("[", multiname, "] Sub Multi Begin")
        for i in range(one_work_num):
            print("第 ",msg+1," 次请求！")

            data = \
                {
                    "box_codes": [],
                    "tray": tray
                }

            # 用于迭代添加多个箱号数据
            for i in range(boxNumPerTime):
                box = "CZDH" + str(int(boxInitial.replace("CZDH","")) + i)
                data["box_codes"].append(box)

            CreateMultiprocesses.multi_api(header, data)
            print("接口请求时间： ", CreateMultiprocesses.multi_time())
            response_time.append(CreateMultiprocesses.multi_response())
            CreateMultiprocesses.multi_error()
            sleep(loop_sleep)
        print("[", multiname, "] Sub Multi End")
    # 工作线程循环

    @classmethod
    def multi_main(cls):
        start = time.time()
        # multis = []
        p = multiprocessing.Pool(processes = maxNum)
        for i in range(multi_num):
            t = p.apply_async(CreateMultiprocesses.multi_work(i,))
            t.daemon = True
            # multis.append(t)

        p.close()
        p.join()
        # 主线程中等待所有子线程退出
        end = time.time()

        print("========================================================================")
        print("接口性能测试开始时间：", time.asctime(time.localtime(start)))
        print("接口性能测试结束时间：", time.asctime(time.localtime(end)))
        print("接口地址：", url)
        print("接口类型：", method)
        print("总进程数：", multi_num)
        print("最大进程数：", maxNum)
        print("每个进程循环次数：", one_work_num)
        print("每次请求时间间隔：", loop_sleep)
        print("总请求数：", multi_num * one_work_num)
        print("错误请求数：", len(error))
        print("总耗时（秒）：", end - start)
        print("每次请求耗时（秒）：", (end - start) / (multi_num * one_work_num))
        print("每秒承载请求数（TPS)：", (multi_num * one_work_num) / (end - start))
        print("平均响应时间（毫秒）：", CreateMultiprocesses.multi_response_avg())
        print("========================================================================")


if __name__ == '__main__':
    CM = CreateMultiprocesses()
    # 登陆
    url = "http://cdwpdev01.chinacloudapp.cn:9400/login"
    header = {"Content-Type": "application/json"}
    data = {"login": "liuqing", "pwd": "123sap"}
    r = CM.multi_api(header, data).json()
    token = r["rst"]["data"]["token"]
    del url,header

    # 交易
    url = "http://cdwpdev01.chinacloudapp.cn:9400/wms-core/uptray"
    header = {"Authorization": "Bearer " + token,"Content-Type": "application/json"}

    boxInitial = "CZDH1812190583"
    tray = "1000000145"
    boxNumPerTime = 1
    # data = {"login": "liuqing", "pwd": "123sap"}
    # data = json.dumps(data).replace("'","\"")
    CreateMultiprocesses.multi_main()