import socket
import threading
import collections
import time
import json
from datetime import datetime, timedelta
import common
import errno

class Server(object):
    debug = True

    def __init__(self, server_name=socket.gethostname(), udp_port=23456, tcp_port=23456, client_udp=23457):
        self.going = False
        self.server_name = server_name
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.client_udp_port = client_udp
        # Make our UDP socket
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_sock.bind(('', self.udp_port))
        self.udp_sock.setblocking(False)
        # Set broadcast
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Set up our listening TCP
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_sock.bind(('', self.tcp_port))
        self.tcp_sock.listen(64)
        self.tcp_sock.settimeout(0)
        self.main_thread = None
        # Set up our queues
        self.recv_queues = {}
        # Client Storage
        self.clients = []
        super(Server, self).__init__()

    def start(self):
        if self.going:
            return
        self.going = True
        if self.main_thread:
            self.main_thread.join()
        self.main_thread = threading.Thread(None, Server._main_server_thread, "Main server thread", [self])
        self.main_thread.start()

    def __enter__(self):
        self.start()
        return self

    def stop(self):
        if not self.going:
            return
        self.going = False
        self.main_thread.join()

    def __exit__(self, type, value, tb):
        self.stop()

    def stream_generator(self, stream_id=1):
        if stream_id < 1 or stream_id > 255:
            raise ValueError("Stream id is invalid")
        if stream_id in self.recv_queues:
            raise ValueError("A generator for this stream is already open")
        self.recv_queues[stream_id] = collections.deque()
        return common.StreamGenerator(self.recv_queues[stream_id], (Server._close_stream, (self, stream_id)))

    def _close_stream(self, stream_id):
        del self.recv_queues[stream_id]

    def send_to_stream(self, message, stream_id=1, client_id=None):
        if stream_id < 1 or stream_id > 255:
            raise ValueError("Stream id is invalid")
        if chr(0) in message:
            raise ValueError("There is no support for null characters on the stream.")
        if client_id is not None:
            if self.clients[client_id] is not None:
                self.clients[client_id][2].append((stream_id, message))
        else:
            for client in self.clients:
                if client is not None:
                    client[2].append((stream_id, message))

    def _main_server_thread(self):
        try:
            if threading.current_thread() != self.main_thread:
                raise Exception("Don't call this like this!")
            last_broadcast_time = datetime.now() - timedelta(minutes=30)
            info = common._BROADCAST_IP + json.dumps([self.server_name, socket.gethostbyname_ex(socket.gethostname())[2], (self.udp_port, self.tcp_port)])
            while self.going:
                try:
                    # Try the UDP socket
                    data, other = self.udp_sock.recvfrom(1024)
                    if data[0] == common._BROADCAST_REQUEST:
                        self.udp_sock.sendto(info, other)
                    elif Server.debug:
                        print("Received data: ", data)
                except socket.error as err:
                    if err.errno != errno.EWOULDBLOCK:
                        raise err
                # Read the TCP stream
                try:
                    sock, address = self.tcp_sock.accept()
                    the_thread = threading.Thread(None, Server._client_server_thread, "Server client thread", [self, sock, len(self.clients)])
                    self.clients.append((address, the_thread, collections.deque()))
                    the_thread.start()
                except socket.error as err:
                    if err.errno != errno.EWOULDBLOCK:
                        raise
                # Send the server query
                if datetime.now() - last_broadcast_time > timedelta(seconds=5):
                    self.udp_sock.sendto(info, ('<broadcast>', self.client_udp_port))
                    last_broadcast_time = datetime.now()
                time.sleep(1./20)
        finally:
            self.going = False

    def _client_server_thread(self, client, client_number):
        client.settimeout(0.1)
        in_buffer = ""
        out_buffer = ""
        while self.going:
            # Handle incoming message
            try:
                message = client.recv(1024)
                if not message:
                    # Our client has disconnected.
                    break
                in_buffer += message
            except socket.timeout as err:
                pass
            except socket.error as err:
                if err.errno != errno.EWOULDBLOCK:
                    raise
            while chr(0) in in_buffer:
                message, in_buffer = in_buffer.split(chr(0), 1)
                mess_id = ord(message[0])
                if mess_id in self.recv_queues:
                    self.recv_queues[mess_id].append((client_number, message[1:]))

            # Post all outgoing
            while True:
                try:
                    message = self.clients[client_number][2].popleft()
                except IndexError:
                    break
                out_buffer += chr(message[0]) + message[1] + chr(0)
            if out_buffer:
                sent_count = client.send(out_buffer)
                out_buffer = out_buffer[sent_count:]
        self.clients[client_number] = None
        client.close()

if __name__ == "__main__":
    sid = 1
    with Server() as my_server:
        with my_server.stream_generator(stream_id=sid) as it:
            for x in it:
                if x is None:
                    time.sleep(0.5)
                else:
                    print(x)
                    my_server.send_to_stream(x[1], stream_id=sid, client_id=x[0])