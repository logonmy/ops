import requests
from configs import etcd_config_cmd
from helpers.logger import log_error, log_debug
import simplejson as json
import time


class Cmd:
    def __init__(self):
        self.cmdkeys = {}
        self.etcd_config = etcd_config_cmd

    def help(self, req, resp):
        return ''

    def cmd(self, req, resp):
        try:
            cmd = req.get_param(name='c')
            ip = req.get_param(name='i')
            timeout = req.get_param(name='5') or 3

            if 'c' is None:
                return '-c(cmd) require'
            if 'i' is None:
                return '-i(ip) require'
            data = {'value': cmd.encode('utf-8')}
            req = requests.post(
                url="http://%s/v2/keys/%s/servers/%s/" %
                (self.etcd_config['server'], self.etcd_config['prefix'], ip),
                data=data)
            ret = req.json()

            index = str(ret['node']['createdIndex'])
            self.cmdkeys[index] = ''
            start = time.time()
            if ret['node']['value'] == cmd:
                while True:
                    if (time.time() - start > timeout
                        ) or self.cmdkeys[index] != '':
                        log_debug('%s timeout' % data)
                        break
                    else:
                        time.sleep(0.1)
                if self.cmdkeys[index] != '':
                    ret = self.cmdkeys[index]
                    del self.cmdkeys[index]
                    return ret
                return '(success) submit command success'
            else:
                return '(unsafe) submit command success '
        except Exception as er:
            log_error(er)
            return 'fail'
