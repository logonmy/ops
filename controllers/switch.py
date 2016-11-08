#!/usr/bin/env python
# -*- coding:utf8 -*-

import netmiko
from configs import switch_config
from helpers.logger import log_error, log_debug

class Switch:
    def help(self, req, resp):
        h = '''
                        交换机管理
        '''
        return h
