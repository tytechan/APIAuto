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
    ''' 报销单审批流_凭证科目 '''

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


    def test01_get_KJPZH(self):
        ''' 获取报销单详情，进行财务标记，获取会计凭证号 '''
        import datetime

        if self.terminateProcess != "":
            self.testResult = "跳过"
            return

        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = getInterfaceData("调用接口").split("|")

        # 与库表中数据主键重复情况均需考虑是否用初始化
        if getInterfaceData("是否数据库初始化") == "是":
            DB().delete(tableName,deleteData)

        md = [
            {
                "单据状态": "success",
                "报销单号": "BXA201903003120",
                "报销金额": 10,
                "票据类型": "资料费",
                "费用种类": "间接运营费用",
                "费用种类详情": "管理费用"
            },
            {
                "单据状态": "success",
                "报销单号": "BXA201903001008",
                "报销金额": 15,
                "票据类型": "生育保险",
                "费用种类": "福利支出",
                "费用种类详情": "保险"
            }
        ]

        try:
            for i in range(len(md)):
                # ***** 业务标记 *****
                # **************************** 登陆部分 ****************************
                username = makeJsonData("经办登录名")
                password = makeJsonData("登陆密码")

                token = get_token(login_url,username,password, errInfo=False)
                time.sleep(1)

                # **************************** 查询部分 ****************************
                header = \
                    {
                    "Authorization": "Bearer " + token,
                    "Content-Type": "application/json"
                }

                params = {
                    "code": md[i]["报销单号"]
                }
                params = json.dumps(params).replace("'","\"")

                self.result = myRequest(self.url + base_url[0],
                                        headers=header, data=params)

                # 校验
                if self.result.get("code") == 200:
                    print("📈 第 ",i + 1," 条报销单（", md[i]["报销单号"], "）“单据查询”响应成功")

                    if self.result["rst"]["data"]["finance"].get("certcode"):
                        print("📈 第 ",i + 1," 条报销单（", md[i]["报销单号"],
                              "）“单据查询”已做过财务标记")
                        md[i]["会计凭证号"] = self.result["rst"]["data"]["finance"]["certcode"]
                        md[i]["标记状态"] = "成功"
                        continue
                    else:
                        doc = self.result["rst"]["data"]
                else:
                    print("📈 第 ",i + 1," 条报销单（", md[i]["报销单号"], "）“单据查询”响应失败，结果为：\n",self.result, "\n")
                    md[i]["标记状态"] = "失败"
                    continue

                # **************************** 财务标记部分 ****************************
                params = {
                    "certdate": str(datetime.date.today()),
                    "docs": [
                        doc
                    ]
                }

                params = json.dumps(params).replace("'","\"")

                self.result = myRequest(self.url + base_url[1],
                                        headers=header, data=params)

                # 校验
                if self.result.get("code") == 200 \
                        and len(self.result["rst"]["fail"]) == 0:
                    print("📈 第 ",i + 1," 条报销单（", md[i]["报销单号"], "）“财务标记”响应成功")
                    md[i]["标记状态"] = "成功"
                    md[i]["会计凭证号"] = self.result["rst"]["data"]["finance"]["certcode"]
                else:
                    print("📈 第 ",i + 1," 条报销单（", md[i]["报销单号"],
                          "）“财务标记”响应失败，结果为：\n",self.result, "\n")
                    md[i]["标记状态"] = "失败"
                    md[i]["会计凭证号"] = "未生成"
                    continue

            print("📈 最终标记结果为：\n", md)
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
            loadProcessValue("#单据数据",realValue=str(md))
            writeTextResult(myRow=self.myRow)


if __name__ == '__main__':
    test_data.init_data()       # 初始化接口测试数据
    unittest.main()
