#! /usr/bin/env python3
import json, sys

version = '0.1'
jsonFile = open('stats-8x8:10.json')
data = json.load(jsonFile)
games = None
if data == None:
    data = []
for d in data:
    if d['version'] == version:
        games = d['games']
jsonFile.close()
if games == None:
    print('No info yet')
    sys.exit(0)

wins = 0
ngames = 0
secureInLost = 0
secureInWin = 0
randomsInLost = 0
randomsInWin = 0

for g in games:
    if g["win"]:
        wins += 1
        secureInWin += g["secure"]
        randomsInWin += g["randoms"]
    else:
        secureInLost += g["secure"]
        randomsInLost += g["randoms"]
    ngames += 1

print('Total games:', ngames)
print('Won percent:', wins / ngames)
print('Average guesses by lost game:', (secureInLost + randomsInLost) / ngames)
print('Average guesses by won game:', (secureInWin + randomsInWin) / ngames)
