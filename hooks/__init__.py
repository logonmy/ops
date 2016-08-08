#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
from configs import advance_path
import falcon


#记录访问日志
def do_log_history(req, resp):
    return
    print req.path, req.headers


#记录结果
def do_log_result(req, resp):
    return
    print resp.body


def rbac(req, resp):
    for item in advance_path:
        path = item.keys()[0]
        if not re.search(req.path, path):
            continue
        else:
            user_group = req.get_header('LOGIN-USER')
            groups = item.values()[0]
            if user_group not in groups:
                raise falcon.HTTPForbidden(
                    title='You not allow access it',
                    description='Please connect the manager')
