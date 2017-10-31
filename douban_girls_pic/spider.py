# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import sqlalchemy
import time
import requests
import urllib
import multiprocessing
from bs4 import BeautifulSoup

from settings import *


task_queue = multiprocessing.Queue(10000)

def get_topic_list(topic_id, page_num):
    """
    :param topic_id: 豆瓣小组id
    :return:
    """
    topic_url = "https://www.douban.com/group/{}/discussion?start={}".format(topic_id, page_num)
    time.sleep(2)
    response = requests.get(topic_url, proxies=proxies, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(response.content, 'lxml')
    for item in soup.body.find_all('td', class_='title'):
        link = item.a['href']
        if not (link and link.find('group/topic') > 0):
            continue
        if link not in visited:
            visited.add(link)
            task_queue.put(link)


def get_page_detail():
    """解析详情页图片
    :return:
    """
    detail_url = task_queue.get(block=True)
    response = requests.get(detail_url, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'lxml')
    divs = soup.find_all('div', class_='topic-figure')
    for div in divs:
        if not div.img.get('src'):
            continue
        img = div.img.get('src')
        print img
        name = str(int(time.time()))
        suffix = img.rsplit('.')[-1]
        img_name = name + '.' + suffix
        urllib.urlretrieve(img, "{}/{}".format(IMAGE_DIR, img_name))


def producer(topic_id):
    page_num = 0
    page_offset = 25
    while True:
        get_topic_list(topic_id, page_num)
        page_num += page_offset



def worker():
    time.sleep(5)
    while True:
        time.sleep(2)
        get_page_detail()


def main(topic_id):
    p1 = multiprocessing.Process(target=producer, args=(topic_id, ))
    p2 = multiprocessing.Process(target=worker, args=tuple())
    p1.start()
    p2.start()
    p1.join()
    p2.join()


if __name__ == '__main__':
    main('qiaoPP')
