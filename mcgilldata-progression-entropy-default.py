import string, os, sys, collections, pprint, csv, cProfile, re, mcgilldata, entropytree
from mcgilldata import *
from entropytree import *

#This script will output a table of all progressions above a certain entropy treshold (set in entropy.py).
#(This will derive the most common progressions (> 10 occurrences), with ending H > 0.9, given reduced chord names (no inversions). 
#All values are set by dummy variables:
#testMode = True (parses whole corpus) or False (parses ten first songs)
#keyMode = True (based on tonic key) or False (key-blind: progressions are all transposed to that C M/m = the first chord)
#triadMode = 0 (parses only using triads) or 1 (parses all chord-tones with no inversion tones) or 7 (parses only triads and 7ths); 2 includes all inversion symbols as part of chord (not implemented yet)
#beatMode = True (includes chord Beat info) or False (no beat info included)
#formMode = True (include form value for each chord) or False
#treeDepth - delimits the number of levels created for suffix probability tree
#countThreshold - delimits the size of the count for each case within the suffix tree
#entropyThreshold - delimits how high entropy cut-off should be (default is 0.9)
#probThreshold - delimits how high probability cut-off should be for hash/entropy algorithm (default is 0.5)

##Set default variables
##If change key, triad, beat, or form mode will affect SUFFIXTREE pickle
global keyMode
keyMode = False
global triadMode #Change of triad mode will affect DATA and SUFFIXTREE PICKLE
triadMode = 0
global beatMode
beatMode = False  
global formMode
formMode = False
#####DO NOT CHANGE UNLESS NECESSARY
treeDepth = 20
countThreshold = 20
entropyThreshold = 0
probThreshold = 0.25
testMode = False
singleMode = True#Determines whether only run once or run as automatic mode

mcgillPath = 'mcgill-billboard'
theCorpus = mcgilldata.mcgillCorpus(mcgillPath, triadMode, keyMode, testMode)

###Run in Single Mode (Will only run one value per variable type)
if singleMode:
    ##RUN entropy algorithm
    if keyMode == False:
        theCorpus.findLicksNoKey(keyMode, beatMode, formMode, triadMode, treeDepth, countThreshold, entropyThreshold, probThreshold)
        filename = 'csv-results/entropyResults/ngrams-entropy' + '_noKey' + '_TriadMode' + str(triadMode) + '_BeatMode' + str(beatMode) + '_formMode' + str(formMode) + '_' + str(entropyThreshold) + '_' + str(probThreshold)
    else: 
        theCorpus.findLicks(keyMode, beatMode, formMode, triadMode, treeDepth, countThreshold, entropyThreshold, probThreshold)
        filename = 'csv-results/entropyResults/ngrams-entropy' + '_Key' + '_TriadMode' + str(triadMode) + '_BeatMode' + str(beatMode) + '_formMode' + str(formMode) + '_' + str(entropyThreshold) + '_' + str(probThreshold)
    
    #Output progressions
    outputList = theCorpus.listLicks(keyMode, beatMode, formMode, triadMode, entropyThreshold, probThreshold)

    #Write progressions
    filename = filename + '.csv'
    w = csv.writer(open(filename, 'w'))
    for row in outputList:
        w.writerow(row)

####Run in automatic mode (Will run a range of variables)
else: 
    triadValues = [0, 1, 7] #Add 2 when it is implemented
    for triadMode in triadValues:
        print ('TM', triadMode)
        for beatMode in (True, False):
            print ('bM', beatMode)
            for formMode in (True, False): 
                print ('fM', formMode)
                for ent in range(5,16): #Determine entropy values (default is in increments of .1)
                    entropyThreshold = ent/10
                    print ('ent', entropyThreshold)
                    ##RUN entropy algorithm (Change when implement keymode as True)
                    if keyMode == False:
                        theCorpus.findLicksNoKey(keyMode, beatMode, formMode, triadMode, treeDepth, countThreshold, entropyThreshold, probThreshold)
                        filename = 'csv-results/entropyResults/ngrams-entropy' + '_noKey' + '_TriadMode' + str(triadMode) + '_BeatMode' + str(beatMode) + '_formMode' + str(formMode) + '_' + str(entropyThreshold) + '_' + str(probThreshold)
                    else: 
                        theCorpus.findLicks(keyMode, beatMode, formMode, triadMode, treeDepth, countThreshold, entropyThreshold, probThreshold)
                        filename = 'csv-results/entropyResults/ngrams-entropy' + '_Key' + '_TriadMode' + str(triadMode) + '_BeatMode' + str(beatMode) + '_formMode' + str(formMode) + '_' + str(entropyThreshold) + '_' + str(probThreshold)

                    #Output progressions
                    outputList = theCorpus.listLicks(keyMode, beatMode, formMode, triadMode, entropyThreshold, probThreshold)

                    #Write progressions
                    filename = filename + '.csv'
                    w = csv.writer(open(filename, 'w'))
                    for row in outputList:
                        w.writerow(row)



    