from multiprocessing import  Pool
import asyncio
import time
import requests
import json
import copy


def multi_api(url, header, data, method="post"):
    global results
    try:
        s = requests.session()
        data = json.dumps(data).replace("'", "\"")
        if method == "post":
            results = s.post(url, headers=header, data=data)
        if method == "get":
            results = s.get(url)
        return results.json()
    except requests.ConnectionError:
        return results


async def fristwork(url, header, data, error):
    # global sucNum,errNum
    await asyncio.sleep(1)
    r = multi_api(url, header, data)
    if r.get("code") != 200:
        error.append(r.get("msg"))
    print("fristwork take" ,str(time.time()))
    return "Done"

async def secondwork(url, header, data, error):
    a = await  fristwork(url, header, data, error)
    print (a)

def task(url, header, data, error):
    coroutine = secondwork(url, header, data, error)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(coroutine)
    # print("task {}".format(num))

async def run_more(num, poolNUm, initialBox, url, header, data, error):
    print("start run_more")
    pool = Pool(processes = poolNUm)
    myData = copy.deepcopy(data)


    for i in range(num):
        for j in range(sumPerTime):
            box = "CZDH" + str(int(initialBox.replace("CZDH","")) + j)
            myData["box_codes"].append(box)

            if j + 1 == sumPerTime:
                # del initialBox
                initialBox = "CZDH" + str(int(box.replace("CZDH","")) + 1)

        pool.apply_async(task,args=(url, header, myData, error))
        print("第 ",i+1," 次并发开始...")
        myData = copy.deepcopy(data)
        # time.sleep(loop_sleep)

    pool.close()
    pool.join()

def main(num, poolNUm, initialBox, url, header, data):
    # global errNum,sucNum
    # errNum = 0
    # sucNum = 0
    error = []
    # 开始时间
    start = time.time()
    coroutine = run_more(num, poolNUm, initialBox, url, header, data, error)
    tasks = [
        asyncio.ensure_future(coroutine),
    ]
    loop2 = asyncio.get_event_loop()
    loop2.run_until_complete(asyncio.wait(tasks))
    # 结束时间
    end = time.time()

    print("========================================================================")
    print("接口性能测试开始时间：", time.asctime(time.localtime(start)))
    print("接口性能测试结束时间：", time.asctime(time.localtime(end)))
    print("接口地址：", url)
    print("接口类型：", "post")
    print("总进程数：", coNum)
    print("最大进程数：", poolNUm)
    print("每个进程循环次数：", 1)
    print("每次请求含箱数：", sumPerTime)
    print("每次请求时间间隔：", 0)
    print("总请求数：", coNum * 1)
    print("总耗时（秒）：", end - start)
    print("每次请求耗时（秒）：", (end - start) / (coNum * 1))
    # print("成功数：", sucNum)
    # print("失败数：", errNum)
    # print("错误请求数：", len(error))
    # print("错误信息：", error)
    print("每秒承载请求数（TPS)：", (coNum * 1) / (end - start))
    # print("平均响应时间（毫秒）：", CreateMultiprocesses.multi_response_avg())
    print("========================================================================")


if __name__ == '__main__':
    Environment_Select = \
        {
            "200": "http://cdwpdev01.chinacloudapp.cn:9001",
            "500": "http://kintergration.chinacloudapp.cn:9002",
            "400": "http://cdwpdev01.chinacloudapp.cn:9400",
            "450": "http://cdwpdev01.chinacloudapp.cn:9003",
            "510": "http://kintergration01.chinacloudapp.cn:9510",
            "530": "http://kintergration02.chinacloudapp.cn:9530",
            "600": "http://kintergration.chinacloudapp.cn:9003",
            "700": "http://kdevelop.chinacloudapp.cn:9003"
        }

    # 基础数据
    env = "400"
    initialBox = "CZDH1901210001"                 # 起始箱号
    tray = "1000000001"                         # 仓库
    sumPerTime = 1                             # 每次请求箱数
    coNum = 5                                  # 并发数
    poolNUm = 3                                # 进程池最大进程数


    # 登陆
    login_url = Environment_Select[env] + "/login"
    login_header = {"Content-Type": "application/json"}
    login_data = {"login": "yanyongfeng", "pwd": "123sap"}

    login_result = multi_api(login_url,login_header,login_data)
    token = login_result["rst"]["data"]["token"]

    # 交易
    # errNum = 0
    # sucNum = 0

    url = Environment_Select[env] + "/wms-core/uptray"
    header = \
        {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json"
        }
    data = \
        {
            "box_codes": [],
            "tray": tray
        }

    # for i in range(sumPerTime):
    #     box = "CZDH" + str(int(initialBox.replace("CZDH","")) + i)
    #     data["box_codes"].append(box)

    # print(data)

    main(coNum, poolNUm, initialBox, url, header, data)