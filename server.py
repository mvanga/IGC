#!/usr/bin/python

import socket
import sys
import getopt
import threading
import Queue
import time
import json
import datetime

sys.path.append('.')
from igc.protocol import BroadcastNetworkProtocol
from igc.node import Node

config = {}
config['is_bootstrap'] = True
config['port'] = 8888

class IGCShell:
    def __init__(self):
        self.is_running = True

    def run(self):
        while self.is_running == True:
            try:
                cmd = raw_input('IGC> ')
                if self.shell_parse(cmd) == False:
                    self.is_running = False
            except KeyboardInterrupt:
                print "\nBye"
                self.is_running = False

    def shell_parse(self, cmd):
        cmd = cmd.split(' ')
        if cmd[0] == 'exit' or cmd[0] == 'q':
            return False
        else:
            print "Unknown command: " + cmd[0]
        return True

def configure():
    global connected
    optlist, args = getopt.getopt(sys.argv[1:], "b:p:")
    for opt, arg in optlist:
        if opt == '-b':
            config['bootstrap:host'] = arg.split(':')[0]
            config['bootstrap:port'] = int(arg.split(':')[1])
            config['is_bootstrap'] = False
        elif opt == '-p':
            config['port'] = int(arg)
        else:
            print "Error parsing command line args"
            sys.exit(2)

if __name__ == '__main__':
    configure()

    n = Node('localhost', config['port'], BroadcastNetworkProtocol(100, config))
    n.start()

    shell = IGCShell()
    shell.run()

    n.stop()
