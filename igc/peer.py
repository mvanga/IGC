import datetime
import json

class PeerEncoder(json.JSONEncoder):
    def default(self, o):
        return { 'host': o.addr[0], 'port': o.addr[1] }

class Peer:
    def __init__(self, addr):
        self.addr = addr
        self.last_seen = datetime.datetime(1970, 1, 1)
        self.last_pinged = datetime.datetime.now()
        self.ping_once = False

    def update_last_seen(self):
        self.last_seen = datetime.datetime.now()

    def update_last_pinged(self):
        self.last_pinged = datetime.datetime.now()

    def needs_ping(self):
        now = datetime.datetime.now()
        delta = now - self.last_pinged
        return delta > datetime.timedelta(seconds=5)

    def is_dead(self):
        now = datetime.datetime.now()
        delta = now - self.last_seen
        return (delta > datetime.timedelta(seconds=10))

    def set_pinged(self):
        self.last_pinged = datetime.datetime.now()
        if self.ping_once == False:
            self.ping_once = True

    def __repr__(self):
        return str(self.addr[0]) + ':' + str(self.addr[1])

