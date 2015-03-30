from __future__ import print_function

import sys
import json
import socket
import common
import threading
import errno
from datetime import datetime, timedelta
import time
import collections

class Client(object):
    def __init__(self, udp_port=23457):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind(('', udp_port))
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_sock.settimeout(0)
        # Set broadcast
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.going = False
        self.servers = []
        self.server_list = {}
        self.server_update_time = datetime.now()
        self.server_udp_port = 23456
        self.main_thread = None
        # Receive Queue
        self.recv_queues = {}

    def start(self):
        if self.going:
            return
        if self.main_thread:
            self.main_thread.join()
        self.going = True
        self.my_thread = threading.Thread(None, Client._main_client_thread, "Main client thread", [self])
        self.my_thread.start()

    def stop(self, close_servers=True):
        if not self.going:
            return
        self.going = False
        self.my_thread.join()
        if close_servers:
            for x in self.servers:
                x.disconnect()

    def last_update(self):
        return self.server_update_time

    def stream_generator(self, stream_id=1):
        if stream_id < 1 or stream_id > 255:
            raise ValueError("Stream id is invalid")
        if stream_id in self.recv_queues:
            raise ValueError("A generator for this stream is already open")
        self.recv_queues[stream_id] = collections.deque()
        return self._stream_generator(stream_id)

    def _stream_generator(self, stream_id):
        my_queue = self.recv_queues[stream_id]
        while True:
            value = None
            try:
                value = my_queue.popleft()
            except IndexError:
                pass
            if (yield value) is not None:
                break
        del self.recv_queues[stream_id]

    def _main_client_thread(self):
        try:
            my_last_broadcast = datetime.now() - timedelta(minutes=30)
            while self.going:
                # Check for server broadcasts
                try:
                    data, other = self.udp_sock.recvfrom(1024)
                    if data[0] == common._BROADCAST_IP: # Server broadcasting it's presence
                        server_data = json.loads(data[1:])
                        for address in server_data[1]:
                            if address in self.server_list:
                                self.server_list[address].seen()
                                break
                        else:
                            self.server_update_time = datetime.now()
                            server = Server(self, server_data[0], other[0], server_data[2], server_data[1])
                            for address in server_data[1]:
                                self.server_list[address] = server
                            self.server_list[other[0]] = server
                            self.servers.append(server)
                    else:
                        print(data, file=sys.stderr)
                except socket.error as error:
                    if error.errno != errno.EWOULDBLOCK:
                        raise
                # Query servers
                if datetime.now() - my_last_broadcast > timedelta(seconds=5):
                    self.udp_sock.sendto(common._BROADCAST_REQUEST, ('<broadcast>', self.server_udp_port))
                    my_last_broadcast = datetime.now()

                # Check for dead servers
                dead = [server for server in self.servers if server.has_expired()]
                for server in dead:
                    for address in server.addresses:
                        del self.server_list[address]
                    del self.server_list[server.address]
                    self.servers.remove(server)
                    self.server_update_time = datetime.now()

                # Sleepy time
                time.sleep(1./20)
        finally:
            self.going = False

class Server(object):
    def __init__(self, client, name, address, ports, addresses):
        self.client = client
        self.name = name
        self.address = address
        self.ports = ports
        self.addresses = addresses
        self.last_seen = datetime.now()
        self.connected = False
        self.sock = None
        self.thread = None
        # Queues
        self.out_buffer = ""

    def seen(self):
        self.last_seen = datetime.now()

    def has_expired(self):
        if self.connected:
            self.seen()
        return datetime.now() - self.last_seen > timedelta(minutes=1)

    def connect(self):
        if self.connected:
            return
        if self.thread:
            self.thread.join()
        self.connected = True
        self.thread = threading.Thread(None, Server._connection_thread, "Server connection", [self])
        self.thread.start()

    def is_connected(self):
        return self.connected

    def disconnect(self):
        if not self.connected:
            return
        self.connected = False
        self.thread.join()

    def send_to_stream(self, message, stream_id=1):
        if stream_id < 1 or stream_id > 255:
            raise ValueError("Stream id is invalid")
        if chr(0) in message:
            raise ValueError("There is no support for null characters on the stream.")
        if not self.connected:
            raise Exception("The socket is closed.")
        self.out_buffer += chr(stream_id) + message + chr(0)

    def _connection_thread(self):
        # TODO: Connect using alternate addresses if possible.
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.address, self.ports[1]))
            self.sock.settimeout(0.1)
            in_buffer = ""
            self.out_buffer = ""
            while self.connected:
                try:
                    message = self.sock.recv(1024)
                    if not message:
                        break
                    in_buffer += message
                except socket.timeout:
                    pass
                except socket.error as e:
                    if e.errno == errno.EWOULDBLOCK:
                        pass
                    else:
                        raise
                while chr(0) in in_buffer:
                    message, in_buffer = in_buffer.split(chr(0), 1)
                    mess_id = ord(message[0])
                    if mess_id in self.client.recv_queues:
                        self.client.recv_queues[mess_id].append((self, message[1:]))
                if self.out_buffer:
                    sent = self.sock.send(self.out_buffer)
                    self.out_buffer = self.out_buffer[sent:]
        finally:
            self.connected = False
            self.sock.close()


if __name__ == '__main__':
    client = Client()
    update = client.last_update()
    try:
        client.start()
        loop_count = 0
        iterators = [client.stream_generator(stream_id=sid) for sid in xrange(1, 11)]
        while True:
            time.sleep(.1)
            if update < client.last_update():
                update = client.last_update()
                print([(x.name, x.last_seen) for x in client.servers])
                for x in client.servers:
                    x.connect()
            loop_count += 1
            if not loop_count % 10:
                for server in client.servers:
                    if server.is_connected():
                        for x in xrange(1, 11):
                            server.send_to_stream("Testing Channel " + str(x), stream_id=x)
                    else:
                        server.connect()
            for iterate in iterators:
                for x in iterate:
                    if x is None:
                        break
                    print(x)
    finally:
        client.stop()