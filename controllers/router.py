#!/usr/bin/env python
# -*- coding:utf8 -*-

import netmiko
from configs import router_config
from helpers.logger import log_error, log_debug

class Router:
    def help(self, req, resp):
        h = '''
                            路由器管理

        '''
        return h
