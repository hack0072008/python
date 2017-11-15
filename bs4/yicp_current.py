#!/usr/bin/python
#-*-coding:utf-8-*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# copyright 2017 Sengled, Inc.
# All Rights Reserved.

from bs4 import BeautifulSoup
import requests

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


r = requests.get('http://www.yicp.com/actkaijiang/ssqinfo.html')
soup = BeautifulSoup(r.text, "html.parser")

#soup = BeautifulSoup(open('index.html'))

#print(soup.prettify())
#t = soup.find_all('div',class_='kjinfo_res_container border_grey')


#获取红球
red_ball =  []
red_data = soup.find_all('span', class_ = 'kjinfo_res_ball kjinfo_res_red_ball')
for item in red_data:
    red_ball.append(unicode(item.string))

#获取蓝球
blue_ball =  []
blue_data = soup.find_all('span', class_ = 'blue')
for item in blue_data:
    blue_ball.append(unicode(item.string))

#获取开奖期数
t = soup.find_all('b')
kj_qs = t[0].string

#获取开奖时间
t = soup.find_all('b')
kj_sj = t[1].string

#获取奖池金额
t1  = soup.find_all('span')
jcje = unicode(t1[19].string).split(' ')[-1]
jcje = jcje.split('元')[0]

#获取本期销量
t1  = soup.find_all('span')
bqxl = unicode(t1[18].string).split(' ')[-1]
bqxl = bqxl.split('元')[0]

#print red_ball
#print blue_ball

print('第[%s]期 开奖时间[%s] 号码[%s-%s] 本期销量[%s] 奖池金额[%s]' % (kj_qs, kj_sj, ' '.join(red_ball), ''.join(blue_ball), bqxl, jcje))


