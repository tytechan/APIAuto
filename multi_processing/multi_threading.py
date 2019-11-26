#!/usr/bin/env python
# -*- coding: utf_8 -*-

import threading
import threadpool
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
thread_num = 5
# 线程数
one_work_num = 1
# 每个线程循环次数
loop_sleep = 0
# 每次请求时间间隔
response_time = []
# 平均响应时间列表
error = []
# 错误信息列表


class CreateThread:
    def __init__(self):
        pass

    @classmethod
    def thread_api(cls):
        global results
        try:
            s = requests.session()
            if method == "post":
                results = s.post(url, headers=header, data=data)
            if method == "get":
                results = s.get(url)
            return results
        except requests.ConnectionError:
            return results
    # 接口函数

    @classmethod
    def thread_response(cls):
        responsetime = float(CreateThread.thread_api().elapsed.microseconds) / 1000
        return responsetime
    # 获取响应时间 单位ms

    @classmethod
    def thread_response_avg(cls):
        avg = 0.000
        l = len(response_time)
        for num in response_time:
            avg += 1.000 * num / l
        return avg
    # 获取平均相应时间 单位ms

    @classmethod
    def thread_time(cls):
        return time.asctime(time.localtime(time.time()))
    # 获取当前时间格式

    @classmethod
    def thread_error(cls):
        try:
            pa = u"个人信息"
            pattern = re.compile(pa)
            match = pattern.search(CreateThread.thread_api().text)
            if CreateThread.thread_api().status_code == 200:
                pass
                if match.group() == pa:
                    pass
            else:
                error.append(CreateThread.thread_api().status_code)
        except AttributeError:
            error.append("登录失败")
    # 获取错误的返回状态码

    @classmethod
    def thread_work(cls):
        threadname = threading.currentThread().getName()
        print("[", threadname, "] Sub Thread Begin")
        for i in range(one_work_num):
            CreateThread.thread_api()
            print("接口请求时间： ", CreateThread.thread_time())
            response_time.append(CreateThread.thread_response())
            CreateThread.thread_error()
            sleep(loop_sleep)
        print("[", threadname, "] Sub Thread End")
    # 工作线程循环

    @classmethod
    def thread_main(cls):
        start = time.time()
        threads = []
        for i in range(thread_num):
            t = threading.Thread(target=CreateThread.thread_work())
            t.setDaemon(True)
            threads.append(t)
        for t in threads:
            t.start()
        # 启动所有线程
        for t in threads:
            t.join()
        # 主线程中等待所有子线程退出
        end = time.time()

        print("========================================================================")
        print("接口性能测试开始时间：", time.asctime(time.localtime(start)))
        print("接口性能测试结束时间：", time.asctime(time.localtime(end)))
        print("接口地址：", url)
        print("接口类型：", method)
        print("线程数：", thread_num)
        print("每个线程循环次数：", one_work_num)
        print("每次请求时间间隔：", loop_sleep)
        print("总请求数：", thread_num * one_work_num)
        print("错误请求数：", len(error))
        print("总耗时（秒）：", end - start)
        print("每次请求耗时（秒）：", (end - start) / (thread_num * one_work_num))
        print("每秒承载请求数（TPS)：", (thread_num * one_work_num) / (end - start))
        print("平均响应时间（毫秒）：", CreateThread.thread_response_avg())
        print("========================================================================")


if __name__ == '__main__':
    CreateThread.thread_main()