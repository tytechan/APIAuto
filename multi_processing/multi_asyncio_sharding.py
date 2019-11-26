from multiprocessing import  Pool
import asyncio
import time
import requests
import json
import copy


class MultiPro():
    def __init__(self):
        # # 错误接口数初始化
        # self.errNum = 0
        # 环境地址
        self.Environment_Select = \
            {
                "200": "http://cdwpdev01.chinacloudapp.cn:9001",
                "500": "http://kintergration.chinacloudapp.cn:9002",
                "400": "http://cdwpdev01.chinacloudapp.cn:9400",
                "450": "http://cdwpdev01.chinacloudapp.cn:9003",
                "510": "http://kintergration01.chinacloudapp.cn:9510",
                "530": "http://kintergration01.chinacloudapp.cn:9530",
                "600": "http://kintergration.chinacloudapp.cn:9003",
                "700": "http://kdevelop.chinacloudapp.cn:9003",
                "810": "http://pre-mongodb-01.chinacloudapp.cn:9003",
                "sharding": "http://pt-kuserapp.chinacloudapp.cn",
            }

        # 接口信息
        self.API = \
            {
                "首页标签页": "/approval/getcountbytype",
                "待办查询": "/approval/mydoing",

            }

        self.data = \
            {
                "标签页_待办": [{"showtype": ["mydoings"]}],
                "标签页_已办": [{"showtype": ["mydones"]}],
                "标签页_订阅": [{"showtype": ["mysubscribers"]}],
                "标签页_申请": [{"showtype": ["myapplys"]}],
                "标签页_草稿": [{"showtype": ["mybegins"]}],

                "待办_销售合同": [{"page":1,"limit":20,"processtype":["CONT","CONT_CHANGE","CONT_CONTENTCHANGE","COGN","COGN_CHANGE","COGN_CONTENTCHANGE","SERVICE_CONT","SERVICE_CONT_CHANGE","CONT_CANCEL","COGNCONT_CANCEL"],"querys":{},"orderby":{}}],
                "待办_采购合同": [{"page":1,"limit":20,"processtype":["CGHT","CGHT_CHANGE","CGHT_CANCEL"],"querys":{}}],
                "待办_付款申请": [{"page":1,"limit":20,"processtype":["FKSQ","HBFK","FKZF","FKBG"],"querys":{"ZSQJE":"","ZSJFKJE":""}}],
                "待办_开票申请": [{"page":1,"limit":20,"processtype":["KPSQN"],"querys":{"kptype":"kpfast","ZFPLX":"","contracttype":""}}],

            }


    def multi_api(self, url, header, data, method="post"):
        global results
        try:
            s = requests.session()
            data = json.dumps(data).replace("'", "\"")
            if method == "post":
                results = s.post(url, headers=header, data=data)
            if method == "get":
                results = s.get(url)
            return results.json()
        except requests.ConnectionError:
            return results


    async def fristwork(self, url, header, data, error):
        # global sucNum,errNum
        await asyncio.sleep(1)
        r = self.multi_api(url, header, data)
        if r.get("code") != 200:
            # error.append(r.get("msg"))
            error.append(r.get("message"))
            # errNum += 1
        print("fristwork take", str(time.time()))
        return "Done"

    async def secondwork(self, url, header, data, error):
        a = await  self.fristwork(url, header, data, error)
        print (a)

    def task(self, url, header, data, error):
        coroutine = self.secondwork(url, header, data, error)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(coroutine)
        # print("task {}".format(num))

    async def run_more(self, num, poolNUm, url, header, data):
        global error
        print("start run_more")
        pool = Pool(processes = poolNUm)
        myData = copy.deepcopy(data)

        error = []

        for i in range(num):
            pool.apply_async(self.task, args=(url, header, myData, error))
        # for i in range(num):
        #     for j in range(sumPerTime):
        #         box = "CZDH" + str(int(initialBox.replace("CZDH","")) + j)
        #         myData["box_codes"].append(box)
        #
        #         if j + 1 == sumPerTime:
        #             # del initialBox
        #             initialBox = "CZDH" + str(int(box.replace("CZDH","")) + 1)
        #
        #     pool.apply_async(task, args=(url, header, myData, error))
        #     print("第 ",i+1," 次并发开始...")
        #     myData = copy.deepcopy(data)
        #     # time.sleep(loop_sleep)

        pool.close()
        pool.join()

    def main(self, num, poolNUm, url, header, data):
        '''
        :param num: 并发数
        :param poolNUm: 进程池最大进程数
        '''
        # global errNum,sucNum
        # errNum = 0
        # sucNum = 0
        # error = []

        # 开始时间
        start = time.time()
        coroutine = self.run_more(num, poolNUm, url, header, data)
        tasks = [
            asyncio.ensure_future(coroutine),
        ]
        loop2 = asyncio.get_event_loop()
        loop2.run_until_complete(asyncio.wait(tasks))
        # 结束时间
        end = time.time()

        print("========================================================================")
        print("接口性能测试开始时间：", time.asctime(time.localtime(start)))
        print("接口性能测试结束时间：", time.asctime(time.localtime(end)))
        print("接口地址：", url)
        print("接口类型：", "post")
        print("总进程数：", coNum)
        print("最大进程数：", poolNUm)
        print("每个进程循环次数：", 1)
        # print("每次请求含箱数：", sumPerTime)
        # print("每次请求时间间隔：", 0)
        print("总请求数：", coNum * 1)
        print("总耗时（秒）：", end - start)
        print("每次请求耗时（秒）：", (end - start) / (coNum * 1))
        # print("成功数：", sucNum)
        # print("失败数：", errNum)
        # print("错误请求数：", len(error))
        print("错误信息：", error)
        print("每秒承载请求数（TPS)：", (coNum * 1) / (end - start))
        # print("平均响应时间（毫秒）：", CreateMultiprocesses.multi_response_avg())
        print("========================================================================")


    def requestDetail(self, APIType, dataType):
        # 登陆
        login_url = self.Environment_Select[env] + "/login"
        login_header = {"Content-Type": "application/json"}
        login_data = {"login": "hanpeng", "pwd": "12345sap"}

        login_result = self.multi_api(login_url,login_header,login_data)
        token = login_result["rst"]["data"]["token"]

        # 交易
        # errNum = 0
        # sucNum = 0

        url = self.Environment_Select[env] + self.API[APIType]
        header = \
            {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

        # data = \
        #     {
        #         "showtype": [
        #             "mydones"
        #         ]
        # }
        data = self.data[dataType][0]

        self.main(coNum, poolNUm, url, header, data)



if __name__ == '__main__':
    MP = MultiPro()

    # 基础数据
    env = "530"
    coNum = 200000                                  # 并发数
    poolNUm = 3                                # 进程池最大进程数

    # MP.requestDetail("首页标签页", "标签页_待办")
    MP.requestDetail("首页标签页", "标签页_待办")