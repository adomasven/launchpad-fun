import threading
import time
import json
from datetime import datetime, timedelta

class SpecialInputReceiver(object):
    def __init__(self, server):
        self.server = server
        self.need_keyboard = False
        self.need_joypad = False
        # Global keyboard set-up
        self.keyboard = {}
        # Global joypad set-up
        self.joypad_button = {}
        self.joypad_hat = {}
        self.joypad_axis = {}
        # Thread stuff
        self.running = False
        self.thread = None
        self.channel = None

    def get_key(self, keycode, default=0):
        try:
            return self.keyboard[keycode]
        except KeyError:
            return default

    def get_joypad_button(self, button_id, default=0):
        try:
            return self.keyboard[button_id]
        except KeyError:
            return default

    def get_joypad_axis(self, axis_id, default=0):
        try:
            return self.keyboard[axis_id]
        except KeyError:
            return default

    def get_joypad_hat(self, hat_id, default=(0, 0)):
        try:
            return self.keyboard[hat_id]
        except KeyError:
            return default

    def start(self):
        if self.running:
            return
        if self.thread is not None:
            self.thread.join()
        self.running = True
        self.thread = threading.Thread(None, SpecialInputReceiver._thread, "", (self, 2))
        self.thread.start()

    def __enter__(self):
        self.start()
        return self

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()

    def __exit__(self, type, val, tb):
        self.stop()

    def set_keyboard(self, need=True):
        self.need_keyboard = need

    def set_joypad(self, need=True):
        self.need_joypad = need

    def _thread(self, stream_id):
        last_broadcast = datetime.now() - timedelta(hours=30)
        with self.server.stream_generator(stream_id=stream_id) as channel:
            while self.running:
                for x in channel:
                    if x is None:
                        break
                    try:
                        obj = json.loads(x[1])
                    except ValueError:
                        continue
                    if "control_type" in obj:
                        self._receive(x[0], obj)
                if datetime.now() - last_broadcast > timedelta(seconds=1):
                    self.server.send_to_stream(json.dumps({
                        "keyboard": self.need_keyboard,
                        "joypad": self.need_joypad,
                    }), stream_id=2)
                    last_broadcast = datetime.now()
                time.sleep(0.1)

    def _receive(self, client_number, value):
        # TODO: none global inputs
        if value["control_type"] == "keyboard":
            # Receive on keyboard
            if value["keypress_type"] == "up":
                self.keyboard[value["key"]] = 0
            else:
                self.keyboard[value["key"]] = 1
        elif value["control_type"] == "joypad":
            if value["joypad_type"] == "button_up":
                self.joypad_button[value["button_id"]] = 0
            elif value["joypad_type"] == "button_down":
                self.joypad_button[value["button_id"]] = 1
            elif value["joypad_type"] == "axis_motion":
                self.joypad_axis[value["axis_id"]] = value["position"]
            elif value["joypad_type"] == "hat_motion":
                self.joypad_hat[value["hat_id"]] = value["position"]

if __name__ == "__main__":
    try:
        from netlink.server import Server
    except ImportError:
        print("Could not import the netlink client. Did you mean to run from the root directory?")
        print("You should run with: python -m remote.specialinputreceiver")
        raise
    with Server() as server:
        with SpecialInputReceiver(server) as inpt:
            inpt.set_keyboard()
            inpt.set_joypad()
            while True:
                print(inpt.keyboard, inpt.joypad_axis, inpt.joypad_button, inpt.joypad_hat)
                time.sleep(0.5)