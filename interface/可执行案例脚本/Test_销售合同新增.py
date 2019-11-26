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


class CaigouContractsTest(unittest.TestCase):
    ''' 销售合同审批流 '''

    def setUp(self):
        self.dict = global_config._global_dict                              # 全局变量字典
        self.moduleName = "销售合同审批流"                                   # 当前流程名称
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


    def test01_get_customer_kunnr(self):
        ''' 经办岗登陆，根据客户名称获取客户编码 '''
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
                    "KTOKD": "ZC01",
                    "KUNNR": "",
                    "NAME": makeJsonData("客户名称/开票客户"),
                    "limit": 20,
                    "page": 1
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取“token”
            global_config.set_value("TOKEN",token)

            # 获取“客户编码”
            global_config.set_value("客户编码",
                                    combineJson(self.result,"rst","data","items",0,"KUNNR"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test02_get_user_message(self):
        ''' 经办岗登陆，根据销售人员姓名获取用户信息 '''
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
                    "limit": "5",
                    "name": makeJsonData("销售人员姓名"),
                    "page": 1
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            global_config.set_value("SALESID",
                                    combineJson(self.result,"rst","data","items",0,"_id"))
            global_config.set_value("ORGID",
                                    combineJson(self.result,"rst","data","items",0,"orgid"))
            global_config.set_value("申请部门",
                                    combineJson(self.result,"rst","data","items",0,"orgname"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test03_get_org_data(self):
        ''' 经办岗登陆，获取销售人员归属信息 '''
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
                    "level": 1,
                    "orgid": self.dict["ORGID"]
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取“事业部”
            global_config.set_value("事业部",
                                    combineJson(self.result,"rst","data","orgname"))
            global_config.set_value("ORGID2",
                                    combineJson(self.result,"rst","data","_id"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test04_get_contract_data(self):
        ''' 经办岗登陆，查询报文对应值，产品线信息 '''
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

            params = {"contrattype":makeJsonData("合同类型")}
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            myMsg = eval(combineJson(self.result,"rst","data","enum","CPX"))
            productLine = makeJsonData("产品线")
            for k in range(0,200):
                if myMsg[k]["name"] == productLine:
                    # print(myMsg[k]["code"])
                    global_config.set_value("PRODUCTID",myMsg[k]["code"])
                    break

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test05_save_list01(self):
        ''' 经办岗登陆，填写合同订单信息并保存，获取合同信息 '''
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

            # 映射“销售主体”与“是否双主体”的回显关系
            escompany_dict = \
                {
                    "中建材信息技术股份有限公司": "否",
                    "中建材集团进出口有限公司": "是"
                }

            params = \
                {
                    "doc": {
                        "contractId": "",
                        "contractbase": {
                            "KPstomer": makeJsonData("客户名称/开票客户"),
                            "KPstomerid": self.dict["客户编码"],
                            "contactreceivablescondition": [],
                            "contactreceivablesconditionshowarea": "",
                            "contractmoney": makeJsonData("合同金额"),
                            "contracttemplate": makeJsonData("合同模板"),
                            "contracttype": makeJsonData("项目类型"),
                            "cp": makeJsonData("配套服务"),
                            "deliverconditionarea": "交货日期：供方在合同生效且收到预付款后25个日历日内交货",
                            "deliverwaycheck": {},
                            "escompany": makeJsonData("销售主体"),
                            "finalconsumer": makeJsonData("最终用户"),
                            "guarantyterm": "按原厂标准执行",
                            "hasservicecontract": makeJsonData("是否关联合同"),
                            "is2body": escompany_dict[makeJsonData("销售主体")],
                            "isshowunitprice": "否",
                            "product": makeJsonData("产品线"),
                            "productId": self.dict["PRODUCTID"],
                            "project": makeJsonData("项目名称"),
                            "rebateitem": [],
                            "rebatemoney": "0",
                            "rebatepercent": "0",
                            "receiptdesc": "供方就合同金额开具增值税专用发票",
                            "receiptdescarea": "供方就合同金额开具增值税专用发票",
                            "receipttype": makeJsonData("开票税率"),
                            "receiver": [],
                            "salesid": self.dict["SALESID"],
                            "salesname": makeJsonData("销售人员姓名"),
                            "salesorgid": self.dict["ORGID"],
                            "salesorgid2": self.dict["ORGID2"],
                            "salesorgnanme": self.dict["申请部门"],
                            "salesorgnanme2": self.dict["事业部"],
                            "servicemethod": "",
                            "stomer": makeJsonData("客户名称/开票客户"),
                            "stomerid": self.dict["客户编码"],
                            "traderlogin": pinyinTransform(makeJsonData("商务人员")),
                            "tradername": makeJsonData("商务人员")
                        }
                    }
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            loadProcessValue("#processId","rst","doc","processId")
            loadProcessValue("#nodeId","rst","doc","nodeId")
            loadProcessValue("#合同号","rst","doc","contractNO")

            # if combineJson(self.result,"rst","doc","candidates",0,"receivers",0,"name") == "刘迪":
            #     loadProcessValue("#审批一岗","rst","doc","candidates",0,"receivers",1,"name")
            #     loadProcessValue("#下岗审批人信息/candidates","rst","doc","candidates",0,"receivers",1)
            # else:
            #     loadProcessValue("#审批一岗","rst","doc","candidates",0,"receivers",0,"name")
            #     loadProcessValue("#下岗审批人信息/candidates","rst","doc","candidates",0,"receivers",0)


            # 获取当前节点合同信息
            global_config.set_value("合同信息",eval(params)["doc"]["contractbase"])
            # 获取“contractId”
            global_config.set_value("CONTRACTID",
                                    combineJson(self.result,"rst","doc","contractId"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test06_get_materiel_info(self):
        ''' 经办岗登陆，通过“内部物料编码”获取物料信息 '''
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

            materiel_dict = []
            for i in range(1,30):
                if i < 10:
                    varNum = "0%s" %i
                else:
                    varNum = str(i)

                if makeJsonData("内部物料编码-%s" %varNum) is not None \
                        and makeJsonData("内部物料编码-%s" %varNum) != "":
                    print("📦 第 %d 个物料为：%s" %(i,makeJsonData("内部物料编码-%s" %varNum)))
                    params = \
                        {
                            "MAKTX": "",
                            "ZZGKXH": "",
                            "code": makeJsonData("内部物料编码-%s" %varNum),
                            "contracttype": makeJsonData("项目类型"),
                            "escompany": makeJsonData("销售主体"),
                            "limit": "5",
                            "page": 1,
                            "salesid": self.dict["SALESID"]
                        }
                else:
                    break

                params = json.dumps(params).replace("'", "\"")
                self.result = myRequest(base_url, headers=header, data=params)

                # **************************** 校验部分 ****************************
                checkTheMessage("code",varNameInExcel="code")
                checkTheMessage("msg",varNameInExcel="msg")

                # **************************** 返回值部分 ****************************
                materiel_info = \
                {
                    "amountcost": "",
                    "cashrebate": "",
                    "cess": 0,
                    "contractId": self.dict["CONTRACTID"],
                    "count": makeJsonData("数量-01"),
                    "desc": combineJson(self.result,"rst","data","items",0,"MAKTX"),
                    "devicecost": "",
                    "from": 0,
                    "goodscode": makeJsonData("内部物料编码-%s" %varNum),
                    "goodstype": "",
                    "purchasecontractid": "",
                    "purchasecount": 0,
                    "purchaseid": "",
                    "purchaseorderid": "",
                    "purchaseprice": "",
                    "salesitemid": "",
                    "sapid": "",
                    "selfpickupcost": "",
                    "servicecost": "",
                    "singTotal": makeJsonData("小计-%s" %varNum),
                    "sourcegoodscode": combineJson(self.result,"rst","data","items",0,"BISMT"),
                    "sourcegoodsdesc": combineJson(self.result,"rst","data","items",0,"ZZMAKTX"),
                    "storeplace": "",
                    "supplierorderid": "",
                    "thesum": "",
                    "thetype": 0,
                    "unitprice": makeJsonData("单价-%s" %varNum),
                    "version": combineJson(self.result,"rst","data","items",0,"ZZGKXH")
                }

                materiel_dict.append(materiel_info)

            global_config.set_value("MATEREIL_DICT",materiel_dict)

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test07_save_contract_items(self):
        ''' 经办岗登陆，保存物料信息 '''
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
                    "doc": {
                        "contractId": self.dict["CONTRACTID"],
                        "handwork": self.dict["MATEREIL_DICT"],
                        "lend": [],
                        "nodeId": makeProcessData("#nodeId"),
                        "processId": makeProcessData("#processId"),
                        "purchase": [],
                        "purchaseConfirm": [],
                        "upload": []
                    }
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


    def test08_save_list02(self):
        ''' 经办岗登陆，填写物料信息并保存，获取合同信息 '''
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
                    "doc": {
                        "contractId": self.dict["CONTRACTID"],
                        "contractbase": self.dict["合同信息"],
                        "nodeId": makeProcessData("#nodeId"),
                        "processId": makeProcessData("#processId")
                    }
                }
            params = json.dumps(params).replace("'","\"")
            # print(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            loadProcessValue("#processId","rst","doc","processId")
            loadProcessValue("#nodeId","rst","doc","nodeId")
            loadProcessValue("#contractNO","rst","doc","contractNO")

            if combineJson(self.result,"rst","doc","candidates",0,"receivers",0,"name") == "刘迪":
                loadProcessValue("#审批一岗","rst","doc","candidates",0,"receivers",1,"name")
                loadProcessValue("#下岗审批人信息/candidates","rst","doc","candidates",0,"receivers",1)
            else:
                loadProcessValue("#审批一岗","rst","doc","candidates",0,"receivers",0,"name")
                loadProcessValue("#下岗审批人信息/candidates","rst","doc","candidates",0,"receivers",0)

            # 获取“contractId”
            global_config.set_value("CONTRACTID",
                                    combineJson(self.result,"rst","doc","contractId"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test09_listcontact(self):
        ''' 经办岗登陆，完善文本信息 '''
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
                    "KUNNR": self.dict["客户编码"],
                    "NAME": makeJsonData("商务联系人姓名")
                }
            params = json.dumps(params).replace("'","\"")
            # print(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test10_selectcus(self):
        ''' 经办岗登陆，完善文本信息 '''
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
                    "KUNNR":self.dict["客户编码"]
                }
            params = json.dumps(params).replace("'","\"")
            # print(params)

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


    def test11_save_contract_items(self):
        ''' 经办岗登陆，保存合同信息 '''
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
                    "doc": {
                        "contractId": self.dict["CONTRACTID"],
                        "handwork": self.dict["MATEREIL_DICT"],
                        "lend": [],
                        "nodeId": makeProcessData("#nodeId"),
                        "processId": makeProcessData("#processId"),
                        "purchase": [],
                        "purchaseConfirm": [],
                        "upload": []
                    }
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


    def test12_create_new_process(self):
        ''' 经办岗登陆，提交新建审批流 '''
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

            # 映射“销售主体”与“是否双主体”的回显关系
            escompany_dict = \
                {
                    "中建材信息技术股份有限公司": "否",
                    "中建材集团进出口有限公司": "是"
                }

            # 映射“运输方式”与编号的回显关系
            transferway_dict = \
                {
                    "专车": "10",
                    "国内海运": "02",
                    "国内空运": "03",
                    "国内陆运": "01",
                    "国际海运": "05",
                    "国际空运": "06",
                    "国际陆运": "04",
                    "快递": "09",
                    "无实物发货": "12",
                    "火车运输": "08",
                    "自提": "11",
                    "陆运快件": "07"
                }

            params = \
                {
                    "candidates": [
                        {
                            "receivers": [
                                eval(makeProcessData("#下岗审批人信息/candidates"))
                            ],
                            "type": "purchase"
                        }
                    ],
                    "doc": {
                        "contractId": self.dict["CONTRACTID"],
                        "nodeId": makeProcessData("#nodeId"),
                        "processId": makeProcessData("#processId"),
                        "contractbase": {
                            "KPstomer": makeJsonData("客户名称/开票客户"),
                            "KPstomerid": self.dict["客户编码"],
                            "contactname": makeJsonData("商务联系人姓名"),
                            "contactphone": makeJsonData("商务联系人电话"),

                            "contactreceivablescondition": [
                                {
                                    "cond": makeJsonData("收款条件-01"),
                                    "days": makeJsonData("收款天数-01"),
                                    "method": makeJsonData("收款方式-01"),
                                    "money": makeJsonData("收款金额-01"),
                                    "scale": makeJsonData("收款比例(％)-01"),
                                    "thetype": makeJsonData("收款类型-01"),
                                    "type": ""
                                },
                                {
                                    "cond": makeJsonData("收款条件-02"),
                                    "days": makeJsonData("收款天数-02"),
                                    "method": makeJsonData("收款方式-02"),
                                    "money": makeJsonData("收款金额-02"),
                                    "scale": makeJsonData("收款比例(％)-02"),
                                    "thetype": makeJsonData("收款类型-02"),
                                    "type": ""
                                }
                            ],
                            # "contactreceivablesconditionshowarea": "需方于本合同生效之日起8个日历日内支付供方合同全款的50%作为预付款，支付方式为电汇;   需方于收到货物之日起5日内支付供方合同全款的50%，支付方式为支票;",

                            "contractmoney": makeJsonData("合同金额"),
                            "contracttemplate": makeJsonData("合同模板"),
                            "contracttype": makeJsonData("项目类型"),
                            "cp": makeJsonData("配套服务"),
                            "deliverconditionarea": "交货日期：供方在合同生效且收到预付款后25个日历日内交货",
                            "deliverwaycheck": {},
                            "escompany": makeJsonData("销售主体"),
                            "finalconsumer": makeJsonData("最终用户"),
                            "guarantyterm": "按原厂标准执行",
                            "hasservicecontract": makeJsonData("是否关联合同"),
                            "is2body": escompany_dict[makeJsonData("销售主体")],
                            "isshowunitprice": "否",
                            "paymentdate": notChooseNull(makeJsonData("货期要求"),
                                                         getCurrentDate("-")),
                            "product": makeJsonData("产品线"),
                            "productId": self.dict["PRODUCTID"],
                            "project": makeJsonData("项目名称"),
                            "projectserviceterm": makeJsonData("项目工程服务方式"),
                            "projectservicetermarea": "工程安装：本合同项下设备的工程由%s，服务内容详见服务清单"
                                                      %makeJsonData("项目工程服务方式"),
                            "rebateitem": [],
                            "rebatemoney": "0",
                            "rebatepercent": "0",
                            "receiptdesc": "供方就合同金额开具增值税专用发票",
                            "receiptdescarea": "供方就合同金额开具增值税专用发票",
                            "receipttype": makeJsonData("开票税率"),
                            "receiver": [
                                {
                                    "address": "",
                                    "city": "420100",
                                    "name": "自动化收货人",
                                    "phone": "",
                                    "province": "42",
                                    "tel": "",
                                    "zipcode": ""
                                }
                            ],
                            "salesid": self.dict["SALESID"],
                            "salesname": makeJsonData("销售人员姓名"),
                            "salesorgid": self.dict["ORGID"],
                            "salesorgid2": self.dict["ORGID2"],
                            "salesorgnanme": self.dict["申请部门"],
                            "salesorgnanme2": self.dict["事业部"],
                            "servicemethod": "",
                            "sktj": makeJsonData("收款条件"),
                            "stomer": makeJsonData("客户名称/开票客户"),
                            "stomerid": self.dict["客户编码"],
                            "stomerxydj": "",
                            "traderlogin": pinyinTransform(makeJsonData("商务人员")),
                            "tradername": makeJsonData("商务人员"),
                            "transferway": transferway_dict[makeJsonData("运输方式")]
                        }
                    }
                }

            params = json.dumps(params).replace("'","\"")
            # print(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            loadProcessValue("#processId","rst","processId")

            # 获取当前节点合同信息
            global_config.set_value("合同信息",eval(params)["doc"]["contractbase"])

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test13_approval_process_01(self):
        ''' [第一岗] 第一岗登陆，获取第一岗审批人nodeid '''
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
            username = pinyinTransform(makeJsonData("#审批一岗"))
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
                    "limit": 500,
                    "orderby": {},
                    "page": 1,
                    "processtype": [
                        "CONT",
                        "CONT_CHANGE",
                        "CONT_CONTENTCHANGE",
                        "COGN",
                        "COGN_CHANGE",
                        "COGN_CONTENTCHANGE",
                        "SERVICE_CONT",
                        "SERVICE_CONT_CHANGE",
                        "CONT_CANCEL",
                        "COGNCONT_CANCEL"
                    ],
                    "querys": {
                        "groupno": makeProcessData("#合同号")
                    }
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取第一岗登陆token
            global_config.set_value("TOKEN",token)

            loadProcessValue("#nodeId","rst","data","items",0,"node","_id")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test14_approval_process_01(self):
        ''' [第一岗] 第一岗登陆，获取合同信息及审批信息 '''
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
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取完整合同信息，用于审批接口
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))

            # 获取下一岗登陆审批人信息
            loadProcessValue("#下岗审批人信息/candidates","rst","candidates")
            loadProcessValue("#审批二岗","rst","candidates",0,"receivers",0,"name")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test15_approval_process_01(self):
        ''' [第一岗] 第一岗登陆，进行审批 '''
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
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
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


    def test16_approval_process_02(self):
        ''' [第二岗] 第二岗登陆，获取第二岗审批人nodeid '''
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
            username = pinyinTransform(makeJsonData("#审批二岗"))
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
                    "limit": 500,
                    "orderby": {},
                    "page": 1,
                    "processtype": [
                        "CONT",
                        "CONT_CHANGE",
                        "CONT_CONTENTCHANGE",
                        "COGN",
                        "COGN_CHANGE",
                        "COGN_CONTENTCHANGE",
                        "SERVICE_CONT",
                        "SERVICE_CONT_CHANGE",
                        "CONT_CANCEL",
                        "COGNCONT_CANCEL"
                    ],
                    "querys": {
                        "groupno": makeProcessData("#合同号")
                    }
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取第一岗登陆token
            global_config.set_value("TOKEN",token)

            loadProcessValue("#nodeId","rst","data","items",0,"node","_id")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test17_approval_process_02(self):
        ''' [第二岗] 第二岗登陆，获取合同信息及审批信息 '''
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
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取完整合同信息，用于审批接口
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))

            # 获取下一岗登陆审批人信息
            loadProcessValue("#下岗审批人信息/candidates","rst","candidates")
            loadProcessValue("#审批三岗","rst","candidates",0,"receivers",0,"name")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test18_approval_process_02(self):
        ''' [第二岗] 第二岗登陆，进行审批 '''
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
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
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


    def test19_approval_process_03(self):
        ''' [第三岗] 第三岗登陆，获取第三岗审批人nodeid '''
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
            username = pinyinTransform(makeJsonData("#审批三岗"))
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
                    "limit": 500,
                    "orderby": {},
                    "page": 1,
                    "processtype": [
                        "CONT",
                        "CONT_CHANGE",
                        "CONT_CONTENTCHANGE",
                        "COGN",
                        "COGN_CHANGE",
                        "COGN_CONTENTCHANGE",
                        "SERVICE_CONT",
                        "SERVICE_CONT_CHANGE",
                        "CONT_CANCEL",
                        "COGNCONT_CANCEL"
                    ],
                    "querys": {
                        "groupno": makeProcessData("#合同号")
                    }
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取第一岗登陆token
            global_config.set_value("TOKEN",token)

            loadProcessValue("#nodeId","rst","data","items",0,"node","_id")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test20_approval_process_03(self):
        ''' [第三岗] 第三岗登陆，获取合同信息及审批信息 '''
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
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取完整合同信息，用于审批接口
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))

            # 获取下一岗登陆审批人信息
            loadProcessValue("#下岗审批人信息/candidates","rst","candidates")
            loadProcessValue("#审批四岗","rst","candidates",0,"receivers",0,"name")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test21_approval_process_03(self):
        ''' [第三岗] 第三岗登陆，进行审批 '''
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
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }

            if makeProcessData("#审批三岗") == makeJsonData("商务人员"):
                # 当前岗审批人为商务人员（倒数第二岗）
                updateDict = \
                    {
                        "receivabletype":makeJsonData("业务应收创建方式"),
                        "effectdate":notChooseNull(makeJsonData("签订日期"),
                                                   getCurrentDate("-"))
                    }

                params["candidates"] = eval(makeProcessData("#下岗审批人信息/candidates"))
                params["doc"]["contractbase"].update(updateDict)

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


    def test22_approval_process_04(self):
        ''' [第四岗] 第四岗登陆，获取第四岗审批人nodeid '''
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
            username = pinyinTransform(makeJsonData("#审批四岗"))
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
                    "limit": 500,
                    "orderby": {},
                    "page": 1,
                    "processtype": [
                        "CONT",
                        "CONT_CHANGE",
                        "CONT_CONTENTCHANGE",
                        "COGN",
                        "COGN_CHANGE",
                        "COGN_CONTENTCHANGE",
                        "SERVICE_CONT",
                        "SERVICE_CONT_CHANGE",
                        "CONT_CANCEL",
                        "COGNCONT_CANCEL"
                    ],
                    "querys": {
                        "groupno": makeProcessData("#合同号")
                    }
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取第一岗登陆token
            global_config.set_value("TOKEN",token)

            loadProcessValue("#nodeId","rst","data","items",0,"node","_id")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test23_approval_process_04(self):
        ''' [第四岗] 第四岗登陆，获取合同信息及审批信息 '''
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
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)
            nextUser = combineJson(self.result, "rst", "candidates")

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取完整合同信息，用于审批接口
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))
            # 获取下一岗登陆审批人信息
            loadProcessValue("#下岗审批人信息/candidates","rst","candidates")

            if nextUser != "[]":
                loadProcessValue("#审批五岗","rst","candidates",0,"receivers",0,"name")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test24_approval_process_04(self):
        ''' [第四岗] 第四岗登陆，进行审批 '''
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
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }

            if makeProcessData("#审批四岗") == makeJsonData("商务人员"):
                # 当前岗审批人为商务人员（倒数第二岗）
                updateDict = \
                    {
                        "receivabletype":makeJsonData("业务应收创建方式"),
                        "effectdate":notChooseNull(makeJsonData("签订日期"),
                                                   getCurrentDate("-"))
                    }

                params["candidates"] = eval(makeProcessData("#下岗审批人信息/candidates"))
                params["doc"]["contractbase"].update(updateDict)

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
            if makeJsonData("#审批五岗"):
                writeTextResult()
            else:
                loadProcessValue("#流程开关",realValue="四岗审批")
                writeTextResult(myRow=self.myRow)


    def test25_approval_process_05(self):
        ''' [第五岗] 第五岗登陆，获取第五岗审批人nodeid '''
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
            username = pinyinTransform(makeJsonData("#审批五岗"))
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
                    "limit": 500,
                    "orderby": {},
                    "page": 1,
                    "processtype": [
                        "CONT",
                        "CONT_CHANGE",
                        "CONT_CONTENTCHANGE",
                        "COGN",
                        "COGN_CHANGE",
                        "COGN_CONTENTCHANGE",
                        "SERVICE_CONT",
                        "SERVICE_CONT_CHANGE",
                        "CONT_CANCEL",
                        "COGNCONT_CANCEL"
                    ],
                    "querys": {
                        "groupno": makeProcessData("#合同号")
                    }
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取第一岗登陆token
            global_config.set_value("TOKEN",token)

            loadProcessValue("#nodeId","rst","data","items",0,"node","_id")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test26_approval_process_05(self):
        ''' [第五岗] 第五岗登陆，获取合同信息及审批信息 '''
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
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)
            nextUser = combineJson(self.result, "rst", "candidates")

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取完整合同信息，用于审批接口
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))
            # 获取下一岗登陆审批人信息
            loadProcessValue("#下岗审批人信息/candidates","rst","candidates")

            if nextUser != "[]":
                loadProcessValue("#审批六岗","rst","candidates",0,"receivers",0,"name")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test27_approval_process_05(self):
        ''' [第五岗] 第五岗登陆，进行审批 '''
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
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }

            if makeProcessData("#审批五岗") == makeJsonData("商务人员"):
                # 当前岗审批人为商务人员（倒数第二岗）
                updateDict = \
                    {
                        "receivabletype":makeJsonData("业务应收创建方式"),
                        "effectdate":notChooseNull(makeJsonData("签订日期"),
                                                   getCurrentDate("-"))
                    }

                params["candidates"] = eval(makeProcessData("#下岗审批人信息/candidates"))
                params["doc"]["contractbase"].update(updateDict)

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
            if makeJsonData("#审批六岗"):
                writeTextResult()
            else:
                loadProcessValue("#流程开关",realValue="五岗审批")
                writeTextResult(myRow=self.myRow)


    def test28_approval_process_06(self):
        ''' [第六岗] 第六岗登陆，获取第六岗审批人nodeid '''
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
            username = pinyinTransform(makeJsonData("#审批六岗"))
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
                    "limit": 500,
                    "orderby": {},
                    "page": 1,
                    "processtype": [
                        "CONT",
                        "CONT_CHANGE",
                        "CONT_CONTENTCHANGE",
                        "COGN",
                        "COGN_CHANGE",
                        "COGN_CONTENTCHANGE",
                        "SERVICE_CONT",
                        "SERVICE_CONT_CHANGE",
                        "CONT_CANCEL",
                        "COGNCONT_CANCEL"
                    ],
                    "querys": {
                        "groupno": makeProcessData("#合同号")
                    }
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取第一岗登陆token
            global_config.set_value("TOKEN",token)

            loadProcessValue("#nodeId","rst","data","items",0,"node","_id")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test29_approval_process_06(self):
        ''' [第六岗] 第六岗登陆，获取合同信息及审批信息 '''
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
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)
            nextUser = combineJson(self.result, "rst", "candidates")

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取完整合同信息，用于审批接口
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))
            # 获取下一岗登陆审批人信息
            loadProcessValue("#下岗审批人信息/candidates","rst","candidates")

            if nextUser != "[]":
                loadProcessValue("#审批七岗","rst","candidates",0,"receivers",0,"name")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test30_approval_process_06(self):
        ''' [第六岗] 第六岗登陆，进行审批 '''
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
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }
            if makeProcessData("#审批六岗") == makeJsonData("商务人员"):
                # 当前岗审批人为商务人员（倒数第二岗）
                updateDict = \
                    {
                        "receivabletype":makeJsonData("业务应收创建方式"),
                        "effectdate":notChooseNull(makeJsonData("签订日期"),
                                                   getCurrentDate("-"))
                    }

                params["candidates"] = eval(makeProcessData("#下岗审批人信息/candidates"))
                params["doc"]["contractbase"].update(updateDict)


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
            if makeJsonData("#审批七岗"):
                writeTextResult()
            else:
                loadProcessValue("#流程开关",realValue="六岗审批")
                writeTextResult(myRow=self.myRow)


    def test31_approval_process_07(self):
        ''' [第七岗] 第七岗登陆，获取第七岗审批人nodeid '''
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
            username = pinyinTransform(makeJsonData("#审批七岗"))
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
                    "limit": 500,
                    "orderby": {},
                    "page": 1,
                    "processtype": [
                        "CONT",
                        "CONT_CHANGE",
                        "CONT_CONTENTCHANGE",
                        "COGN",
                        "COGN_CHANGE",
                        "COGN_CONTENTCHANGE",
                        "SERVICE_CONT",
                        "SERVICE_CONT_CHANGE",
                        "CONT_CANCEL",
                        "COGNCONT_CANCEL"
                    ],
                    "querys": {
                        "groupno": makeProcessData("#合同号")
                    }
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取第一岗登陆token
            global_config.set_value("TOKEN",token)

            loadProcessValue("#nodeId","rst","data","items",0,"node","_id")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test32_approval_process_07(self):
        ''' [第七岗] 第七岗登陆，获取合同信息及审批信息 '''
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
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)
            nextUser = combineJson(self.result, "rst", "candidates")

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取完整合同信息，用于审批接口
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))
            # 获取下一岗登陆审批人信息
            loadProcessValue("#下岗审批人信息/candidates","rst","candidates")

            if nextUser != "[]":
                loadProcessValue("#审批八岗","rst","candidates",0,"receivers",0,"name")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test33_approval_process_07(self):
        ''' [第七岗] 第七岗登陆，进行审批 '''
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
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }

            if makeProcessData("#审批七岗") == makeJsonData("商务人员"):
                # 当前岗审批人为商务人员（倒数第二岗）
                updateDict = \
                    {
                        "receivabletype":makeJsonData("业务应收创建方式"),
                        "effectdate":notChooseNull(makeJsonData("签订日期"),
                                                   getCurrentDate("-"))
                    }

                params["candidates"] = eval(makeProcessData("#下岗审批人信息/candidates"))
                params["doc"]["contractbase"].update(updateDict)


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
            if makeJsonData("#审批八岗"):
                writeTextResult()
            else:
                loadProcessValue("#流程开关",realValue="七岗审批")
                writeTextResult(myRow=self.myRow)


    def test34_approval_process_08(self):
        ''' [第八岗] 第八岗登陆，获取第八岗审批人nodeid '''
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
            username = pinyinTransform(makeJsonData("#审批八岗"))
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
                    "limit": 500,
                    "orderby": {},
                    "page": 1,
                    "processtype": [
                        "CONT",
                        "CONT_CHANGE",
                        "CONT_CONTENTCHANGE",
                        "COGN",
                        "COGN_CHANGE",
                        "COGN_CONTENTCHANGE",
                        "SERVICE_CONT",
                        "SERVICE_CONT_CHANGE",
                        "CONT_CANCEL",
                        "COGNCONT_CANCEL"
                    ],
                    "querys": {
                        "groupno": makeProcessData("#合同号")
                    }
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取第一岗登陆token
            global_config.set_value("TOKEN",token)

            loadProcessValue("#nodeId","rst","data","items",0,"node","_id")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test35_approval_process_08(self):
        ''' [第八岗] 第八岗登陆，获取合同信息及审批信息 '''
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
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)
            nextUser = combineJson(self.result, "rst", "candidates")

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取完整合同信息，用于审批接口
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))
            # 获取下一岗登陆审批人信息
            loadProcessValue("#下岗审批人信息/candidates","rst","candidates")

            if nextUser != "[]":
                loadProcessValue("#审批九岗","rst","candidates",0,"receivers",0,"name")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test36_approval_process_08(self):
        ''' [第八岗] 第八岗登陆，进行审批 '''
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
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }

            if makeProcessData("#审批八岗") == makeJsonData("商务人员"):
                # 当前岗审批人为商务人员（倒数第二岗）
                updateDict = \
                    {
                        "receivabletype":makeJsonData("业务应收创建方式"),
                        "effectdate":notChooseNull(makeJsonData("签订日期"),
                                                   getCurrentDate("-"))
                    }

                params["candidates"] = eval(makeProcessData("#下岗审批人信息/candidates"))
                params["doc"]["contractbase"].update(updateDict)


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
            if makeJsonData("#审批九岗"):
                writeTextResult()
            else:
                loadProcessValue("#流程开关",realValue="八岗审批")
                writeTextResult(myRow=self.myRow)


    def test37_approval_process_09(self):
        ''' [第九岗] 第九岗登陆，获取第九岗审批人nodeid '''
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
            username = pinyinTransform(makeJsonData("#审批九岗"))
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
                    "limit": 500,
                    "orderby": {},
                    "page": 1,
                    "processtype": [
                        "CONT",
                        "CONT_CHANGE",
                        "CONT_CONTENTCHANGE",
                        "COGN",
                        "COGN_CHANGE",
                        "COGN_CONTENTCHANGE",
                        "SERVICE_CONT",
                        "SERVICE_CONT_CHANGE",
                        "CONT_CANCEL",
                        "COGNCONT_CANCEL"
                    ],
                    "querys": {
                        "groupno": makeProcessData("#合同号")
                    }
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取第一岗登陆token
            global_config.set_value("TOKEN",token)

            loadProcessValue("#nodeId","rst","data","items",0,"node","_id")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test38_approval_process_09(self):
        ''' [第九岗] 第九岗登陆，获取合同信息及审批信息 '''
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
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }
            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)
            nextUser = combineJson(self.result, "rst", "candidates")

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取完整合同信息，用于审批接口
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))
            # 获取下一岗登陆审批人信息
            loadProcessValue("#下岗审批人信息/candidates","rst","candidates")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test39_approval_process_09(self):
        ''' [第九岗] 第九岗登陆，进行审批 '''
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
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }

            if makeProcessData("#审批九岗") == makeJsonData("商务人员"):
                # 当前岗审批人为商务人员（倒数第二岗）
                updateDict = \
                    {
                        "receivabletype":makeJsonData("业务应收创建方式"),
                        "effectdate":notChooseNull(makeJsonData("签订日期"),
                                                   getCurrentDate("-"))
                    }

                params["candidates"] = eval(makeProcessData("#下岗审批人信息/candidates"))
                params["doc"]["contractbase"].update(updateDict)


            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
            loadProcessValue("#流程开关",realValue="九岗审批")
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            self.terminateProcess = True
            writeTextResult(myRow=self.myRow)


if __name__ == '__main__':
    test_data.init_data() # 初始化接口测试数据
    unittest.main()
