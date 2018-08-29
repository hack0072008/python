#!/usr/bin/python
#-*-coding:utf-8-*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# copyright 2018 xxxx, Inc.
# All Rights Reserved.

# @author: Zhangyh, xxxx, Inc.

import mysql.connector
from DBUtils.PooledDB import PooledDB



import logging
import time
def get_logger(path_home, fix):
    if fix is None:
        raise NameError

    #loger
    logger = logging.getLogger()

    #Log等级总开关
    logger.setLevel(logging.INFO)
    
    #handler
    rq = time.strftime('%Y%m%d', time.localtime(time.time()))
    log_path = path_home + fix + '/'
    log_name = log_path + rq + '.log'
    logfile = log_name
    fh = logging.FileHandler(logfile) #默认是追加模式

    #输出到file的log等级的开关
    fh.setLevel(logging.INFO)
    
    #handler format
    logging_format = logging.Formatter('[%(asctime)s] [%(process)d] [%(thread)d] [%(filename)18s:%(lineno)4d] [%(funcName)21s] [%(levelname)-6s] %(message)s')
    fh.setFormatter(logging_format)
    
    #关联handler 与 logger
    logger.addHandler(fh)
    
    return logger


class MysqlHandler(object):
    def __init__(self, host, port, user, password, db, use_unicode = True, logger = None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.use_unicode = use_unicode
        self.conn = None
        self.cursor = None
        self.pool = None
        self.log = logger if logger is not None else get_logger('/var/log/', 'mysql')
        self.log.info('init mysql succ.')

    def connect(self):
        try:
            if self.conn is None:
                self.conn = mysql.connector.connect(host = self.host, port = self.port, user = self.user, password = self.password, database = self.db, use_unicode = self.use_unicode)
        except Exception,e:
            self.log.error('connect to host[%s] port[%s] exception[%s].' % (self.host, self.port, str(e)))
            return False
        self.log.info('connect to host[%s] port[%s] succ.' % (self.host, self.port))

        try:
            if self.cursor is None:
                self.cursor = self.conn.cursor()
        except Exception,e:
            self.log.error('init cursor host[%s] port[%s] exception[%s].' % (self.host, self.port, str(e)))
            return False
        self.log.info('init cursor host[%s] port[%s] succ.' % (self.host, self.port))
        return True

    def dis_connect(self):
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception,e:
            self.log.error('dis_connect to host[%s] port[%s] exception[%s].' % (self.host, self.port, str(e)))
            return False
        self.log.info('dis_connect to host[%s] port[%s] succ.' % (self.host, self.port))

        try:
            if self.cursor is not None:
                self.cursor.close()
        except Exception,e:
            self.log.error('close cursor host[%s] port[%s] exception[%s].' % (self.host, self.port, str(e)))
            return False
        self.log.info('close cursor host[%s] port[%s] succ.' % (self.host, self.port))

        return True

    def get_connect(self):
        if self.conn is None:
            try:
                self.connect()
            except Exception,e:
                self.log.info('get host[%s] port[%s] connect exception[%s].' % (self.host, self.port, str(e)))
                raise NameError
        self.log.info('get host[%s] port[%s] connect succ.' % (str(e), self.host, self.port))
        return self.conn

    def dql(self, sql):
        try:
            self.cursor.execute(sql)
            datas = self.cursor.fetchall()
        except Exception, e:
            self.log.error('dql host[%s] port[%s] dql[%s] exception[%s].' % (self.host, self.port, sql, str(e)))
            return []
        self.log.info('dql host[%s] port[%s] dql[%s] succ.' % (self.host, self.port, sql))

        return datas

    def ddl(self, sql):
        rowcount = 0

        try:
            self.cursor.execute(sql)
            rowcount = self.cursor.rowcount
            self.conn.commit()
        except Exception, e:
            self.log.error('ddl host[%s] port[%s] sql[%s] exception[%s].' % (self.host, self.port, sql, str(e)))
            return 0

        self.log.info('ddl host[%s] port[%s] sql[%s] succ.' % (self.host, self.port, sql))
        return rowcount




if __name__ == '__main__':
    mysql_handler = MysqlHandler(host = '127.0.0.1', port = '3306', user = 'root', password = 'root', db = 'test')                                                                                                                                                         
    mysql_handler.connect()
    sql = 'select * from parameter'
    datas = mysql_handler.dql(sql)
    for item in datas:
        print item

    sql = 'create table test_01 (id varchar(20) primary key, name varchar(20))'
    count = mysql_handler.ddl(sql)
    datas = mysql_handler.dql('select * from test_01')
    print count
    print datas

    count = mysql_handler.ddl('drop table test_01')
    print count

    mysql_handler.dis_connect()
    
    
    
