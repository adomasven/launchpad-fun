#!/usr/bin/env python2.7
"""Python interface for Novation Launchpads

Requires pyPortMidi from http://alumni.media.mit.edu/~harrison/code.html
But that version doesn't compile on a modern python without patching. You
can instead use pyGame's MIDI support which is more up to date.

TODO:
    LED double-buffering and flashing
"""

from __future__ import division
import datetime
from time import sleep
from threading import Thread
from copy import deepcopy
from collections import deque
from random import randint

try:
    import pypm
except ImportError:
    from pygame import pypm


class TerminateException(Exception):
    pass


class LaunchPadError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def findLaunchpads():
    ins = []
    outs = []
    for loop in range(pypm.CountDevices()):
        interf,name,inp,outp,opened = pypm.GetDeviceInfo(loop)
        if name.startswith("Launchpad"):
            if inp:
                ins.append(loop)
            else:
                outs.append(loop)
    return zip(ins,outs)


class Frame(list):
    def __init__(self, x=9, y=9):
        self.extend([(0, 0)] * x for _ in range(y))
    def __getitem__(self, key):
        try:
            return super(Frame, self).__getitem__(key)
        except TypeError:
            return self[key[1]][key[0]]
    def __setitem__(self, key, val):
        try:
            super(Frame, self).__setitem__(key, val)
        except TypeError:
            self[key[1]][key[0]] = val
    def diff_update(self, other):
        for x in range(len(other[0])):
            for y in range(len(other)):
                r = g = 0
                if other[y][x][0] != self[y][x][0]:
                    r = -1 if self[y][x][0] > other[y][x][0] else 1
                if other[y][x][1] != self[y][x][1]:
                    g = -1 if self[y][x][1] > other[y][x][1] else 1
                if r != 0 or g != 0:
            #        print x,y,(r,g), self[y][x]
                    self[y][x] = (self[y][x][0]+r, self[y][x][1]+g)


class Animation(object):
    def __init__(self, launchpad, x=0, y=0, w=9, h=9, time=None):
        self.l = launchpad
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.time = time

    def transition(self, next_frame=None, frame=None, time=0, exclude=list()):
        next_frame = next_frame or self.l.next_frame
        frame = frame or self.l.frame
        for y in range(self.y, self.h):
            for x in range(self.x, self.w):
                if frame[(x,y)] != next_frame[(x, y)] and not self.excluded(x,y,exclude):
                    self.l.light((x,y), next_frame[(x,y)])

    def excluded(self, x, y, exclude):
        for e in exclude:
            if e.x <= x < e.x+e.w and e.y <= y < e.y+e.h:
                return True
        return False

    def frames_equal(self, f1, f2):
        for x in range(self.x, self.x+self.w):
            for y in range(self.y, self.y+self.h):
                if f1[(x,y)] != f2[(x,y)]:
                    return False
        return True


class FadeAnimation(Animation):
    def transition(self, next_frame, frame, time=1, exclude=list()):
        time = self.time or time
        s = datetime.datetime.now()
        frame = deepcopy(frame)
        for i in range(4):
            frame.diff_update(next_frame)
            super(FadeAnimation, self).transition(frame)
            e = datetime.datetime.now()
            if time/4 - (e-s).microseconds/1000000/4 > 0:
                sleep(time/4 - (e-s).microseconds/1000000/4)


class DrizzleAnimation(Animation):
    def __init__(self, *args, **kwargs):
        self.d = (0, 1)
        self.c = (0, 3)
        self.prob = 100000
        super(DrizzleAnimation, self).__init__(*args, **kwargs)

    def transition(self, next_frame, frame, time=1, exclude=list()):
        #no need to drizzle, same frame
        if self.frames_equal(next_frame, frame): 
            return

        time = self.time or time
        x = self.x if self.d[0] != -1 else self.x + self.w - 1
        y = self.y if self.d[1] != -1 else self.y + self.h - 1
        queue = deque()
        visited = set()
        if self.d[0] == 0:
            queue.extend([(i, y) for i in range(x, x+self.w)])
        if self.d[1] == 0:
            queue.extend([(x, i) for i in range(y, y+self.h)])
        if not (self.d[0] or self.d[1]):
            queue.append((x, y))

        n = len(queue)
        s = 0
        while len(queue):
            if n == len(queue):
                s = datetime.datetime.now()
            n -= 1
            p = queue.popleft()
            if p in visited or not self.inside_bounds(p):
                continue
            if not randint(0,self.prob): #randomly drizzle
                queue.append(p)
            else:
                visited.add(p)
                if self.d[0]:
                    queue.append((p[0] + self.d[0], p[1]))
                if self.d[1]:
                    queue.append((p[0], p[1] + self.d[1]))

                self.l.light(p, self.c)
            
            if n == 0:
                n = len(queue)
                e = datetime.datetime.now()
                if time - (e-s).microseconds/1000000/4 > 0:
                    sleep(time - (e-s).microseconds/1000000/4)

        x = self.x if self.d[0] != -1 else self.x + self.w - 1
        y = self.y if self.d[1] != -1 else self.y + self.h - 1
        queue = deque()
        visited = set()

        if self.d[0] == 0:
            queue.extend([(i, y) for i in range(x, x+self.w)])
        if self.d[1] == 0:
            queue.extend([(x, i) for i in range(y, y+self.h)])
        if not (self.d[0] or self.d[1]):
            queue.append((x, y))

        n = len(queue)
        s = 0
        while len(queue):
            if n == len(queue):
                s = datetime.datetime.now()
            n -= 1
            p = queue.popleft()
            if p in visited or not self.inside_bounds(p):
                continue
            if not randint(0,self.prob): #randomly drizzle
                queue.append(p)
            else:
                visited.add(p)
                if self.d[0]:
                    queue.append((p[0] + self.d[0], p[1]))
                if self.d[1]:
                    queue.append((p[0], p[1] + self.d[1]))

                self.l.light(p, next_frame[p])
            
            if n == 0:
                n = len(queue)
                e = datetime.datetime.now()
                if time - (e-s).microseconds/1000000/4 > 0:
                    sleep(time - (e-s).microseconds/1000000/4)
    def inside_bounds(self, p):
        return self.x <= p[0] < self.x+self.w and self.y <= p[1] < self.y+self.h


class Launchpad:
    _midiIn = None
    _midiOut = None
    _drumrackMode = False

    def __init__(self, idIn, idOut):
        self._midiIn = pypm.Input(idIn)
        self._midiOut = pypm.Output(idOut, 0)

        self.terminate_threads = False

        self.frame = Frame()
        self.next_frame = Frame()
        self.animation = Animation(self)
        self.animations = list()

        self.threads = None

        self.event_handler = lambda x, y, p: False


    def reset(self):
        self._midiOut.WriteShort(0xb0, 0, 0)
        self._drumrackMode = False

    def reset_state(self):
        self.frame = Frame()
        self.next_frame = Frame()
        self.animation = Animation(self)
        self.animations = list()
        self.terminate_threads = True
        for t in threads():
            t.join()
        self.terminate_threads = False

        self.threads = None
        self.reset()


    def setDutyCycle(self, numerator, denominator):
        if numerator < 9:
            data = (16 * (numerator - 1)) + (denominator - 3)
            self._midiOut.WriteShort(0xb0, 0x1e, data)
        else:
            data = (16 * (numerator - 9)) + (denominator - 3)
            self._midiOut.WriteShort(0xb0, 0x1f, data)

    def setDrumRackMode(self, drumrack=True):
        self._drumrackMode = drumrack
        self._midiOut.WriteShort(0xb0, 0, drumrack and 2 or 1)

    def update(self, grid, x=0, y=0, colour=None):
        if colour is None:
            if isinstance(grid, list):
                for i in range(len(grid[0])):
                    for j in range(len(grid)):
                        if grid[j][i] != (0, 0):
                            self.next_frame[(i+x,j+y)] = grid[j][i]
            else:
                if grid != (0, 0):
                    self.next_frame[(x, y)] = grid
        else:
            for i in range(len(grid[0])):
                for j in range(len(grid)):
                    if int(grid[j][i]) == 1:
                        self.next_frame[(i+x,j+y)] = colour


    def animate(self, time=1):
        s = datetime.datetime.now()

        threads = []
        for a in self.animations:
            threads.append(Thread(target=a.transition, args=(self.next_frame, self.frame, time)))
        threads.append(Thread(target=self.animation.transition, args=(self.next_frame, self.frame, time, self.animations)))
        
        if not self.threads:
            self.threads = threads
        for i, t in enumerate(threads):
            if not self.threads[i].is_alive():
                print "wtf"
                self.threads[i] = t
                t.start()
        for t in threads:
            if t.is_alive():
                t.join(time)
        #self.animation.transition(self.next_frame, self.frame, time)

        self.switch_frames()

        e = datetime.datetime.now()
        if time - (e-s).microseconds/1000000 > 0:
            sleep(time - (e-s).microseconds/1000000)
        
        # probably the best place to check if the thread
        # should be terminated, since #animate gets called often
        if self.terminate_threads:
            raise TerminateException

    def switch_frames(self):
        self.frame = self.next_frame
        self.next_frame = Frame()

    def light(self, x, y, red=None, green=None):
        if red is not None:
            pos = (x,y); col = (red, green)
        else:
            pos = x; col = y
        if not 0 <= pos[0] <= 8: 
            raise LaunchPadError("Bad x value {}".format(pos[0]))
        if not 0 <= pos[1] <= 8: 
            raise LaunchPadError("Bad y value {}".format(pos[1]))
        if not 0 <= col[0] <= 3: 
            raise LaunchPadError("Bad red value {}".format(col[0]))
        if not 0 <= col[1] <= 3: 
            raise LaunchPadError("Bad green value {}".format(col[1]))

        velocity = 16*col[1] + col[0] + 8 + 4

        if pos[1]==0:
            if pos[0] != 8:
                note = 104 + pos[0]
                self._midiOut.WriteShort(0xb0,note,velocity)
            return

        if self._drumrackMode:
            if pos[0]==8:
                # Last column runs from 100 - 107
                note = 100 + pos[1];
            elif pos[0]<4:
                note = 64 + pos[0] - 4*pos[1]
            else:
                # Second half starts at 68, but x will start at 4
                note = 92 + pos[0] - 4*pos[1]
        else:
            note = pos[0] + 16*pos[1] - 16

        self._midiOut.WriteShort(0x90,note,velocity)

    def lightAll(self, levels):
        velocity = 0
        for level in self._orderAll(levels):
            red = level[0]
            green = level[1]
            if velocity:
                velocity2 = 16*green + red + 8 + 4
                self._midiOut.WriteShort(0x92, velocity, velocity2)
                velocity = 0
            else:
                velocity = 16*green + red + 8 + 4
        self.light(0,0,levels[0][0][0],levels[0][0][1])

    def _orderAll(self,levels):
        for y in range(8):
            for x in range(8):
                yield levels[x][7-y]
        x = 8
        for y in range(8):
            yield levels[x][7-y]

        y = 8
        for x in range(8):
            yield levels[x][y]



    def lightAllTest(self,r=None,g=None):
        grid = []
        for x in range(9):
            grid.append([])
            for y in range(9):
                if (r==None):
                    grid[x].append( (x%4, y%4) )
                else:
                    grid[x].append( (r%4, g%4) )

        self.lightAll(grid)

    def poll(self):
        if self._midiIn.Poll():
            data = self._midiIn.Read(1);
            [status,note,velocity,extraData] = data[0][0]
            if status == 176:
                y = 8
                x = note - 104
#                print x, y
            elif self._drumrackMode:
                if note>99:
                    x=8
                    y=107-note
                else:
                    x = note % 4
                    y = (note//4)-9
                    if y>7:
                        x += 4
                        y -= 8
            else: # Normal mode
                x = note % 16
                y = 7 - (note // 16)
#            print x,y,velocity==127
            self.event_handler(x,y,velocity==127)
            return x,y,velocity==127
        return None
    
pypm.Initialize()

if __name__=="__main__":
    import time

    launchPads = findLaunchpads()
    l = launchpad(*launchPads[0])

    l.reset()
    l.setDrumRackMode()

    # Wait half a second before exiting to make sure all data has got out.
    time.sleep(.5)

