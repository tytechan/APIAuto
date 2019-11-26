import unittest
import requests
import os, sys
import json
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
from db_fixture import test_data

from excel_config.excel_data import *
from excel_config.ParseExcel import ParseExcel
from db_fixture.mysql_db import DB
# 用于通过token保存登陆信息
from preinfo_config.set_token import *
from preinfo_config.set_cookie import *
#引入功能函数
from preinfo_config.preactions import *
from preinfo_config.interface_config import *
from preinfo_config import global_config
from interface import Environment_Select


class CaigouContractsTest(unittest.TestCase):
    ''' 报销单审批流_验证凭证科目 '''

    def setUp(self):
        self.dict = global_config._global_dict                              # 全局变量字典
        self.moduleName = "报销单审批流"                                     # 当前流程名称
        global_config.set_value("MODULENAME",self.moduleName)

        self.url = Environment_Select[self.dict.get("ENVIRONMENT")]         # 环境基础地址
        self.caseName = None                                                # 被测案例的案例名

        self.myRow = global_config.get_value('TESTROW')                     # 调用数据行
        self.result = None                                                  # 当前案例响应报文
        self.testResult = None                                              # 当前案例执行状态（在最后一个案例中还作为流程执行状态）
        self.terminateProcess = makeProcessData("#流程开关")                 # 案例执行开关

        if self.terminateProcess == "":
            for (k,v) in self.dict.items():
                if k != "TESTROW" and k != "TESTLOOPTIME":
                    print("🔼 全局变量 %s 的值为： %s" %(k,v))

    def tearDown(self):
        if self.result:
            print("🐱‍👤 案例执行结果为:\n",initial_json(self.result))

        if self.testResult == "失败":
            loadProcessValue("#流程开关",realValue="流程失败")
            writeTextResult(myRow=self.myRow)
        elif self.testResult == "跳过":
            print("🎈案例",self.caseName,"在本流程中跳过...")
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test01_get_costtype(self):
        ''' 遍历获取所有“费用种类-票据类型”组合项，并存入全局变量 '''
        import copy

        if self.terminateProcess != "":
            self.testResult = "跳过"
            return

        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        # 与库表中数据主键重复情况均需考虑是否用初始化
        if getInterfaceData("是否数据库初始化") == "是":
            DB().delete(tableName,deleteData)

        try:
            # **************************** 登陆部分 ****************************
            username = makeJsonData("经办登录名")
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password, errInfo=False)
            time.sleep(1)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            params = {}
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取“token”
            global_config.set_value("TOKEN",token)

            ct1 = self.result["rst"]["data"]["costtype"]
            costType = []
            for k1 in ct1.keys():
                # 用于划分模块执行
                if makeJsonData("费用种类") != "":
                    if ct1[k1]["text"] != makeJsonData("费用种类"):
                        continue

                myDict = {}
                if ct1[k1].get("status") == "x":
                    continue

                myDict["category"] = k1
                myDict["text1"] = ct1[k1]["text"]

                ct2 = ct1[k1]["sub"]
                md1 = copy.deepcopy(myDict)
                for k2 in ct2.keys():
                    if ct2[k2].get("status") == "x":
                        continue

                    myDict["costtype"] = k2
                    myDict["text2"] = ct2[k2]["text"]

                    ct3 = ct2[k2]["sub"]
                    md2 = copy.deepcopy(myDict)
                    for i, k3 in enumerate(ct3.keys()):
                        myDict["invoicetype"] = k3
                        myDict["invoicetypestr"] = ct3[k3]["text"]

                        myDict["flag"] = ""
                        costType.append(myDict)

                        if i + 1 == len(ct3):
                            myDict = copy.deepcopy(md1)
                        else:
                            myDict = copy.deepcopy(md2)

            # 获取“供应商编号”
            global_config.set_value("费用类型组合项", costType)

            # a = []
            # for k in range(5):
            #     a.append(self.dict["费用类型组合项"][k])
            # global_config.set_value("费用类型组合项", a)


            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test02_get_limitperiod_and_createprocess(self):
        ''' （如有）查询该费用种类下额度信息，并创建审批流（此案例采取查询一条创建一条的方式） '''
        import datetime
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = getInterfaceData("调用接口").split("|")

        if self.terminateProcess != "":
            self.testResult = "跳过"
            return


        # 与库表中数据主键重复情况均需考虑是否用初始化
        if getInterfaceData("是否数据库初始化") == "是":
            DB().delete(tableName,deleteData)

        try:
            md = self.dict["费用类型组合项"]

            for i in range(len(md)):
                # **************************** 登陆部分 ****************************
                username = makeJsonData("经办登录名")
                password = makeJsonData("登陆密码")

                token = get_token(login_url, username, password, errInfo=False)
                time.sleep(1)

                header = \
                    {
                    "Authorization": "Bearer " + token,
                    "Content-Type": "application/json"
                }

                # ***** 查询额度信息 *****
                params = {
                        "amount": (10 + i),
                        "category": md[i]["category"],
                        "costtype": md[i]["costtype"],
                        "enddate": "2019-03",
                        "fromdate": "2019-03",
                        "hasfysqd": "0"
                    }

                params = json.dumps(params).replace("'","\"")
                self.result = myRequest(self.url + base_url[0],
                                        headers=header, data=params)

                # **************************** 校验部分 ****************************
                if self.result.get("code") == 200:
                    print("📈 第 ",i + 1," 条流程中“额度查询”响应成功")
                    md[i]["limit"] = self.result["rst"]["data"]["items"]
                else:
                    print("📈 第 ",i + 1," 条流程中“额度查询”响应失败，结果为：\n",self.result, "\n")
                    md[i]["flag"] = "fail"
                    continue



                # ***** 创建审批流 *****
                # **************************** 登陆部分（获取token放入原有） ****************************
                # header = \
                #     {
                #     "Authorization": "Bearer " + token,
                #     "Content-Type": "application/json",
                #     "cookie": "connect.sid=s%3A3YnGCJfqNt_oOj5s-YkGzL92etUSMwCH.4E1iphzTMXlihUbKyeft2yEDBA1T4XRUxU1%2BwtwPoQM"
                #     # "cookie": "connect.sid=s%3A8f76wCFMPoBLO2BtlGEZD71vioO9HsXy.Bb6vYQ7YpzLLpp0RWQbKy0BjIufZyiqHn8f9D0Vkrcc"
                # }


                # cookie = login_cookie(login_url, username, password)
                # time.sleep(1)
                # for item in cookie:
                #     if item.name == "connect.sid":
                #         cookieStr = "connect.sid=" + item.value
                # header["cookie"] = cookieStr


                # 此方法获取cookie不可用
                # cookie = get_cookie(login_url, username, password)
                # header["cookie"] = "connect.sid=" + cookie["connect.sid"]

                params = {
                        "doc": {
                            "model": {
                                "amount": str(10 + i),
                                "applydate": str(datetime.date.today()),
                                "corp": "1000",
                                "cost": {
                                    "accomcost": 0,
                                    "amount": str(10 + i),
                                    "attanum": "3",
                                    "category": md[i]["category"],
                                    "citytranscost": 0,
                                    "costtype": md[i]["costtype"],
                                    "enddate": "2019-03",
                                    "fromdate": "2019-03",
                                    "haszzs": "否",
                                    "invoicetype": md[i]["invoicetype"],
                                    "invoicetypestr": md[i]["invoicetypestr"],
                                    "jtjehz": 0,
                                    "othercost": 0,
                                    "tax": "",
                                    "tripcost": [
                                    ],
                                    "typestr": md[i]["text1"] + "-" + md[i]["text2"]
                                },
                                "department": {
                                    "_id": "5742a607779ec2cb7405180c",
                                    "name": "软件及应用事业部"
                                },
                                "division": "4000",
                                "extra": {
                                    "note": "自动化"
                                },
                                "finance": {
                                    "costcenter": "9100A21999",
                                    "costcenterstr": "软件事业部公共成本中心",
                                    "due": str(10 + i),
                                    "loan": 0,
                                    "returnmoney": "0"
                                },
                                "fysqd": [
                                ],
                                "hasfysqd": "0",
                                "isintegration": "0",
                                "jcfwxm": {
                                },
                                "limit": md[i]["limit"],
                                "profit_center": "8100A29001",
                                "user": {
                                    "_id": "5742a607779ec2cb74051a5d",
                                    "code": "00001853",
                                    "costype": "9100A21999",
                                    "login": "wangqiaochen",
                                    "name": "王乔晨"
                                }
                            }
                        }
                    }

                params = json.dumps(params).replace("'","\"")
                self.result = myRequest(self.url + base_url[1],
                                        headers=header, data=params)
                # self.result = requestWithCookie(self.url + base_url[1],
                #                         headers=header, data=params, cookies=cookie)

                # **************************** 校验部分 ****************************
                if self.result.get("code") == 200:
                    print("📈 第 ",i + 1," 条流程中“创建审批流”响应成功")
                    md[i]["nodeId"] = self.result["rst"]["nodeId"]
                    md[i]["processId"] = self.result["rst"]["processId"]
                    md[i]["报销金额"] = (10 + i)
                else:
                    print("📈 第 ",i + 1," 条流程中“创建审批流”响应失败，结果为：\n",self.result, "\n")
                    md[i]["flag"] = "fail"
                    continue


                # ***** 查询审批流信息 *****
                # del header["cookie"]

                params = {
                        "nodeId": md[i]["nodeId"],
                        "processId": md[i]["processId"]
                    }

                params = json.dumps(params).replace("'","\"")
                self.result = myRequest(self.url + base_url[2],
                                        headers=header, data=params)

                # **************************** 校验部分 ****************************
                if self.result.get("code") == 200:
                    print("📈 第 ",i + 1," 条流程中“查询审批流信息”响应成功")
                    md[i]["processlog"] = self.result["rst"]["processlog"]
                    md[i]["candidates"] = self.result["rst"]["candidates"]
                    md[i]["doc"] = self.result["rst"]["doc"]
                    md[i]["报销单号"] = self.result["rst"]["doc"]["model"]["code"]
                else:
                    print("📈 第 ",i + 1," 条流程中“查询审批流信息”响应失败，结果为：\n",self.result, "\n")
                    md[i]["flag"] = "fail"
                    continue


                # 费用类型为“固定费用”或“间接费用”，且额度充足时，自动审批
                # if md[i]["text1"] == "固定报销" \
                #     or md[i]["text1"] == "间接运营费用":
                if md[i]["text1"] == "固定报销":
                    continue


                # ***** 审批流 *****
                for j in range(len(md[i]["processlog"]) - 1):
                    # **************************** 登陆部分 ****************************
                    username = md[i]["candidates"][0]["receivers"][0]["login"]
                    token = get_token(login_url, username, password, errInfo=False)
                    time.sleep(1)

                    header = \
                        {
                        "Authorization": "Bearer " + token,
                        "Content-Type": "application/json"
                    }

                    # ***** （审批前）查询审批流信息 *****
                    # if j > 0:
                    params = {
                        "nodeId": md[i]["processlog"][j + 1]["nodeid"],
                        "processId": md[i]["processId"]
                    }

                    params = json.dumps(params).replace("'", "\"")
                    self.result = myRequest(self.url + base_url[2],
                                            headers=header, data=params)

                    # **************************** 校验部分 ****************************
                    if self.result.get("code") == 200:
                        print("📈 第 ", i + 1, " 条流程中第 ", j + 1, " 次“（审批前）查询审批流信息”响应成功")
                        md[i]["processlog"] = self.result["rst"]["processlog"]
                        md[i]["candidates"] = self.result["rst"]["candidates"]
                        md[i]["doc"] = self.result["rst"]["doc"]
                    else:
                        print("📈 第 ", i + 1, " 条流程中第 ", j + 1,
                              " 次“（审批前）查询审批流信息”响应失败，结果为：\n", self.result, "\n")
                        md[i]["flag"] = "fail"
                        break


                    # ***** （开始审批后）审批 *****
                    if len(md[i]["processlog"]) == j + 2:
                        # 最后一岗
                        candidates = []
                    else:
                        # 中间岗
                        candidates = md[i]["candidates"]
                    params = \
                        {
                            "candidates": candidates,
                            "doc": md[i]["doc"],
                            "nodeId": md[i]["processlog"][j + 1]["nodeid"],
                            "processId": md[i]["processId"]
                        }

                    params = json.dumps(params).replace("'","\"")
                    self.result = myRequest(self.url + base_url[3],
                                            headers=header, data=params)

                    # **************************** 校验部分 ****************************
                    if self.result.get("code") == 200:
                        print("📈 第 ",i + 1," 条流程中第 ", j + 1, " 次“查询审批流信息”响应成功")
                    else:
                        print("📈 第 ",i + 1," 条流程中第 ", j + 1, " 次“查询审批流信息”响应失败，结果为：\n",self.result, "\n")
                        md[i]["flag"] = "fail"
                        break


                    # ***** （审批后）查询审批流信息，用于获取下一岗nodeid *****
                    if len(md[i]["processlog"]) > j + 2:
                        params = {
                            "nodeId": md[i]["processlog"][j + 1]["nodeid"],
                            "processId": md[i]["processId"]
                        }

                        params = json.dumps(params).replace("'", "\"")
                        self.result = myRequest(self.url + base_url[2],
                                                headers=header, data=params)

                        # **************************** 校验部分 ****************************
                        if self.result.get("code") == 200:
                            print("📈 第 ", i + 1, " 条流程中第 ", j + 1, " 次“（审批后）查询审批流信息”响应成功")
                            md[i]["processlog"] = self.result["rst"]["processlog"]
                        else:
                            print("📈 第 ", i + 1, " 条流程中第 ", j + 1, " 次“（审批后）查询审批流信息”响应失败，结果为：\n", self.result, "\n")
                            md[i]["flag"] = "fail"
                            break

            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test03_checkpoint(self):
        ''' 遍历查询所有报销单数据有效性 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "":
            self.testResult = "跳过"
            return


        # 与库表中数据主键重复情况均需考虑是否用初始化
        if getInterfaceData("是否数据库初始化") == "是":
            DB().delete(tableName,deleteData)

        try:
            # **************************** 登陆部分 ****************************
            username = makeJsonData("经办登录名")
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password, errInfo=False)
            time.sleep(1)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }


            md = self.dict["费用类型组合项"]
            result = []

            for i in range(len(md)):
                params = {
                        "approval_status": "1",
                        "certcode": "",
                        "code": md[i].get("报销单号"),
                        "costtype": "",
                        "finenddate": "",
                        "finfromdate": "",
                        "invoicetypestr": "",
                        "limit": "10",
                        "page": 1,
                        "profit_center": "",
                        "status": "valid",
                        "usercode": "",
                        "username": ""
                    }

                params = json.dumps(params).replace("'","\"")
                self.result = myRequest(base_url, headers=header, data=params)

                # **************************** 校验部分 ****************************
                if self.result.get("code") == 200 \
                        and self.result["rst"]["data"]["total"] > 0:
                    print("📈 第 ",i + 1," 条流程报销单新建成功")
                    md[i]["flag"] = "success"
                else:
                    print("📈 第 ",i + 1," 条流程报销单新建后查询失败，请手工校验！结果为：\n",self.result, "\n")
                    md[i]["flag"] = "fail"

                r = {}
                r["报销单号"] = md[i].get("报销单号")
                r["单据状态"] = md[i]["flag"]
                r["费用种类"] = md[i]["text1"]
                r["费用种类详情"] = md[i]["text2"]
                r["票据类型"] = md[i]["invoicetypestr"]
                r["报销金额"] = md[i].get("报销金额")
                result.append(r)

            print("📈 最终新建结果为：\n", result)

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            self.terminateProcess = True
            loadProcessValue("#流程开关",realValue="流程结束")
            loadProcessValue("#单据数据",realValue=str(result))
            writeTextResult(myRow=self.myRow)


if __name__ == '__main__':
    test_data.init_data() # 初始化接口测试数据
    unittest.main()
