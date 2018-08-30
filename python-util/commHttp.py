#!/usr/bin/python
#-*-coding:utf-8-*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# copyright 2017 , Inc.
# All Rights Reserved.


import requests

'''
Http Client
pip install requests
'''
class HttpClient(object):
    '''
    host - str: 主机地址, 如: 127.0.0.1 或 www.baidu.com
    port - str or int: 主机端口 
    '''
    def __init__(self, host, port):
        self.host = host
        self.port = port
        return

    def post(self, url, json_body, headers = None):
        '''
        url - str: URL资源路径
        json_body - json object: 参数 
        '''
        request_url = 'http://{0}:{1}/{2}'.format(self.host, self.port, url)
        try:
            headers = {"Content-Type": "application/json"} 
            result = requests.post(request_url, json = json_body, headers = headers, timeout = 15)
            print result.status_code
            if result.status_code != 200:
                data = False
            else:
                data = result.text
        except Exception as e:
            data = False
        return data

    def get(self, url, json_body):
        '''
        url - str: URL资源路径
        json_body - json object: 参数 
        '''
        request_url = 'http://{0}:{1}/{2}'.format(self.host, self.port, url)
        print 'request_url is [%s]' % request_url
        try:
            result = requests.get(request_url, params = json_body, timeout = 15)
            print result.status_code
            if result.status_code != 200:
                data = False
            else:
                data = result.text
        except Exception as e:
            data = False
        return data

'''
例子
'''
import sys
if __name__ == '__main__':
    http_client = HttpClient('127.0.0.1', 5927)
    print http_client.get('service/arn/', {'cluster_name': 'test-cn1-docker'})
    sys.exit(0)
