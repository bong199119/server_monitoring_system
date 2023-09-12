import os
import time
import sys
import psutil
import pandas as pd
from datetime import datetime
import traceback

import paramiko
import threading
import mariadb

pid = os.getpid()
lock = threading.Lock()

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from config import config

class_config = config.config()

pool = mariadb.ConnectionPool(
        user=class_config.mariadb['user'],
        password=class_config.mariadb['password'],
        host=class_config.mariadb['host'],
        port=class_config.mariadb['port'],
        database=class_config.mariadb['database'],
        pool_name="web-app",
        pool_size=13,
        )

conn = pool.get_connection()
cur = conn.cursor()

#### pid check ####
'''
already exists pid  => update pid
not exists pid => insert pid
'''
sql_check_pid = "SELECT * FROM check_pid"
df_check_pid = pd.read_sql(sql_check_pid, conn)

if len(df_check_pid) == 0:
    query = "INSERT INTO check_pid (pid) VALUES (%s)"
    values = (pid,)
    cur.execute(query, values)
    conn.commit()
else: 
    query = "UPDATE check_pid SET pid = %s"
    values = (pid,)
    cur.execute(query, values)
    conn.commit()

conn.close()

#### initialize db ####
'''
initialize list
1. server_info table
2. gpu_info table
3. status table
'''

sql_gpu_info = "SELECT * FROM gpu_info"
sql_server_info = "SELECT * FROM server_info"
# Use the read_sql function to load the data into a DataFrame
df_gpu_info = pd.read_sql(sql_gpu_info, conn)
df_server_info = pd.read_sql(sql_server_info, conn)

list_server = class_config.list_server
dict_server_gpu = {}
for gpu_idx in df_gpu_info['gpu_idx']:
    gpu_idx = int(gpu_idx)
    if df_gpu_info['server_name'][gpu_idx] not in dict_server_gpu:
        dict_server_gpu[df_gpu_info['server_name'][gpu_idx]] = []
        dict_server_gpu[df_gpu_info['server_name'][gpu_idx]].append(df_gpu_info['uuid'][gpu_idx])
    else:
        dict_server_gpu[df_gpu_info['server_name'][gpu_idx]].append(df_gpu_info['uuid'][gpu_idx])

DEFAULT_ATTRIBUTES = (
        'index',
        'uuid',
        'name',
        'timestamp',
        'memory.total',
        'memory.free',
        'memory.used',
        'utilization.gpu',
        'utilization.memory',
        'temperature.gpu',
        'temperature.memory'
    )

def get_gpu_info(cli, nvidia_smi_path='nvidia-smi', keys=DEFAULT_ATTRIBUTES, no_units=True):
    nu_opt = '' if not no_units else ',nounits'
    cmd = '%s --query-gpu=%s --format=csv,noheader%s' % (nvidia_smi_path, ','.join(keys), nu_opt)
    # output = subprocess.check_output(cmd, shell=True)
    stdin, output, stderr = cli.exec_command(cmd)
    lines = output.readlines()
    lines = [ line.strip() for line in lines if line.strip() != '' ]

    return [ { k: v for k, v in zip(keys, line.split(', ')) } for line in lines ]

def _check_usage_of_cpu_and_memory(cli):
        
        pid = os.getpid()
        py  = psutil.Process(pid)
        
        # cpu_usage   = os.popen("ps aux | grep " + str(pid) + " | grep -v grep | awk '{print $3}'").read()
        # cpu_usage   = cpu_usage.replace("\n","")
        cmd = 'top -b -n1'
                
        stdin, stdout, stderr = cli.exec_command(cmd)
        output = stdout.read().decode('utf-8')
        for line in output.split('\n'):
            if 'Cpu(s)' in line:
                cpu_usage = line.split(',')[0].split(':')[1].strip()
                # print(f'CPU usage: {cpu_usage}')

        # cpu_usage   = cpu_usage.replace("\n","")
        memory_usage  = round(py.memory_info()[0] /2.**30, 2)
        
        # print("cpu usage\t\t:", cpu_usage, "%")
        # print("memory usage\t\t:", memory_usage, "%")
        
        dict_server_cpu_ram = {
            "cpu" : f"cpu usage : {cpu_usage}%",
            "ram" : f"ram usage : {memory_usage}%"
        }

        return dict_server_cpu_ram  

def check_server(server_ip, pool, count_log, dict_for_cli, dict_for_thread):
    now = datetime.now()
    server = server_ip.split('.')[-1]

    dict_server = {}
    gpu_running = False
    dict_server['server_connect'] = {}
    dict_server['gpu_detail'] = {}
    dict_server['gpu_abstarct'] = {}
    dict_server['server_cpu_ram'] = {}
    
    # try:
    #     conn = pool.get_connection()
    #     cur = conn.cursor()
    # except Exception as e:
    #     print(server, e)
    #     dict_for_thread[server]['thread'] ='off'
    #     return
    try:
        conn = mariadb.connect(
            user=class_config.mariadb['user'],
            password=class_config.mariadb['password'],
            host=class_config.mariadb['host'],
            port=class_config.mariadb['port'],
            database=class_config.mariadb['database'],
            )
    except Exception as e:
        print(server, e)
        dict_for_thread[server]['thread'] ='off'
        time.sleep(1)
        return
    
    try:
        cur = conn.cursor() 
    except Exception as e:
        print(server, e)
        # cur.close()
        conn.close()
        dict_for_thread[server]['thread'] ='off'
        time.sleep(1)
        return
    
    print('----------------------------------------------------------')

    try:
        cli = paramiko.SSHClient()
        cli.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        # cli = dict_for_cli[server]
    except Exception as e:
        print(server, e)
        conn.close()
        # cur.close()
        dict_for_thread[server]['thread'] ='off'
        time.sleep(1)
        return
    try:
        print(server)
        cli.connect(server_ip, username="bseo", password="105wkd4dlaak")
        dict_server['server_connect'][server] = 'connect'
        print(f'{server} connect')
    except Exception as e:
        dict_server['server_connect'][server] = 'disconnected'
        print(f'{server} discoonected')
        cli.close() 
        conn.close()
        # cur.close()
        dict_for_thread[server]['thread'] ='off'
        time.sleep(1)
        return
    try:
        stdin, stdout, stderr = cli.exec_command('nvidia-smi')
        lines = stdout.readlines()
        print(server, lines[0])
    except Exception as e:
        print(server, e)
        cli.close() 
        conn.close()
        # cur.close()
        dict_for_thread[server]['thread'] ='off'
        time.sleep(1)
        return
    
    try:
        list_str = lines
        index_for_uppergpuid = 0

        for idx, i in enumerate(list_str):
            if '=============================================================================' in i:
                index_for_uppergpuid = idx
        list_gpu_line = list_str[index_for_uppergpuid+1:-1]
        dict_gpu = {}
        dict_gpu['gpu id'] = {}
    except Exception as e:
        print(server, e)
        cli.close() 
        conn.close()
        # cur.close()
        dict_for_thread[server]['thread'] ='off'
        time.sleep(1)
        return

    if 'No' in list_gpu_line[0] and 'running' in list_gpu_line[0] and 'processes' in list_gpu_line[0] and 'found' in list_gpu_line[0]:
        gpu_running = False
    else:
        gpu_running = True

    if gpu_running:
        try:
            for idx, gpu_line in enumerate(list_gpu_line):
                list_gpu_line_ele = gpu_line.split(' ')
                while '' in list_gpu_line_ele:
                    list_gpu_line_ele.remove('')
                
                list_gpu_line_ele = list_gpu_line_ele[1:-1]        
                # print(list_gpu_line_ele)    

                if  list_gpu_line_ele[0] not in dict_gpu['gpu id']:
                    dict_gpu['gpu id'][list_gpu_line_ele[0]] = []
                    dict_gpu['gpu id'][list_gpu_line_ele[0]].append(
                                            {'GPU ID' : list_gpu_line_ele[0],
                                            'GIID' : list_gpu_line_ele[1],
                                            'CIID' : list_gpu_line_ele[2],
                                            'PID' : list_gpu_line_ele[3],
                                            'Type' : list_gpu_line_ele[4],
                                            'Process name' : list_gpu_line_ele[5],
                                            'GPU Memory Usage' : list_gpu_line_ele[6]})
                else:
                    dict_gpu['gpu id'][list_gpu_line_ele[0]].append(
                                            {'GPU ID' : list_gpu_line_ele[0],
                                            'GIID' : list_gpu_line_ele[1],
                                            'CIID' : list_gpu_line_ele[2],
                                            'PID' : list_gpu_line_ele[3],
                                            'Type' : list_gpu_line_ele[4],
                                            'Process name' : list_gpu_line_ele[5],
                                            'GPU Memory Usage' : list_gpu_line_ele[6]})

            dict_server['gpu_detail'][server] = dict_gpu
        except Exception as e:
            print(server, e)    
            cli.close()
            conn.close()
            # cur.close()
            dict_for_thread[server_name]['thread'] = 'off' 
            time.sleep(1)
            return

        try:
            dict_server['gpu_abstarct'][server] = get_gpu_info(cli)
        except Exception as e:
            print(server, e)
            cli.close()
            conn.close()
            # cur.close()
            dict_for_thread[server_name]['thread'] = 'off'          
            time.sleep(1)
            return
    else:
        dict_server['gpu_detail'][server] = 'not use'

    print('gpu_running : ', gpu_running)

    try:
        server_cpu_ram = _check_usage_of_cpu_and_memory(cli)
        dict_server['server_cpu_ram'][server] = server_cpu_ram
    except Exception as e:
        print(server, e)
        cli.close()
        conn.close()
        # cur.close()
        dict_for_thread[server_name]['thread'] = 'off'
        time.sleep(1)
        return
    
    try:
        cpu_usage = dict_server['server_cpu_ram'][server]['cpu']
        ram_usage = dict_server['server_cpu_ram'][server]['ram']
        server_name = server
        cpu_temp = ''
    except Exception as e:
        print(server, e)
        cli.close()
        conn.close()
        # cur.close()
        dict_for_thread[server_name]['thread'] = 'off'
        time.sleep(1)
        return
    
    date = now.strftime('%Y-%m-%d %H:%M:%S')
    ################################################################################################################################################################
    try:
        if dict_server['server_connect'][server] == 'connect':
            # gpu not use
            if dict_server['gpu_detail'][server] == 'not use':
                # print('use')
                # server_info에 server 상태 추가
                query = "UPDATE server_info SET cpu_usage = %s, cpu_temp = %s, ram_usage = %s, use_info = %s WHERE server_name = %s"
                # print(server)
                values = (cpu_usage, cpu_temp, ram_usage, 'use', server)
                ############################
                cur.execute(query, values)
                conn.commit()
                ############################
                # print(server, 'gpu not use server info')

                # gpu_info에 gpu 상태 추가
                query = "UPDATE gpu_info SET use_info = %s, gpu_usage = %s, temp = %s WHERE server_name = %s"
                values = ('not use', 'not use', 'not use', server)
                ############################
                cur.execute(query, values)
                conn.commit()
                ############################
                # print(server, 'gpu not use gpu info')
                
                if count_log%60 == 0:
                    # log 테이블에 서버정보 추가
                    query = "INSERT INTO log (date, server_name, cpu_temp, cpu_usage, ram_usage) VALUES (%s, %s, %s, %s, %s)"
                    values = (date, server_name, cpu_temp, cpu_usage, ram_usage)
                    ############################
                    cur.execute(query, values)
                    conn.commit()
                    ############################
                    # var_for_log = 0
                    # print(server, 'gpu not use log')

            # gpu use
            else:
                # server_info에 server 상태 추가
                query = "UPDATE server_info SET cpu_usage = %s, cpu_temp = %s, ram_usage = %s, use_info = %s WHERE server_name = %s"
                values = (cpu_usage, cpu_temp, ram_usage, 'use', server)
                ############################
                cur.execute(query, values)
                conn.commit()
                # print(server, 'conn')
                ############################
                # print(server, 'gpu use server info')

                # gpu_info에 gpu 상태 추가
                process_gpu_id = dict_server['gpu_detail'][server]['gpu id']
                # print(process_gpu_id)

                list_gpuid_use = []
                for idx, gpuid in enumerate(process_gpu_id):
                    list_gpuid_use.append(gpuid)
                    # print(dict_server['gpu_abstarct'][server], idx)
                    uuid = dict_server['gpu_abstarct'][server][idx]['uuid']
                    gpu_idx = df_gpu_info[df_gpu_info['uuid'] == uuid]['gpu_idx'].values[0]
                    gpu_temp = dict_server['gpu_abstarct'][server][idx]['temperature.gpu']    
                    total_gpu_memory_usage = 0
                    for process_info in process_gpu_id[gpuid]:
                        # print(server, process_info)
                        gpu_usage = process_info['GPU Memory Usage']
                        total_gpu_memory_usage += int(gpu_usage[:-3])

                    gpu_usage = total_gpu_memory_usage
                    query = "UPDATE gpu_info SET use_info = %s, gpu_usage = %s, temp = %s WHERE uuid = %s"
                    values = ('use', gpu_usage, gpu_temp, uuid)
                    ############################
                    cur.execute(query, values)
                    conn.commit()
                    ############################
                    # print(server, 'gpu use gpu info')

                # print(list_gpuid_use)
                for idx_usegpu, gpu_uuid in enumerate(dict_server_gpu[server]):
                    if str(idx_usegpu) not in list_gpuid_use:
                        query = "UPDATE gpu_info SET use_info = %s, gpu_usage = %s, temp = %s WHERE uuid = %s"
                        values = ('not use', 'not use', 'not use', gpu_uuid)
                        ############################
                        cur.execute(query, values)
                        conn.commit()
                        ############################
                        # print(server, 'gpu use extra gpu info')
                    
                if count_log%60 == 0:
                    # log 테이블에 서버정보와 gpu정보 추가
                    process_gpu_id = dict_server['gpu_detail'][server]['gpu id']
                    for idx, gpuid in enumerate(process_gpu_id):
                        for process_info in process_gpu_id[gpuid]:
                            process = process_info['Process name']
                            gpu_usage = process_info['GPU Memory Usage']
                            uuid = dict_server['gpu_abstarct'][server][idx]['uuid']
                            gpu_idx = df_gpu_info[df_gpu_info['uuid'] == uuid]['gpu_idx'].values[0]
                            gpu_temp = dict_server['gpu_abstarct'][server][idx]['temperature.gpu']

                            query = "INSERT INTO log (date, server_name, process, gpu_idx, cpu_temp, gpu_temp, cpu_usage, gpu_usage, ram_usage) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                            values = (date, server_name, process, gpu_idx, cpu_temp, gpu_temp, cpu_usage, gpu_usage, ram_usage)
                            ############################
                            cur.execute(query, values)
                            conn.commit()
                            ############################
                            # print(server, 'gpu not use log')
                    # var_for_log = 0

        # 서버 disconnect   
        else:
            # server_info에 server 상태 추가
            query = "UPDATE server_info SET cpu_usage = %s, cpu_temp = %s, ram_usage = %s, use_info = %s WHERE server_name = %s"
            values = ('not use', 'not use', 'not use', 'not use', server)
            ############################
            cur.execute(query, values)
            conn.commit()
            ############################

            # gpu_info에 gpu 상태 추가
            query = "UPDATE gpu_info SET use_info = %s, gpu_usage = %s, temp = %s WHERE server_name = %s"
            values = ('not use', 'not use', 'not use', server)
            ############################
            cur.execute(query, values)
            conn.commit()
            ############################

    except Exception as e:
        print(server, e)
        print(traceback.format_exc())
        cli.close()
        conn.close()
        # cur.close()
        dict_for_thread[server_name]['thread'] = 'off'
        time.sleep(1)
        return
    ################################################################################################################################################################
    # try:
    #     gpu_info = get_gpu_info(cli)
    #     print(server, gpu_info)
    #     server_cpu_ram = _check_usage_of_cpu_and_memory(cli)
    #     print(server, server_cpu_ram)
    # except:
    #     cli.close() 
    #     conn.close()
    #     dict_for_thread[server]['thread'] ='off'
    #     return
    
    cli.close() 
    conn.close()
    # cur.close()
    dict_for_thread[server]['thread'] ='off'
    time.sleep(1)
    
dict_for_thread = {}
for server_name in df_server_info['server_name']:
    if server_name not in dict_for_thread:
        dict_for_thread[server_name] = {}
        dict_for_thread[server_name]['thread'] = 'off'

dict_thread_server = {}

dict_for_cli = {}
for server_ip in list_server:
    server_name = server_ip.split('.')[-1]

    if server_name not in dict_for_cli:
        cli = paramiko.SSHClient()
        cli.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        dict_for_cli[server_name] = cli

count_log = 0
while True:
    threads = []
    for server_ip in list_server:
        # print(server_ip)
        server_name = server_ip.split('.')[-1]
        # print(dict_for_thread[server_name]['thread'])
        # print(dict_for_thread)

        if dict_for_thread[server_name]['thread'] == 'off':
            dict_for_thread[server_name]['thread'] = 'on'
            thread = threading.Thread(target=check_server, args=(server_ip, pool, count_log, dict_for_cli, dict_for_thread))
            # dict_thread_server[server_name] = thread
            threads.append(thread)
            thread.start()
            print(server_name, 'thread start')
    count_log += 1 

    # Wait for the threads to finish
    # for server_name in dict_thread_server:
    #     dict_thread_server[server_name].join()       
    #     print(server_name, 'thread join')
