import unittest
import requests
import os, sys,time
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

class CaigouContractsTest(unittest.TestCase):
    ''' 库存调整 '''

    def setUp(self):
        self.dict = global_config._global_dict                              # 全局变量字典
        self.moduleName = "库存调整_02"                                      # 当前流程名称
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


    def test01_get_boxes_info(self):
        ''' 登陆相应环境壳后，根据库存调整单查询拣配单及新旧箱子信息 '''
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
                    "code": makeJsonData("库存调整单")
                }

            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取新旧箱子信息及拣配单信息
            jianpidanhao = combineJson(self.result,"rst","data","info","outer","code")
            loadProcessValue("#出库拣配单号",realValue=jianpidanhao)
            global_config.set_value("#出库拣配单号",jianpidanhao)

            oldBoxesInfo = eval(combineJson(self.result, "rst", "outerMaterials", "out"))
            boxArray = []
            for i in range(len(oldBoxesInfo)):
                boxArray.append(oldBoxesInfo[i]["code"])

            loadProcessValue("#旧箱号",realValue=str(boxArray))
            global_config.set_value("#旧箱号", boxArray)

            # 获取调整类型代码
            adjustType = combineJson(self.result,"rst","data","type")
            global_config.set_value("#调整类型", adjustType)

            # 获取壳登陆信息
            global_config.set_value("TOKEN", token)


            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test02_get_available_boxes(self):
        ''' 查询已有箱子，筛选出实物箱子 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        base_url = self.url + getInterfaceData("调用接口")

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

            for i in range(len(self.dict["#旧箱号"])):
                boxName = self.dict["#旧箱号"][i]
                params = \
                    {
                        "limit": "10",
                        "no": boxName,
                        "page": 1,
                        "pos": {}
                    }

                params = json.dumps(params).replace("'","\"")

                self.result = myRequest(base_url, headers=header, data=params)

                # **************************** 校验部分 ****************************
                checkTheMessage("code",varNameInExcel="code")
                checkTheMessage("msg",varNameInExcel="msg")

                # **************************** 返回值部分 ****************************
                # 将非实物箱子剔除待调拨范围
                boxInfo = self.result["rst"]["data"]["items"][0]
                if boxInfo.get("physics"):
                    if boxInfo["physics"].get("package") != "纸箱":
                        self.dict["#旧箱号"].remove(boxName)

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test03_get_adjust_type(self):
        ''' 获取调整类型 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        base_url = self.url + getInterfaceData("调用接口")

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
                    "enumnames": [
                        "adjust_type"
                    ]
                }

            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取调整类型代码
            adjustType = self.result["rst"]["data"]["adjust_type"].get(self.dict["#调整类型"])
            loadProcessValue("#调整类型",realValue=adjustType)
            global_config.set_value("#调整类型", adjustType)


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
        ''' 登陆相同环境的PDA后，对每个箱子分别拣配（有n个箱子，则此案例中循环请求n次） '''
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

            time.sleep(1)
            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            boxNum = deepcopy(len(self.dict["#旧箱号"]))
            boxes = deepcopy(self.dict["#旧箱号"])

            for i in range(boxNum):
                boxName = boxes[i]
                print("📦 第 %d 次扫描箱子，箱号为：%s" %(i+1,boxName))
                params = \
                    {
                        "bill_code": makeJsonData("#出库拣配单号"),
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
            # 获取“token”
            global_config.set_value("TOKEN",token)

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            self.terminateProcess = True
            loadProcessValue("#流程开关",realValue="拣配成功")
            writeTextResult(myRow=self.myRow)


    def test05_box_uptray(self):
        ''' 登陆相应环境PDA后，扫码进行箱子上托盘 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        base_url = self.url + getInterfaceData("调用接口")

        # “仓位”字段为本案例的执行开关
        if self.terminateProcess != ("" and "拣配成功") \
                or makeJsonData("仓位",whetherToInitialize="是") == "中断":
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
                    "box_codes": self.dict["#新箱号"],
                    "tray": makeJsonData("托盘")
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


    def test06_tray_up_to_positon(self):
        ''' 扫码进行托盘入仓位 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        base_url = self.url + getInterfaceData("调用接口")

        # “仓位”字段为本案例的执行开关
        if self.terminateProcess != ("" and "拣配成功") \
                or makeJsonData("仓位",whetherToInitialize="是") == "中断":
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
                    "sl": makeJsonData("仓位"),
                    "trays": [
                        makeJsonData("托盘")
                    ]
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
            self.terminateProcess = True
            loadProcessValue("#流程开关",realValue="库存调整成功")
            writeTextResult(myRow=self.myRow)


if __name__ == '__main__':
    test_data.init_data() # 初始化接口测试数据
    unittest.main()
