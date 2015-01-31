#! /usr/bin/env python3

from random import random, shuffle, randint
import sys, math, json, os
# Matrix manipulation
from scipy.linalg import lu, inv
import numpy as np
# colors
from colorama import init, Fore, Back, Style

if len(sys.argv) == 4:
    w, h, mines = [int(i) for i in sys.argv[1:]]
else:
    w, h, mines = [int(i) for i in input('Give width height mines: ').split(' ')]

class Case:
    def __init__(self, x, y):
        self.visible = False;
        self.marked = False; # marked as a mine by the user
        self.minesAround = 0; # -1 -> it's a mine
        self.probOfMine = 0;
        self.neighbors = [] # contain non visible neighbors
        self.x = x
        self.y = y

    def isMine(self):
        return self.minesAround < 0

    # keep only non visible cases
    def refreshNeighbors(self):
        self.neighbors = [i for i in self.neighbors if not i.visible]

    def printCase(self, force=False):
        if not self.visible and not force and not self.marked:
            print('-', end=' ')
        else:
            if self.marked:
                print(Fore.CYAN + Back.MAGENTA + '🏁 ' + Back.WHITE + Fore.BLACK, end='')
            elif self.minesAround == 0:
                print(' ', end=' ')
            elif self.isMine():
                print(Back.RED + Style.BRIGHT + '💣 ' + Style.NORMAL + Back.WHITE, end='')
            else:
                print(str(self.minesAround), end=' ')

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    # I'd prefer not to do that...
    def __hash__(self):
        return self.x+self.y

# Case with a prob of being a mine and operator overload
class GuessCase(Case):
    def __init__(self, case, prob):
        super(GuessCase, self).__init__(case.x, case.y)
        self.prob = prob

    def __le__(self, other):
        return self.prob <= other.prob

    def __str__(self):
        return '('+str(self.x)+','+str(self.y)+';'+str(self.prob)+')'

# remove duplicated and null rows in a matrix
def cleanSystem(a, b):
    a = np.column_stack((a, b))
    bef = len(a)
    #print('Removing 0 from '+str(len(a)))
    a = a[~np.all(a == 0, axis=1)]
    #print(len(a))
    order = np.lexsort(a.T)
    a = a[order]
    diff = np.diff(a, axis=0)
    ui = np.ones(len(a), 'bool')
    ui[1:] = (diff != 0).any(axis=1)
    a = a[ui]
    if len(a) == 0:
        return a, a
    # remove zeros
    end = (a.size / len(a) - 1)
    return a[:,0:end], a[:, end:(end+1)]

class Board:
    def __init__(self, width, height, mines):
        self._randoms = []
        self._mines = mines
        self._foundMines = 0
        self._dirty = False
        self.revealableMines = [] # mines that doesn't have a 100% prob of being a mine
        self.resize(width, height)
        self.generateMines(mines);

    # resize a grid without generating the mines
    def resize(self, width, height):
        self._width = width;
        self._height = height;
        self._dirty = True
        self._array = [ [ Case(i, j) for i in range(width) ] for j in range(height) ]
        self.revealableMines = []
        for row in self._array:
            for c in row:
                self.revealableMines.append(c)
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

    # generate random positions in grid no repetition until list is empty
    def getRandomPos(self):
        if len(self._randoms) == 0 or self._dirty: # gen the randomizer
            self._randoms.clear()
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
        self._foundMines = 0
        self._minesCases = []
        self.guesses = 0 # number of reveals he made
        self.randoms = 0 # number of random guesses
        self.secure = 0 # number of secure guesses
        # reset randomPos
        self._randoms.clear()
        while n > 0:
            x, y = self.getRandomPos()
            n -= 1
            self._array[y][x].minesAround = -1
            self._minesCases.append(self._array[y][x])
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
        print(Back.WHITE + Fore.BLACK, end='')
        for row in self._array:
            for c in row:
                c.printCase()
            print() # new line
        print(Style.RESET_ALL)

    def printSolution(self):
        print(Back.WHITE + Fore.BLACK, end='')
        for row in self._array:
            for c in row:
                c.printCase(True)
            print() # new line
        print(Style.RESET_ALL)

    # Reveal a case and return True is you lost (revealed a mine)
    # reveals adjacent cases when revealing a 0
    def reveal(self, x, y=0):
        if issubclass(type(x), Case):
            r = self._reveal(x.x, x.y)
        else:
            r = self._reveal(x, y)
        self.refreshCases()
        return r

    def _reveal(self, x, y):
        case = self._array[y][x]
        if case.isMine(): # don't enter the loop, we lost :(
            case.visible = True
            return True
        rev = set() # add the cases that must be revealed
        rev.add(case)
        while len(rev) > 0:
            case = rev.pop()
            case.visible = True
            self.revealableMines.remove(case)
            if case.minesAround == 0: # reveal moar
                for c in case.neighbors:
                    if not c.visible: # prevent infinite loop
                        rev.add(c)
        return False

    def refreshCases(self):
        for row in self._array:
            for c in row:
                c.refreshNeighbors();

    # get visible cases that can help determine mines around
    # ignore 0 and invisble case
    def getVisibleCases(self):
        r = []
        for row in self._array:
            for c in row:
                if c.visible and c.minesAround > 0:
                    r.append(c)
        return r

    def getBestGuess(self):
        # best is sorted, we can use that
        best = self.generateProbs()
        a = [best[0]]
        i = 1
        # Stack best choices by getting the best ones
        while i < len(a) and best[i] <= a[0]:
            a.append(best[i])
            i += 1
        # Get randomly one of them
        return a[randint(0, len(a)-1)]

    def generateProbs(self):
        # first get non visible neighbors that can be used for the system
        visi = self.getVisibleCases();
        params = set()
        for v in visi:
            for c in v.neighbors:
                params.add(c)
        #print('params:', len(params))
        params = list(params)

        # container of the system
        # at the end linsys will be like ( [0, 1, 1], 1 )
        sysMat = []
        bVec = []
        for v in visi:
            bVec.append(v.minesAround - sum([1 for p in params if p.marked and p in v.neighbors]))
            sysMat.append([int(p in v.neighbors) for p in params if not p.marked])

        # update params array with non-marked cases only
        params = [p for p in params if not p.marked]

        # stop earlier if possible
        if len(bVec) == 0: # Beginning of the game. Just return a random Case
            #print('First guess')
            return [GuessCase(self._array[randint(0, self._height-1)][randint(0, self._width-1)], self._mines / (self._width * self._height))]

        # look for 100% porb mines in order to discard them when picking random cases
        sumVec = [] # sum of the line
        for i in range(len(bVec)):
            s = sum(sysMat[i])
            if s == bVec[i]: # these are mines!
                for k in range(len(params)):
                    if sysMat[i][k]:
                        if not params[k].marked:
                            self._foundMines += 1
                            params[k].marked = True

        # calc A and b again
        visi = self.getVisibleCases();
        params = set()
        for v in visi:
            for c in v.neighbors:
                params.add(c)
        #print('params:', len(params))
        params = list(params)

        # container of the system
        # at the end linsys will be like ( [0, 1, 1], 1 )
        sysMat = []
        bVec = []
        for v in visi:
            bVec.append(v.minesAround - sum([1 for p in params if p.marked and p in v.neighbors]))
            sysMat.append([int(p in v.neighbors) for p in params if not p.marked])

        # update params array with non-marked cases only
        params = [p for p in params if not p.marked]


        # convert to np.array and remove duplicated rows
        sysMat = np.array(sysMat)
        bVec = np.array([[i] for i in bVec])
        sysMat, bVec = cleanSystem(sysMat, bVec);
        #print('A', sysMat)
        #print('b', bVec)

        # Search for bVec = 0. Theses cases are safe
        # TODO caches safe values and avoid all calcs
        for i in range(len(bVec)):
            if bVec[i] == 0:
                #print('Found a safe Case!')
                self.secure += 1
                return [GuessCase(params[k], 0) for k in range(len(params)) if sysMat[i][k]]

        # look for some magic
        onlyOnes = True # check if the matrix is Ones only

        #print('Revealing with random :(')
        self.randoms += 1
        return [GuessCase(self.revealableMines[randint(0, len(self.revealableMines)-1)], 2)]

    def isOver(self):
        if self._foundMines == self._mines:
            return True
        for c in self._minesCases:
            if c.visible:
                return True
        return False


board = Board(w, h, mines)
board.printSolution()
print('---')
print('Game Start')
print('---')
lost = False
c = board.getBestGuess()
while not lost and not board.isOver():
    print('Revealing', str(c))
    lost = board.reveal(c)
    c = board.getBestGuess()
    board.guesses += 1
    #board.printBoard()
    #input()
if lost:
    print(Back.RED+'Bot lost :('+Style.RESET_ALL)
    board.printSolution()
else:
    print(Back.GREEN+Fore.BLACK+'Bot won :D'+Style.RESET_ALL)
print('---')
print('Guesses: %d, randoms: %d, secured %d'%(board.guesses, board.randoms, board.secure))
print('---')
print('Game End')
print('---')

# Save data for stats
version = '0.1'
stats = 'stats-'+str(board._width)+'x'+str(board._height)+':'+str(board._mines)+'.json'
if os.path.isfile(stats):
    jsonFile = open(stats)
    data = json.load(jsonFile)
else:
    jsonFile = None
    data = None
games = None
if data == None:
    data = []
for d in data:
    if d['version'] == version:
        games = d['games']
if jsonFile != None:
    jsonFile.close()
if games == None:
    obj = { "version": version, "games": [] }
    data.append(obj)
    games = obj["games"]
games.append({ "win": not lost, "randoms": board.randoms, "secure": board.secure })
with open(stats, 'w') as outfile:
    json.dump(data, outfile)
