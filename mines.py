#! /usr/bin/env python3

from random import random, shuffle
import sys, math
import numpy as np

def unique(a):
    order = np.lexsort(a.T)
    a = a[order]
    diff = np.diff(a, axis=0)
    ui = np.ones(len(a), 'bool')
    ui[1:] = (diff != 0).any(axis=1) 
    return a[ui]

if len(sys.argv) == 4:
    w, h, mines = [int(i) for i in sys.argv[1:]]
else:
    w, h, mines = [int(i) for i in input('Give width height mines: ').split(' ')]

class Case:
    def __init__(self):
        self.visible = False;
        self.minesAround = 0; # -1 -> it's a mine
        self.probOfMine = 0;
        self.neighbors = [] # contain non visible neighbors

    def isMine(self):
        return self.minesAround < 0

    # keep only non visible cases
    def refreshNeighbors(self):
        self.neighbors = [i for i in self.neighbors if not i.visible]

    def printCase(self, force=False):
        if not self.visible and not force:
            print('-', end=' ')
        else:
            print('*' if self.isMine() else str(self.minesAround), end=' ')

class Board:
    def __init__(self, width, height, mines):
        self._randoms = []
        self._mines = mines
        self._dirty = False
        self.resize(width, height)
        self.generateMines(mines);

    # resize a grid without generating the mines
    def resize(self, width, height):
        self._width = width;
        self._height = height;
        self._dirty = True
        self._array = [ [ Case() for i in range(width) ] for j in range(height) ]
        self.generateNeighbors()

    # generate the neighbors list for every case
    def generateNeighbors(self):
        for y in range(self._height):
            for x in range(self._width):
                c = self._array[y][x]
                c.neighbors = []
                if x > 0:
                    c.neighbors.append(self._array[y][x-1])
                    if y > 0:
                        c.neighbors.append(self._array[y-1][x-1])
                    if y < self._height-1:
                        c.neighbors.append(self._array[y+1][x-1])
                if x < self._width-1:
                    c.neighbors.append(self._array[y][x+1])
                    if y > 0:
                        c.neighbors.append(self._array[y-1][x+1])
                    if y < self._height-1:
                        c.neighbors.append(self._array[y+1][x+1])
                if y > 0:
                    c.neighbors.append(self._array[y-1][x])
                if y < self._height-1:
                    c.neighbors.append(self._array[y+1][x])

    # generate random positions in grid
    def getRandomPos(self):
        if len(self._randoms) == 0 or self._dirty: # gen the randomizer
            self._randoms = []
            self._dirty = False
            for y in range(self._height):
                for x in range(self._width):
                    self._randoms.append((x, y))
            shuffle(self._randoms)
        return self._randoms.pop()

    # generate the mines for the current board
    # this function must be called only once after a resize
    def generateMines(self, n):
        self._mines =  min(self._width * self._height, n) # limit number of mines
        while n > 0:
            x, y = self.getRandomPos()
            n -= 1
            self._array[y][x].minesAround = -1
            if x > 0:
                if not self._array[y][x-1].isMine():
                    self._array[y][x-1].minesAround += 1
                if y > 0 and not self._array[y-1][x-1].isMine():
                    self._array[y-1][x-1].minesAround += 1
                if y < self._height-1 and not self._array[y+1][x-1].isMine():
                    self._array[y+1][x-1].minesAround += 1
            if x < self._width-1:
                if not self._array[y][x+1].isMine():
                    self._array[y][x+1].minesAround += 1
                if y > 0 and not self._array[y-1][x+1].isMine():
                    self._array[y-1][x+1].minesAround += 1
                if y < self._height-1 and not self._array[y+1][x+1].isMine():
                    self._array[y+1][x+1].minesAround += 1
            if y > 0 and not self._array[y-1][x].isMine():
                self._array[y-1][x].minesAround += 1
            if y < self._height-1 and not self._array[y+1][x].isMine():
                self._array[y+1][x].minesAround += 1

    def printBoard(self):
        for row in self._array:
            for c in row:
                c.printCase()
            print() # new line

    def printSolution(self):
        for row in self._array:
            for c in row:
                c.printCase(True)
            print() # new line

    # Reveal a case and return True is you lost (revealed a mine)
    # reveals adjacent cases when revealing a 0
    def reveal(self, x, y):
        r = self._reveal(x, y)
        self.refreshCases()
        return r

    def _reveal(self, x, y):
        case = self._array[y][x]
        if case.visible:
            return False
        case.visible = True
        case.probOfMine = 0 # TODO
        if case.isMine():
            return True
        if case.minesAround == 0: # Let's reveal more!
            if x > 0:
                self._reveal(x-1, y)
                if y > 0:
                    self._reveal(x-1, y-1)
                if y < self._height-1:
                    self._reveal(x-1, y+1)
            if x < self._width-1:
                self._reveal(x+1, y)
                if y > 0:
                    self._reveal(x+1, y-1)
                if y < self._height-1:
                    self._reveal(x+1, y+1)
            if y > 0:
                self._reveal(x, y-1)
            if y < self._height-1:
                self._reveal(x, y+1)
        return False

    def refreshCases(self):
        for row in self._array:
            for c in row:
                c.refreshNeighbors();

    # get visible cases that can help determine mines around
    # ignore 0 and invisble case
    def getVisibleCase(self):
        r = []
        for row in self._array:
            for c in row:
                if c.visible and c.minesAround > 0:
                    r.append(c)
        return r

    def calcProbs(self):
        visi = self.getVisibleCase()
        params = set()
        for v in visi:
            for c in v.neighbors:
                params.add(c)
        print('params:', len(params))
        params = list(params)
        # M * a = b
        linsys = []
        b = []
        for v in visi:
            b.append(v.minesAround)
            linsys.append([int(p in v.neighbors) for p in params])
        linsys = np.array(linsys)
        b = np.array([[i] for i in b])
        print('M:', linsys)
        print('B:', b)
        sol = GEPP(linsys, b)
        print(linsys)
        print(sol)
        print(b)



board = Board(w, h, mines)
board.printSolution()
print('---')
board.reveal(1, 1)
board.calcProbs()
board.printBoard()
print('---')

