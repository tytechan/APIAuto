# coding=utf8
import pymysql.cursors
import os
import configparser as cparser


# ======== Reading db_config.ini setting ===========
base_dir = str(os.path.dirname(os.path.dirname(__file__)))
base_dir = base_dir.replace('\\', '/')
file_path = base_dir + "/db_config.ini"

cf = cparser.ConfigParser()

cf.read(file_path)
host = cf.get("mysqlconf", "host")
port = cf.get("mysqlconf", "port")
db   = cf.get("mysqlconf", "db_name")
user = cf.get("mysqlconf", "user")
password = cf.get("mysqlconf", "password")


# ======== MySql base operating ===================
class DB:

    def __init__(self):
        try:
            # Connect to the database
            self.connection = pymysql.connect(host=host,
                                              port=int(port),
                                              user=user,
                                              password=password,
                                              db=db,
                                              charset='utf8mb4',
                                              cursorclass=pymysql.cursors.DictCursor)
        except pymysql.err.OperationalError as e:
            print("👻Mysql Error %d: %s" % (e.args[0], e.args[1]))

    # 清空整张表数据
    def clear(self, table_name):
        # real_sql = "truncate table " + table_name + ";"
        real_sql = "delete from " + table_name + ";"
        with self.connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
            cursor.execute(real_sql)
        self.connection.commit()

    # 删除具体表中具体数据
    def delete(self,table_name,data_dic):
        real_sql = "delete from " + table_name + " where "
        keyNum = 0
        for key in data_dic:
            mid_sql = key + "='" + data_dic[key] + "'"
            # print(keyNum,mid_sql)
            if keyNum == 0:
                real_sql = real_sql + mid_sql
            else:
                real_sql = real_sql + " and " + mid_sql

            keyNum += 1

        print("👨‍💻初始化（delete）该案例对应表值:",real_sql)
        with self.connection.cursor() as cursor:
            cursor.execute(real_sql)
        self.connection.commit()

    # 修改具体表中某一条数据键值
    def update(self,table_name,data_dic1,data_dic2):
        real_sql = "update " + table_name + " set "
        keyNum = 0
        for key in data_dic1:
            mid_sql = key + "='" + data_dic1[key] + "'"
            # print(keyNum,mid_sql)
            if keyNum == 0:
                real_sql = real_sql + mid_sql
            else:
                real_sql = real_sql + " and " + mid_sql
            keyNum += 1

        keyNum = 0
        for key in data_dic2:
            mid_sql = key + "='" + data_dic2[key] + "'"
            # print(keyNum,mid_sql)
            if keyNum == 0:
                real_sql = real_sql + " where " + mid_sql
            else:
                real_sql = real_sql + " and " + mid_sql
            keyNum += 1

        print("🐱‍🚀初始化（update）该案例对应表值:",real_sql)
        with self.connection.cursor() as cursor:
            cursor.execute(real_sql)
        self.connection.commit()


    # 向表中插入数据
    def insert(self, table_name, table_data):
        for key in table_data:
            table_data[key] = "'"+str(table_data[key])+"'"
        key   = ','.join(table_data.keys())
        value = ','.join(table_data.values())
        real_sql = "INSERT INTO " + table_name + " (" + key + ") VALUES (" + value + ")"
        print("🐱‍👤插入数据sql为：",real_sql," **********")

        with self.connection.cursor() as cursor:
            cursor.execute(real_sql)

        self.connection.commit()

    # close database
    def close(self):
        self.connection.close()

    # init data
    def init_data(self, datas):
        # for table, data in datas.items():
        #     # 插入数据前先清空数据库表,TODO
        #     self.clear(table)
        #     for d in data:
        #         self.insert(table, d)

        self.close()


if __name__ == '__main__':

    db = DB()
    table_name = "sign_event"
    data = {'id':1,'name':'红米','`limit`':2000,'status':1,'address':'北京会展中心','start_time':'2016-08-20 00:25:42'}
    table_name2 = "sign_guest"
    data2 = {'realname':'alen','phone':12312341234,'email':'alen@mail.com','sign':0,'event_id':1}

    db.clear(table_name)
    db.insert(table_name, data)
    db.close()
