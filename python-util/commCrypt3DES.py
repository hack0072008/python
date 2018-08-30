#!/usr/bin/python
# -*- coding:utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# copyright 2018 , Inc.
# All Rights Reserved.


from Crypto.Cipher import DES
import base64
from binascii import b2a_hex, a2b_hex
import json

class Crypt3DES(object):
    def __init__(self, key = None):
        self.key = key if key else "zyh_-_zl" # 密钥 8位或16位,必须为bytes
        self.mode = DES.MODE_ECB
        self.fill_character = ' '
        #print('key[%s] len[%s]' % (self.key, len(self.key)))

    def pad(self, text):
        """
        # 如果text不是key长度的倍数，那就补足为key长度的倍数
        :param text: 
        :return: 
        """
        while len(text) % len(self.key) != 0:
            text += self.fill_character
        return text

    def encrypt(self, text):
        """
        #3DES加密
        :param text: 
        :return: 
        """
        des = DES.new(self.key, self.mode)
        return base64.b64encode(b2a_hex(des.encrypt(self.pad(text).encode('utf-8'))))

    def decrypt(self, text):
        """
        #3DES解密
        :param text: 
        :return: 
        """
        try:
            des = DES.new(self.key, self.mode)
            plain_text = des.decrypt(a2b_hex(base64.b64decode(text)))
            return plain_text.decode().rstrip(self.fill_character)
        except Exception as e:
            print e
            return '29001'

import sys
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", help="type",type=str, choices=['encode', 'decode'], required=True)
    parser.add_argument("--text", help="text",type=str, required=True)
    args = parser.parse_args()

    print 'init   :',args.text,len(args.text)
    des = Crypt3DES()
    if args.type == 'encode':
        new_text = des.encrypt(args.text)
        print 'encrypt:',new_text,len(new_text)
    elif args.type == 'decode':
        print des.decrypt(args.text)

    old_text = des.decrypt(new_text)
    print 'decrypt:',old_text,len(old_text)

    json_text = json.dumps(new_text)
    print 'new_text json_text:',json_text

    sys.exit(0)
