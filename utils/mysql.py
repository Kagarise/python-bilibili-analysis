import pymysql

from dbutils.pooled_db import PooledDB

mysql_args = {
    'host': '',
    'port': 3307,
    'user': 'root',
    'password': '',
    'database': '',
    'charset': 'utf8mb4'
}

pool = PooledDB(pymysql, **mysql_args)


def fetch(sql, args=None):
    conn = pool.connection()
    cursor = conn.cursor()
    cursor.execute(sql, args)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def commit(sql, args=None):
    conn = pool.connection()
    cursor = conn.cursor()
    cursor.execute(sql, args)
    conn.commit()
    cursor.close()
    conn.close()
