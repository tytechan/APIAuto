import json
import asyncio, multiprocessing
from excel_config.excel_data import *
from excel_config.ParseExcel import ParseExcel
# 用于通过token保存登陆信息
from preinfo_config.set_token import *
#引入功能函数
from preinfo_config.interface_config import *
from preinfo_config import global_config


# async def run_more(login_url,base_url,token):
#     print("start run_more")
#     pool = multiprocessing.Pool(processes = 4)
#     multiAccount = eval(makeJsonData("并发流程数"))
#     for i in range(multiAccount):
#         pool.apply_async(task,args=(login_url,base_url,i,token))
#         # print(i)
#     pool.close()
#     pool.join()
#
#
# async def task(login_url,base_url,time,token):
#     multiRow = global_config.get_value("TESTROW") + time
#     coroutine = box_uptray(login_url,base_url,multiRow,token)
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(coroutine)


# def box_uptray(login_url,base_url,multiRow):
# async def box_uptray(login_url,base_url,multiRow,token):
def box_uptray(login_url,base_url,multiRow,token):
    '''箱子上托盘主流程
    :param loopTime: 并发数量
    :param login_url: 登陆接口地址
    :param base_url: 上架接口地址
    :return:
    '''
    # **************************** 登陆部分 ****************************
    # username = makeProcessData("经办登录名",multiRow=multiRow)
    # password = makeProcessData("登陆密码",multiRow=multiRow)
    #
    # token = get_token(login_url,username,password)

    # **************************** 交易部分 ****************************
    header = \
        {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    }

    params = \
        {
            "box_codes": [],
            "tray": makeProcessData("托盘",multiRow=multiRow)
        }

    # 用于迭代添加多个箱号数据
    for i in range(1, 100):
        if i < 10:
            varNum = "0%s" %i
        else:
            varNum = str(i)

        varName = "箱号-%s" %varNum
        varValue = makeProcessData(varName,multiRow=multiRow)

        if varValue != "" and varValue is not None \
                and varValue != "":
            params["box_codes"].append(varValue)
        else:
            break


    params = json.dumps(params).replace("'","\"")
    result = myRequest(base_url, headers=header, data=params)

    # **************************** 校验部分 ****************************
    initRow = global_config.get_value("TESTROW")
    global_config.set_value("TESTROW",multiRow)

    # if result.get("code") == 200 and result.get("msg") == "OK":
    #     loadProcessValue("#流程开关",realValue="上架成功")
    # else:
    #     # 交易失败,在该数据行“#流程开关”中写入报错信息
    #     if result:
    #         loadProcessValue("#流程开关",realValue="报错："+result.get("msg"))
    #     else:
    #         loadProcessValue("#流程开关",realValue="报错：系统未响应！")
    # initRow = global_config.get_value("TESTROW")
    # global_config.set_value("TESTROW",multiRow)

    if result.get("code") != 200 or result.get("msg") != "OK":
        # 交易失败,在该数据行“#流程开关”中写入报错信息
        if result:
            loadProcessValue("#流程开关",realValue="报错："+result.get("msg"))
        else:
            loadProcessValue("#流程开关",realValue="报错：系统未响应！")
    else:
        loadProcessValue("#流程开关",realValue="上架成功")

    global_config.set_value("TESTROW",initRow)
    time.sleep(1)