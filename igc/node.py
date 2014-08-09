import sys
import socket
import json
import time
import threading
import SocketServer

sys.path.append('..')
from igc.peer import Peer, PeerEncoder

config = {}
config['is_bootstrap'] = True
config['port'] = 8888

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(2048)
        response = self.server.private.proto.dispatch(data, self.client_address)
        if response != '':
            #print "sending: " + response
            self.request.sendall(response)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class Node:
    def __init__(self, host, port, proto):
        SocketServer.TCPServer.allow_reuse_address = True
        self.server = ThreadedTCPServer((host, port), ThreadedTCPRequestHandler)
        self.server.private = self

        self.ip, self.port = self.server.server_address
        self.server_thread = threading.Thread(target = self.server.serve_forever)
        self.proto = proto

    def start(self):
        self.server_thread.daemon = True
        self.server_thread.start()
        self.proto.init(self)

    def send(self, ip, port, message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((ip, port))
            sock.sendall(message)
            response = sock.recv(2048)
            if response != '':
                #print "received: " + response
                self.server.private.proto.dispatch(response, (ip, port))
        except:
            return
        finally:
            sock.close()

    def stop(self):
        self.server.shutdown()
        self.proto.exit(self)

if __name__ == '__main__':
    n = Node('localhost', 8888, BroadcastNetworkProtocol(100, config))
    n.start()
    n.send('localhost', 8888, '{ "layer": "net", "type": "PING", "port": 8889 }')
    time.sleep(10)
    n.stop()
