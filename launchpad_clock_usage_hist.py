#!/usr/bin/env python2.7
from pylaunchpad import launchpad
import time
import random
from datetime import datetime
import psutil

def display_pattern(x, y, pattern, colour):
    for y_off, line in enumerate(pattern):
        for x_off, cell in enumerate(line):
            c = colour if cell == '1' else (0, 0)
            l.light(x + x_off, 8 - y - y_off, c[0], c[1])
        

if __name__=="__main__":
    ls = launchpad.findLaunchpads()
    l = ls[0]
    l = launchpad.launchpad(*l)
    l.setDrumRackMode()

    l.reset()
    #l.ledTest(1)

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

    display_pattern(0, 1, roman[0], red)
    minute = 0
    sec = 0
    usages = [0]*8
    while 1:
        '''event = l.poll()'''
        curtim = datetime.now()
        if sec != curtim.second:
            cpu_usage = psutil.cpu_percent()
            usages = usages[1:] + [cpu_usage]
            for x, usage in enumerate(usages):
                for i in xrange(8):
                    l.light(x, 7-i, 1, 0 if cpu_usage > (i*100)/8. else 1)     
        #if minute != curtim.minute:
        display_pattern(0, 1, roman[curtim.hour % 12], red)
        display_pattern(1, 4, digit[curtim.minute / 10], green)
        display_pattern(5, 4, digit[curtim.minute % 10], green)
        minute = curtim.minute
        for i in xrange(6):
            if sec != curtim.second:
                l.light(8, 5-i, 0 if curtim.second & (0x1 << i) == 0 else 3, 0 if curtim.second & (0x1 << i) == 0 else 3)     
        sec = curtim.second
        time.sleep(0.2)
        continue
        if event and event[2]:
            num += 1
            '''display_pattern(0, 1, roman[num % len(roman)], red)
            display_pattern(1, 4, digit[num % len(digit)], green)
            display_pattern(5, 4, digit[num % len(digit)], green)
            '''
        else:
            time.sleep(0.05)
