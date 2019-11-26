#encoding = utf - 8
# 用于存放预处理数据方法

def randomNum(len,*arg):        # 生成指定长度的随机数（长度>=6）
    try:
        import random,datetime
        list_num = ['0','1','2','3','4','5','6','7','8','9']
        result = []
        len = int(len)
        mydate = datetime.datetime.now().strftime('%Y%m%d')
        result.append(mydate[2:])
        for i in range(0,len-6):
            result.append(random.choice(list_num))
        return "".join(result)
    except Exception as e:
        raise e

def getCurrentDate(MyStr):       # 获取指定连接符的当前日期
    try:
        import datetime
        MyDate = datetime.datetime.now().strftime("%Y"+MyStr+"%m"+MyStr+"%d")
        return MyDate
    except Exception as e:
        raise e
