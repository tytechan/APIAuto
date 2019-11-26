from multiprocessing import  Pool
import asyncio
import time
import requests
import json
import copy
import threading
import random


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
        self. API = \
            {
                "查询": "/data-api/topic-analyse/list",
                "新建采购合同": "/purchase-contract/createProcess",
                "新建采购确认单": "/purchase_confirm/createProcess",
            }
        self.data = \
            {
                "choice": {
                    "group": [],
                    "order": [],
                    "page": {
                        "num": 1,
                        "size": 100
                    },
                    "where": {
                        "contract_code": ""
                    }
                },
                "topic": "DeliveryProcessTopic"
            }

        self.contractNoList = ["SOA1910000034", "SON2019000013", "SON2019000007", "SON2019000001", "SON2018013878-V001", "SOA1910000013", "SOA1909000036", "SOA1910000010", "SOA1910000043", "SOSA1910000003", "SOSA1910000004", "SOSB1910000005", "SOSB1910000008", "SOA1910000061"]
        self.caigoudingdanList = ["4500087359", "4500074036", "4500087359"]
        self.gongyingshangList = ["20190929001", "1Y02501812160K", "1Y05101812240G", "1Y01001812210U", "1Y02101809090J", "CG201910110003", "XX2019101701"]

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


    async def fristwork(self, url, header, error, dataType):
        # global sucNum,errNum
        await asyncio.sleep(1)

        data = copy.deepcopy(self.data)
        contractNo = random.choice(self.contractNoList)
        # print(contractNo)
        caigoudingdan = random.choice(self.caigoudingdanList)
        print(caigoudingdan)
        gongyingshang = random.choice(self.gongyingshangList)
        # print(gongyingshang)

        if dataType == "按销售合同号查询":
            data["choice"]["where"] = {"contract_code": contractNo}
        elif dataType == "按采购订单号查询":
            data["choice"]["where"] = {"sap_code":["in",[caigoudingdan]]}
        elif dataType == "按供应商订单号查询":
            data = {"topic":"SalesContractProcessTopic","choice":{"where":{"supplier_orders":gongyingshang},"group":[],"order":["fullcode desc"],"page":{"num":1,"size":25}}}
        elif dataType == "链接点击放货过账金额":
            data = {"topic":"DeliveryProcessTopic","choice":{"where":{"contract_code":contractNo},"group":[],"order":[],"page":{"num":1,"size":100}}}
        elif dataType == "链接点击开票金额":
            data = {"topic":"InvoiceProcessTopic","choice":{"where":{"sales_contract_code":contractNo},"group":[],"order":["code asc"],"page":{"num":1,"size":100}}}
        elif dataType == "链接点击红票金额":
            data = {"topic":"InvoiceProcessTopic","choice":{"where":{"sales_contract_code":contractNo},"group":[],"order":["code asc"],"page":{"num":1,"size":100}}}
        elif dataType == "链接点击应收金额":
            data = {"topic":"ReceivablesTopic","choice":{"where":{"contract_code":contractNo},"group":[],"order":["code desc"],"page":{"num":1,"size":100}}}
        elif dataType == "链接点击已付款金额":
            data = {"topic":"PaymentProcessTopic","choice":{"where":{"purchase_order_id":caigoudingdan},"group":[],"order":["code asc"],"page":{"num":1,"size":25}}}
        elif dataType == "链接点击冲抵核销金额":
            data = {"topic":"PaymentProcessTopic","choice":{"where":{"purchase_order_id":caigoudingdan},"group":[],"order":["code asc"],"page":{"num":1,"size":25}}}

        elif dataType == "新建采购合同":
            data = {
                "doc": {
                    "addition": {
                        "attachment": {},
                        "contacts": {}
                    },
                    "currency_type": "CNY",
                    "items": [
                        {
                            "checked": False,
                            "code": "00007YAQ-FCA00",
                            "count": 10,
                            "description": "2U机架式结构；1TB硬盘；最大配置为34个接口，默认包括4光4电千兆接口扩展卡、3个可插拨的扩展槽和2个10/100/1000BASE-T接口；标配双电源，接口支持Bypass；处理能力≥1200Mbps；最大并发连接≥12,000,000；四层处理能力≥150K CPS；七层处理能力≥425K RPS；最大SSL加密吞吐量≥8Gbps",
                            "factory": "1000",
                            "group": "FC",
                            "item_type": "ZCP1",
                            "mater_type": "ZCP1",
                            "model": "天融信安全审计系统V3（TCM-51612）",
                            "origin_code": "00007YAQ",
                            "price": 1.68,
                            "pstat": "ELBSVG",
                            "status": "0",
                            "sum": 5000,
                            "tax_rate": "J7",
                            "unit": "ST",
                            "unitname": "件"
                        },
                        {
                            "checked": False,
                            "code": "00010RFZ-FCA00",
                            "count": 10,
                            "description": "用于此设备配套系统功能软件",
                            "factory": "1000",
                            "group": "FC",
                            "item_type": "ZCP5",
                            "mater_type": "ZCP5",
                            "model": "AD-1000-G642-1",
                            "origin_code": "00010RFZ",
                            "price": 43.36,
                            "pstat": "ELBSVG",
                            "status": "0",
                            "sum": 5000,
                            "tax_rate": "J7",
                            "unit": "ST",
                            "unitname": "件"
                        }
                    ],
                    "money": {
                        "amount": 10000,
                        "device": 10000,
                        "service": 0
                    },
                    "pay": {},
                    "payments": [
                        {
                            "cate": "货款",
                            "cond": "发货前",
                            "days": 7,
                            "mode": "电汇",
                            "percent": 100
                        }
                    ],
                    "product_line": "F1",
                    "profit_center": "8100A10005",
                    "project_name": "自动化",
                    "purchaser": {
                        "division": "10",
                        "employee": "罗莎莎",
                        "group": "110",
                        "org": "1000",
                        "vendee": "1000"
                    },
                    "rebate": {
                        "amount": 0,
                        "device_amount": 0,
                        "device_percent": 0,
                        "items": [],
                        "percent": 0,
                        "service_amount": 0,
                        "service_percent": 0
                    },
                    "sales_conts": [],
                    "sales_info": {
                        "org": {
                            "_id": "5742a607779ec2cb740517fd",
                            "orgname": "华北区"
                        },
                        "sales_group": "华北区",
                        "user": {
                            "_id": "5742a607779ec2cb74051877",
                            "login": "liukai",
                            "name": "刘凯"
                        }
                    },
                    "supplier": {
                        "id": "1000000010",
                        "name": "华为软件技术有限公司",
                        "order": "自动化191023000011",
                        "org": [
                            "1000",
                            "1002",
                            "2002",
                            "3002",
                            "9002"
                        ]
                    },
                    "transport_type": "自提-陆运",
                    "type": "NB"
                }
            }
        elif dataType == "新建采购确认单":
            data = {
            "doc": {
                "base": {
                    "customer": "华为",
                    "order_type": "NB",
                    "pay_type": "电汇",
                    "product_line": "F1",
                    "project": "zidonghua",
                    "purchase_group": "110",
                    "supplier": {
                        "id": "1000000091",
                        "name": "华为数字技术（苏州）有限公司"
                    },
                    "supplier_order_code": "自动化191023000002",
                    "transport_type": "自提-陆运",
                    "vendee": {
                        "id": "1000",
                        "name": "中建材信息技术股份有限公司"
                    }
                },
                "cost": {
                    "amount": 10000,
                    "currency": "CNY",
                    "device_amount": 0,
                    "service_amount": 10000
                },
                "extra_info": {
                    "daibiaochu": "安徽代表处"
                },
                "items": [
                    {
                        "checked": False,
                        "code": "XMPT000012",
                        "count": 10,
                        "factory": "1000",
                        "group": "FX",
                        "item_type": "ZCP5",
                        "mater_type": "ZCP5",
                        "origin_code": "XMPT000002",
                        "price": 1.53,
                        "pstat": "VELSBG",
                        "station": "10",
                        "sum": 10000,
                        "tax_rate": "J3",
                        "unit": "ST",
                        "unitname": "件"
                    }
                ],
                "sales_info": {
                    "isurgentinvoice": "0"
                }
            }
        }

        myData = copy.deepcopy(data)


        r = self.multi_api(url, header, myData)
        if r.get("code") != 200:
            # error.append(r.get("msg"))
            error.append(r.get("message"))
            # errNum += 1
        print("fristwork take", str(time.time()))
        return "Done"

    async def secondwork(self, url, header, error, dataType):
        a = await  self.fristwork(url, header, error, dataType)
        print (a)

    def task(self, url, header, data, error):
        coroutine = self.secondwork(url, header, data, error)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(coroutine)
        # print("task {}".format(num))

    async def run_more(self, num, poolNUm, url, header, dataType):
        global error
        print("start run_more")
        pool = Pool(processes = poolNUm)

        error = []

        for i in range(num):
            pool.apply_async(self.task, args=(url, header, error, dataType))
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

    def main(self, num, poolNUm, url, header, dataType):
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
        coroutine = self.run_more(num, poolNUm, url, header, dataType)
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
        login_data = {"login": "liukai", "pwd": "12345sap"}

        login_result = self.multi_api(login_url,login_header,login_data)
        token = login_result["rst"]["data"]["token"]

        # 交易
        # errNum = 0
        # sucNum = 0

        # url = self.Environment_Select[env] + "/data-api/topic-analyse/list"
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

        self.main(coNum, poolNUm, url, header, dataType)



if __name__ == '__main__':
    MP = MultiPro()

    # 基础数据
    env = "530"
    coNum = 3                                  # 并发数
    poolNUm = 3                                # 进程池最大进程数

    # t1 = threading.Thread(target=MP.requestDetail, args=("按销售合同号查询",))
    # t2 = threading.Thread(target=MP.requestDetail, args=("按采购订单号查询",))
    # t1.start()
    # t2.start()

    ''' 业务可视化查询 '''
    # MP.requestDetail("查询", "按销售合同号查询")
    # MP.requestDetail("查询", "按供应商订单号查询")
    # MP.requestDetail("查询", "按采购订单号查询")
    MP.requestDetail("查询", "链接点击放货过账金额")
    # MP.requestDetail("查询", "链接点击开票金额")
    # MP.requestDetail("查询", "链接点击应收金额")
    # MP.requestDetail("查询", "链接点击已付款金额")

    ''' 请求报文重复 '''
    # MP.requestDetail("查询", "链接点击红票金额")
    # MP.requestDetail("查询", "链接点击冲抵核销金额")

    ''' 创建审批流 '''
    # MP.requestDetail("新建采购合同", "新建采购合同")
    # MP.requestDetail("新建采购确认单", "新建采购确认单")