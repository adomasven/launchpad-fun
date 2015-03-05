#!/usr/bin/env python2.7

from __future__ import division
from datetime import datetime
import launchpad
import psutil

def clock(l, show_usage=False):
    l.animation = launchpad.FadeAnimation(l)
    l.animations.append(launchpad.DrizzleAnimation(l,1,4,3,5,0.1)) #drizzle animate numbers
    l.animations.append(launchpad.DrizzleAnimation(l,5,4,3,5,0.1))
    for a in l.animations:
        a.c = (0, 1)
        a.prob = 3    
    green = (0, 3)
    red = (3, 0)
    yellow = (3, 3)
    none = (0, 0)

    roman = [
        ['01010101', '00100101', '01010101'],
        ['00001000'] * 3,
        ['00010100'] * 3,
        ['00101010'] * 3,
        ['00101010', '00101010', '00100100'],
        ['00010100', '00010100', '00001000'],
        ['00101010', '00101010', '00010010'],
        ['01010101', '01010101', '00100101'],
        ['01010101', '01010010', '01010101'],
        ['00101010', '00100100', '00101010'],
        ['00010100', '00001000', '00010100'],
        ['00101010', '00010010', '00101010'],
    ]
    digit = [
        ['111', '101', '101', '101', '111'],
        ['010', '110', '010', '010', '111'],
        ['111', '001', '111', '100', '111'],
        ['111', '001', '011', '001', '111'],
        ['101', '101', '111', '001', '001'],
        ['111', '100', '111', '001', '111'],
        ['111', '100', '111', '101', '111'],
        ['111', '001', '001', '001', '001'],
        ['111', '101', '111', '101', '111'],
        ['111', '101', '111', '001', '001'],
    ]
    num = 0

    sec = 0
    usages = [0]*8
    while 1:
        while 1:
            event = l.poll()
            if event and event[2] == True:
                x, y, press = event
                evt_handler(event)
                if x == 8:
                    yellow = ((yellow[0] - 1)%4, (yellow[1] - 1)%4)
                elif y > 4 and y < 8:
                    red = ((red[0] - 1)%4, 0)
                else:
                    green = (0, (green[1] - 1)%4)
            elif not event:
                break

        curtim = datetime.now()
        
        if show_usage:
            cpu_usage = psutil.cpu_percent()
            if sec != curtim.second:
                usages = usages[1:] + [cpu_usage]
            for x, usage in enumerate(usages):
                for i in xrange(8):
                    col = (int(yellow[0] * 0.7), int(yellow[1] * 0.7)) if usage > (i*100)/8 else none
                    l.update(col, x, 8-i)
            for i in xrange(8):
                l.update((yellow if cpu_usage > (i*100)/8 else none), 8, 8-i)

        sec = curtim.second

        l.update(roman[curtim.hour % 12], 0, 1, red)
        l.update(digit[curtim.minute // 10], 1, 4, green)
        l.update(digit[curtim.minute % 10], 5, 4, green)
        for i in xrange(8):
            mu = curtim.second * 1000000 + curtim.microsecond
            bit = int(mu/60/10**6 * 2**8) & (0x1 << i) != 0
            colour = green if bit else none
            l.update(colour, 7-i, 0)

        l.animate(0.33)
        
