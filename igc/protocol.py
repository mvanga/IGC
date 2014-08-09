import sys
import json
import threading

sys.path.append('..')
from igc.peer import Peer

class NetworkProtocol(object):
    def __init__(self):
        self.__ops__ = {}

    def register_handler(self, command, handler):
        self.__ops__[command] = handler

    def dispatch(self, data, addr):
        ret, cmd = self.decode(data)
        if ret == False:
            return ''
        if not 'layer' in cmd:
            return ''

        if cmd['layer'] == 'net':
            if not 'type' in cmd or not 'port' in cmd:
                return ''
            if cmd['type'] not in self.__ops__:
                return ''
            with self.lock:
                resp = self.__ops__[cmd['type']](addr[0], cmd['port'], cmd)
            return resp
        elif cmd['layer'] == 'app':
            print "Received application message"
            return ''
        else:
            print "Unknown layer message"
            return ''

    def init(self, net):
        pass

    def exit(self, net):
        pass

    def decode(self, data):
        # Attempt to decode from JSON to dict
        try:
            cmd = json.loads(data)
        except ValueError, e:
            return (False, {})

        return (True, cmd)


class BroadcastNetworkProtocol(NetworkProtocol):
    def __init__(self, maxpeers, config):
        super(BroadcastNetworkProtocol, self).__init__()

        self.config = config
        self.peers = []
        self.maxpeers = maxpeers
        self.is_connected = False

        self.register_handler('GETPEERS', self.handle_getpeers)
        self.register_handler('PEERLIST', self.handle_peerlist)
        self.register_handler('PING', self.ping_handler)
        self.register_handler('PONG', self.pong_handler)
    
    def init(self, net):
        self.net = net
        self.lock = threading.Lock()
        self.is_running = True
        self.port = self.net.server.server_address[1]

        self.is_connected = False
        if self.config['is_bootstrap'] == True:
            self.is_connected = True

        # Create a recurring timer thread here
        self.timer = threading.Timer(1.0, self.timer_handler)
        self.timer.start()

    def ping_handler(self, ip, port, data):
        print 'PING from ' + ip + ':' + str(port)
        self.peer_add((ip, port), True)
        return '{ "layer": "net", "type": "PONG", "port": ' + str(self.port) + ' }'

    def pong_handler(self, ip, port, data):
        print 'PONG from ' + ip + ':' + str(port)
        self.peer_add((ip, port), True)
        return ''

    def exit(self, net):
        self.is_running = False
        self.timer.cancel()

    def get_peer(self, addr):
        for p in self.peers:
            if p.addr[0] == addr[0]:
                return p
        return None

    def peer_add(self, addr, seen):
        if self.get_peer(addr) == None:
            if len(self.peers) < self.maxpeers - 1:
                try:
                    self.peers.append(Peer(addr))
                except:
                    print sys.exc_info()

        if self.get_peer(addr) != None and seen:
            self.get_peer(addr).update_last_seen()
            self.get_peer(addr).update_last_pinged()
        print str(self.peers)

    def handle_getpeers(self, ip, port, data):
        print 'GETPEERS: from ' + str(ip) + ':' + str(port)

        # Send list of currently known peers
        ret = {'layer': 'net'}
        ret['type'] = 'PEERLIST'
        ret['port'] = self.port
        ret['peers'] = []
        for p in self.peers:
            ret['peers'].append(PeerEncoder().encode(p))
        return json.dumps(ret)

    def handle_peerlist(self, ip, port, data):
        print 'PEERLIST received from ' + str(ip) + ':' + str(port)
        # Add sender if he wasn't in list
        self.peer_add((ip, port), True)
        if not 'peers' in data:
            return
        # Add each peer if they aren't in list. Not seen yet
        for p in data['peers']:
            self.peer_add((p['host'], p['port']), False)
        self.is_connected = True

    def timer_handler(self):
            # While, we're running, repeat forever
            if self.is_running:
                threading.Timer(1.0, self.timer_handler).start()

            # If offline, keep trying to connect to bootstrap server
            if not self.is_connected:
                self.net.send(self.config['bootstrap:host'],
                    self.config['bootstrap:port'],
                    '{ "layer": "net", "type": "GETPEERS", "port": ' + str(self.port) + '}')

            # Prune all peers that are dead
            for p in self.peers:
                if p.is_dead():
                    print "Peer: " + str(p) + " disconnected"
                    self.peers.remove(p)
                    print str(self.peers)

            # Ping all peers that need to be pinged
            for p in self.peers:
                if p.needs_ping():
                    print 'Peer ' + str(p) + ' needs to be pinged. Pinging!'
                    p.set_pinged()
                    self.net.send(p.addr[0], p.addr[1],
                        '{ "layer": "net", "type": "PING", "port": ' + str(self.port) + '}')

