#!/usr/bin/env python

from __future__ import division
from datetime import datetime
from time import sleep
from collections import deque
from numpy import ndarray, array
from random import randint, choice
import launchpad

NONE = (0, 0)
WALL = (3, 3)
WALL_ = (3, 2)
TAIL = (0, 3)
TAIL_ = (0, 2)
HEAD = (3, 0)
ITEM = (3, 0)
ITEM_HINT = (1, 0)

class Vector(tuple):
    def __new__(cls, x, y=None):
        if y is not None:
            x = (x, y)
        return super(Vector, cls).__new__(cls, x)
    def __add__(self, other):
        return Vector(self[i] + other[i] for i in xrange(len(self)))
    def __sub__(self, other):
        return Vector(self[i] - other[i] for i in xrange(len(self)))
    def __neg__(self):
        return Vector(-x for x in self)
    @property
    def length(self):
        return sum(abs(i) for i in self)
    @property
    def neighbours(self):
        return [self+UP, self+DOWN, self+LEFT, self+RIGHT]

UP = Vector(1, 0)
DOWN = Vector(-1, 0)
LEFT = Vector(0, -1)
RIGHT = Vector(0, 1)


class World(ndarray):
    def __new__(cls, w=16, h=16, num_items=1):
        obj = array([[NONE] * w for _ in range(h)], dtype=Vector).view(type=World)
        obj.w = w
        obj.h = h
        return obj

    def __array_finalize__(self, obj):
            if obj is None: return
            self.w = getattr(obj, 'w', None)
            self.h = getattr(obj, 'h', None)

    def __init__(self, w=16, h=16, num_items=1):
        self.items = set()
        for i in range(num_items):
            self.gen_item()

    def gen_item(self, rem_item=None):
        if rem_item:
            self.items.remove(rem_item)
        while(1):
            item = Vector(randint(1, self.w-2), randint(1, self.h-2))
            if tuple(self[item]) == NONE:
                self[item] = ITEM
                self.items.add(item)
                break



class Snake(object):
    def __init__(self, pos, direction=RIGHT):
        self.pos = pos
        self._d = direction
        self.length = 2
        self.tail = deque()
        self.neck = TAIL

    @property
    def d(self):
        return self._d
    
    @d.setter
    def d(self, direction):
        if (self._d+direction).length > 0:
            self._d = direction

    def update_world(self, world):
        self.tail.append(self.pos)
        if len(self.tail) > self.length:
            world[self.tail.popleft()] = NONE

        self.pos += self.d
        curCell = tuple(world[self.pos])
        if curCell != NONE and curCell != ITEM:
            return False
        if curCell == ITEM:
            self.length += 1
            world.gen_item(self.pos)
        world[self.pos] = HEAD
        world[self.tail[-1]] = self.neck
        self.neck = TAIL if self.neck == TAIL_ else TAIL_
        return True


def get_viewport(snake, viewport, w, h):
    diff = snake.pos - viewport
    x,y = viewport
    if diff[0] < 3 and x > 0:
        x -= 1
    if diff[0] > 4 and x < w - 8:
        x += 1
    if diff[1] < 3 and y > 0:
        y -= 1
    if diff[1] > 4 and y < h - 8:
        y += 1
    return Vector(x, y)


def add_hints(v, view, world):
    for item in world.items:
        y = item[0] - v[0]
        x = item[1] - v[1]
        if x > 7:
            x = 7
        if x < 0:
            x = 0
        if y > 7:
            y = 7
        if y < 0:
            y = 0
        if tuple(view[y][x]) == NONE:
            view[y][x] = ITEM_HINT

def add_score(l, view, snake):
    for i in xrange(8):
        bit = int(snake.length) & (0x1 << i) != 0
        colour = (1,2) if bit else (0,0)
        l.update(colour, 8, 8-i)

death = [
            [1, 0, 0, 0, 0, 0, 0, 1], 
            [0, 1, 0, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 1, 0, 0], 
            [0, 0, 0, 1, 1, 0, 0, 0], 
            [0, 0, 0, 1, 1, 0, 0, 0], 
            [0, 0, 1, 0, 0, 1, 0, 0], 
            [0, 1, 0, 0, 0, 0, 1, 0], 
            [1, 0, 0, 0, 0, 0, 0, 1]
        ]


def bfs_move(snake, world):
    paths = {snake.pos: (0, [])}
    queue = deque([snake.pos])
    while len(queue):
        pos = queue.popleft()
        dist, path = paths.get(pos)
        for n in pos.neighbours:
            if tuple(world[n]) != NONE and tuple(world[n]) != ITEM:
                continue
            old_dist, old_path = paths.setdefault(n, 
                    (len(world)*len(world[0]), []))
            if dist+1 < old_dist:
                paths[n] = (dist+1, path + [n])
                if n in world.items:
                    return paths[n][1][0] - snake.pos
                queue.append(n)
    del paths[snake.pos]
    try:
        return choice(paths.values())[1][0] - snake.pos
    except IndexError: #empty paths
        return snake.d



def snake(l, w=16, h=16, speed=0.5, ai=True, num_items=1):
    while(1):
        l.reset_state()
        world = World(w, h, num_items)
        world[0] = [WALL, WALL_] * (w//2)
        world[-1] = [WALL, WALL_] * (w//2)
        world[:,0] = [WALL, WALL_] * (h//2)
        world[:,-1] = [WALL, WALL_] * (h//2)
        snake = Snake(Vector(w//2, h//2))
        world[snake.pos] = HEAD
        v = Vector(w//2-3, h//2-3)

        v = get_viewport(snake, v, w, h)
        view = world[v[0]:v[0]+8, v[1]:v[1]+8].tolist()
        add_hints(v, view, world)
        l.update(view, 0, 1)
        l.animate(0)
        sleep(speed)

        while(1):
            s = datetime.now()

            while(1):
                e = l.poll()
                if ai:
                   snake.d = bfs_move(snake, world)
                elif e and e[2]:
                    if e[0] == 0 and e[1] == 8:
                        snake.d = LEFT
                    if e[0] == 1 and e[1] == 8:
                        snake.d = DOWN
                    if e[0] == 2 and e[1] == 8:
                        snake.d = RIGHT
                    if e[0] == 1 and e[1] == 7:
                        snake.d = UP
                if not e:
                    break

            if not snake.update_world(world):
                break #lose condition

            v = get_viewport(snake, v, w, h)
            view = world[v[0]:v[0]+8, v[1]:v[1]+8].tolist()
            add_hints(v, view, world)
            add_score(l, view, snake)
            l.update(view, 0, 1)
            l.animate(0)

            count = 0
            for line in world:
                for x in line:
                    if tuple(x) == TAIL:
                        count += 1

            e = datetime.now()
            sp = speed / (snake.length/16 + 1)
            sp = sp if sp > 0.05 else 0.05 # don't go tooo fast
            if sp - (e-s).microseconds / 10**6 > 0:
                sleep(sp - (e-s).microseconds / 10**6)

        for x in range(3):
            l.update(death, 0, 1, (3, 0))
            l.animate(0)
            sleep(0.3)
            l.animate(0)
            sleep(0.3)

if __name__=="__main__":

    ls = launchpad.findLaunchpads()
    l = ls[0]
    l = launchpad.Launchpad(*l)

    sleep(0.5)
    snake(l, w=32, h=32, speed=0.1, ai=True, num_items=3)
        
