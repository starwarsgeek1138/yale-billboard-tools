###List of functions used across various scripts (mainly, entropy.py and ngramfinder.py)
import os, string, sys, time, json, csv, collections, math, fractions, operator, music21

###############################################
#######DICTIONARIES USED FOR TRANSLATIONS#######
###############################################
pitchClassTranslate = {
    'C' : 0,
    'B#' : 0,
    'C#' : 1,
    'D-' : 1,
    'D' : 2,
    'E--': 2,
    'D#' : 3,
    'E-' : 3,
    'E' : 4,
    'F-' : 4,
    'E#' : 5, 
    'F' : 5,
    'F#' : 6,
    'G-' : 6,
    'F##' : 7,
    'G' : 7,
    'A--': 7,
    'G#' : 8,
    'A-' : 8,
    'A' : 9,
    'B--' : 9,
    'A#' : 10,
    'B-' : 10,
    'B' : 11,
    'C-' : 11}
    
###############################################
#######FUNCTIONS#######
###############################################
    
def sortTuple(key):
    return key[1]

###FUNCTION TO TURN STRING INTO BOOLEAN
def boolean (mode):
    if mode == "True":
        mode = True
    else:
        mode = False
    return mode

###FUNCTION TO FIND INDEX NUMBER IN A DICTIONARY###
##Finds index number within dictionary given a key and its value (returns index - thing -  of dictionary item with value - i - for certain key)#####################
def findIndex (lst, key, i):
    for thing, dic in enumerate(lst):
        if dic[key] == i:
            return thing
    return -1
    
###FUNCTION TO FIND INTERVAL DISTANCE BETWEEN CHORD ROOTS
def chordDistance(prevRoot, chordRoot):
    if prevRoot == '': 
        chordDist = '' 
    else: 
        if isinstance(prevRoot, int) == True: #control for prevRoot as string or already translated to int)
            x = prevRoot
        else:
            x = int(pitchClassTranslate[prevRoot])
        y = int(pitchClassTranslate[chordRoot])
        chordDist = (y - x) % 12 #find interval distance mod 12
    return chordDist