def _init():  # 初始化
    global _global_dict
    _global_dict = {}

# @setVar
def set_value(key, value):
    """ 定义一个全局变量 """
    _global_dict[key] = value

def get_value(key, defValue=None):
    """ 获得一个全局变量,不存在则返回默认值 """
    try:
        # if key != "TESTROW" and key != "TESTLOOPTIME":
        #     print("🔼 全局变量 %s 的值为： %s" %(key,_global_dict[key]))
        return _global_dict[key]
    except KeyError:
        return defValue

# def setVar(func):
#     def recall(key,value):
#         func(key,value)
#         key = value
#     return recall