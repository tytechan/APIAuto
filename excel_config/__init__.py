#encoding = utf - 8

import os
from excel_config.ParseExcel import *
# from preinfo_config.global_config import *

parentDirPath = os.path.dirname(os.path.abspath(__file__))
dataFilePath = parentDirPath + u"\\数据管理.xlsx"

# 创建解析excel对象
excelObj = ParseExcel()
# 将excel数据文件加载至内存
excelObj.loadWorkBook(dataFilePath)

IntroSheet = excelObj.getSheetByName("案例汇总")
# dataSheetName = get_value("DATASHEETNAME")
# DataSheet = excelObj.getSheetByName(dataSheetName)

# 汇总页
Intro_caseRowNum = "C"        # 案例列号

Intro_testResult = 6
Intro_currentTimeResult = 7

# 数据表
Data_dataIsExecute = "C"        # 是否使用

Data_dataToBeUsed = 3
Data_testResult = 4
Data_currentTimeResult = 5
Data_reportFileName = 6

# 流程页
Step_caseRowNum = "B"