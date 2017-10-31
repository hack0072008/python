#!/usr/bin/python
#-*-coding:utf-8-*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# copyright 2017 Sengled, Inc.
# All Rights Reserved.

# @author: Zhangyh, Sengled, Inc.


from sys import argv
import json
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import datetime

from prettytable import PrettyTable

import os
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw


class Json2Image(object):
    def __init__(self):
        pass

    def json_to_tables(self, data):
        if len(data) == 0:
            print 'json_to_tables: data is None, please retry.'
            return None

        table_title = data[0]
        table_body = data[1:]

        print 'table_title:' +  json.dumps(table_title)
        print 'table_body:' +  json.dumps(table_body)
        print 'data:' +  json.dumps(data)

        try:
            #table = PrettyTable(table_title, encoding=sys.stdout.encoding)
            table = PrettyTable(table_title, encoding='UTF-8')
            table.padding_width = 1
            table.hrules = 1

            for row in table_body:
                table.add_row(row)
            table = table.get_string()
        except Exception,e:
            print 'generate json to table_string exception.'
            print str(e)
            return None

        return table

    def string_to_image(self, data, font_path, font_name, font_size, obj_image_full_name, wide, high):
        if not data or not font_path or not font_name or not font_size or not obj_image_full_name or not wide or not high:
            print 'string_to_image check params error.'
            return None
        print '[%s] [%s] [%d] [%s] [%d] [%d]' % (font_path, font_name, font_size, obj_image_full_name, wide, high)
 
        try:
            im = Image.new("RGB", (int(wide), int(high)), (255, 255, 255))
            dr = ImageDraw.Draw(im)
            font = ImageFont.truetype(font_path +  font_name, int(font_size))

            im = im.resize(dr.textsize(data, font = font),Image.ANTIALIAS)
            dr = ImageDraw.Draw(im)
            dr.text((0, 0), data, font=font, fill="#000000")
            im.save(obj_image_full_name , "JPEG")
        except Exception,e:
            print 'string_to_image create image [%s] from string exception.' % obj_image_full_name
            print str(e)
            return None

        return obj_image_full_name

if __name__ == '__main__':
    if len(argv) != 3:
        print "useage: json2image.py json_data base_path"
        print "    example: json2image.py json_data /home/ec2-user/impage/"
        print "       Note:"
        print "           json_data         : [['title1','title2',...],['col1','col2',...]]"
        print "           base_path         : /home/ec2-user/impage/"
        print "       Return:"
        print "           /home/ec2-user/impage/Image_2017-10-26_17-50-00.jpg"
        exit(1)

    local_time = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d_%H-%M-%S")

    json_data = argv[1]
    base_path = argv[2]
    image_full_path = base_path + 'image/'
    image_font_path = base_path + 'font/'

    image_full_name = 'Image_' + local_time + '.jpg'

    #image_font_name = 'msyh.ttf'
    image_font_name = 'simsun.ttc'
    image_font_size = 15

    image_wide = 1024
    image_high = 768

    print 'json_data:' + json_data
    print 'image_full_path:' + image_full_path
    print image_full_path + image_full_name

    try:
        json_data = json.loads(json_data)
    except Exception,e:
        print 'json loads input json_data exception, pleate recheck.'
        print str(e)
        exit(1)
    print 'json loads input json_data succ.'

    if not os.path.exists(image_full_path):
        print 'check input image_full_path params error: [%s] is not exists.' % image_full_path
        exit(1)
    print 'check input image_full_path params succ: [%s] is exists.' % image_full_path

    if os.path.exists(image_full_path + image_full_name):
        print 'warnning:check input image_full_path params : [%s%s] is exists.' % (image_full_path, image_full_name)
        os.remove(image_full_path + image_full_name)
        print 'delete existed file : [%s%s] finish.' % (image_full_path, image_full_name)

    if not os.path.exists(image_font_path + image_font_name):
        print 'check input image_font_path image_font_name params error: [%s%s] is not exists.' % (image_font_path, image_font_name)
        exit(1)

    try:
        j = Json2Image()
        str_tab = j.json_to_tables(data = json_data)
        print 'table:'
        print str_tab

        image = j.string_to_image(data = str_tab, font_path = image_font_path, font_name = image_font_name, font_size = image_font_size, obj_image_full_name = image_full_path + image_full_name, wide = image_wide , high = image_high)
    except Exception,e:
        print str(e)
        exit(1)

    if image:
        sys.exit(image)

