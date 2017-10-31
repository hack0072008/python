# -*- coding: utf-8 -*-
import os

IMAGE_DIR = '/Users/gao/Desktop/douban'
if not os.path.isdir(IMAGE_DIR):
    os.mkdir(IMAGE_DIR)

HEADERS = {
    "Connection": "keep-alive",
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4,ja;q=0.2',
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.douban.com/",
    "Upgrade-Insecure-Requests": "1",
    "Host": "www.douban.com",
    "Cookie": """bid=ierOIMLQaGU; viewed="6847455"; gr_user_id=c7c7f768-a04c-4995-b784-bf625cb29d70; ps=y; _vwo_uuid_v2=F58D48F699CBFE79B385615D7FAAB350|60e25ac4146fb9e49058d85a90f24be5; __yadk_uid=mMZ0DUuIe2M3xLdLGtiiwJTJWJ6tyWSn; ct=y; _ga=GA1.2.1448222632.1490149129; ll="108288"; dbcl2="49845587:xNnoNFHto+Q"; ck=3SQH; ap=1; _pk_ref.100001.8cb4=%5B%22%22%2C%22%22%2C1508750634%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D; __utmt=1; _pk_id.100001.8cb4=6f86b42bea4f242d.1490149128.39.1508750739.1508746503.; _pk_ses.100001.8cb4=*; push_noty_num=0; push_doumail_num=0; __utma=30149280.1448222632.1490149129.1508743053.1"""
}

proxies = {
    'http': 'http://179.91.120.1:8080',
    # 'https': 'xxx'
}

visited = set()
