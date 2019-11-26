#encoding = utf - 8

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
#引入功能函数
from preinfo_config.preactions import *
from preinfo_config.interface_config import *
from preinfo_config import global_config
# from interface import Environment_Select, Function_Select,
from interface import *


class CaigouContractsTest(unittest.TestCase):
    ''' 审批流处理 '''

    def setUp(self):
        self.dict = global_config._global_dict                              # 全局变量字典
        self.moduleName = "审批流处理"                                       # 当前流程名称
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

        self.funcType = makeJsonData("审批流类型")
        self.func = Function_Select[makeJsonData("审批流类型")]
        self.flag = makeJsonData("#审批状态")                                # 跳出审批流标志位


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


    def test01_get_list_01(self):
        ''' admin登陆，获取审批流processid、当前岗用户名（验证单据审批状态） '''

        if self.terminateProcess != "":
            self.testResult = "跳过"
            return

        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + self.func + getInterfaceData("调用接口")
        loadProcessValue("#审批状态", realValue="")

        try:
            # **************************** 登陆部分 ****************************
            username = makeJsonData("管理员登录名")
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["list_unfinished"]
            myKey = params_dict["list_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            rst = self.result["rst"]
            if isinstance(rst, dict):
                data = self.result["rst"]["data"]
                sum = data.get("total")
            else:
                sum = 0

            # 若根据单据号未查询到单据信息，则结束次案例后在最后一案例中查询状态是否为“审批完成”
            if sum > 0:
                # 获取当前岗用户名、nodeid及processid
                nextUser = combineJson(self.result,"rst", "data", "items", 0, "curreceiver", 0)
                if nextUser in specialUser.keys():
                    loginName = specialUser[nextUser]
                else:
                    loginName = pinyinTransform(nextUser)
                global_config.set_value("当前节点处理人", loginName)
                global_config.set_value("审批岗位", loginName)
                loadProcessValue("#审批岗位", realValue=loginName)

                global_config.set_value("processId",
                                        combineJson(self.result, "rst", "data", "items", 0, "processId"))

                loadProcessValue("#审批状态", realValue="审批中")
            else:
                loadProcessValue("#审批状态", realValue="非审批中")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test02_get_mydoing_01(self):
        ''' admin登陆，获取当前节点nodeid '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 登陆部分 ****************************
            username = self.dict["当前节点处理人"]
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["mydoing_dict"]
            myKey = params_dict["mydoing_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取登陆信息
            global_config.set_value("TOKEN", token)

            global_config.set_value("nodeId",
                                    combineJson(self.result, "rst", "data", "items", 0, "node", "_id"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test03_get_detail_01(self):
        ''' [第一岗] 查询单据详细信息 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            header = {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            # TODO:myflag
            params = {
                "processId": self.dict["processId"],
                "nodeId": self.dict["nodeId"],
                # "myflag": "mysubscriber"
            }
            # print(params)
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            if self.func == "/reimburse":
                # 审批流为“报销单”时
                doc = eval(combineJson(self.result, "rst", "doc"))
            else:
                doc = eval(combineJson(self.result, "rst", "doc", "model"))

            global_config.set_value("doc", doc)

            if self.func == "/contract":
                tradeName = doc["contractbase"].get("traderlogin")
                global_config.set_value("商务人员", tradeName)

            global_config.set_value("candidates",
                                    eval(combineJson(self.result, "rst", "candidates")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test03_get_detail_02(self):
        ''' [第一岗] 审批流为“销售合同”，且配套服务为“1”时，维护成本分析信息 '''
        import re
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中" \
                or self.funcType != "销售合同":
            self.testResult = "跳过"
            return

        try:
            # **************************** 校验数据是否遗漏 ****************************
            # 销售合同/配套服务
            cp = self.dict["doc"]["contractbase"]["cp"]
            ca = {}

            if cp == "1":
                # 销售合同，配套服务=1，但已做过成本分析
                othercost = self.dict["doc"]["othercost"]
                for i in range(len(othercost)):
                    oc_init = othercost[i]
                    if oc_init["orderscost"] != 0 \
                        or oc_init["outorderost"] != 0 \
                        or oc_init["purchaserebate"] != 0 \
                        or oc_init["selfpickup"] != 0 \
                        or oc_init["cashrebate"] != 0 \
                        or oc_init["mating"] != 0:
                        self.testResult = "跳过"
                        return

                ca_17 = makeJsonData("0.17").split("|")
                assert len(ca_17) == 6, "请先维护数据表中“成本分析（17%）”相关数据！"
                ca_6 = makeJsonData("0.06").split("|")
                assert len(ca_6) == 6, "请先维护数据表中“成本分析（6%）”相关数据！"
                ca_0 = makeJsonData("0").split("|")
                assert len(ca_0) == 6, "请先维护数据表中“成本分析（0%）”相关数据！"
                ca_16 = makeJsonData("0.16").split("|")
                assert len(ca_16) == 6, "请先维护数据表中“成本分析（16%）”相关数据！"
                ca_13 = makeJsonData("0.13").split("|")
                assert len(ca_13) == 6, "请先维护数据表中“成本分析（13%）”相关数据！"

                ca["17"] = ca_17
                ca["6"] = ca_6
                ca["0"] = ca_0
                ca["16"] = ca_16
                ca["13"] = ca_13
            elif cp == "0":
                v = "0|0|0|0|0|0".split("|")
                ca["17"] = v
                ca["6"] = v
                ca["0"] = v
                ca["16"] = v
                ca["13"] = v


            # **************************** 交易部分 ****************************
            header = {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            # 成本分析
            params = {
                "contractId": self.dict["doc"]["contractId"],
                "contractInterest": self.dict["doc"]["contractbase"]["contractInterest"],
                "interest": self.dict["doc"]["contractbase"]["interest"],
                "interestContainTax": self.dict["doc"]["contractbase"]["interestContainTax"],
                "internalPriceObj": self.dict["doc"].get("internalPriceObj", ""),
                "othercost": self.dict["doc"].get("othercost", ""),
                "sellcontractInterest": self.dict["doc"]["contractbase"]["sellcontractInterest"],
                "sellinterest": self.dict["doc"]["contractbase"]["sellinterest"],
                "sellinterestContainTax": self.dict["doc"]["contractbase"]["sellinterestContainTax"],
            }

            # if cp == "1" \
            #         or (cp == "0" and len(params["othercost"]) == 0):
            # for i in range(len(params["othercost"])):
            #     oc = params["othercost"][i]
            #     for key in ca.keys():
            #         if oc["thetype"] == key:
            #             oc["orderscost"] = ca[key][0]
            #             oc["outorderost"] = ca[key][1]
            #             oc["purchaserebate"] = ca[key][2]
            #             oc["selfpickup"] = ca[key][3]
            #             oc["cashrebate"] = ca[key][4]
            #             oc["mating"] = ca[key][5]
            #             # oc["money"] = self.dict["doc"]["contractbase"]["contractmoney"]
            #             del ca[key]
            #             break

            for key in ca.keys():
                cost = {
                    "orderscost": int(ca[key][0]),
                    "outorderost": int(ca[key][1]),
                    "purchaserebate": int(ca[key][2]),
                    "selfpickup": int(ca[key][3]),
                    "cashrebate": int(ca[key][4]),
                    "mating": int(ca[key][5]),

                    "amount": 0,
                    "contractId": self.dict["doc"]["contractId"],
                    # "money": 0,
                    "orderscount": 0,
                    "other": 0,
                    "outordercount": 0,
                    "project": 0,
                    "salerebate": 0,
                    "salesListingCost": 0,
                    "thetype": key,
                    "third": 0
                }
                # if cost["thetype"] == self.dict["doc"]["contractbase"]["receipttype"]:
                taxRate = self.dict["doc"]["contractbase"]["receipttype"]
                if cost["thetype"] == re.sub("\D", "", taxRate):
                    cost["money"] = self.dict["doc"]["contractbase"]["contractmoney"]
                else:
                    cost["money"] = 0
                params["othercost"].append(cost)

            # print(params)
            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except AssertionError as e:
            self.testResult = "失败"
            raise AssertionError(e)
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test04_agree_01(self):
        ''' [第一岗] 审批 '''
        import datetime
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 前交易部分 ****************************
            # 审批流为“销售合同”，且当前岗为“商务人员时”
            if self.func == "/contract" \
                    and self.dict["商务人员"] == self.dict["当前节点处理人"]:
                self.dict["doc"]["contractbase"]["receivabletype"] = makeJsonData("业务应收创建方式")

                effectdate = makeJsonData("签订日期")
                if effectdate == "":
                    ed = str(datetime.date.today())
                else:
                    ed = effectdate
                self.dict["doc"]["contractbase"]["effectdate"] = ed

            # 下岗审批人
            candidates_init = self.dict["candidates"]

            if candidates_init != []:
                receivers = candidates_init[0]["receivers"]
                for i in range(len(receivers)):
                    if receivers[i]["name"] == "刘迪":
                        # 离职员工跳过
                        del receivers[i]
                        continue
                    else:
                        nextUser = receivers[i]["login"]
                        self.dict["candidates"][0]["receivers"] = [
                            receivers[i]
                        ]

                        # global_config.set_value("candidates", candidates)
                        global_config.set_value("当前节点处理人", nextUser)
                        self.dict["审批岗位"] += ("," + nextUser)
                        loadProcessValue("#审批岗位", realValue=self.dict["审批岗位"])
                        break

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = \
                {
                    "candidates": self.dict["candidates"],
                    "doc": self.dict["doc"],
                    "nodeId": self.dict["nodeId"],
                    "processId": self.dict["processId"]
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()
            writeTextResult()


    def test05_get_list_01(self):
        ''' [第一岗] 审批后用上一岗节点信息查询下一节点处理人（验证单据审批状态） '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            if self.func in ["/credit", "/reimburse"]:
                # “付款申请单/报销单”的list接口数据只可用admin查询
                username = makeJsonData("管理员登录名")
                password = makeJsonData("登陆密码")
                myToken = get_token(login_url,username,password)
            else:
                myToken = self.dict["TOKEN"]

            header = \
                {
                "Authorization": "Bearer " + myToken,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["list_unfinished"]
            myKey = params_dict["list_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            rst = self.result["rst"]
            if isinstance(rst, dict):
                data = self.result["rst"]["data"]
                sum = data.get("total")
            else:
                sum = 0

            # 若根据单据号未查询到单据信息，则结束次案例后在最后一案例中查询状态是否为“审批完成”
            if sum > 0:
                nextUser = combineJson(self.result,"rst", "data", "items", 0, "curreceiver", 0)
                if nextUser in specialUser.keys():
                    loginName = specialUser[nextUser]
                else:
                    loginName = pinyinTransform(nextUser)
                global_config.set_value("当前节点处理人", loginName)

                loadProcessValue("#审批状态", realValue="审批中")
            else:
                loadProcessValue("#审批状态", realValue="非审批中")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test06_get_mydoing_02(self):
        ''' [第二岗] 第二岗登陆，获取当前节点nodeid '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 登陆部分 ****************************
            username = self.dict["当前节点处理人"]
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["mydoing_dict"]
            myKey = params_dict["mydoing_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取登陆信息
            global_config.set_value("TOKEN", token)

            global_config.set_value("nodeId",
                                    combineJson(self.result, "rst", "data", "items", 0, "node", "_id"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test07_get_detail_02(self):
        ''' [第二岗] 第二岗登陆，查询单据详细信息 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            header = {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = {
                "processId": self.dict["processId"],
                "nodeId": self.dict["nodeId"]
            }
            # print(params)
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            if self.func == "/reimburse":
                # 审批流为“报销单”时
                doc = eval(combineJson(self.result, "rst", "doc"))
            else:
                doc = eval(combineJson(self.result, "rst", "doc", "model"))

            global_config.set_value("doc", doc)

            global_config.set_value("candidates",
                                    eval(combineJson(self.result, "rst", "candidates")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test08_agree_02(self):
        ''' [第二岗] 审批 '''
        import datetime
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 前交易部分 ****************************
            # 审批流为“销售合同”，且当前岗为“商务人员时”
            if self.func == "/contract" \
                    and self.dict["商务人员"] == self.dict["当前节点处理人"]:
                self.dict["doc"]["contractbase"]["receivabletype"] = makeJsonData("业务应收创建方式")

                effectdate = makeJsonData("签订日期")
                if effectdate == "":
                    ed = str(datetime.date.today())
                else:
                    ed = effectdate
                self.dict["doc"]["contractbase"]["effectdate"] = ed

            # 下岗审批人
            candidates_init = self.dict["candidates"]

            if candidates_init != []:
                receivers = candidates_init[0]["receivers"]
                for i in range(len(receivers)):
                    if receivers[i]["name"] == "刘迪":
                        # 离职员工跳过
                        del receivers[i]
                        continue
                    else:
                        nextUser = receivers[i]["login"]
                        self.dict["candidates"][0]["receivers"] = [
                            receivers[i]
                        ]

                        # global_config.set_value("candidates", candidates)
                        global_config.set_value("当前节点处理人", nextUser)
                        self.dict["审批岗位"] += ("," + nextUser)
                        loadProcessValue("#审批岗位", realValue=self.dict["审批岗位"])
                        break

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = \
                {
                    "candidates": self.dict["candidates"],
                    "doc": self.dict["doc"],
                    "nodeId": self.dict["nodeId"],
                    "processId": self.dict["processId"]
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test09_get_list_02(self):
        ''' [第二岗] 审批后用上一岗节点信息查询当前岗用户名（验证单据审批状态） '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            if self.func in ["/credit", "/reimburse"]:
                # “付款申请单/报销单”的list接口数据只可用admin查询
                username = makeJsonData("管理员登录名")
                password = makeJsonData("登陆密码")
                myToken = get_token(login_url,username,password)
            else:
                myToken = self.dict["TOKEN"]

            header = \
                {
                "Authorization": "Bearer " + myToken,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["list_unfinished"]
            myKey = params_dict["list_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            rst = self.result["rst"]
            if isinstance(rst, dict):
                data = self.result["rst"]["data"]
                sum = data.get("total")
            else:
                sum = 0

            # 若根据单据号未查询到单据信息，则结束次案例后在最后一案例中查询状态是否为“审批完成”
            if sum > 0:
                nextUser = combineJson(self.result,"rst", "data", "items", 0, "curreceiver", 0)
                if nextUser in specialUser.keys():
                    loginName = specialUser[nextUser]
                else:
                    loginName = pinyinTransform(nextUser)
                global_config.set_value("当前节点处理人", loginName)

                loadProcessValue("#审批状态", realValue="审批中")
            else:
                loadProcessValue("#审批状态", realValue="非审批中")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test10_get_mydoing_03(self):
        ''' [第三岗] 第三岗登陆，获取当前节点nodeid '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 登陆部分 ****************************
            username = self.dict["当前节点处理人"]
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["mydoing_dict"]
            myKey = params_dict["mydoing_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取登陆信息
            global_config.set_value("TOKEN", token)

            global_config.set_value("nodeId",
                                    combineJson(self.result, "rst", "data", "items", 0, "node", "_id"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test11_get_detail_03(self):
        ''' [第三岗] 第三岗登陆，查询单据详细信息 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            header = {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = {
                "processId": self.dict["processId"],
                "nodeId": self.dict["nodeId"]
            }
            # print(params)
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            if self.func == "/reimburse":
                # 审批流为“报销单”时
                doc = eval(combineJson(self.result, "rst", "doc"))
            else:
                doc = eval(combineJson(self.result, "rst", "doc", "model"))

            global_config.set_value("doc", doc)

            global_config.set_value("candidates",
                                    eval(combineJson(self.result, "rst", "candidates")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test12_agree_03(self):
        ''' [第三岗] 审批 '''
        import datetime
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 前交易部分 ****************************
            # 审批流为“销售合同”，且当前岗为“商务人员时”
            if self.func == "/contract" \
                    and self.dict["商务人员"] == self.dict["当前节点处理人"]:
                self.dict["doc"]["contractbase"]["receivabletype"] = makeJsonData("业务应收创建方式")

                effectdate = makeJsonData("签订日期")
                if effectdate == "":
                    ed = str(datetime.date.today())
                else:
                    ed = effectdate
                self.dict["doc"]["contractbase"]["effectdate"] = ed

            # 下岗审批人
            candidates_init = self.dict["candidates"]

            if candidates_init != []:
                receivers = candidates_init[0]["receivers"]
                for i in range(len(receivers)):
                    if receivers[i]["name"] == "刘迪":
                        # 离职员工跳过
                        del receivers[i]
                        continue
                    else:
                        nextUser = receivers[i]["login"]
                        self.dict["candidates"][0]["receivers"] = [
                            receivers[i]
                        ]

                        # global_config.set_value("candidates", candidates)
                        global_config.set_value("当前节点处理人", nextUser)
                        self.dict["审批岗位"] += ("," + nextUser)
                        loadProcessValue("#审批岗位", realValue=self.dict["审批岗位"])
                        break

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = \
                {
                    "candidates": self.dict["candidates"],
                    "doc": self.dict["doc"],
                    "nodeId": self.dict["nodeId"],
                    "processId": self.dict["processId"]
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test13_get_list_03(self):
        ''' [第三岗] 审批后用上一岗节点信息查询当前岗用户名（验证单据审批状态） '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            if self.func in ["/credit", "/reimburse"]:
                # “付款申请单/报销单”的list接口数据只可用admin查询
                username = makeJsonData("管理员登录名")
                password = makeJsonData("登陆密码")
                myToken = get_token(login_url,username,password)
            else:
                myToken = self.dict["TOKEN"]

            header = \
                {
                "Authorization": "Bearer " + myToken,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["list_unfinished"]
            myKey = params_dict["list_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            rst = self.result["rst"]
            if isinstance(rst, dict):
                data = self.result["rst"]["data"]
                sum = data.get("total")
            else:
                sum = 0

            # 若根据单据号未查询到单据信息，则结束次案例后在最后一案例中查询状态是否为“审批完成”
            if sum > 0:
                nextUser = combineJson(self.result,"rst", "data", "items", 0, "curreceiver", 0)
                if nextUser in specialUser.keys():
                    loginName = specialUser[nextUser]
                else:
                    loginName = pinyinTransform(nextUser)
                global_config.set_value("当前节点处理人", loginName)

                loadProcessValue("#审批状态", realValue="审批中")
            else:
                loadProcessValue("#审批状态", realValue="非审批中")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test14_get_mydoing_04(self):
        ''' [第四岗] 第四岗登陆，获取当前节点nodeid '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 登陆部分 ****************************
            username = self.dict["当前节点处理人"]
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["mydoing_dict"]
            myKey = params_dict["mydoing_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取登陆信息
            global_config.set_value("TOKEN", token)

            global_config.set_value("nodeId",
                                    combineJson(self.result, "rst", "data", "items", 0, "node", "_id"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test15_get_detail_04(self):
        ''' [第四岗] 第四岗登陆，查询单据详细信息 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            header = {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = {
                "processId": self.dict["processId"],
                "nodeId": self.dict["nodeId"]
            }
            # print(params)
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            if self.func == "/reimburse":
                # 审批流为“报销单”时
                doc = eval(combineJson(self.result, "rst", "doc"))
            else:
                doc = eval(combineJson(self.result, "rst", "doc", "model"))

            global_config.set_value("doc", doc)

            global_config.set_value("candidates",
                                    eval(combineJson(self.result, "rst", "candidates")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test16_agree_04(self):
        ''' [第四岗] 审批 '''
        import datetime
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 前交易部分 ****************************
            # 审批流为“销售合同”，且当前岗为“商务人员时”
            if self.func == "/contract" \
                    and self.dict["商务人员"] == self.dict["当前节点处理人"]:
                self.dict["doc"]["contractbase"]["receivabletype"] = makeJsonData("业务应收创建方式")

                effectdate = makeJsonData("签订日期")
                if effectdate == "":
                    ed = str(datetime.date.today())
                else:
                    ed = effectdate
                self.dict["doc"]["contractbase"]["effectdate"] = ed

            # 下岗审批人
            candidates_init = self.dict["candidates"]

            if candidates_init != []:
                receivers = candidates_init[0]["receivers"]
                for i in range(len(receivers)):
                    if receivers[i]["name"] == "刘迪":
                        # 离职员工跳过
                        del receivers[i]
                        continue
                    else:
                        nextUser = receivers[i]["login"]
                        self.dict["candidates"][0]["receivers"] = [
                            receivers[i]
                        ]

                        # global_config.set_value("candidates", candidates)
                        global_config.set_value("当前节点处理人", nextUser)
                        self.dict["审批岗位"] += ("," + nextUser)
                        loadProcessValue("#审批岗位", realValue=self.dict["审批岗位"])
                        break

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = \
                {
                    "candidates": self.dict["candidates"],
                    "doc": self.dict["doc"],
                    "nodeId": self.dict["nodeId"],
                    "processId": self.dict["processId"]
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test17_get_list_04(self):
        ''' [第四岗] 审批后用上一岗节点信息查询当前岗用户名（验证单据审批状态） '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            if self.func in ["/credit", "/reimburse"]:
                # “付款申请单/报销单”的list接口数据只可用admin查询
                username = makeJsonData("管理员登录名")
                password = makeJsonData("登陆密码")
                myToken = get_token(login_url,username,password)
            else:
                myToken = self.dict["TOKEN"]

            header = \
                {
                "Authorization": "Bearer " + myToken,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["list_unfinished"]
            myKey = params_dict["list_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            rst = self.result["rst"]
            if isinstance(rst, dict):
                data = self.result["rst"]["data"]
                sum = data.get("total")
            else:
                sum = 0

            # 若根据单据号未查询到单据信息，则结束次案例后在最后一案例中查询状态是否为“审批完成”
            if sum > 0:
                nextUser = combineJson(self.result,"rst", "data", "items", 0, "curreceiver", 0)
                if nextUser in specialUser.keys():
                    loginName = specialUser[nextUser]
                else:
                    loginName = pinyinTransform(nextUser)
                global_config.set_value("当前节点处理人", loginName)

                loadProcessValue("#审批状态", realValue="审批中")
            else:
                loadProcessValue("#审批状态", realValue="非审批中")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test18_get_mydoing_05(self):
        ''' [第五岗] 第五岗登陆，获取当前节点nodeid '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 登陆部分 ****************************
            username = self.dict["当前节点处理人"]
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["mydoing_dict"]
            myKey = params_dict["mydoing_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取登陆信息
            global_config.set_value("TOKEN", token)

            global_config.set_value("nodeId",
                                    combineJson(self.result, "rst", "data", "items", 0, "node", "_id"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test19_get_detail_05(self):
        """ [第五岗] 第五岗登陆，查询单据详细信息 """
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            header = {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = {
                "processId": self.dict["processId"],
                "nodeId": self.dict["nodeId"]
            }
            # print(params)
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            if self.func == "/reimburse":
                # 审批流为“报销单”时
                doc = eval(combineJson(self.result, "rst", "doc"))
            else:
                doc = eval(combineJson(self.result, "rst", "doc", "model"))

            global_config.set_value("doc", doc)

            global_config.set_value("candidates",
                                    eval(combineJson(self.result, "rst", "candidates")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test20_agree_05(self):
        ''' [第五岗] 审批 '''
        import datetime
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 前交易部分 ****************************
            # 审批流为“销售合同”，且当前岗为“商务人员时”
            if self.func == "/contract" \
                    and self.dict["商务人员"] == self.dict["当前节点处理人"]:
                self.dict["doc"]["contractbase"]["receivabletype"] = makeJsonData("业务应收创建方式")

                effectdate = makeJsonData("签订日期")
                if effectdate == "":
                    ed = str(datetime.date.today())
                else:
                    ed = effectdate
                self.dict["doc"]["contractbase"]["effectdate"] = ed

            # 下岗审批人
            candidates_init = self.dict["candidates"]

            if candidates_init != []:
                receivers = candidates_init[0]["receivers"]
                for i in range(len(receivers)):
                    if receivers[i]["name"] == "刘迪":
                        # 离职员工跳过
                        del receivers[i]
                        continue
                    else:
                        nextUser = receivers[i]["login"]
                        self.dict["candidates"][0]["receivers"] = [
                            receivers[i]
                        ]

                        # global_config.set_value("candidates", candidates)
                        global_config.set_value("当前节点处理人", nextUser)
                        self.dict["审批岗位"] += ("," + nextUser)
                        loadProcessValue("#审批岗位", realValue=self.dict["审批岗位"])
                        break

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = \
                {
                    "candidates": self.dict["candidates"],
                    "doc": self.dict["doc"],
                    "nodeId": self.dict["nodeId"],
                    "processId": self.dict["processId"]
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test21_get_list_05(self):
        ''' [第五岗] 审批后用上一岗节点信息查询当前岗用户名（验证单据审批状态） '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            if self.func in ["/credit", "/reimburse"]:
                # “付款申请单/报销单”的list接口数据只可用admin查询
                username = makeJsonData("管理员登录名")
                password = makeJsonData("登陆密码")
                myToken = get_token(login_url,username,password)
            else:
                myToken = self.dict["TOKEN"]

            header = \
                {
                "Authorization": "Bearer " + myToken,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["list_unfinished"]
            myKey = params_dict["list_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            rst = self.result["rst"]
            if isinstance(rst, dict):
                data = self.result["rst"]["data"]
                sum = data.get("total")
            else:
                sum = 0

            # 若根据单据号未查询到单据信息，则结束次案例后在最后一案例中查询状态是否为“审批完成”
            if sum > 0:
                nextUser = combineJson(self.result,"rst", "data", "items", 0, "curreceiver", 0)
                if nextUser in specialUser.keys():
                    loginName = specialUser[nextUser]
                else:
                    loginName = pinyinTransform(nextUser)
                global_config.set_value("当前节点处理人", loginName)

                loadProcessValue("#审批状态", realValue="审批中")
            else:
                loadProcessValue("#审批状态", realValue="非审批中")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test22_get_mydoing_06(self):
        ''' [第六岗] 第六岗登陆，获取当前节点nodeid '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 登陆部分 ****************************
            username = self.dict["当前节点处理人"]
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["mydoing_dict"]
            myKey = params_dict["mydoing_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取登陆信息
            global_config.set_value("TOKEN", token)

            global_config.set_value("nodeId",
                                    combineJson(self.result, "rst", "data", "items", 0, "node", "_id"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test23_get_detail_06(self):
        """ [第六岗] 第六岗登陆，查询单据详细信息 """
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            header = {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = {
                "processId": self.dict["processId"],
                "nodeId": self.dict["nodeId"]
            }
            # print(params)
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            if self.func == "/reimburse":
                # 审批流为“报销单”时
                doc = eval(combineJson(self.result, "rst", "doc"))
            else:
                doc = eval(combineJson(self.result, "rst", "doc", "model"))

            global_config.set_value("doc", doc)

            global_config.set_value("candidates",
                                    eval(combineJson(self.result, "rst", "candidates")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test24_agree_06(self):
        ''' [第六岗] 审批 '''
        import datetime
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 前交易部分 ****************************
            # 审批流为“销售合同”，且当前岗为“商务人员时”
            if self.func == "/contract" \
                    and self.dict["商务人员"] == self.dict["当前节点处理人"]:
                self.dict["doc"]["contractbase"]["receivabletype"] = makeJsonData("业务应收创建方式")

                effectdate = makeJsonData("签订日期")
                if effectdate == "":
                    ed = str(datetime.date.today())
                else:
                    ed = effectdate
                self.dict["doc"]["contractbase"]["effectdate"] = ed

            # 下岗审批人
            candidates_init = self.dict["candidates"]

            if candidates_init != []:
                receivers = candidates_init[0]["receivers"]
                for i in range(len(receivers)):
                    if receivers[i]["name"] == "刘迪":
                        # 离职员工跳过
                        del receivers[i]
                        continue
                    else:
                        nextUser = receivers[i]["login"]
                        self.dict["candidates"][0]["receivers"] = [
                            receivers[i]
                        ]

                        # global_config.set_value("candidates", candidates)
                        global_config.set_value("当前节点处理人", nextUser)
                        self.dict["审批岗位"] += ("," + nextUser)
                        loadProcessValue("#审批岗位", realValue=self.dict["审批岗位"])
                        break

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = \
                {
                    "candidates": self.dict["candidates"],
                    "doc": self.dict["doc"],
                    "nodeId": self.dict["nodeId"],
                    "processId": self.dict["processId"]
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test25_get_list_06(self):
        ''' [第六岗] 审批后用上一岗节点信息查询当前岗用户名（验证单据审批状态） '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            if self.func in ["/credit", "/reimburse"]:
                # “付款申请单/报销单”的list接口数据只可用admin查询
                username = makeJsonData("管理员登录名")
                password = makeJsonData("登陆密码")
                myToken = get_token(login_url,username,password)
            else:
                myToken = self.dict["TOKEN"]

            header = \
                {
                "Authorization": "Bearer " + myToken,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["list_unfinished"]
            myKey = params_dict["list_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            rst = self.result["rst"]
            if isinstance(rst, dict):
                data = self.result["rst"]["data"]
                sum = data.get("total")
            else:
                sum = 0

            # 若根据单据号未查询到单据信息，则结束次案例后在最后一案例中查询状态是否为“审批完成”
            if sum > 0:
                nextUser = combineJson(self.result,"rst", "data", "items", 0, "curreceiver", 0)
                if nextUser in specialUser.keys():
                    loginName = specialUser[nextUser]
                else:
                    loginName = pinyinTransform(nextUser)
                global_config.set_value("当前节点处理人", loginName)

                loadProcessValue("#审批状态", realValue="审批中")
            else:
                loadProcessValue("#审批状态", realValue="非审批中")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test26_get_mydoing_07(self):
        ''' [第七岗] 第七岗登陆，获取当前节点nodeid '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 登陆部分 ****************************
            username = self.dict["当前节点处理人"]
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["mydoing_dict"]
            myKey = params_dict["mydoing_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取登陆信息
            global_config.set_value("TOKEN", token)

            global_config.set_value("nodeId",
                                    combineJson(self.result, "rst", "data", "items", 0, "node", "_id"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test27_get_detail_07(self):
        """ [第七岗] 第七岗登陆，查询单据详细信息 """
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            header = {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = {
                "processId": self.dict["processId"],
                "nodeId": self.dict["nodeId"]
            }
            # print(params)
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            if self.func == "/reimburse":
                # 审批流为“报销单”时
                doc = eval(combineJson(self.result, "rst", "doc"))
            else:
                doc = eval(combineJson(self.result, "rst", "doc", "model"))

            global_config.set_value("doc", doc)

            global_config.set_value("candidates",
                                    eval(combineJson(self.result, "rst", "candidates")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test28_agree_07(self):
        ''' [第七岗] 审批 '''
        import datetime
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 前交易部分 ****************************
            # 审批流为“销售合同”，且当前岗为“商务人员时”
            if self.func == "/contract" \
                    and self.dict["商务人员"] == self.dict["当前节点处理人"]:
                self.dict["doc"]["contractbase"]["receivabletype"] = makeJsonData("业务应收创建方式")

                effectdate = makeJsonData("签订日期")
                if effectdate == "":
                    ed = str(datetime.date.today())
                else:
                    ed = effectdate
                self.dict["doc"]["contractbase"]["effectdate"] = ed

            # 下岗审批人
            candidates_init = self.dict["candidates"]

            if candidates_init != []:
                receivers = candidates_init[0]["receivers"]
                for i in range(len(receivers)):
                    if receivers[i]["name"] == "刘迪":
                        # 离职员工跳过
                        del receivers[i]
                        continue
                    else:
                        nextUser = receivers[i]["login"]
                        self.dict["candidates"][0]["receivers"] = [
                            receivers[i]
                        ]

                        # global_config.set_value("candidates", candidates)
                        global_config.set_value("当前节点处理人", nextUser)
                        self.dict["审批岗位"] += ("," + nextUser)
                        loadProcessValue("#审批岗位", realValue=self.dict["审批岗位"])
                        break

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = \
                {
                    "candidates": self.dict["candidates"],
                    "doc": self.dict["doc"],
                    "nodeId": self.dict["nodeId"],
                    "processId": self.dict["processId"]
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test29_get_list_07(self):
        ''' [第七岗] 审批后用上一岗节点信息查询当前岗用户名（验证单据审批状态） '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            if self.func in ["/credit", "/reimburse"]:
                # “付款申请单/报销单”的list接口数据只可用admin查询
                username = makeJsonData("管理员登录名")
                password = makeJsonData("登陆密码")
                myToken = get_token(login_url,username,password)
            else:
                myToken = self.dict["TOKEN"]

            header = \
                {
                "Authorization": "Bearer " + myToken,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["list_unfinished"]
            myKey = params_dict["list_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            rst = self.result["rst"]
            if isinstance(rst, dict):
                data = self.result["rst"]["data"]
                sum = data.get("total")
            else:
                sum = 0

            # 若根据单据号未查询到单据信息，则结束次案例后在最后一案例中查询状态是否为“审批完成”
            if sum > 0:
                nextUser = combineJson(self.result,"rst", "data", "items", 0, "curreceiver", 0)
                if nextUser in specialUser.keys():
                    loginName = specialUser[nextUser]
                else:
                    loginName = pinyinTransform(nextUser)
                global_config.set_value("当前节点处理人", loginName)

                loadProcessValue("#审批状态", realValue="审批中")
            else:
                loadProcessValue("#审批状态", realValue="非审批中")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test30_get_mydoing_08(self):
        ''' [第八岗] 第八岗登陆，获取当前节点nodeid '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 登陆部分 ****************************
            username = self.dict["当前节点处理人"]
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["mydoing_dict"]
            myKey = params_dict["mydoing_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取登陆信息
            global_config.set_value("TOKEN", token)

            global_config.set_value("nodeId",
                                    combineJson(self.result, "rst", "data", "items", 0, "node", "_id"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test31_get_detail_08(self):
        """ [第八岗] 第八岗登陆，查询单据详细信息 """
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            header = {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = {
                "processId": self.dict["processId"],
                "nodeId": self.dict["nodeId"]
            }
            # print(params)
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            if self.func == "/reimburse":
                # 审批流为“报销单”时
                doc = eval(combineJson(self.result, "rst", "doc"))
            else:
                doc = eval(combineJson(self.result, "rst", "doc", "model"))

            global_config.set_value("doc", doc)

            global_config.set_value("candidates",
                                    eval(combineJson(self.result, "rst", "candidates")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test32_agree_08(self):
        ''' [第八岗] 审批 '''
        import datetime
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 前交易部分 ****************************
            # 审批流为“销售合同”，且当前岗为“商务人员时”
            if self.func == "/contract" \
                    and self.dict["商务人员"] == self.dict["当前节点处理人"]:
                self.dict["doc"]["contractbase"]["receivabletype"] = makeJsonData("业务应收创建方式")

                effectdate = makeJsonData("签订日期")
                if effectdate == "":
                    ed = str(datetime.date.today())
                else:
                    ed = effectdate
                self.dict["doc"]["contractbase"]["effectdate"] = ed

            # 下岗审批人
            candidates_init = self.dict["candidates"]

            if candidates_init != []:
                receivers = candidates_init[0]["receivers"]
                for i in range(len(receivers)):
                    if receivers[i]["name"] == "刘迪":
                        # 离职员工跳过
                        del receivers[i]
                        continue
                    else:
                        nextUser = receivers[i]["login"]
                        self.dict["candidates"][0]["receivers"] = [
                            receivers[i]
                        ]

                        # global_config.set_value("candidates", candidates)
                        global_config.set_value("当前节点处理人", nextUser)
                        self.dict["审批岗位"] += ("," + nextUser)
                        loadProcessValue("#审批岗位", realValue=self.dict["审批岗位"])
                        break

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = \
                {
                    "candidates": self.dict["candidates"],
                    "doc": self.dict["doc"],
                    "nodeId": self.dict["nodeId"],
                    "processId": self.dict["processId"]
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test33_get_list_08(self):
        ''' [第八岗] 审批后用上一岗节点信息查询当前岗用户名（验证单据审批状态） '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            if self.func in ["/credit", "/reimburse"]:
                # “付款申请单/报销单”的list接口数据只可用admin查询
                username = makeJsonData("管理员登录名")
                password = makeJsonData("登陆密码")
                myToken = get_token(login_url,username,password)
            else:
                myToken = self.dict["TOKEN"]

            header = \
                {
                "Authorization": "Bearer " + myToken,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["list_unfinished"]
            myKey = params_dict["list_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            rst = self.result["rst"]
            if isinstance(rst, dict):
                data = self.result["rst"]["data"]
                sum = data.get("total")
            else:
                sum = 0

            # 若根据单据号未查询到单据信息，则结束次案例后在最后一案例中查询状态是否为“审批完成”
            if sum > 0:
                nextUser = combineJson(self.result,"rst", "data", "items", 0, "curreceiver", 0)
                if nextUser in specialUser.keys():
                    loginName = specialUser[nextUser]
                else:
                    loginName = pinyinTransform(nextUser)
                global_config.set_value("当前节点处理人", loginName)

                loadProcessValue("#审批状态", realValue="审批中")
            else:
                loadProcessValue("#审批状态", realValue="非审批中")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test34_get_mydoing_09(self):
        ''' [第九岗] 第九岗登陆，获取当前节点nodeid '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 登陆部分 ****************************
            username = self.dict["当前节点处理人"]
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["mydoing_dict"]
            myKey = params_dict["mydoing_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取登陆信息
            global_config.set_value("TOKEN", token)

            global_config.set_value("nodeId",
                                    combineJson(self.result, "rst", "data", "items", 0, "node", "_id"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test35_get_detail_09(self):
        """ [第九岗] 第九岗登陆，查询单据详细信息 """
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            header = {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = {
                "processId": self.dict["processId"],
                "nodeId": self.dict["nodeId"]
            }
            # print(params)
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            if self.func == "/reimburse":
                # 审批流为“报销单”时
                doc = eval(combineJson(self.result, "rst", "doc"))
            else:
                doc = eval(combineJson(self.result, "rst", "doc", "model"))

            global_config.set_value("doc", doc)

            global_config.set_value("candidates",
                                    eval(combineJson(self.result, "rst", "candidates")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test36_agree_09(self):
        ''' [第九岗] 审批 '''
        import datetime
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 前交易部分 ****************************
            # 审批流为“销售合同”，且当前岗为“商务人员时”
            if self.func == "/contract" \
                    and self.dict["商务人员"] == self.dict["当前节点处理人"]:
                self.dict["doc"]["contractbase"]["receivabletype"] = makeJsonData("业务应收创建方式")

                effectdate = makeJsonData("签订日期")
                if effectdate == "":
                    ed = str(datetime.date.today())
                else:
                    ed = effectdate
                self.dict["doc"]["contractbase"]["effectdate"] = ed

            # 下岗审批人
            candidates_init = self.dict["candidates"]

            if candidates_init != []:
                receivers = candidates_init[0]["receivers"]
                for i in range(len(receivers)):
                    if receivers[i]["name"] == "刘迪":
                        # 离职员工跳过
                        del receivers[i]
                        continue
                    else:
                        nextUser = receivers[i]["login"]
                        self.dict["candidates"][0]["receivers"] = [
                            receivers[i]
                        ]

                        # global_config.set_value("candidates", candidates)
                        global_config.set_value("当前节点处理人", nextUser)
                        self.dict["审批岗位"] += ("," + nextUser)
                        loadProcessValue("#审批岗位", realValue=self.dict["审批岗位"])
                        break

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = \
                {
                    "candidates": self.dict["candidates"],
                    "doc": self.dict["doc"],
                    "nodeId": self.dict["nodeId"],
                    "processId": self.dict["processId"]
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test37_get_list_09(self):
        ''' [第九岗] 审批后用上一岗节点信息查询当前岗用户名（验证单据审批状态） '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            if self.func in ["/credit", "/reimburse"]:
                # “付款申请单/报销单”的list接口数据只可用admin查询
                username = makeJsonData("管理员登录名")
                password = makeJsonData("登陆密码")
                myToken = get_token(login_url,username,password)
            else:
                myToken = self.dict["TOKEN"]

            header = \
                {
                "Authorization": "Bearer " + myToken,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["list_unfinished"]
            myKey = params_dict["list_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            rst = self.result["rst"]
            if isinstance(rst, dict):
                data = self.result["rst"]["data"]
                sum = data.get("total")
            else:
                sum = 0

            # 若根据单据号未查询到单据信息，则结束次案例后在最后一案例中查询状态是否为“审批完成”
            if sum > 0:
                nextUser = combineJson(self.result,"rst", "data", "items", 0, "curreceiver", 0)
                if nextUser in specialUser.keys():
                    loginName = specialUser[nextUser]
                else:
                    loginName = pinyinTransform(nextUser)
                global_config.set_value("当前节点处理人", loginName)

                loadProcessValue("#审批状态", realValue="审批中")
            else:
                loadProcessValue("#审批状态", realValue="非审批中")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test38_get_mydoing_10(self):
        ''' [第十岗] 第十岗登陆，获取当前节点nodeid '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 登陆部分 ****************************
            username = self.dict["当前节点处理人"]
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["mydoing_dict"]
            myKey = params_dict["mydoing_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取登陆信息
            global_config.set_value("TOKEN", token)

            global_config.set_value("nodeId",
                                    combineJson(self.result, "rst", "data", "items", 0, "node", "_id"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test39_get_detail_10(self):
        """ [第十岗] 第十岗登陆，查询单据详细信息 """
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            header = {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = {
                "processId": self.dict["processId"],
                "nodeId": self.dict["nodeId"]
            }
            # print(params)
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            if self.func == "/reimburse":
                # 审批流为“报销单”时
                doc = eval(combineJson(self.result, "rst", "doc"))
            else:
                doc = eval(combineJson(self.result, "rst", "doc", "model"))

            global_config.set_value("doc", doc)

            global_config.set_value("candidates",
                                    eval(combineJson(self.result, "rst", "candidates")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test40_agree_10(self):
        ''' [第十岗] 审批 '''
        import datetime
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        if self.funcType == "销售合同作废":
            base_url = self.url + "/contractcancel" + getInterfaceData("调用接口")
        else:
            base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 前交易部分 ****************************
            # 审批流为“销售合同”，且当前岗为“商务人员时”
            if self.func == "/contract" \
                    and self.dict["商务人员"] == self.dict["当前节点处理人"]:
                self.dict["doc"]["contractbase"]["receivabletype"] = makeJsonData("业务应收创建方式")

                effectdate = makeJsonData("签订日期")
                if effectdate == "":
                    ed = str(datetime.date.today())
                else:
                    ed = effectdate
                self.dict["doc"]["contractbase"]["effectdate"] = ed

            # 下岗审批人
            candidates_init = self.dict["candidates"]

            if candidates_init != []:
                receivers = candidates_init[0]["receivers"]
                for i in range(len(receivers)):
                    if receivers[i]["name"] == "刘迪":
                        # 离职员工跳过
                        del receivers[i]
                        continue
                    else:
                        nextUser = receivers[i]["login"]
                        self.dict["candidates"][0]["receivers"] = [
                            receivers[i]
                        ]

                        # global_config.set_value("candidates", candidates)
                        global_config.set_value("当前节点处理人", nextUser)
                        self.dict["审批岗位"] += ("," + nextUser)
                        loadProcessValue("#审批岗位", realValue=self.dict["审批岗位"])
                        break

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = \
                {
                    "candidates": self.dict["candidates"],
                    "doc": self.dict["doc"],
                    "nodeId": self.dict["nodeId"],
                    "processId": self.dict["processId"]
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test41_get_list_10(self):
        ''' [第十岗] 审批后用上一岗节点信息查询当前岗用户名（验证单据审批状态） '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or self.flag == "非审批中":
            self.testResult = "跳过"
            return

        try:
            # **************************** 交易部分 ****************************
            if self.func in ["/credit", "/reimburse"]:
                # “付款申请单/报销单”的list接口数据只可用admin查询
                username = makeJsonData("管理员登录名")
                password = makeJsonData("登陆密码")
                myToken = get_token(login_url,username,password)
            else:
                myToken = self.dict["TOKEN"]

            header = \
                {
                "Authorization": "Bearer " + myToken,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["list_unfinished"]
            myKey = params_dict["list_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            rst = self.result["rst"]
            if isinstance(rst, dict):
                data = self.result["rst"]["data"]
                sum = data.get("total")
            else:
                sum = 0

            # 若根据单据号未查询到单据信息，则结束次案例后在最后一案例中查询状态是否为“审批完成”
            if sum > 0:
                nextUser = combineJson(self.result,"rst", "data", "items", 0, "curreceiver", 0)
                if nextUser in specialUser.keys():
                    loginName = specialUser[nextUser]
                else:
                    loginName = pinyinTransform(nextUser)
                global_config.set_value("当前节点处理人", loginName)

                loadProcessValue("#审批状态", realValue="审批中")
            else:
                loadProcessValue("#审批状态", realValue="非审批中")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test42_check_status(self):
        ''' admin登陆，查询单据状态，校验是否审批结束 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + self.func + getInterfaceData("调用接口")

        if self.terminateProcess != "":
            self.testResult = "跳过"
            return

        try:
            # **************************** 登陆部分 ****************************
            username = makeJsonData("管理员登录名")
            password = makeJsonData("登陆密码")

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            func = makeJsonData("审批流类型")
            myDict = params_dict["list_done"]
            myKey = params_dict["list_key"]
            params = myDict[func]
            md = params
            queryPath = myKey[func].split(".")

            for i in range(len(queryPath)):
                if len(queryPath) == i + 1:
                    break
                md = md[queryPath[i]]
            md[queryPath[-1]] = makeJsonData("单据号")

            params = json.dumps(params).replace("'","\"")
            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            data = self.result["rst"]["data"]
            sum = data.get("total")
            # 若根据单据号未查询到单据信息，则审批失败
            assert sum > 0, "已跳出审批流，但单据状态校验失败！"
            assert sum == 1, "已跳出审批流，但未唯一检索到该单据，请在壳上手工确认！"

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except AssertionError as e:
            self.testResult = "失败"
            raise AssertionError(e)
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT", self.testResult)
            self.terminateProcess = True
            loadProcessValue("#流程开关", realValue="流程正常结束")
            loadProcessValue("#审批状态", realValue="审批成功")
            writeTextResult(myRow=self.myRow)


if __name__ == '__main__':
    test_data.init_data() # 初始化接口测试数据
    unittest.main()
