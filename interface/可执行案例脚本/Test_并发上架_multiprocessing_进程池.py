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
# 引入功能函数
from preinfo_config.preactions import *
from preinfo_config.interface_config import *
from preinfo_config import global_config
from interface import Environment_Select
from multi_processing.multi_processing import CreateMultiprocesses as CM

# 引入并发功能模块
import threading,multiprocessing
from interface.并发执行脚本.Multi_并发上架 import *

class CaigouContractsTest(unittest.TestCase):
    ''' PDA扫码上架（并发） '''

    def setUp(self):
        self.dict = global_config._global_dict                              # 全局变量字典
        self.moduleName = "PDA扫码上架"                                      # 当前流程名称
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
            # loadProcessValue("#流程开关",realValue="流程失败")
            writeTextResult(myRow=self.myRow)
        elif self.testResult == "跳过":
            print("🎈案例",self.caseName,"在本流程中跳过...")
            global_config.set_value("TESTRESULT",self.testResult)
            writeTextResult()


    def test01_box_uptray(self):
        ''' 登陆500环境PDA后，扫码进行箱子上托盘 '''
        # **************************** 案例公共信息初始化 ****************************
        self.caseName = (lambda: sys._getframe(1).f_code.co_name)()
        global_config.set_value("CASENAME",self.caseName)
        login_url = self.url + getInterfaceData("登陆接口")
        base_url = self.url + getInterfaceData("调用接口")

        # 与库表中数据主键重复情况均需考虑是否用初始化
        if getInterfaceData("是否数据库初始化") == "是":
            DB().delete(tableName,deleteData)

        try:
            # 确定并发流程数
            multiAccount = eval(makeJsonData("并发流程数"))
            token = get_token(login_url,makeJsonData("经办登录名"),makeJsonData("登陆密码"))
            errAccount = 0
            start = time.time()
            maxNum = 10
            # multis = []

            p = multiprocessing.Pool(processes = maxNum)

            for i in range(multiAccount):
                multiRow = global_config.get_value("TESTROW") + i
                myProcess = p.apply_async(func=box_uptray,args=(login_url,base_url,multiRow,token,))
                myProcess.daemon = True
                # multis.append(myProcess)

            p.close()
            p.join()

            end = time.time()

            for i in range(multiAccount):
                multiRow = global_config.get_value("TESTROW") + i
                if makeProcessData("#流程开关",multiRow=multiRow).find("报错") != -1:
                    errAccount += 1
                print("第 %d 次进程中累计报错数为： %d" %(i+1,errAccount))

            print("========================================================================")
            print("接口性能测试开始时间：", time.asctime(time.localtime(start)))
            print("接口性能测试结束时间：", time.asctime(time.localtime(end)))
            print("接口地址：", base_url)
            print("接口类型：", "post")
            print("最大进程数：", maxNum)
            print("每个进程循环次数：", 1)
            print("每次请求时间间隔：", 0)
            print("总请求数：", multiAccount * 1)
            # print("错误请求数：", len(error))
            print("总耗时（秒）：", end - start)
            print("每次请求耗时（秒）：", (end - start) / (multiAccount * 1))
            print("每秒承载请求数（TPS)：", (multiAccount * 1) / (end - start))
            print("平均响应时间（毫秒）：", CM.multi_response_avg())
            print("========================================================================")

            # **************************** 常规部分 ****************************
            assert errAccount == 0, \
                "😭 箱子入托盘中，\n共需处理 '%s' 个流程， 有 '%d' 个失败！" \
                %(multiAccount,errAccount)
            print("😭 箱子入托盘中，\n共需处理 '%s' 个流程， 有 '%d' 个失败！" \
                %(multiAccount,errAccount))
        except AssertionError as e:
            self.testResult = "失败"
            raise AssertionError(e)
        except Exception as e:
            self.testResult = "失败"
            raise e
        finally:
            if errAccount == 0:
                self.testResult = "成功"

            # 在excel中写值脚本不可写入try/except，否则html报告中无法区别体现“失败”和“异常”
            global_config.set_value("TESTRESULT",self.testResult)
            self.terminateProcess = True
            writeTextResult(myRow=self.myRow)


if __name__ == '__main__':
    test_data.init_data() # 初始化接口测试数据
    unittest.main()
