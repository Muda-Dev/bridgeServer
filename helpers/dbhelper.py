from flask import request, jsonify
from application import mysql

class Database:
    def __init__(self):
        self.conn = mysql.connection.cursor()
        print("connection created")

    
    def checkConnection(self):
        try:
            rows = self.select("SELECT name FROM sys.tables")
            print("Database connected!")
            return True
        except Exception as e:
            print(e)
            return False

    
    def select(self, query):
        self.conn.execute(query)
        rows = self.conn.fetchall()
        return rows

    
    def delete(self, query):
        self.conn.execute(query)
        mysql.connection.commit()
        self.conn.close()
        return True

    
    def insert(self, table_name, **data):
        keys = ', '.join(['%s'] * len(data))
        columns = ', '.join(data.keys())
        values = tuple(data.values())
        sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % (table_name, columns, keys)
        self.conn.execute(sql, values)
        mysql.connection.commit()
        self.conn.close()
        last_id = self.conn.lastrowid
        return last_id

    
    def Update(self, table, where, **d):
        sql = 'UPDATE ' + table + ' SET {}'.format(', '.join('{}=%s'.format(k) for k in d))
        sql = sql + ' WHERE ' + where
        write_to_file(sql)
        values = tuple(d.values())
        self.conn.execute(sql, values)
        mysql.connection.commit()
        self.conn.close()
        last_id = self.conn.lastrowid
        return last_id


def write_to_file(data):
    f = open("output.txt", "w")
    f.write(data)
    f.close()