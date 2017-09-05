import string, os, sys, collections, pprint, csv, cProfile, re, mcgilldata
from mcgilldata import *
from ngramfinder import *

#This script will output a table of all ngrams with count > countThreshold
#All values are set by dummy variables:
#testMode = True (parses whole corpus) or False (parses ten first songs)
#keyMode = True (based on tonic key) or False (key-blind: progressions are all transposed to that C M/m = the first chord)
#triadMode = 0 (parses only using triads) or 1 (parses all chord-tones with no inversion tones) or 7 (parses only triads and 7ths); 2 includes all inversion symbols as part of chord (not implemented yet)
#beatMode = True (includes chord Beat info) or False (no beat info included)
#formMode = True (include form value for each chord) or False
#countThreshold - delimits the size of the count for each ngram case

##Set default variables
##If change key, triad, beat, or form mode will affect NGRAM pickle
global keyMode
keyMode = False
global triadMode #Change of triad mode will affect DATA and NGRAM PICKLE
triadMode = 0
global beatMode
beatMode = False
global formMode
formMode = False
#####DO NOT CHANGE UNLESS NECESSARY
countThreshold = 10
testMode = True

mcgillPath = 'mcgill-billboard'
theCorpus = mcgilldata.mcgillCorpus(mcgillPath, triadMode, keyMode, testMode)

##RUN ngram algorithm
if keyMode == False:
    theCorpus.findNgramsNoKey(keyMode, beatMode, formMode, triadMode, countThreshold, testMode)
    filename = 'csv-results/nGramResults/ngrams' + '_' +str(countThreshold) + '_noKey' + '_TriadMode' + str(triadMode) + '_BeatMode' + str(beatMode) + '_formMode' + str(formMode)
else: 
    theCorpus.findNgrams(keyMode, beatMode, formMode, triadMode, countThreshold,)
    filename = 'csv-results/nGramResults/ngrams' + '_' +str(countThreshold) + '_Key' + '_TriadMode' + str(triadMode) + '_BeatMode' + str(beatMode) + '_formMode' + str(formMode)
    
#Output progressions
outputList = theCorpus.listNgrams(keyMode, beatMode, formMode, triadMode, countThreshold)

#Write progressions
filename = filename + '.csv'
w = csv.writer(open(filename, 'w'))
for row in outputList:
    w.writerow(row)
    