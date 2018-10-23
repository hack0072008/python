#!/usr/bin/python
#-*-coding:utf-8-*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# copyright 2017.
# All Rights Reserved.

# @author: Zhangyh.


import json
import requests
import random

from CpHandler import CpHandler
from RedisHandler import RedisHandler


class WhatappHandler(object):
    def __init__(self):
        self.corpid = None 
        self.corpsecret = None
        self.redis_handler = None
        self.access_key = 'weixin_token_ssq'

    def get_access_token(self, corpid = None, corpsecret = None):
        self.corpid = corpid
        self.corpsecret = corpsecret

        url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + corpid + '&corpsecret=' + corpsecret

        #print url
        try:
            rsp = requests.get(url, timeout = 30)
            #print rsp.text
            if rsp.status_code != 200 or json.loads(rsp.text)['errcode'] != 0:
                print('get access token error, ret[%s] errcode[%s] errmsg[%s]' % (rsp.status_code, json.loads(rsp.text)['errcode'], json.loads(rsp.text)['errmsg']))
                return False
            access_token = json.loads(rsp.text)['access_token']
            expires_time = json.loads(rsp.text)['expires_in']
            print('get access token succ, access_token[%s] expires_time[%s]' % (access_token, expires_time))
            return access_token,expires_time
        except Exception,e:
            print('Excetpion')
            print e
            return False

    def get_token(self, host = '10.10.10.1', port = 6379, db = 0, password = 'pass', corpid = None, corpsecret = None):
        self.corpid = corpid
        self.corpsecret = corpsecret

        self.redis_handler = RedisHandler()
        if self.redis_handler.connect(host = host, port = port, db = db, password = password):
            access_token = self.redis_handler.get_kv(key = self.access_key)
            if access_token:
                print 'get access_toke from redis succ.'
                return access_token
            else:
                access_token,expires_time = self.get_access_token(corpid = corpid, corpsecret = corpsecret)
                self.redis_handler.set_kv(key = self.access_key, value = access_token, time_s = expires_time)
                print 'get access_toke from weixin succ.'
                return access_token

    def get_all_department(self, access_token = None):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token=' + access_token
        try:
            rsp = requests.get(url, timeout = 30)
            if rsp.status_code != 200 or json.loads(rsp.text)['errcode'] != 0:
                print('get all department error, ret[%s] errcode[%s] errmsg[%s]' % (rsp.status_code, json.loads(rsp.text)['errcode'], json.loads(rsp.text)['errmsg']))
                return False
            departments = json.loads(rsp.text)['department']
            print('get all department succ, department[%s]' % str(departments))
            return departments
        except Exception,e:
            print('get all department Excetpion')
            print e
            return False

    def get_department_users(self, access_token = None, department_id = None, fetch_child = None):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/simplelist?access_token=' + access_token + '&department_id=' + str(department_id) + '&fetch_child=' + str(fetch_child)

        try:
            rsp = requests.get(url, timeout = 30)
            if rsp.status_code != 200 or json.loads(rsp.text)['errcode'] != 0:
                print('get department users error, ret[%s] errcode[%s] errmsg[%s]' % (rsp.status_code, json.loads(rsp.text)['errcode'], json.loads(rsp.text)['errmsg']))
                return False
            users = json.loads(rsp.text)['userlist']
            print('get department users succ, users[%s]' % str(users))
            return users
        except Exception,e:
            print('get department users Excetpion')
            print e
            return False

    def send_text_message(self, access_token = None, user_id = None, agent_id = None, msg = None):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + access_token
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        message = {
                    'touser' : '|'.join(user_id),
                    'msgtype' : 'text',
                    'agentid' : agent_id,
                    'text' : {
                               'content' : msg
                    },
                    'safe' : 0
                }

        print message
        try:
            rsp = requests.post(url, data = json.dumps(message), headers = headers, timeout = 30)
            if rsp.status_code != 200 or json.loads(rsp.text)['errcode'] != 0:
                print('send text message error, ret[%s] errcode[%s] errmsg[%s]' % (rsp.status_code, json.loads(rsp.text)['errcode'], json.loads(rsp.text)['errmsg']))
                return False
            print('send text message succ, ret[%s] errcode[%s] errmsg[%s]' % (rsp.status_code, json.loads(rsp.text)['errcode'], json.loads(rsp.text)['errmsg']))
            return True
        except Exception,e:
            print('send text message Excetpion')
            print e
            return False

class WhatappClientHandler(object):
    def __init__(self):
        pass
    def DecryptMsg(self, msg_signature, timestamp, nonce, postdata, xml_msg):
        pass
    def EncryptMsg(self, ReplyMsg, timestamp, nonce, xml_msg):
        pass
    def VerifyURL(self, msg_signature, timestamp, nonce, echostr, reply_echostr):
        pass
    def get_server_ips(self, token):
        pass


if __name__ == '__main__':
    corpid = 'xxxxxxxxxxxxx'
    corpsecret = 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy'
    w = WhatappHandler()
    #access_token,expires_time = w.get_access_token(corpid = corpid, corpsecret = corpsecret)
    access_token = w.get_token(corpid = corpid, corpsecret = corpsecret)

    departments = w.get_all_department(access_token = access_token)
    #print departments[0]['name']

    department_id = departments[0]['id']
    #print('department_id[%s]' % department_id)
    users = w.get_department_users(access_token = access_token, department_id = department_id, fetch_child = 1)

    user_list = [item['userid'] for item in users]
    #user_id = users[0]['userid']
    #msg = "hello, everyBody....come on,gay......"
    #ret = w.send_text_message(access_token = access_token, user_id = user_id, agent_id = '1000001', msg = json.dumps(msg, ensure_ascii=False))
    #print ret

    result = CpHandler().get_result_by_key(key = '快三')
    list =  ['1', '2', '3', '4', '5', '6']
    slice = random.sample(list, 3)
    slice.sort()
    rs = ','.join(slice)
    result2 = ' 下一期推荐号码【' + rs + '】 祝君好运~'
    ret = w.send_text_message(access_token = access_token, user_id = user_list, agent_id = '1000001', msg = json.dumps(result + result2, ensure_ascii=False))
    print ret


