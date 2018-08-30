#!/usr/bin/python
#-*-coding:utf-8-*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# copyright 2016 , Inc.
# All Rights Reserved.


class CommResponse(object):
    def __init__(self):
        self.rsp_info = {
            # system
            200: '成功',
        }

    def generate_rsp_msg(self, rsp_code, rsp_data):
        try:
            rsp_info = self.rsp_info[rsp_code]
        except:
            rsp_info = 'failed'
        rsp_head = {
            'rsp_head': {
                'rsp_code': rsp_code,
                'rsp_info': rsp_info,
            }
        }
        if not rsp_data:
            return rsp_head
        else:
            return dict(rsp_head.items() + rsp_data.items())
