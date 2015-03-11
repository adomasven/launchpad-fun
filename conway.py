#!/usr/bin/env python2
from __future__ import division

__author__ = 'Albert James Wigmore'

#----------------------------#
#    Conways Game of Life    #
#    Written for Launchpad   #
#----------------------------#


import launchpad
import time
from random import randint
from datetime import datetime

class Game(object):

    def __init__(self, state, infinite_board = True):

        self.state = state
        self.width = state.width
        self.height = state.height
        self.infinite_board = infinite_board

    def step(self, count = 1):

        for generation in range(count):

            new_board = [[False] * self.width for row in range(self.height)]

            for y, row in enumerate(self.state.board):
                for x, cell in enumerate(row):
                    neighbours = self.neighbours(x, y)
                    previous_state = self.state.board[y][x]
                    should_live = neighbours == 3 or (neighbours == 2 and previous_state == True)
                    new_board[y][x] = should_live

            self.state.board = new_board

    def neighbours(self, x, y):

        count = 0

        for hor in [-1, 0, 1]:
            for ver in [-1, 0, 1]:
                if not hor == ver == 0 and (self.infinite_board == True or (0 <= x + hor < self.width and 0 <= y + ver < self.height)):
                    count += self.state.board[(y + ver) % self.height][(x + hor) % self.width]

        return count

    def display(self):
        return self.state.display()

class State(object):

    def __init__(self, positions, width, height):

        active_cells = []

        for y, row in enumerate(positions.splitlines()):
            for x, cell in enumerate(row.strip()):
                if cell == '1':
                    active_cells.append((x,y))

        board = [[False] * width for row in range(height)]

        for cell in active_cells:
            board[cell[1]][cell[0]] = True

        self.board = board
        self.width = width
        self.height = height

    def display(self):
        return [[cell for cell in row]for y, row in enumerate(self.board)]

def board_random():
    pass


def conway(launchpad_instance):
    launchpad_instance.animation = launchpad.FadeAnimation(launchpad_instance)
    stop = False
    while not stop:
        green = (0, 3)
        red = (3, 0)
        glider = """ 110
                     101
                     100 """
        
        death = [[1, 0, 0, 0, 0, 0, 0, 1], [0, 1, 0, 0, 0, 0, 1, 0],
                 [0, 0, 1, 0, 0, 1, 0, 0], [0, 0, 0, 1, 1, 0, 0, 0], 
                 [0, 0, 0, 1, 1, 0, 0, 0], [0, 0, 1, 0, 0, 1, 0, 0], 
                 [0, 1, 0, 0, 0, 0, 1, 0], [1, 0, 0, 0, 0, 0, 0, 1]]
        
    
        random_board = ""
        for x in range(8):
            for y in range (8):
                random_board += str(randint(0,1))
            if x != 7:
                random_board += str("\n")
    
        my_game = Game(State(random_board, width = 8, height = 8))
        k = 0
        
        prev = None
        while True:
            event = launchpad_instance.poll()
            if event and event[2] == True:
                pressx, pressy, press = event
                if pressy ==8:
                    if pressx == 4:
                        break
                    if pressx == 7:
                        stop = True
                        break
    
            current = my_game.step(1)
            launchpad_conway = my_game.display()
            launchpad_instance.update(launchpad_conway, 0, 1, green)
            launchpad_instance.animate(0.3)
            k +=1
    
            if prev == launchpad_conway:
                
                for x in range(3):
                    time.sleep(0.5)
                    launchpad_instance.update(death, 0, 1, red)
                    launchpad_instance.animate(0)
                    time.sleep(0.1)
                    launchpad_instance.update([[False for x in xrange(8)] for y in xrange(8)], 0, 1, green)
                    launchpad_instance.animate(0)
                    time.sleep(0.1)
                    
                time.sleep(0.5)
                break
                
    
            prev = launchpad_conway

if __name__=="__main__":

    ls = launchpad.findLaunchpads()
    l = ls[0]
    l = launchpad.Launchpad(*l)
    l.setDrumRackMode()

    l.reset()

    time.sleep(0.5)
    conway(l)
        
