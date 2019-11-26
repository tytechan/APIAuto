#encoding = utf - 8

import os
from excel_config.ParseExcel import ParseExcel
# from preinfo_config.global_config import *

parentDirPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dataFilePath = parentDirPath + u"\\excel_config\\数据管理.xlsx"

# 创建解析excel对象
excelObj = ParseExcel()
# 将excel数据文件加载至内存
excelObj.loadWorkBook(dataFilePath)
# dataSheetName = get_value("DATASHEETNAME")
IntroSheet = excelObj.getSheetByName("案例汇总")
# DataSheet = excelObj.getSheetByName(dataSheetName)