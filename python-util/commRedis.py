#!/usr/bin/python                                                                                                                                                                                                                
#-*-coding:utf-8-*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# copyright 2017.
# All Rights Reserved.

# @author: Zhangyh.
import redis
import time



class RedisHandler(object):
    def __init__(self):
        self.host = None
        self.port = None
        self.db = None
        self.password = None
        self.conn = None

    def connect(self, host, port, db, password = None):
        try:
            conn = redis.Redis(host = host, port = port, db = db, password = password)
            self.host = host
            self.port = port
            self.db = db
            self.password = password
            self.conn = conn
        except Exception,e:
            self.conn = None
            print('RedisHandler connect host[%s] port[%d] db[%s] password[%s] Exception.' % (host, port, db, password))
            print e
            return False
        print('RedisHandler connect host[%s] port[%d] db[%s] password[%s] succ.' % (host, port, db, password))
        return True

    def set_kv(self, key, value, time_s, time_ms = None, nx_flag = False, xx_flag = False):
        now_time = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.conn.set(name = key, value = value, ex = time_s, px = time_ms, nx = nx_flag, xx = xx_flag)
        except Exception,e:
            print('RedisHandler set key[%s] value[%s] host[%s] port[%d] db[%s] now[%s] ex[%s] px[%s] Exception.' % (key, value, self.host, self.port, self.db, now_time, time_s, time_ms))
            print e
            return False
        print('RedisHandler set key[%s] value[%s] host[%s] port[%d] db[%s] now[%s] ex[%s] px[%s] succ.' % (key, value, self.host, self.port, self.db, now_time, time_s, time_ms))
        return True

    def get_kv(self, key):
        try:
            value = self.conn.get(name = key)
        except Exception,e:
            print('RedisHandler get key[%s] host[%s] port[%d] db[%s] Exception.' % (key, self.host, self.port, self.db))
            print e
            return False
        if value:
            print('RedisHandler get key[%s] host[%s] port[%d] db[%s] succ.' % (key, self.host, self.port, self.db))
            return value
        else:
            print('RedisHandler get key[%s] host[%s] port[%d] db[%s] fail.' % (key, self.host, self.port, self.db))
            return False

    def delete_kv(self, key):
        try:
            value = self.conn.delete(key)
            self.conn.save()
        except Exception,e:
            print('RedisHandler delete key[%s] host[%s] port[%d] db[%s] Exception.' % (key, self.host, self.port, self.db))
            print e
            return False
        if value == 1:
            print('RedisHandler delete key[%s] host[%s] port[%d] db[%s] succ 1 items.' % (key, self.host, self.port, self.db))
            return True
        else:
            print('RedisHandler delete key[%s] host[%s] port[%d] db[%s] succ 0 items.' % (key, self.host, self.port, self.db))
            return False


if __name__ == '__main__':
    redis_handler = RedisHandler()
    if redis_handler.connect(host = '10.100.102.206', port = 6379, db = 0, password = 'pass'):
        redis_handler.set_kv(key = 'weixin_accesstoken_ssq', value = '12345678klsjdhfkj', time_s = 7200)
        value = redis_handler.get_kv(key = 'weixin_accesstoken_ssq')
        print('value[%s]' % value)
        value = redis_handler.delete_kv(key = 'weixin_accesstoken_ssq')
        print('value[%s]' % value)
        value = redis_handler.delete_kv(key = 'weixin_accesstoken_ssq')
        print('value[%s]' % value)
        value = redis_handler.get_kv(key = 'weixin_accesstoken_ssq')
        print('value[%s]' % value)






