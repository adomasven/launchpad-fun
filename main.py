#!/usr/bin/env python2.7

from __future__ import division
from threading import Thread
from datetime import datetime
from random import randint
import launchpad
from launchpad import TerminateException
from clock import clock
from langtons import langtons_ant
from conway import conway

ls = launchpad.findLaunchpads()
l = ls[0]
l = launchpad.Launchpad(*l)
l.setDrumRackMode()

processes = [
    [7, 8, clock, (l, )],
    [0, 8, conway, (l, )],
    [1, 8, langtons_ant, (l, True, None, ((0, 1), (1, 0), (1, 1)))]
]

def set_process(pid):
    global next_target, args, running_proc
    running_proc = pid
    p = processes[pid]
    next_target = p[2]
    args = p[3]
    l.terminate = True
    raise TerminateException(p)

def event_handler(x, y, press):
    if not press:
        return False
    proc = processes if running_proc == 0 else processes[0]
    for i, p in enumerate(proc):
        if x == p[0] and y == p[1]:
            set_process(pid)
    if x == 8 and y == 0:
        global col_cap, othr_cap
        col_cap, othr_cap = othr_cap, col_cap
        l.frame = launchpad.Frame() #forces redraw


def colour_filter(col):
    global s, switchover
    col = (col[0] if col[0] <= col_cap[0] else col_cap[0],
           col[1] if col[1] <= col_cap[1] else col_cap[1])
    e = datetime.now()
    d = e-s

    if d.seconds/60 > (1 if running_proc == 0 else 0.3):
        s = e
        switchover += 1
        if randint(0, switchover):
            switchover = 0
            pid = randint(0, len(processes)-1)
            if running_proc == 0:
                set_process(pid)
            else:
                set_process(0)
    return col

cur_thread = None
running_proc = 0
next_target = clock
args = (l, )

col_cap = (3, 3)
othr_cap = (1, 1)

s = datetime.now()
switchover = 0

if __name__=="__main__":
    l.animate()
    l.reset()
    l.event_handler = event_handler
    l.colour_filter = colour_filter

    while 1:
        print next_target
        cur_thread = Thread(target=next_target, args=args)

        next_target = clock #if shit crashes
        args = (l, )

        l.reset_state()
        cur_thread.start()
        cur_thread.join()
