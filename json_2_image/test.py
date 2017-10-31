# -*- coding: utf-8 -*- 
from PIL import Image
from PIL import  ImageDraw
import sys
import json
from PIL import ImageFont
import StringIO
if __name__ == '__main__':  
    #"[\"1,2,3,4\",\"2,2,2,2\"]" "[\"1,2,3,4\",\"2,2,2,2\"]" "[\"1,2,3,4\",\"2,2,2,2\"]"

    font = ImageFont.truetype('simsun.ttc',18)
    image = Image.new('RGB', (1000, 1000), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    ifile = open("txt.txt", "r")
    s = '''+------+------+--------+---------------------+----------------+----------------+
| 区域 | 类型 | 在线数 |   最新数据收集时间  | 前一日同比增加 | 前一周同比增加 |
+------+------+--------+---------------------+----------------+----------------+
| 美国 | iot  |  3917  | 2017-10-27 12:52:00 |       31       |      207       |
| 欧洲 | iot  |  7490  | 2017-10-27 12:52:00 |       21       |      250       |
| 欧洲 | iot  |  7490  | 2017-10-27 12:52:00 |       21       |      250       |
| 欧洲 | iot  |  7490  | 2017-10-27 12:52:00 |       21       |      250       |
| 欧洲 | iot  |  7490  | 2017-10-27 12:52:00 |       21       |      250       |
| 欧洲 | iot  |  7490  | 2017-10-27 12:52:00 |       21       |      250       |
| 欧洲 | iot  |  7490  | 2017-10-27 12:52:00 |       21       |      250       |
| 欧洲 | iot  |  7490  | 2017-10-27 12:52:00 |       21       |      250       |
| 欧洲 | iot  |  7490  | 2017-10-27 12:52:00 |       21       |      250       |
| 欧洲 | iot  |  7490  | 2017-10-27 12:52:00 |       21       |      250       |
| 欧洲 | iot  |  7490  | 2017-10-27 12:52:00 |       21       |      250       |
| 欧洲 | iot  |  7490  | 2017-10-27 12:52:00 |       21       |      250       |
| 欧洲 | iot  |  7490  | 2017-10-27 12:52:00 |       21       |      250       |
| 欧洲 | iot  |  7490  | 2017-10-27 12:52:00 |       21       |      250       |
+------+------+--------+---------------------+----------------+----------------+'''
    buf = StringIO.StringIO(s)
    try:
        num = 0
        while True:
            #line = ifile.readline()
            line = buf.readline()
            num = num + 1
            print line
            print "\n"
            if line:
                draw.text((10, 10 + 20*num), unicode(line,'UTF-8'),  font = font, fill='#ff0000')
            else:
                break
    finally:
        ifile.close()
    #draw.text((10, 10), unicode(str1,'UTF-8'), font = font, fill='#ff0000')
    image.save("test.jpg", 'JPEG')
    #draw(src,dst,pos1josn,pos2josn,pos3josn)
    


