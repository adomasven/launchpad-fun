import time
import pygame
import json
try:
    from netlink.client import Client
except ImportError:
    print("Could not import the netlink client. Did you mean to run from the root directory?")
    print("You should run with: python -m remote.input")
    raise

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((100, 100))
    with Client() as client:
        update = client.last_update()
        pygame.register_quit(client.stop)
        pygame.joystick.init()
        joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
        for joystick in joysticks:
            joystick.init()
        keyboard_receivers = set()
        joypad_receivers = set()
        servers = []
        going = True
        loop_number = 0
        # Control queue is on the 1 stream id
        control_queue = client.stream_generator()
        # Special Input queue is on the 2 stream id
        with client.stream_generator(stream_id=2) as input_queue:
            try:
                while going:
                    time.sleep(.05)
                    if update < client.last_update():
                        update = client.last_update()
                        for server in client.servers:
                            if server in servers:
                                continue
                            print("Found new server: " + server.name)
                            server.connect()
                        servers = client.servers
                    for x in input_queue:
                        if x is None:
                            break
                        try:
                            data = json.loads(x[1])
                        except ValueError:
                            print("Could not read incoming packet: " + x[1])
                            continue
                        if "keyboard" in data:
                            if data["keyboard"]:
                                if x[0] not in keyboard_receivers:
                                    print(x[0].name + " has requested keyboard access")
                                    keyboard_receivers.add(x[0])
                            elif x[0] in keyboard_receivers:
                                print(x[0].name + " has stopped keyboard access")
                                keyboard_receivers.remove(x[0])
                        if "joypad" in data:
                            if data["joypad"]:
                                if x[0] not in joypad_receivers:
                                    print(x[0].name + " has requested joypad access")
                                    joypad_receivers.add(x[0])
                            elif x[0] in joypad_receivers:
                                print(x[0].name + " has stopped joypad access")
                                joypad_receivers.remove(x[0])
                    kb_disc = {server for server in keyboard_receivers if not server.is_connected()}
                    if kb_disc:
                        keyboard_receivers -= kb_disc
                    jp_disc = {server for server in joypad_receivers if not server.is_connected()}
                    if jp_disc:
                        joypad_receivers -= jp_disc
                    disc = kb_disc | jp_disc
                    if disc:
                        print("Servers disconnected: " + ", ".join([x.name for x in disc]))
                    if loop_number % 20 == 0:
                        for server in servers:
                            if not server.is_connected():
                                server.connect()
                        try:
                            server.send_to_stream(json.dumps({
                                "joypads_available": len(joysticks),
                                }), stream_id=2)
                        except:
                            pass
                    for my_event in pygame.event.get():
                        if my_event.type == pygame.QUIT:
                            going = False
                        elif my_event.type == pygame.KEYUP or my_event.type == pygame.KEYDOWN:
                            if not keyboard_receivers:
                                pass#continue
                            my_json = json.dumps({
                                "control_type": "keyboard",
                                "keypress_type": "up" if my_event.type == pygame.KEYUP else "down",
                                "key": my_event.key,
                                "scancode": my_event.scancode,
                                "modifiers": my_event.mod,
                            })
                            for server in keyboard_receivers:
                                if server.is_connected():
                                    server.send_to_stream(my_json, stream_id=2)
                        elif my_event.type in [pygame.JOYAXISMOTION, pygame.JOYBALLMOTION, 
                                pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, pygame.JOYHATMOTION]:
                            info = {
                                    "control_type": "joypad",
                                    "joypad_id": my_event.joy,
                            }
                            if my_event.type == pygame.JOYAXISMOTION:
                                info.update({
                                    "joypad_type": "axis_motion",
                                    "axis_id": my_event.axis,
                                    "position": my_event.value,
                                })
                            elif my_event.type == pygame.JOYHATMOTION:
                                info.update({
                                    "joypad_type": "hat_motion",
                                    "hat_id": my_event.hat,
                                    "position": my_event.value,
                                })
                            elif my_event.type == pygame.JOYBALLMOTION:
                                # TODO: No idea what this has
                                continue
                            elif my_event.type == pygame.JOYBUTTONDOWN or my_event.type == pygame.JOYBUTTONUP:
                                info.update({
                                    "joypad_type": "button_up" if my_event.type == pygame.JOYBUTTONUP else "button_down",
                                    "button_id": my_event.button,
                                })
                            my_json = json.dumps(info)
                            for server in joypad_receivers:
                                if server.is_connected():
                                    server.send_to_stream(my_json, stream_id=2)
                    loop_number += 1
            finally:
                pygame.quit()