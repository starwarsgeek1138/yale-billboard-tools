### THIS CODE FINDS THE TOTAL NUMBER OF ENTROPY-BOUNDED abstractLoopsDirectory IN THE CORPUS (eliminating nested abstractLoopsDirectory/loops) using the entropy output (original .csv ngram abstractLoopsDirectory output - aka abstractLoopsDirectory file) and the analysis of the files (entropyStats_ files aka analysis file)

import mcgilldata, methods, functions, os, string, music21, sys, time, json, csv, collections, math, fractions, operator, pickle, re
from time import *
from mcgilldata import *
from methods import *
from functions import *

mcgillPath = 'mcgill-billboard' #define path for McGill Corpus Methods and Files
csvPath = 'csv-results/entropyResults'  #define path of csv files
testMode = False
outputLoopsDict = dict() #Dictionary of loops (per individual analysis file) for output
outputLicksDict = dict() #Dictionary of licks (per individual analysis file) for output
allFilesLoops = dict() #Dictionary to keep track of loops across multiple files

##########################
#########METHODS##########
##########################

###METHOD TO ABSTRACT EACH LICK FROM OUTPUT FILES INTO AN NGRAM
def abstractLicks (lick, theCorpus, triadMode, beatMode, formMode):
    analysisLick = lick
    prevRoot = 0
    absLick = ''
    firstChord = True
    for chord in analysisLick: 
        #Get rid of blank chords
        if chord == '':
            continue
        #abstract chord
        absChord = methods.absChord(theCorpus, chord, prevRoot, beatMode, formMode, triadMode)
        #Control for the first chord of a lick having a different starting interval
        if firstChord == True:          
            absChordString = '.' + str(absChord[3])
            absLick = absChordString
            firstChord = False
        else:
            absChordString = str(absChord[1]) + '.' + str(absChord[3])
            absLick = absLick + '_' + absChordString
        #Reset previous root to equal current chord
        prevRoot = absChord[2]
    return absLick

#METHOD TO ITERATE THROUGH ROWS of ENTROPY abstractLoopsDirectory OUTPUT AND CREATE DIRECTORY OF ABSTRACT LOOPS and corresponding abstractLoopsDirectory
def loopDictCreate (licksFileName, functions, testMode, mcgillPath):
    abstractLoopsDirectory = dict()
    licksFile = open(licksFileName, 'r', newline = '').read().splitlines()
    variables = licksFile[-1].split(',')
    #extract keymode, triadmode, beatmode, formmode
    kMode = variables[0].split(' ')[1] 
    tMode = variables[1].split(' ')[1]
    bMode = variables[2].split(' ')[1]
    fMode = variables[3].split(' ')[1] 
    #Identify and re-format variables for each analysis file (for song chord list propagation later)
    keyMode = functions.boolean(kMode)
    triadMode = int(tMode)
    beatMode = functions.boolean(bMode)
    formMode = functions.boolean(fMode)
    theCorpus = mcgillCorpus(mcgillPath, triadMode, keyMode, testMode)
    #Identify row index for specific variables from header titles in licks output file
    header = licksFile[0].split(',')
    progIDIndex = header.index('progID')
    sortedSongsIndex = header.index('Sorted Songs')
    absLoopIndex = header.index('LoopAbs')
    lickIndex = header.index('Lick String')
    lickLengthIndex = header.index('Prog Length')
    lickTotalIndex = header.index('Prog Count')
    formIndex = header.index('Forms')
    #Propagate dictionary based on these variables (includes abstract form as key, values are prodID, songs, and lick)
    for row in licksFile[1:-1]: #ignores header and footer rows
        row = row.split(',')
        absLoop = row[absLoopIndex]
        sortedSongs = row[sortedSongsIndex].split(' ')
        sortedSongs = list(filter(None, sortedSongs))
        progID = row[progIDIndex]
        lickName = row[lickIndex]
        lick = row[lickIndex].split('_')
        lick = list(filter(lambda x:x != '', lick))    #Remove empty objects in lick
        absLick = abstractLicks(lick, theCorpus, triadMode, beatMode, formMode)
        if absLick[0:2] == "._": #Gets rid of opening lick character (created if ">S" marker)
            absLick = absLick[2:]
        length = row[lickLengthIndex]
        total = int(row[lickTotalIndex])
        forms = row[formIndex].split()
        #UPDATE DICTIONARY FOR ABSTRACT LOOP INFORMATION
        if absLoop not in abstractLoopsDirectory:
            abstractLoopsDirectory[absLoop] = dict()
            abstractLoopsDirectory[absLoop]['keyMode'] = keyMode
            abstractLoopsDirectory[absLoop]['formMode'] = formMode
            abstractLoopsDirectory[absLoop]['triadMode'] = triadMode
            abstractLoopsDirectory[absLoop]['beatMode'] = beatMode
            abstractLoopsDirectory[absLoop]['total'] = 0
            abstractLoopsDirectory[absLoop]['progIDs'] = set()
            abstractLoopsDirectory[absLoop]['forms'] = set()
            abstractLoopsDirectory[absLoop]['licks'] = list()
            abstractLoopsDirectory[absLoop]['songs'] = set()
        if absLick not in abstractLoopsDirectory[absLoop]:
            abstractLoopsDirectory[absLoop][absLick] = dict()
            abstractLoopsDirectory[absLoop][absLick]['total'] = 0
            abstractLoopsDirectory[absLoop][absLick]['progIDs'] = set()
            abstractLoopsDirectory[absLoop][absLick]['forms'] = set()
            abstractLoopsDirectory[absLoop][absLick]['songs'] = set()
            abstractLoopsDirectory[absLoop][absLick]['testSongs'] = set()
            abstractLoopsDirectory[absLoop][absLick]['length'] = len(absLick.split('_'))
        abstractLoopsDirectory[absLoop][absLick]['forms'].update(forms)
        abstractLoopsDirectory[absLoop][absLick]['progIDs'].add(int(progID))
        abstractLoopsDirectory[absLoop][absLick]['testSongs'].update(sortedSongs)   
        abstractLoopsDirectory[absLoop]['progIDs'].add(int(progID))
        abstractLoopsDirectory[absLoop]['forms'].update(forms)
        abstractLoopsDirectory[absLoop]['licks'].append(absLick)
        abstractLoopsDirectory[absLoop]['licks'].sort(key = len, reverse = True)
    return abstractLoopsDirectory, keyMode, triadMode, beatMode, formMode, total, theCorpus

#METHOD TO ITERATE THROUGH CORPUS AND CREATE DICTIONARY OF SONGS FOR COMPARISON 
#Needs to be done for each file since it's triadMode/keyMode dependent
def songDirectory (triadMode, keyMode, beatMode, formMode, theCorpus):
    songDict = dict()
    if keyMode not in songDict:
        songDict[keyMode] = dict()
    if triadMode not in songDict[keyMode]:
        songDict[keyMode][triadMode] = dict()
    for theSongID, theSong in theCorpus.songs.items():
        if theSongID not in songDict[keyMode][triadMode]:
            songDict[keyMode][triadMode][theSongID] = dict()
        songDict[keyMode][triadMode][theSongID]['chords'] = theSong.chordsFlat
        chords = theSong.chordsFlat
        #Create lists of pruned lists for each song based on beatMode and formMode
        if formMode == True:
            if beatMode == True: 
                songDict[keyMode][triadMode][theSongID]['FBPruned'] = methods.chordPrune(theCorpus, chords, beatMode, formMode, triadMode)[0]
            else:
                songDict[keyMode][triadMode][theSongID]['FPruned'] = methods.chordPrune(theCorpus, chords, beatMode, formMode, triadMode)[0]
        else:
            if beatMode == True: 
                songDict[keyMode][triadMode][theSongID]['BPruned'] = methods.chordPrune(theCorpus, chords, beatMode, formMode, triadMode)[0]
            else:
                songDict[keyMode][triadMode][theSongID]['Pruned'] = methods.chordPrune(theCorpus, chords, beatMode, formMode, triadMode)[0]            
    return songDict
    
#METHOD TO CONVERT SONGS TO ABSTRACTED NGRAM LIST (Root Interval Distances + Quality)
#Returns a list of chords in interval.quality format
def absSongNgramFinder (theSongID, songDict, theCorpus, keyMode, beatMode, formMode, triadMode):     
    ###create mList copy of song chords from songDict for finding absLoop within    
    if formMode == True:
        fName = 'F'
    else:
        fName = ''
    if beatMode == True:
        bName = 'B'
    else:
        bName = ''
    bfMode = str(fName + bName + 'Pruned')
    analysisChords = songDict[keyMode][triadMode][theSongID][bfMode]
    transAnalysisChords= methods.transToC(theCorpus, analysisChords, beatMode, formMode) #transposes to C based on first chord of song
    songNgram = methods.ngramCreate(theCorpus, transAnalysisChords) #Create songNgram
    prevRoot = ''
    absSongNgram = list() #create abstracted songNGram
    for chord in songNgram:
        #Delete starting and ending markers
        if chord == '>S' or chord == '>E':
            continue
        #Convert chord to abstracted chord
        absChord = methods.absChord(theCorpus, chord, prevRoot, beatMode, formMode, triadMode)
        absChordString = str(absChord[1]) + '.' + str(absChord[3])
        absSongNgram.append(absChordString)
        #Reset previous chord 
        prevRoot = absChord[2]
    #Add '0' as initial interval for first song chord:    
    absSongNgram[0] = '0' + absSongNgram[0]
    songNgramList = ''
    for chord in absSongNgram:
        songNgramList = songNgramList + '_' + chord
    return songNgramList

#METHOD TO COMPARE abstractLoopsDirectory AND SONGS, COUNTING ABSTRACT abstractLoopsDirectory IN EACH SONG
def findLick(absAnalysisLick, analysisSongNgram, absLoop, abstractLoopsDirectory, theSongID, songNgramDict):
    length = len(absAnalysisLick)
    index = analysisSongNgram.find(absAnalysisLick)
    if index == -1:
        found = False
        newSongNgram = analysisSongNgram
    else:
        found = True
        #Delete lick from songNgram
        endIndex = index + length
        begSongNgram = analysisSongNgram[:index]
        newSongNgram = begSongNgram + analysisSongNgram[endIndex:]
        #update directories
        songNgramDict[theSongID] = newSongNgram
        abstractLoopsDirectory[absLoop]['total'] += 1
        abstractLoopsDirectory[absLoop][absAnalysisLick]['total'] += 1
        abstractLoopsDirectory[absLoop]['songs'].add(theSongID)
        abstractLoopsDirectory[absLoop][absAnalysisLick]['songs'].add(theSongID)
    return (newSongNgram, found, songNgramDict, abstractLoopsDirectory)

#############################
##########MAIN CODE##########
#############################
##Iterate through all analysis files in csv results directory, extract data from entropy statistics files (being with 'entropyStats')
for fileName in os.listdir(csvPath):
    if fileName.startswith("entropyStats"):  #Looks at analysis files within directory
        #Create a directory of abstract loops and corresponding abstractLoopsDirectory from the relevant abstractLoopsDirectory file
        licksFileName = fileName[13:]
        entropy = licksFileName.split('_')[5]
        licksFileName = csvPath + '/' + licksFileName #rename file to include csvPath info
        
        #Create directory of loops for each analysis file
        lickStuff = loopDictCreate(licksFileName, functions, testMode, mcgillPath)
        abstractLoopsDirectory = lickStuff[0]
        lickTotal = lickStuff[5]
        
        #Identify and re-format variables for each analysis file (for chord list propagation later)
        keyMode = lickStuff[1]
        triadMode = lickStuff[2]
        beatMode = lickStuff[3]
        formMode = lickStuff[4]
        
        ####CREATE DICTIONARY OF SONGS####
        #Create directory of songs for comparison - these will remain intact through analysis
        theCorpus = lickStuff[6]
        #########################################
        #####LOAD SONG DIRECTORY FROM PICKLE#####
        #########################################
        pickleFilename = 'pickles/mcgillCorpusLoopsAnalysisSongDict_tM' + str(triadMode)+ '_bM'+ str(beatMode) +'_fM'+ str(formMode) +'.pickle'
        if os.path.isfile(pickleFilename):
            sys.stderr.write("getting data from SongDict Tree pickle... ")
            start = time.clock()
            songDict = pickle.load(open(pickleFilename, 'rb'), encoding = 'latin-1')
            sys.stderr.write(str(time.clock()-start) + ' secs\n')                
        else:
            sys.stderr.write("Suffix Tree data pickle not found, recalculating... ")
            start = time.clock()        
            songDict = songDirectory(triadMode, keyMode, beatMode, formMode, theCorpus)
            #Store songDict in pickle 
            pickle.dump(songDict, open(pickleFilename,'wb'))
            sys.stderr.write(str(time.clock()-start) + ' secs\n')
        
        #########################################
        ############SONG COMPARISON##############
        #########################################
        ###A. Load song information from entropy analysis file
        analysisFileName = csvPath + '/' + fileName
        analysisFile = open(analysisFileName, 'r', newline = '').read().splitlines()
        songNgramDict = dict()
        ###B. Create abstract chord list of song for comparison with lick
        for row in sorted(analysisFile[1:], key = lambda row: len(row.split(',')[0]), reverse = True): #Load rows from analysis file based on length of abstract loop (longer loops first)
            row = row.split(',')
            absLoop = row[0]
            found = True
            ###C. Iterate through licks from longest to shortest for representative abstract Loop
            for absLick in sorted(abstractLoopsDirectory[absLoop], key = lambda absLick: len(absLick), reverse = True):
                if absLick[0] != '.':
                    continue
                ###D. Iterate through songs: convert each song to an abstract ngram, and compare with each instantiation of abstract lick 
                for theSongID in sorted(abstractLoopsDirectory[absLoop][absLick]['testSongs']): 
                    #Return ngram in abstract format for each song:
                    if theSongID not in songNgramDict:
                        analysisSongNgram = absSongNgramFinder(theSongID, songDict, theCorpus, keyMode, beatMode, formMode, triadMode)
                        songNgramDict[theSongID] = analysisSongNgram
                    else: 
                        analysisSongNgram = songNgramDict[theSongID]
                    ###############################
                    ##COMPARISON OF LICK AND SONG##
                    ###############################
                    found = True
                    while found == True:
                        #set abstract lick as analysis lick
                        absAnalysisLick = absLick
                        songComparison = findLick(absAnalysisLick, analysisSongNgram, absLoop, abstractLoopsDirectory, theSongID, songNgramDict)
                        analysisSongNgram = songComparison[0]
                        found = songComparison[1]
                        songNgramDict = songComparison[2]
                        abstractLoopsDirectory = songComparison[3]
        ###############################################
        #####OUTPUT ANALYSIS FOR INDIVIDUAL FILES######
        ###############################################
        
        outputList = list()
        #Create spreadsheet header  
        headerRow = list()
        headerRow.append('Abstract Loop')
        headerRow.append('keyMode')
        headerRow.append('triadMode')
        headerRow.append('formMode')
        headerRow.append('beatMode')
        headerRow.append('Loop Total')
        headerRow.append('Loop Total Songs')
        headerRow.append('Loop Song IDs')
        headerRow.append('Loop ProgIDs')
        headerRow.append('Loop Forms')
        headerRow.append('Abstract Lick')
        headerRow.append('Lick Total') 
        headerRow.append('Lick Total Songs')
        headerRow.append('Lick Song IDs')
        headerRow.append('Lick Forms')
        headerRow.append('Lick Length')

        outputList.append(headerRow)
        sumAbstractLicks = 0
        
        for abstractLoop in abstractLoopsDirectory:
            for abstractLick in sorted(abstractLoopsDirectory[abstractLoop], key = lambda abstractLick: len(abstractLick), reverse = True):
                if abstractLick[0] != '.':
                    continue
                if abstractLoopsDirectory[abstractLoop][abstractLick]['total'] == 0:
                    continue
                
                
                sumAbstractLicks += 1
                
                ###populate row information for loop
                outputRow = list()
                songList = ''
                progList = ''
                formList = ''
                songList2 = ''
                formList2 = ''
                outputRow.append(abstractLoop)
                outputRow.append(abstractLoopsDirectory[abstractLoop]['keyMode'])
                outputRow.append(abstractLoopsDirectory[abstractLoop]['triadMode'])
                outputRow.append(abstractLoopsDirectory[abstractLoop]['formMode'])
                outputRow.append(abstractLoopsDirectory[abstractLoop]['beatMode'])
                outputRow.append(abstractLoopsDirectory[abstractLoop]['total'])
                outputRow.append(len(abstractLoopsDirectory[abstractLoop]['songs']))
                for song in sorted(abstractLoopsDirectory[abstractLoop]['songs']):
                    songList = songList + " " + song
                outputRow.append(songList)
                for prog in sorted(abstractLoopsDirectory[abstractLoop]['progIDs']):
                    progList = progList + " " + str(prog)
                outputRow.append(progList)
                for form in sorted(abstractLoopsDirectory[abstractLoop]['forms']):
                    formList = formList + " " + form
                outputRow.append(formList)
                
                #Populate lick information
                outputRow.append(abstractLick)
                total = abstractLoopsDirectory[abstractLoop][abstractLick]['total']
                outputRow.append(total)
                outputRow.append(len(abstractLoopsDirectory[abstractLoop][abstractLick]['songs']))
                for song in sorted(abstractLoopsDirectory[abstractLoop][abstractLick]['songs']):
                    songList2 = songList2 + " " + song
                outputRow.append(songList2)
                for form in sorted(abstractLoopsDirectory[abstractLoop][abstractLick]['forms']):
                    formList2 = formList2 + " " + form
                outputRow.append(formList2)
                outputRow.append(abstractLoopsDirectory[abstractLoop][abstractLick]['length'])
                outputList.append(outputRow)
            
        #Populate last row info
        lastRow = list()
        lastRow.append('Total Loops:')
        lastRow.append(len(abstractLoopsDirectory))
        lastRow.append('Total Abs Licks Count:')
        lastRow.append(sumAbstractLicks)
        outputList.append(lastRow)
        #write rows
        fileNameSum = csvPath + '/loopsAnalysis/' + 'loopsAnalysis_' + fileName
        w = csv.writer(open(fileNameSum, 'w'))
        for row in outputList:
            w.writerow(row)                 
    else: 
        continue

