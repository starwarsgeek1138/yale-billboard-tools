###List of methods used across various scripts (mainly, entropy.py and ngramfinder.py)
import os, string, music21, sys, time, json, csv, collections, math, fractions, operator, functions, mcgilldata
from mcgilldata import *
from functions import *
from collections import deque

mcgillPath = 'mcgill-billboard'

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

chordLabelAbstractionTriad = { #lookup table for chord label abstraction (Fully Reduced; triadMode = 0)
    'maj': 'maj',
    'maj7': 'maj',
    'maj6': 'maj',
    '7': 'maj',
    '': 'maj',
    'min': 'min',
    'min7': 'min',  
    'min6': 'min',
    'sus4': 'mct',
    'no3': 'mct',
    'no3': 'mct',
    'dim': 'dim',
    'dim7': 'dim',
    'hdim': 'dim',
    'aug': 'aug' }
    
chordLabelAbstraction7th = { #lookup table for chord label abstraction (including 7ths; triadMode = 7)
    'maj': 'maj',
    'maj7': 'maj7',
    'maj6': 'maj',
    'ma': 'maj',
    '7': '7',
    '': 'maj',
    'min': 'min',
    'min7': 'min7',  
    'min6': 'min',
    'sus4': 'n3',
    'no3': 'n3',
    'no3': 'n3',
    'dim': 'dim',
    'dim7': 'dim',
    'hdim': 'dim',
    'aug': 'aug' }

#######################
###AUX METHODS#########
####################### 

###METHOD TO FIND SIMILAR CHORDS###
#Finds if chords are similar based on beatMode and formMode (and other) variables:
#Chord must be input as dictionary
#Added variables should be input into loop and into method's arguments
def chordSimilarity (self, chord1, chord2, beatMode, formMode):
    chordSame = False
    if beatMode == True and formMode == True:
        if chord1['root'] == chord2['root'] and chord1['quality'] == chord2['quality'] and chord1['beat'] == chord2['beat'] and chord1['form'] == chord2['form']:
            chordSame = True
        else:
            chordSame = False
    elif beatMode == True and formMode == False:
        if chord1['root'] == chord2['root'] and chord1['quality'] == chord2['quality'] and chord1['beat'] == chord2['beat']:
            chordSame = True
        else:
            chordSame = False
    elif beatMode == False and formMode == True:
        if chord1['root'] == chord2['root'] and chord1['quality'] == chord2['quality'] and chord1['form'] == chord2['form']:
            chordSame = True
        else:
            chordSame = False
    elif beatMode == False and formMode  == False:
        if chord1['root'] == chord2['root'] and chord1['quality'] == chord2['quality']:
            chordSame = True
        else:
            chordSame = False
    return chordSame
    
###METHOD FOR PRUNING CHORDS
#Input is chordsFlat (see mcgilldata.py), turns into mList (for prefix/suffix architecture --> used in
#entropy.py and ngramfinder.py
def chordPrune (self, chords, beatMode, formMode, triadMode):
    mList = list() #list of dictionaries
    mListForms = list() #list of forms
    mListBeats = list() #list of beats
    rootDum = '' #dummy to keep track of similar root, qual, beat, form
    qualDum = ''
    beatDum = ''
    formDum = ''
    ##Create mLIST based on triadMode, formMode, beatMode
    for thing in chords:
        newChord = dict()
        if thing['root'] == '>S':
            newChord['pos'] = int(thing['position'])
            newChord['root'] = thing['root']
            newChord['form'] = ''
            newChord['beat'] = ''
            newChord['quality'] = ''
        elif thing['root'] == '>E':
            newChord['pos'] = int(thing['position'])
            newChord['root'] = thing['root']
            newChord['form'] = ''
            newChord['beat'] = ''
            newChord['quality'] = ''
        else:
            newChord['pos'] = int(thing['position'])
            newChord['root'] = thing['root']
            ###Add quality based on triadMode (0 = triad, 1 = no inversions, 2 = full quality, 7 = reduced)
            if triadMode == 0:
                newChord['quality'] = thing['triadQual']
            elif triadMode == 1:    
                newChord['quality'] = thing['splitQual']
            elif triadMode == 2:    
                newChord['quality'] = thing['qual']
            elif triadMode == 7:    
                newChord['quality'] = thing['redQual']
            #Populate mList information (form, beat, quality)
            newChord['form'] = thing['form']
            newChord['beat'] = thing['beat']
        mList.append(newChord)
        
    ####Further prune mList based on triadMode, formMode, beatMode comparison####
    ###Must use copy of mList for comparison since mList will be modified and chords will be deleted - thus, pos and index number may differ and cause an error later in loop 
    from copy import deepcopy
    
    comparisonMList = deepcopy(mList) #create copy of mList for proper chord indexing
    pastChord = comparisonMList[0] #first pastChord dummy variable 
    mListForms.append([pastChord['pos'], pastChord['form']]) 
    mListBeats.append([pastChord['pos'], pastChord['beat']])
    
    #Iterate through rest of mList - prune based on comparison using beatMode and formMode
    for i in range(1, len(comparisonMList)): #starts from chord 1 since i = 0 is the pastChord ('>S') 
        curChordIndex = functions.findIndex(comparisonMList,'pos',i)
        curChord = comparisonMList[curChordIndex]
        chord1 = pastChord
        chord2 = curChord
        #Are chords the same?
        ####METHOD FOR FINDING SIMILARITY BASED ON BEATMODE, FORMMODE
        same = self.chordSimilarity(chord1, chord2, beatMode, formMode)
        ##Prune different chords from final mList##
        if same == True:    #If chord is the same as the last: add beat and form values (check if same/different) to mListForms and mListBeats, prune current chord from mList
            if chord1['form'] != chord2['form']:
                mListForms.append([chord1['pos'], chord1['form']])
            else:
                mListForms.append([chord1['pos'], chord2['pos'], chord1['form'], chord2['form']])
            if chord1['beat'] != chord2['beat']:
                mListBeats.append([chord1['pos'], chord1['beat']])
            else:
               mListBeats.append([chord1['pos'], chord2['pos'], chord1['beat'], chord2['beat']])
            pastChord = curChord
            chordIndex = functions.findIndex(mList, 'pos', i)
            del mList[chordIndex]
        else: # otherwise: Add each form/beat value to mListForms and mListBeats; delete form/beat info as needed
            mListForms.append([curChord['pos'],curChord['form']])
            mListBeats.append([curChord['pos'],curChord['beat']])
            pastChord = curChord
            if formMode == False:
                index = functions.findIndex(mList, 'pos', i)
                del mList[index]['form']
            if beatMode == False :
                index = functions.findIndex(mList, 'pos', i)
                del mList[index]['beat']
    return mList, mListForms, mListBeats, comparisonMList 

#####METHOD TO TRANSPOSE NGRAMS SO THAT FIRST CHORD ROOTED IN "C"##### 
def transToC(self, mList, beatMode, formMode):
    from copy import deepcopy
    transposedNgram = list() #transposedNgram is pruned list of dictionaries (each chord = dictionary)
    first = True #dummy variable for identifying first chord of a song
    newEvent = dict() #create new chord dictionary for transposed replacement 
    for event in mList: #checks for actual chord
        newEvent = deepcopy(event)
        if event['root'] == '>S' or event['root'] == '>E': 
            transposedNgram.append(newEvent)
        else: 
            if first == True:
                firstChordRoot = event['root']
                first = False
                transInterval = pitchClassTranslate[firstChordRoot]
                newEvent['root'] = 'C'
                first = False
            else:
                newRoot = pitchClassTranslate[event['root']] - transInterval
                newChordRoot = ['C','D-','D','E-','E','F','F#','G','A-','A','B-','B'][newRoot]
                newEvent['root'] = newChordRoot
            transposedNgram.append(newEvent)
    return tuple(transposedNgram)
    
####METHOD TO ABSTRACT CHORDS####
##Input must be string entry of a chord (see entropy and ngramfinder)
def absChord(self, testChord, prevRoot, beatMode, formMode, triadMode):
    #Process testChord into chord parameters
    test = testChord.split('.')
    if test[0] == '>S' or test[0] == '>E':
        chordRoot = ''
        chordQual = ''
        prevRoot = ''
        chordBeat = ''
        chordDist = ''
        chordForm = ''
    else:
        chordRoot = test[0]
        chordQual = test[1]
        if beatMode == True:
            if formMode == True:
                chordForm = test[2]
                chordBeat = test[3]
            else:
                chordBeat = test[2]
                chordForm = ''
        else:
            chordBeat = ''
            if formMode == True:
                chordForm = test[2]
            else: 
                chordForm = ''
    #find distance interval from previous chord (if no prevRoot, leave distance blank)
    chordDist = functions.chordDistance(prevRoot, chordRoot)
    chordAbstTuple = (prevRoot, chordDist, chordRoot, chordQual, chordBeat, chordForm)  
    return chordAbstTuple
    
#####METHOD FOR FINDING IF A LICK LOOPS####
#Input must be duple lick (see entropy.py and ngramfinder.py)
def loopProgs(self, lick):
    if lick[0] == '>S':
        if lick[-1] == '>E':
            lick = lick[1:-1]
        else:
            lick = lick[1:]
    elif lick[-1] == '>E':
        lick = lick[0:-1]
    else:            
        lick = lick
    lickLen = int(len(lick))
    lastChord = lick[-1:] ##Last chord info (appended later)
    lastChordSurr = lick[-3:] ##Context for the last chord (appended later)
    for i in range(lickLen):
        testLoop = lick[0:i+1] #find loop to test as subset
        loopLen = len(testLoop) #find test loop length
        testVal = int(int(lickLen) / int(loopLen)) #find divisor of lick/loopLen, rounds down 
        testValRem= lickLen%loopLen #find remainder
        if lick == (testLoop * testVal) + testLoop[0:testValRem]: # if lick = a multiple of the loop (including remainder), then loop is valid loop 
            loop = lick[0:i+1]
            repeats = round(lickLen/float(loopLen), 2)
            break
        else:
            loop = lick
            repeats = 1
    return loop, loopLen, repeats, lastChord, lastChordSurr
    
###METHOD FOR FINDING the normal form of a loop abstraction (see entropy.py and ngramfinder.py)
def loopNormalForm(self, loopChain):
    allLoops = list()
    for i in range(len(loopChain)):
        allLoops.append(deque(loopChain))
        loopChain.rotate(1)
    return sorted(allLoops)[0]

####METHODS FOR CREATING AN NGRAM FROM A LIST OF CHORD DICTIONARIES
def ngramCreate(self, longNgram):
    ngram = list() #create flat list of pruned, transposed chords (strings)
    preChord = ''
    nowChord = ''
    for i in longNgram:
        for j,k in sorted(i.items(), reverse = True):  #dictionary keys are sorted in reverse order so Root and Quality are first
            if j != 'pos': #do not include chord position in ngram
                nowChord = nowChord + '.' + str(k)
            nowChord = nowChord.strip('.')
        #secondary pruning: gets rid of equal chords in ngram (without 'pos' as a comparison variable)
        if preChord == nowChord:
            preChord = nowChord
            nowChord = ''
        else:
           ngram.append(nowChord) #creates ngram (list of chords)
           preChord = nowChord
           nowChord = ''
    return ngram

########IDENTIFY METHODS AS CLASS OBJECTS (SEE mcgilldata.py)  
mcgillCorpus.chordSimilarity = chordSimilarity
mcgillCorpus.transToC = transToC
mcgillCorpus.chordPrune = chordPrune
mcgillCorpus.absChord = absChord
mcgillCorpus.loopProgs = loopProgs
mcgillCorpus.loopNormalForm = loopNormalForm
mcgillCorpus.ngramCreate = ngramCreate