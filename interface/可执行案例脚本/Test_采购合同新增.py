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
    ''' 采购合同审批流 '''

    def setUp(self):
        self.dict = global_config._global_dict                              # 全局变量字典
        self.moduleName = "采购合同审批流"                                   # 当前流程名称
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


    def test01_get_supplier(self):
        ''' 经办岗登陆，查询供应商信息（供应商编号） '''

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

            token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            params = \
                {
                    "BUKRS": "1000",
                    "ZSKDW": makeJsonData("供应商名称"),
                    "limit": "50",
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

            # 获取“供应商编号”
            global_config.set_value("供应商编号",
                                    combineJson(self.result,"rst","data","items",0,"LIFNR"))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test02_get_materiel_info(self):
        ''' 经办岗登陆，通过“内部物料编码”获取所有物料信息 '''
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

            taxRateList = \
                {
                    "0%": "J0",
                    "10%": "J6",
                    "11%": "J2",
                    "16%": "J5",
                    "17%": "J1",
                    "3%": "J4",
                    "6%": "J3"
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
                            "code": makeJsonData("内部物料编码-%s" %varNum),
                            "description": "",
                            "limit": 500,
                            "model": "",
                            "product_name": "",
                            "moduleType": "CGHT",
                            "vendeeId": "1000",
                        }
                else:
                    break

                params = json.dumps(params).replace("'","\"")

                self.result = myRequest(base_url, headers=header, data=params)

                # **************************** 校验部分 ****************************
                checkTheMessage("code",varNameInExcel="code")
                checkTheMessage("msg",varNameInExcel="msg")

                # **************************** 返回值部分 ****************************
                materiel_info = eval(combineJson(self.result,"rst","data","items",0))
                materiel_info.update(
                    {
                        "count": eval(makeJsonData("数量-%s" %varNum)),
                        "sum": eval(makeJsonData("小计-%s" %varNum))
                    }
                )

                if materiel_info.get("tax_rate") is None:
                    print("物料 %s 的默认税率为空！" %makeJsonData("内部物料编码-%s" %varNum))
                    if makeJsonData("税率-%s" %varNum) == "":
                        print("未在数据表中控制物料 %s 的税率！" %makeJsonData("内部物料编码-%s" %varNum))
                        loadProcessValue("#流程开关",realValue="物料信息错误")
                        global_config.set_value("TESTRESULT","失败")
                        self.testResult = "失败"
                        writeTextResult(myRow=self.myRow)
                        # return
                    else:
                        materiel_info.update(
                            {
                                "tax_rate": taxRateList[makeJsonData("税率-%s" %varNum)]
                            }
                        )

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


    def test03_get_sales_info(self):
        ''' 经办岗登陆，查询销售员信息 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        base_url = self.url + getInterfaceData("调用接口")

        if self.terminateProcess != "" \
                or makeJsonData("销售员") == "":
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
                    "name": makeJsonData("销售员"),
                    "page": 1
                }

            params = json.dumps(params).replace("'","\"")

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            sales_info = \
                {
                    "org": {
                        "_id": combineJson(self.result,"rst","data","items",0,"orgid"),
                        "orgname": combineJson(self.result,"rst","data","items",0,"orgname")
                    },
                    "sales_group": combineJson(self.result,"rst","data","items",0,"belongaddr"),
                    "user": {
                        "_id": combineJson(self.result,"rst","data","items",0,"_id"),
                        "login": combineJson(self.result,"rst","data","items",0,"login"),
                        "name": makeJsonData("销售员")
                    }
                }
            global_config.set_value("销售员信息",sales_info)

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
        ''' 经办岗登陆，查询报文对应值 '''
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

            self.result = myRequest(base_url)

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


    def test05_make_new_process(self):
        ''' 经办岗登陆，在对应环境新建采购合同审批流，获取nodeId、processId '''
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
            # **************************** 交易数据部分 ****************************
            product_line = getDataTransFormed("rst", "data", "product_line", strName="产品线")
            purchase_division = getDataTransFormed("rst", "data", "purchase_division", strName="事业部")
            purchase_group = getDataTransFormed("rst", "data", "purchase_group", strName="采购组")
            purchase_org = getDataTransFormed("rst", "data", "purchase_org", strName="采购组织")
            purchase_type = getDataTransFormed("rst", "data", "purchase_type", strName="采购合同类型")

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + self.dict["TOKEN"],
                "Content-Type": "application/json"
            }

            payments = []
            for i in range(1,30):
                if i < 10:
                    varNum = "0%s" %i
                else:
                    varNum = str(i)

                if makeJsonData("付款类型-%s" %varNum) != "" \
                        and makeJsonData("付款类型-%s" %varNum) is not None:
                    contentAppended = \
                        {
                            "cate": makeJsonData("付款类型-%s" %varNum),
                            "cond": makeJsonData("付款条件-%s" %varNum),
                            "days": eval(makeJsonData("付款天数-%s" %varNum)),
                            "mode": makeJsonData("付款方式-%s" %varNum),
                            "percent": eval(makeJsonData("付款比例-%s" %varNum))
                        }
                    payments.append(contentAppended)
                else:
                    break

            purchase_vendee = \
                {
                    "中建材信息技术股份有限公司": "1000",
                    "中建材信云智联科技有限公司": "1100",
                    "中建材信息技术（香港）有限公司": "9100"
                }

            params = \
                {
                    "doc": {
                        "addition": {
                            "attachment": {},
                            "contacts": {}
                        },
                        "currency_type": "CNY",
                        "items": self.dict["MATEREIL_DICT"],
                        "money": {
                            "amount": eval(makeJsonData("采购总金额")),
                            "device": eval(makeJsonData("设备总金额")),
                            "service": eval(makeJsonData("服务总金额"))
                        },
                        "pay": {},
                        "payments": payments,
                        "product_line": product_line,
                        "project_name": makeJsonData("项目名称"),
                        "purchaser": {
                            "division": purchase_division,
                            "employee": makeJsonData("采购商务"),
                            "group": purchase_group,
                            "org": purchase_org,
                            "vendee": purchase_vendee[makeJsonData("所属公司")]
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
                        "sales_info":self.dict.get("销售员信息"),
                        "supplier": {
                            "id": self.dict["供应商编号"],
                            "name": makeJsonData("供应商名称"),
                            "order": "ZDH" + randomNum(9),
                            "org": [
                                "1000",
                                "2000"
                            ]
                        },
                        "transport_type": makeJsonData("运输方式",whetherToInitialize="是"),
                        "type": purchase_type
                    }
                }
            # print(params)
            params = json.dumps(params).replace("'","\"")

            if makeJsonData("运输方式",whetherToInitialize="是") == "中断":
                self.testResult = "跳过"
                return
            else:
                self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            loadProcessValue("#nodeId","rst","nodeId")
            loadProcessValue("#processId","rst","processId")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test06_approval_process_01(self):
        '''[第一岗] 经办岗登陆，获取审批人及合同信息'''
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
                    "nodeId": makeJsonData("#nodeId"),
                    "processId": makeJsonData("#processId")
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            loadProcessValue("#审批一岗","rst","candidates",0,"receivers",0,"login")
            loadProcessValue("#合同号","rst","doc","model","code")

            # 获取“合同信息”
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test07_approval_process_01(self):
        '''[第一岗] 第一岗登陆，用当前审批人登陆并获取下一岗审批人nodeId'''
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
            username = makeJsonData("#审批一岗")
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
                    "processtype": [
                        "CGHT",
                        "CGHT_CHANGE",
                        "CGHT_CANCEL"
                    ],
                    "querys": {
                        "fullcode": makeJsonData("#合同号")
                    }
                }

            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取“token”
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


    def test08_approval_process_01(self):
        '''[第一岗] 第一岗登陆，通过当前岗nodeId及审批流processId获取下一岗审批信息'''
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
                    "nodeId": makeJsonData("#nodeId"),
                    "processId": makeJsonData("#processId")
                }

            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            loadProcessValue("#下岗审批人信息/candidates","rst","candidates")
            loadProcessValue("#审批二岗","rst","candidates",0,"receivers",0,"login")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test09_approval_process_01(self):
        '''[第一岗] 第一岗登陆，用当前审批人登陆并审批'''
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
                    "candidates": eval(makeProcessData("#下岗审批人信息/candidates")),
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }

            # myJson = json.loads(params)
            # params = json.dumps(myJson, ensure_ascii=False)
            params = json.dumps(params)
            # params = json.dumps(params, indent=2, ensure_ascii=False)
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


    def test10_approval_process_02(self):
        '''[第二岗] 第一岗登陆，获取审批人及更新后的合同信息doc'''
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
                    "nodeId": makeJsonData("#nodeId"),
                    "processId": makeJsonData("#processId")
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取“合同信息”
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test11_approval_process_02(self):
        '''[第二岗] 第二岗登陆，用当前审批人登陆并获取下一岗审批人nodeId'''
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
            username = makeJsonData("#审批二岗",whetherToInitialize="是")
            password = makeJsonData("登陆密码")

            if username == "中断":
                self.testResult = "跳过"
                return
            else:
                token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            params = \
                {
                    "processtype": [
                        "CGHT",
                        "CGHT_CHANGE",
                        "CGHT_CANCEL"
                    ],
                    "querys": {
                        "fullcode": makeJsonData("#合同号")
                    }
                }

            params = json.dumps(params)

            if makeJsonData("#合同号",whetherToInitialize="是") == "中断":
                self.testResult = "跳过"
                return
            else:
                self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取“token”
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


    def test12_approval_process_02(self):
        '''[第二岗] 第二岗登陆，通过当前岗nodeId及审批流processId获取下一岗审批信息'''
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
                    "nodeId": makeJsonData("#nodeId",whetherToInitialize="终止"),
                    "processId": makeJsonData("#processId")
                }

            params = json.dumps(params)

            if makeJsonData("#nodeId",whetherToInitialize="是") == "中断":
                self.testResult = "跳过"
                return
            else:
                self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            loadProcessValue("#下岗审批人信息/candidates","rst","candidates")
            loadProcessValue("#审批三岗","rst","candidates",0,"receivers",0,"login")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test13_approval_process_02(self):
        '''[第二岗] 第二岗登陆，用当前审批人登陆并审批'''
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
                    "candidates": eval(makeProcessData("#下岗审批人信息/candidates")),
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }

            params = json.dumps(params)
            print(params)

            if makeJsonData("#合同号",whetherToInitialize="是") == "中断":
                self.testResult = "跳过"
                return
            else:
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


    def test14_approval_process_03(self):
        '''[第二岗] 第一岗登陆，获取审批人及更新后的合同信息doc'''
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
                    "nodeId": makeJsonData("#nodeId"),
                    "processId": makeJsonData("#processId")
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取“合同信息”
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test15_approval_process_03(self):
        '''[第三岗] 第三岗登陆，用当前审批人登陆并获取下一岗审批人nodeId'''
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
            username = makeJsonData("#审批三岗",whetherToInitialize="是")
            password = makeJsonData("登陆密码")

            if username == "中断":
                self.testResult = "跳过"
                return
            else:
                token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            params = \
                {
                    "processtype": [
                        "CGHT",
                        "CGHT_CHANGE",
                        "CGHT_CANCEL"
                    ],
                    "querys": {
                        "fullcode": makeJsonData("#合同号")
                    }
                }

            params = json.dumps(params)

            if makeJsonData("#合同号",whetherToInitialize="是") == "中断":
                self.testResult = "跳过"
                return
            else:
                self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取“token”
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


    def test16_approval_process_03(self):
        '''[第三岗] 第三岗登陆，通过当前岗nodeId及审批流processId获取下一岗审批信息'''
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
                    "nodeId": makeJsonData("#nodeId",whetherToInitialize="终止"),
                    "processId": makeJsonData("#processId")
                }

            params = json.dumps(params)

            if makeJsonData("#nodeId",whetherToInitialize="是") == "中断":
                self.testResult = "跳过"
                return
            else:
                self.result = myRequest(base_url, headers=header, data=params)
                nextUser = combineJson(self.result, "rst", "candidates")

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            loadProcessValue("#下岗审批人信息/candidates","rst","candidates")

            if nextUser != "[]":
                loadProcessValue("#审批四岗","rst","candidates",0,"receivers",0,"login")

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test17_approval_process_03(self):
        '''[第三岗] 第三岗登陆，用当前审批人登陆并审批'''
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
                    "candidates": eval(makeProcessData("#下岗审批人信息/candidates")),
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }

            params = json.dumps(params)
            # print(params)

            if makeJsonData("#合同号",whetherToInitialize="是") == "中断":
                self.testResult = "跳过"
                return
            else:
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
            if makeJsonData("#审批四岗"):
                writeTextResult()
            else:
                loadProcessValue("#流程开关",realValue="三岗审批")
                checkTheMessage("rst","msg",varNameInExcel="rst.msg")
                checkTheMessage("rst","status",varNameInExcel="rst.status")
                writeTextResult(myRow=self.myRow)


    def test18_approval_process_04(self):
        '''[第四岗] 第三岗登陆，获取审批人及更新后的合同信息doc'''
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
                    "nodeId": makeJsonData("#nodeId"),
                    "processId": makeJsonData("#processId")
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取“合同信息”
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test19_approval_process_04(self):
        '''[第四岗] 第四岗登陆，用当前审批人登陆并获取下一岗审批人nodeId'''
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
            username = makeJsonData("#审批四岗",whetherToInitialize="是")
            password = makeJsonData("登陆密码")

            if username == "中断":
                self.testResult = "跳过"
                return
            else:
                token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            params = \
                {
                    "processtype": [
                        "CGHT",
                        "CGHT_CHANGE",
                        "CGHT_CANCEL"
                    ],
                    "querys": {
                        "fullcode": makeJsonData("#合同号")
                    }
                }

            params = json.dumps(params)

            if makeJsonData("#合同号",whetherToInitialize="是") == "中断":
                self.testResult = "跳过"
                return
            else:
                self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取“token”
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


    def test20_approval_process_04(self):
        '''[第四岗] 第四岗登陆，通过当前岗nodeId及审批流processId获取下一岗审批信息'''
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
                    "nodeId": makeJsonData("#nodeId",whetherToInitialize="终止"),
                    "processId": makeJsonData("#processId")
                }

            params = json.dumps(params)

            if makeJsonData("#nodeId",whetherToInitialize="是") == "中断":
                self.testResult = "跳过"
                return
            else:
                self.result = myRequest(base_url, headers=header, data=params)
                nextUser = combineJson(self.result, "rst", "candidates")

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            loadProcessValue("#下岗审批人信息/candidates","rst","candidates")

            if nextUser != "[]":
                loadProcessValue("#审批五岗","rst","candidates",0,"receivers",0,"login")


            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test21_approval_process_04(self):
        '''[第四岗] 第四岗登陆，用当前审批人登陆并审批'''
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
                    "candidates": eval(makeProcessData("#下岗审批人信息/candidates")),
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }

            params = json.dumps(params)
            print(params)

            if makeJsonData("#合同号",whetherToInitialize="是") == "中断":
                self.testResult = "跳过"
                return
            else:
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
                checkTheMessage("rst","msg",varNameInExcel="rst.msg")
                checkTheMessage("rst","status",varNameInExcel="rst.status")
                writeTextResult(myRow=self.myRow)


    def test22_approval_process_05(self):
        '''[第五岗] 第四岗登陆，获取审批人及更新后的合同信息doc'''
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
                    "nodeId": makeJsonData("#nodeId"),
                    "processId": makeJsonData("#processId")
                }
            params = json.dumps(params)

            self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
            # 获取“合同信息”
            global_config.set_value("合同信息",
                                    eval(combineJson(self.result,"rst","doc","model")))

            # **************************** 常规部分 ****************************
            self.testResult = "成功"
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test23_approval_process_05(self):
        '''[第五岗] 第五岗登陆，用当前审批人登陆并获取下一岗审批人nodeId'''
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
            username = makeJsonData("#审批五岗",whetherToInitialize="是")
            password = makeJsonData("登陆密码")

            if username == "中断":
                self.testResult = "跳过"
                return
            else:
                token = get_token(login_url,username,password)

            # **************************** 交易部分 ****************************
            header = \
                {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }

            params = \
                {
                    "processtype": [
                        "CGHT",
                        "CGHT_CHANGE",
                        "CGHT_CANCEL"
                    ],
                    "querys": {
                        "fullcode": makeJsonData("#合同号")
                    }
                }

            params = json.dumps(params)

            if makeJsonData("#合同号",whetherToInitialize="是") == "中断":
                self.testResult = "跳过"
                return
            else:
                self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")

            # **************************** 返回值部分 ****************************
            # 获取“token”
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


    def test24_approval_process_05(self):
        '''[第五岗] 第五岗登陆，通过当前岗nodeId及审批流processId获取下一岗审批信息'''
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
                    "nodeId": makeJsonData("#nodeId",whetherToInitialize="终止"),
                    "processId": makeJsonData("#processId")
                }

            params = json.dumps(params)

            if makeJsonData("#nodeId",whetherToInitialize="是") == "中断":
                self.testResult = "跳过"
                return
            else:
                self.result = myRequest(base_url, headers=header, data=params)

            # **************************** 校验部分 ****************************
            checkTheMessage("code",varNameInExcel="code")
            checkTheMessage("msg",varNameInExcel="msg")

            # **************************** 返回值部分 ****************************
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


    def test25_approval_process_05(self):
        '''[第五岗] 第五岗登陆，用当前审批人登陆并审批'''
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
                    "candidates": eval(makeProcessData("#下岗审批人信息/candidates")),
                    "doc": self.dict["合同信息"],
                    "nodeId": makeProcessData("#nodeId"),
                    "processId": makeProcessData("#processId")
                }

            params = json.dumps(params)
            print(params)

            if makeJsonData("#合同号",whetherToInitialize="是") == "中断":
                self.testResult = "跳过"
                return
            else:
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
            loadProcessValue("#流程开关",realValue="五岗审批")
            checkTheMessage("rst","msg",varNameInExcel="rst.msg")
            checkTheMessage("rst","status",varNameInExcel="rst.status")
            writeTextResult(myRow=self.myRow)


if __name__ == '__main__':
    test_data.init_data() # 初始化接口测试数据
    unittest.main()
