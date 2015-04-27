_BROADCAST_IP = '0'
_BROADCAST_REQUEST = '1'

class StreamGenerator(object):
    def __init__(self, stream, close_function):
        self.my_queue = stream
        self.on_close = close_function

    def __iter__(self):
        return self.my_generator

    def __enter__(self):
        self.my_generator = self._stream_generator()
        return self

    def __exit__(self, type, value, tb):
        try:
            self.my_generator.send(0)
        except StopIteration:
            pass

    def _stream_generator(self):
        while True:
            value = None
            try:
                value = self.my_queue.popleft()
            except IndexError:
                pass
            if (yield value) is not None:
                break
        self.on_close[0](*self.on_close[1])