#!/usr/bin/env python2.7
from pylaunchpad import launchpad
import time
import random

if __name__=="__main__":
    ls = launchpad.findLaunchpads()
    l = ls[0]
    l = launchpad.launchpad(*l)
    l.setDrumRackMode()

    l.reset()

    time.sleep(1)

    for i in range(4):
        for j in range(4):
            l.light(i, j, i ,j)
