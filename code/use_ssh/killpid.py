import os
import sys
import psutil
import mariadb
import pandas as pd

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

sql_check_pid = "SELECT * FROM check_pid"
df_check_pid = pd.read_sql(sql_check_pid, conn)
pid = int(df_check_pid['pid'])
psutil.Process(pid).kill()