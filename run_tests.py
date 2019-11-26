#encoding = utf - 8

import time, sys, os
sys.path.append('./interface')
sys.path.append('./db_fixture')
from HTMLTestRunner import HTMLTestRunner
from unittest import defaultTestLoader
from db_fixture import test_data
from db_mongo_fixture import Create_Connection
from datetime import datetime

# from excel_config.ParseExcel import *
from excel_config.excel_data import *
from preinfo_config import global_config

class TestRunner(object):

    def __init__(self):
        self.replayKey = 1          # 控制在一次循环多条流程时，判断此条流程是否跳过
        self.mainRow = None         # 数据总入口
        self.dataSheetName = None   # 本次执行流程对应的“数据表”sheet名
        self.environment = None     # 本次执行流程对应环境

    def dataRowInitialization(self):
        '''获取excel“数据表”sheet中，执行的第一个案例可用的数据所在行'''
        if self.replayKey == 1:
            self.mainRow = pickProcessDataRow()
        else:
            self.mainRow = pickProcessDataRow(firstRow=self.mainRow)
        return self.mainRow

    def setGlobalVar(self,varName,varValue):
        '''设置全工程全局变量键值
        :param varName:全局变量键名
        '''
        global_config.set_value(varName,varValue)

    def getDataSheet(self):
        dataFileDirPath = os.path.dirname(os.path.abspath(__file__)) + u"\\interface"
        files = os.listdir(dataFileDirPath)
        for fileName in files:
            if fileName.find("销售合同新增") > 0:
                self.dataSheetName = "数据表-销售合同新增"
                break
            elif fileName.find("采购合同新增") > 0:
                self.dataSheetName = "数据表-采购合同新增"
                break
            elif fileName.find("上架") > 0 or fileName.find("下架") > 0:
                if fileName.find("并发上架") > 0:
                    self.dataSheetName = "数据表-并发上架"
                    break
                else:
                    self.dataSheetName = "数据表-上下架"
                    break
            elif fileName.find("库存调整") > 0:
                self.dataSheetName = "数据表-库存调整"
                break
            elif fileName.find("报销单") > 0:
                if fileName.find("报销单新增") > 0:
                    self.dataSheetName = "数据表-报销单新增"
                    break
                elif fileName.find("报销单标记") > 0:
                    self.dataSheetName = "数据表-报销单标记"
                    break
            elif fileName.find("审批流处理") > 0:
                self.dataSheetName = "数据表-审批流处理"
                break

        if self.dataSheetName:
            self.setGlobalVar("DATASHEETNAME",self.dataSheetName)
            if global_config.get_value("TESTLOOPTIME") == 1:
                print("◾ 遍历数据表：%s" %self.dataSheetName)
        else:
            print("⚡ 请检查 案例文件/excel文件数据表sheet/框架run_tests.py 同步情况！")
            os._exit(0)

    def init_DB(self,environment):       # TODO：初始化数据库表数据（mysql/mongoDB：暂无初始化需求）
        # mysql
        #test_data.init_data()

        # mongoDB
        # Create_Connection.

        pass


    def runTestProcess(self):
        '''单个流程的执行全过程'''
        # 获取数据表sheet及当前执行流程调用的数据所在行
        self.getDataSheet()
        self.setGlobalVar("TESTROW",self.dataRowInitialization())
        # 初始化流程开关
        loadProcessValue("#流程开关",realValue="")

        # 指定测试用例为当前文件夹下的 interface 目录
        test_dir = './interface'
        testsuit = defaultTestLoader.discover(test_dir, pattern='Test_*.py')
        # testsuit = defaultTestLoader.discover(test_dir, pattern='*_test.py')

        # 初始化数据库数据
        self.environment = makeJsonData("测试环境",whetherToInitialize="是")
        self.setGlobalVar("ENVIRONMENT",self.environment)
        self.init_DB(self.environment)

        timeStr = datetime.now()
        now = timeStr.strftime("%Y-%m-%d %H_%M_%S.%f")
        # now = time.strftime("%Y-%m-%d %H_%M_%S")
        filename = './report/' + now + '_result.html'
        fp = open(filename, 'wb')
        runner = HTMLTestRunner(stream=fp,
                                title='"%s"自动化测试报告' %(self.dataSheetName.replace("数据表-","")),
                                description='运行环境：%s' %(self.environment))
        runner.run(testsuit)
        fp.close()

        self.replayKey += 1


if __name__ == "__main__":

    TestRunner = TestRunner()
    loopTime = 1                     # loopTime:待执行流程数

    for i in range(1,loopTime + 1):
        global_config._init()
        TestRunner.setGlobalVar("TESTLOOPTIME",i)
        TestRunner.runTestProcess()