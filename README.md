# Launchpad Fun

Launchpad Fun is a project based off the amazing [pyLaunchpad](https://github.com/rjmunro/pyLaunchpad). It's main purpose is to use the Novation Launchpad as a screen that supports nice animations and very fast refresh rate.

## Requirements

The launchpad controller requires either *pypm* or *pygame* modules for python.

## Features

The features supported are:
- Multi-threaded animations
- Custom button-press handlers
- Custom light handlers
- Double-buffering to minimise the need for redrawing

## Usage

Set up a launchpad

```python
ls = launchpad.findLaunchpads()
l = ls[0]
l = launchpad.Launchpad(*l)
```

Start preparing the buffer:
- Single light
```python
x = 0 #left (range [0 - 8])
y = 0 #top  (range [0 - 8])
r = 3 #red intensity [0 - 3]
g = 1 #green intensity [0 - 3]
l.update((r, g), x, y)
```
- Multiple single coloured lights
```python
grid = ['101', '010', '101'] #drawn top to bottom
col = (3, 0) #all red
l.update(grid, 0, 1, col) #drawing starts at the top left square button
```
- Multiple lights, multiple colours
```python
grid = [[(3, 0), (0, 3)],[(0, 3), (3, 0)]]
l.update(grid, 6, 7) #bottom right on square buttons
```

Call animate
```python
l.animate()
```

Handle button presses
```python
p = l.poll() 
if p: # returns None if no button press
    x, y, pressDown = p
    if pressDown:
        l.update((0, 3), x, 8 - y) #y coordinates are inverted, don't ask why
```

### Other

There are multiple types of animations, e.g.:

```python
l.animation = launchpad.FadeAnimation(l)
l.update(grid, 0, 0)
l.animate(0.5) #the `grid` picture fades in over 0.5 second
```

To find out more, check the examples.


## *main.py*

*main.py* will be kept reasonably functional at all times. It is a program
that combines all other example programs in the repository to convert the launchpad into an interactive clock.

## Remote Control

The *main.py* file has support for networked devices to share their keyboard and/or joypad(s) over the network. In order to run the local service for this on your computer you will need the *pygame* module for python. In the project folder, you should then run:

```shell
python -m remote.input
```