#!/usr/bin/env python2.7

from __future__ import division
import launchpad
import time
import random
from datetime import datetime
import psutil

def resize_board(board, new_pos):
    if new_pos[0] < 0:
        #print("Resize  1")
        new_pos[0] += len(board)
        board = [[0 if x < len(board) else board[x - len(board)][y] for y in xrange(len(board[0]))] for x in xrange(len(board) * 2)]
        #print(board)
    elif new_pos[0] >= len(board):
        #print("Resize 2")
        board = [[0 if x >= len(board) else board[x][y] for y in xrange(len(board[0]))] for x in xrange(len(board) * 2)]
    elif new_pos[1] < 0:
        #print("Resize 3")
        new_pos[1] += len(board[0])
        board = [[0 if y < len(board[0]) else board[x][y - len(board[0])] for y in xrange(len(board[0]) * 2)] for x in xrange(len(board))]
    elif new_pos[1] >= len(board[0]):
        #print("Resize 4")
        board = [[0 if y >= len(board[0]) else board[x][y] for y in xrange(len(board[0]) * 2)] for x in xrange(len(board))]
    else:
        return new_pos, board
    return resize_board(board, new_pos)

def langtons_ant(launchpad_instance, play=False, setup=None, colours=None):
    try:
        #launchpad_instance.animation = launchpad.FadeAnimation(l)
        frame = 0
        green = (0, 3)
        red = (3, 0)
        yellow = (3, 3)
        if colours is not None:
            green, red, yellow = colours
        pos = (4, 4, 0)
        speed = 0.05
        s_pos = [0, 0]

        board = [[0 for x in xrange(8)] for y in xrange(8)]
        if setup is not None:
            frame, board, pos = setup

        while 1:
            event = launchpad_instance.poll()
            if event and event[2] == True:
                x, y, press = event
                if y == 8:
                    if x == 7:
                        print(frame, board, pos)
                        return
                    elif x == 6:
                        play = not play
                    elif x == 5:
                        speed /= 2
                    elif x == 4:
                        speed *= 2
                    elif x == 3:
                        s_pos[1] += 1
                    elif x == 2:
                        s_pos[1] -= 1
                    elif x == 1:
                        s_pos[0] += 1
                    elif x == 0:
                        s_pos[0] -= 1
                elif y < 8 and x < 8:
                    x = x + s_pos[1]
                    y = (7 - y) + s_pos[0]
                    new_pos, board = resize_board(board,[y, x])
                    board[new_pos[0]][new_pos[1]] = not board[new_pos[0]][new_pos[1]]
                    pos = (pos[0] + new_pos[0] - y, pos[1] + new_pos[1] - x, pos[2])
                    s_pos = [s_pos[0] + new_pos[0] - y, s_pos[1] + new_pos[1] - x]
            if play:
                board[pos[0]][pos[1]] = not board[pos[0]][pos[1]]
                new_pos = list(pos)
                if pos[2] == 0: # Up 
                    new_pos[1] -= 1
                elif pos[2] == 1: # Right
                    new_pos[0] = new_pos[0] + 1
                elif pos[2] == 2:
                    new_pos[1] = new_pos[1] + 1
                elif pos[2] == 3:
                    new_pos[0] -= 1
                # Enlarge the board!
                new_pos, board = resize_board(board, new_pos)
                # Move the view
                if new_pos[0] - s_pos[0] > 5:
                    s_pos[0] = new_pos[0] - 5
                if new_pos[0] - s_pos[0] < 2:
                    s_pos[0] = new_pos[0] - 2
                if new_pos[1] - s_pos[1] > 5:
                    s_pos[1] = new_pos[1] - 5
                if new_pos[1] - s_pos[1] < 2:
                    s_pos[1] = new_pos[1] - 2
                # Control direction
                if not board[new_pos[0]][new_pos[1]]: # Turn Counter Clockwise
                    new_pos[2] = new_pos[2] - 1
                    if new_pos[2] == -1:
                        new_pos[2] += 4
                else: # Clockwise
                    new_pos[2] = (new_pos[2] + 1) % 4
                pos = tuple(new_pos)
                frame += 1
            launchpad_instance.update([[1]], 6, 0, (0 if play else 3, 3 if play else 0))
            launchpad_instance.update([[False if x < 0 or y < 0 or x >= len(board) or y >= len(board[0]) else board[x][y] for y in xrange(s_pos[1], s_pos[1] + 8)] for x in xrange(s_pos[0], s_pos[0] + 8)], 0, 1, green)
            launchpad_instance.update([[False if x < 0 or y < 0 or x >= len(board) or y >= len(board[0]) else board[x][y] is False for y in xrange(s_pos[1], s_pos[1] + 8)] for x in xrange(s_pos[0], s_pos[0] + 8)], 0, 1, yellow)
            p_diff = (pos[0] - s_pos[0], pos[1] - s_pos[1])
            if p_diff[0] >= 0 and p_diff[0] < 8 and p_diff[1] >= 0 and p_diff[1] < 8:
                launchpad_instance.update([[1]], p_diff[1], p_diff[0] + 1, red)
            launchpad_instance.animate(speed)
    except KeyboardInterrupt:
        print(frame, board, pos)
        raise


if __name__=="__main__":
    ls = launchpad.findLaunchpads()
    l = ls[0]
    l = launchpad.Launchpad(*l)
    l.setDrumRackMode()

    time.sleep(1)
    try:
        langtons_ant(l, False, input(), [(0, 1), (1, 0), (1, 1)])
    except KeyboardInterrupt:
        pass
