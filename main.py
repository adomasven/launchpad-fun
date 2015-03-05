#!/usr/bin/env python2.7

from __future__ import division
from threading import Thread
import launchpad
from launchpad import TerminateException
from clock import clock
from langtons import langtons_ant
from conway import conway

def event_handler(x, y, press):
    global next_target, args
    if not press:
        return False
    if x == 7 and y == 8:
        next_target = clock
        args = (l,)
        raise TerminateException(0)
    if x == 0 and y == 8 and running_clock:
        next_target = conway
        args = (l,)
        raise TerminateException(1)
    if x == 1 and y == 8 and running_clock:
        next_target = langtons_ant
        args = (l, True, None, ((0, 1), (1, 0), (1, 1)))
        raise TerminateException(2)


ls = launchpad.findLaunchpads()
l = ls[0]
l = launchpad.Launchpad(*l)
l.setDrumRackMode()

cur_thread = None
running_clock = True
next_target = clock
args = (l, )

if __name__=="__main__":
    l.animate()
    l.reset()
    l.event_handler = event_handler

    while 1:
        print next_target
        cur_thread = Thread(target=next_target, args=args)
        running_clock = (next_target == clock)

        next_target = clock #if shit crashes
        args = (l, )

        l.reset_state()
        cur_thread.start()
        cur_thread.join()
