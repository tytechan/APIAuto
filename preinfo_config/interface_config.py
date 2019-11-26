import requests
from excel_config.excel_data import *
from .global_config import *
from . import *

def whetherToIgnore():      # 弃用
    '''根据“数据表”sheet对应列判断该案例是否跳过
    :return: True（跳过）/False（正常执行）
    '''
    myRow = pickProcessDataRow()
    dataSheetName = get_value("DATASHEETNAME")
    DataSheet = excelObj.getSheetByName(dataSheetName)
    myValue = excelObj.getCellOfValue(DataSheet,rowNo=myRow,colsNo=Data_caseNotNullNum)
    if str(myValue) == "0":
        isToIgnore = True
    else:
        # 此分支包含myValue为“0”及为“”的情况
        isToIgnore = False
    return isToIgnore


def myRequest(base_url, headers=None, data=None):
    '''发送get/post请求
    :return: 响应报文
    '''
    set_value("RESULT", None)

    s = requests.session()
    if headers is None and data is None:
        post_ret = s.get(base_url)
    else:
        post_ret = s.post(base_url, headers=headers, data=data)

    set_value("RESULT",post_ret.json())
    return post_ret.json()


def requestWithCookie(base_url, headers=None, data=None, cookies=None):
    '''发送get/post请求
    :return: 响应报文
    '''
    set_value("RESULT", None)

    post_ret = requests.post(base_url, headers=headers, data=data, cookies=cookies)

    set_value("RESULT",post_ret.json())
    return post_ret.json()