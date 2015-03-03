#!/usr/bin/env python2.7
import launchpad
import time
import random
from datetime import datetime
import psutil

def display_pattern(x, y, pattern, colour):
    for y_off, line in enumerate(pattern):
        for x_off, cell in enumerate(line):
            c = colour if cell == '1' else (0, 0)
            l.light(x + x_off, y + y_off, c[0], c[1])
        

if __name__=="__main__":
    ls = launchpad.findLaunchpads()
    l = ls[0]
    l = launchpad.Launchpad(*l)
    l.setDrumRackMode()
    l.animation = launchpad.FadeAnimation(l)

    l.reset()

    time.sleep(1)
    green = (0, 3)
    red = (3, 0)

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
        '''event = l.poll()'''
        curtim = datetime.now()
        cpu_usage = psutil.cpu_percent()
        if sec != curtim.second:
            usages = usages[1:] + [cpu_usage]
        for x, usage in enumerate(usages):
            for i in xrange(8):
                l.update((2 if usage > (i*100)/8 else 0, 2 if usage > (i*100)/8 else 0), x, 8-i)

        sec = curtim.second

        for i in xrange(8):
            l.update((0, 0 if cpu_usage < (i*100)/8. else 3), i, 0)
        l.update(roman[curtim.hour % 12], 0, 1, red)
        l.update(digit[curtim.minute / 10], 1, 4, green)
        l.update(digit[curtim.minute % 10], 5, 4, green)
        for i in xrange(6):
            l.update((0 if curtim.second & (0x1 << i) == 0 else 3, 0 if curtim.second & (0x1 << i) == 0 else 3), 8, 5-i)     

        l.animate(0.33)
        