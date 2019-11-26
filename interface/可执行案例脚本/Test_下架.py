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
from interface import Environment_Select

from copy import deepcopy


class AutomatedTesting (unittest.TestCase):
    ''' 下架 '''

    def setUp(self):
        self.dict = global_config._global_dict                              # 全局变量字典
        self.moduleName = "下架"                                            # 当前流程名称
        global_config.set_value("MODULENAME",self.moduleName)

        self.url = Environment_Select[self.dict.get("ENVIRONMENT")]         # 环境基础地址
        self.caseName = None                                                # 被测案例的案例名

        self.myRow = global_config.get_value('TESTROW')                     # 调用数据行
        self.result = None                                                  # 当前案例响应报文
        self.testResult = None                                              # 当前案例执行状态（在最后一个案例中还作为流程执行状态）
        self.terminateProcess = makeProcessData("#流程开关")                 # 案例执行开关

        if self.terminateProcess == "" \
                and self.terminateProcess != "无箱子可下架":
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


    def test01_get_WithdrawType(self):
        ''' 登陆相应环境壳后，根据“出库拣配单号”/“SAP单据号”查询“出库类型” '''
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

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            params = \
                {
                    "choice": {
                        "EOBtime": "",
                        "SOBtime": "",
                        "code": "",
                        "contract": "",
                        "from": "",
                        "orderId": makeJsonData("SAP单据号"),
                        "purchaseId": "",
                        "status": "",
                        "type": ""
                    },
                    "limit": "10",
                    "page": 1
                }

            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取“token”
            global_config.set_value("TOKEN",token)

            if makeJsonData("出库拣配单号") == "":
                loadProcessValue("出库拣配单号","rst","data","items",0,"code")

            # 获取“出库类型”
            outBoundType = \
                {
                    "ZJ01": "销售放货出库（项目）",
                    "ZJ02": "销售放货出库（分销）",
                    "ZJ032": "销售维修出库",
                    "ZJ04": "样机借出出库",
                    "ZPRF": "采购退货出库"
                }

            withdrawType = outBoundType.get(combineJson(self.result,"rst","data","items",0,"type"))
            loadProcessValue("#下架类型",realValue=withdrawType)
            global_config.set_value("下架类型",withdrawType)

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test02_get_box_info(self):
        ''' 根据“出库拣配单号”查询可下架的箱子信息 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "":
            self.testResult = "跳过"
            return

        # 与库表中数据主键重复情况均需考虑是否用初始化
        if getInterfaceData("是否数据库初始化") == "是":
            DB().delete(tableName,deleteData)

        try:
            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = \
                {
                    "code":makeJsonData("出库拣配单号")
                }

            params = json.dumps(params).replace("'","\"")

            t0 = time.time()
            self.result = myRequest(base_url, headers=header, data=params)
            t1 = time.time()
            print("⏰ 查询接口响应时间：", t1 - t0, "s")

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************

            # 获取拣配单下箱号信息
            boxInfo = eval(combineJson(self.result,"rst","data","allBoxes"))
            boxArray = []

            t2 = time.time()
            for i in range(len(boxInfo)):               # 正序
            # for i in range(len(boxInfo)-1, -1, -1):     # 倒序
                if boxInfo[i].get("physics"):
                    # 非实物箱子均不处理

                    # if (combineJson(boxInfo,i,"physics","package") == "纸箱"
                    #     or combineJson(boxInfo,i,"physics","package") == "胶合板托盘"
                    #     or combineJson(boxInfo,i,"physics","package") == "金属托盘") \
                    #         and boxInfo[i].get("code") not in boxArray:

                    # if combineJson(boxInfo,i,"physics","package") != "" \
                    if boxInfo[i].get("code") not in boxArray \
                            and boxInfo[i].get("status") != 2:
                        boxArray.append(boxInfo[i]["code"])
                        # print(boxArray)

            t3 = time.time()
            print("⏰ 遍历箱子信息时间：", t3 - t2, "s")
            global_config.set_value("t3", t3)

            global_config.set_value("箱号", boxArray)
            # 写入箱号/响应报文到临时文件，便于自动化/手工协同操作
            file = open(r"C:\Users\47612\Desktop\boxNum.txt", "w", encoding="utf-8")
            file.write(str(boxArray))
            file.close()

            # file = open(r"C:\Users\47612\Desktop\result.txt", "w", encoding="utf-8")
            # file.write(str(self.result))
            # file.close()

            # 获取箱子个数
            global_config.set_value("箱子总数",len(boxInfo))
            global_config.set_value("SUM",len(boxInfo))

            if self.dict["箱子总数"] > len(self.dict["箱号"]):
                print("********** 有 %d 个箱子无需下架 **********" %(self.dict["箱子总数"] - len(self.dict["箱号"])))
                self.dict["箱子总数"] = len(self.dict["箱号"])

            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            if self.dict["箱子总数"] != 0:
                writeTextResult()
            else:
                loadProcessValue("#流程开关",realValue="无箱子可下架")
                writeTextResult(myRow=self.myRow)


    def test03_pick_boxes(self):
        ''' 对每个箱子分别拣配（有n个箱子，则此案例中循环请求n次），拣配后查询各箱子的“status”，若为2则为整箱，跳过扫sn '''
        import time
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        t4 = time.time()
        print("⏰ 上一案例切换时间：", t4 - self.dict["t3"], "s")

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

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            boxNum = deepcopy(self.dict["箱子总数"])
            boxes = deepcopy(self.dict["箱号"])

            startPickTime = time.time()
            for i in range(boxNum):
                boxName = boxes[i]
                print("📦 第 %d 次扫描箱子，箱号为：%s" %(i+1,boxName))
                params = \
                    {
                        "bill_code": makeJsonData("出库拣配单号"),
                        "box_code": boxName,
                        "phase": "BoxPhase",
                        "platform": "pda",
                        "sns": []
                    }
                params = json.dumps(params).replace("'","\"")

                self.result = myRequest(base_url, headers=header, data=params)

                # **************************** 校验部分 ****************************
                checkTheMessage("code",varNameInExcel="code")
                checkTheMessage("msg",varNameInExcel="msg")

                # **************************** 返回值部分 ****************************
                materialsInfo = self.result["rst"]["data"].get("materials")
                boxInfo = eval(combineJson(self.result,"rst","data","bill","allBoxes"))

                if "materialsArray" not in locals().keys():
                    materialsArray = {}

                for j in range(len(boxInfo)):
                    if boxInfo[j].get("NO") == boxName \
                            or boxInfo[j].get("code") == boxName:
                        if boxInfo[j]["status"] == 2:
                            # self.dict["箱子总数"] += -1
                            # self.dict["箱号"].remove(boxName)
                            global_config.set_value("箱子总数",
                                                    self.dict["箱子总数"] - 1)

                            self.dict["箱号"].remove(boxName)
                            global_config.set_value("箱号",self.dict["箱号"])
                        elif boxInfo[j]["status"] == 0:
                            # materialsInfo = self.result["rst"]["data"]["bill"]["allBoxes"][j].get("materials")
                            print("%s 对应的 materials 为：%s" %(boxName,materialsInfo))
                            materialsArray[boxName] = materialsInfo

            global_config.set_value("MATERIALARRAY",materialsArray)

            # 获取“token”
            global_config.set_value("TOKEN",token)

            # 保存开始拣配时间
            global_config.set_value("开始拣配时间", startPickTime)
            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test04_pick_boxes(self):
        ''' 扫描SN（若m个箱子中共有n种物料，则此案例请求n次） '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        base_url = self.url + getInterfaceData("调用接口")


        if self.terminateProcess != "" \
                or self.dict["箱子总数"] == 0:
            self.testResult = "跳过"
            return

        # 与库表中数据主键重复情况均需考虑是否用初始化
        if getInterfaceData("是否数据库初始化") == "是":
            DB().delete(tableName,deleteData)

        try:
            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            for i in range(self.dict["箱子总数"]):
                boxName = combineJson(self.dict,"箱号",i)
                boxInfo = self.dict["MATERIALARRAY"].get(boxName)

                for j in range(len(boxInfo)):
                    sn = None
                    for k in range(len(boxInfo[j]["sns"])):
                        # 拼接SN
                        if sn is None:
                            sn = boxInfo[j]["sns"][k]
                        else:
                            sn = sn + u"\n" + boxInfo[j]["sns"][k]

                    params = \
                        {
                            "bill_code": makeJsonData("出库拣配单号"),
                            "box_code": boxName,
                            "material_sn": {
                                "mid": combineJson(boxInfo,j,"mid"),
                                "sapid": combineJson(boxInfo,j,"sapid"),
                                "sn": [
                                    sn
                                ]
                            },
                            "phase": "SnPhase",
                            "platform": "pda"
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


    def test05_pick_boxes(self):
        ''' 扫描SN（有n个箱子，则此案例中循环请求n次） '''
        import time
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        base_url = self.url + getInterfaceData("调用接口")


        if self.terminateProcess != "" \
                or self.dict["箱子总数"] == 0:
            self.testResult = "跳过"
            return

        # 与库表中数据主键重复情况均需考虑是否用初始化
        if getInterfaceData("是否数据库初始化") == "是":
            DB().delete(tableName,deleteData)


        try:
            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            for i in range(self.dict["箱子总数"]):
                boxName = combineJson(self.dict,"箱号",i)

                params = \
                    {
                        "bill_code": makeJsonData("出库拣配单号"),
                        "box_code": boxName,
                        "material_sns": self.dict["MATERIALARRAY"][boxName],
                        "phase": "SubmitPhase",
                        "platform": "pda"
                    }
                params = json.dumps(params).replace("'","\"")
                # print(params)

                self.result = myRequest(base_url, headers=header, data=params)

                # **************************** 校验部分 ****************************
                checkTheMessage("code",varNameInExcel="code")
                checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            endPickTime = time.time()
            # 保存结束拣配时间
            print("结束拣配时间：", endPickTime)
            global_config.set_value("结束拣配时间", endPickTime)

            t = (endPickTime - self.dict["开始拣配时间"])/self.dict["SUM"]
            print("单箱平均拣配耗时：", t, "s")
            global_config.set_value("单箱平均拣配耗时", t)

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test06_approval(self):
        ''' 复合 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        base_url = self.url + getInterfaceData("调用接口")


        if self.terminateProcess != "":
            self.testResult = "跳过"
            return

        # 与库表中数据主键重复情况均需考虑是否用初始化
        if getInterfaceData("是否数据库初始化") == "是":
            DB().delete(tableName,deleteData)


        try:
            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            params = \
                {
                    "bill_code": makeJsonData("出库拣配单号"),
                    "platform": "pda"
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


    def test07_check_undercarriage_result(self):
        ''' 查询下架结果 '''
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

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            params = \
                {
                    "choice": {
                        "EDHtime": "",
                        "SDHtime": "",
                        "boundCode": makeJsonData("出库拣配单号"),
                        "boxCode": "",
                        "type": "",
                        "wh": ""
                    },
                    "limit": "10",
                    "page": 1
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")
            # assert len(self.result["rst"]["data"]["items"]) == self.dict["箱子总数"]

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            self.terminateProcess = True
            loadProcessValue("#流程开关",realValue="下架成功")
            writeTextResult(myRow=self.myRow)


if __name__ == '__main__':
    test_data.init_data() # 初始化接口测试数据
    unittest.main()
