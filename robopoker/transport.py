from subprocess import Popen, PIPE, STDOUT
from urllib import urlencode
from urllib2 import urlopen, URLError
import socket

def create(type, service):
    socket.setdefaulttimeout(HTTP.TIMEOUT + 2)
    return {'local': Local, 'http': HTTP}[type](service)


class Abstract(object):
    def __init__(self, service):
        self.service = service

    def message(self, name, pocket, actions, state):
        raise Exception('Abstract method called')

    def type(self):
        return str(self.__class__.__name__).lower()


class Local(Abstract):
    def message(self, name, pocket, actions, state):
        p = Popen(self.service, stdin=PIPE, stdout=PIPE,stderr=STDOUT, universal_newlines=True, shell=True)
        w = p.stdin.write
        w(name + "\n")
        w(pocket + "\n")
        w("\n")
        for a in actions:
            w(a + "\n")
        w("\n")
        w(state)
        p.stdin.flush()
        p.stdin.close()
        return p.stdout.read().strip()


class HTTP(Abstract):
    TIMEOUT = 5
    RETRY_CNT = 3
    def message(self, name, pocket, actions, state):
        data = {
            'name' :   name,
            'pocket':  str(pocket),
            'actions': '\n'.join(actions),
            'state':   state
        }
        try_no = 1
        last_err = None
        while try_no <= HTTP.RETRY_CNT:
            try:
                response = urlopen(self.service, urlencode(data), HTTP.TIMEOUT)
                return response.read().strip()
            except URLError as e:
                last_err = str(e)
                try_no += 1
        raise Error(last_err)

class Error(Exception):
    pass
