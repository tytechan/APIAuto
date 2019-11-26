from pymongo import MongoClient
from bson.objectid import ObjectId
import configparser as cparser


class MongodbConn(object):

    def __init__(self):

        host = "kintergration.chinacloudapp.cn"
        port = 27017
        username = "sap_root"
        password = "1fc588e8eed48bcbfbf432ed10a0a9cd"
        datebase = "intergration1publishbase"

        client = MongoClient(host,port)
        self.db = client[datebase]
        self.db.authenticate(str(username), str(password))


    def getCollection(self,col):
        '''根据表名获取具体表
        :param col: 表名
        :return: “collection”类型对象
        '''
        # col = self.db.collection_names()[3]
        # print(col)
        collection = self.db.get_collection(col)
        # print(collection)
        return collection


    def getDataFromCollection(self,collectionName,myquery):
        '''根据书库表
        :param collectionName:表名
        :param myquery:查询明细
        :return:
        '''
        # collection = self.db["inbound_orders"]
        # print(collection.find_one())

        # myquery = \
        #     {'boxes.code': 'CF798560087'}
            # {"creatorname": {'$exists': True}}
            # {"_id" : ObjectId("586a264715cb9982e10bb850")}

        collection = self.getCollection(collectionName)
        results = collection.find(myquery)
        # results = collection.find_one(myquery)

        i = 1
        for result in results:
            print("**********结果%d为：********** \n %s" %(i,result))
            print(type(result),"\n")
            i += 1



if __name__ == '__main__':
    mo = MongodbConn()
    # mo.getCollection("inbound_orders")
    mo.getDataFromCollection("wms.materials",
                             {'name': '制成板-OptiX155/622H-SS42POIA--48伏EMC电源输入板'})