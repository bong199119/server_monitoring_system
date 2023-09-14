import os
import time
import sys
import psutil
import pandas as pd
from datetime import datetime
import numpy as np

import paramiko
import threading
import mariadb

now = datetime.now()

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from config import config

class_config = config.config()

conn = mariadb.connect(
        user=class_config.mariadb['user'],
        password=class_config.mariadb['password'],
        host=class_config.mariadb['host'],
        port=class_config.mariadb['port'],
        database=class_config.mariadb['database']
    )

# gpu_name = '3090 RTX'
# cur = conn.cursor()
list_server_name = [200, 201, 202, 203, 204, 205, 206]
list_ip = ['192.168.2.200', '192.168.2.201', '192.168.2.202', '192.168.2.203', '192.168.2.204', '192.168.2.205', '192.168.2.206']
list_rack = [2,2,2,1,1,1,3]

# for i in range(len(list_ip)):
#     query = "INSERT INTO server_info (server_name, IP, rack_number) VALUES (%s, %s, %s)"
#     values = (list_server_name[i], list_ip[i], list_rack[i])
#     cur.execute(query, values)
#     conn.commit()



dict_gpu_info = {
    '200':['001','002','003'],
    '201':['101',],
    '202':['201','202','203'],
    '203':['301','302'],
    '204':['401','402','403','404'],
    '205':[],
    '206':['111','112','113'],

}
# gpu_name = '3090 RTX'

# cur = conn.cursor()
# for server in dict_gpu_info:
#     for idx, gpuid in enumerate(dict_gpu_info[server]):
#         query = "INSERT INTO gpu_info (uuid, gpu_idx, server_name, gpu_name) VALUES (%s, %s, %s, %s)"
#         values = (gpuid, idx, server, gpu_name)
#         cur.execute(query, values)
#         conn.commit()

# for server in dict_gpu_info:
#     for idx, gpuid in enumerate(dict_gpu_info[server]):
#         query = "INSERT INTO gpu_info (uuid, gpu_idx, server_name, gpu_name, use_info, usage, temp) VALUES (%s, %s, %s, %s, %s, %s, %s)"
#         values = (gpuid, idx, server, gpu_name,'','','')
#         cur.execute(query, values)
#         conn.commit()





# date = now.strftime('%Y-%m-%d %H:%M:%S')
# server_name = ''
# gpu_id = ''
# process = ''
# gpu_temp = ''
# ram_usage = ''
# cpu_usage = ''
# cpu_temp = ''
# gpu_usage = ''

# query = "INSERT INTO log (time, server_name, gpu_id, process, gpu_temp, ram_usage, cpu_usage, cpu_temp, gpu_usage) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
# values = (date, server_name, gpu_id, process, gpu_temp, ram_usage, cpu_usage, cpu_temp, gpu_usage)
# cur.execute(query, values)
# conn.commit()


# # class_config = config.config()

# # conn = mariadb.connect(
# #         user=class_config.mariadb['user'],
# #         password=class_config.mariadb['password'],
# #         host=class_config.mariadb['host'],
# #         port=class_config.mariadb['port'],
# #         database=class_config.mariadb['database']
# #     )
use_info = 'True'
list_temp = ['12','76','88','101','26']
list_usage = ['11%','23%','62%','66%','13%','77%']

while True:
    now = datetime.now()
    cur = conn.cursor()
    date = now.strftime('%Y-%m-%d %H:%M:%S')
    server_name = ''
    gpu_id = ''
    process = ''
    gpu_temp = ''
    ram_usage = ''
    cpu_usage = ''
    cpu_temp = ''
    gpu_usage = ''

    # query = "INSERT INTO log (time, server_name, gpu_id, process, gpu_temp, ram_usage, cpu_usage, cpu_temp, gpu_usage) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    # values = (date, server_name, gpu_id, process, gpu_temp, ram_usage, cpu_usage, cpu_temp, gpu_usage)
    # cur.execute(query, values)
    # conn.commit()

    # query = "UPDATE log SET time = %s, server_name = %s, gpu_id = %s, process = %s, gpu_temp = %s, ram_usage = %s, cpu_usage = %s, cpu_temp = %s, gpu_usage= %s"
    # values = (date, server_name, gpu_id, process, gpu_temp, ram_usage, cpu_usage, cpu_temp, gpu_usage)
    # cur.execute(query, values)
    # conn.commit()
    for server in list_server_name:
        query = "UPDATE server_info SET cpu_usage = %s,  cpu_temp = %s, ram_usage = %s, use_info = %s WHERE server_name = %s"
        values = (list_usage[np.random.randint(len(list_usage))], list_temp[np.random.randint(len(list_temp))],list_usage[np.random.randint(len(list_usage))], use_info, server)
        cur.execute(query, values)
        conn.commit()

    for server in dict_gpu_info:
        for idx, gpuid in enumerate(dict_gpu_info[server]):
            query = "UPDATE gpu_info SET use_info = %s,  gpu_usage = %s, temp = %s WHERE server_name = %s AND gpu_idx = %s"
            values = (use_info, list_usage[np.random.randint(len(list_usage))], list_temp[np.random.randint(len(list_temp))], server, idx)
            cur.execute(query, values)
            conn.commit()

    # cur = conn.cursor()
    # sql_log = "SELECT * FROM log"
    # df_gpu_info = pd.read_sql(sql_log, conn)

    # print(date)
    # print(df_gpu_info['time'][0])
    time.sleep(5)
