#!/usr/bin/python                                                                                                                                                                                                                                                             
#-*-coding:utf-8-*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# copyright 2017 , Inc.
# All Rights Reserved.

import requests
from wxpy import *
import json

#图灵机器人
def talks_robot(info = '你叫什么名字'):
    api_url = 'http://www.tuling123.com/openapi/api'
    apikey = '05d571f41bc14e559a178d729cc40381'
    data = {'key': apikey,
    'info': info}
    req = requests.post(api_url, data=data).text
    replys = json.loads(req)['text']
    return replys

#微信自动回复
'''
console_qr:
(/usr/lib/python2.7/site-packages/wxpy/api/bot.py)
            * 在终端中显示登陆二维码，需要安装 pillow 模块 (`pip3 install pillow`)。
            * 可为整数(int)，表示二维码单元格的宽度，通常为 2 (当被设为 `True` 时，也将在内部当作 2)。
            * 也可为负数，表示以反色显示二维码，适用于浅底深字的命令行界面。
            * 例如: 在大部分 Linux 系统中可设为 `True` 或 2，而在 macOS Terminal 的默认白底配色中，应设为 -2。

'''
robot = Bot(console_qr = -2)

# 回复来自其他好友、群聊和公众号的消息
@robot.register()
def reply_my_friend(msg):
    message = '{}'.format(msg.text)
    replys = talks_robot(info=message)
    return replys

# 开始监听和自动处理消息
robot.start()
