import os, string, music21, sys, time, json, csv, collections, math, fractions, operator, pickle
from mcgilldata import *
from methods import *

##This module defines methods for finding ngrams in the corpus (of length 2 to n)
#Requires setting dummy variables in running script (XXXX):
#testMode = True (parses whole corpus) or False (parses ten first songs)
#keyMode = True (based on tonic key) or False (key-blind: progressions are all transposed to that C M/m = the first chord)
#triadMode = 0 (parses only using triads) or 1 (parses all chord-tones) or 7 (parses only triads and 7ths); or 2 (parses all quality including inversion, not implemented yet)
#beatMode = True (includes chord Beat info) or False (no beat info included)
#formMode = True (include form value for each chord) or False (no beat info included)
#countThreshold = number of instances for ngram to be included in output (default is 10)

###NB: All external methods defined in methods.py

###############################################
#######DICTIONARIES USED FOR TRANSLATION#######
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

####################################################################################            
###METHOD FOR FINDING NGRAMS NAIVE TO TONIC/RN (BASED ON CHORD QUALITY AND INTERVAL MOTION ONLY)
##################################################################################################
def findNgramsNoKey(self, keyMode, beatMode, formMode, triadMode, countThreshold, testMode):
    
    ###CREATE SUFFIX TREE###
    self.songIDNgrams = dict()
    self.countThreshold = countThreshold
    self.testMode = testMode
    ########################################
    #########PICKLE #3 #####################
    ########################################
    pickleFilename = 'pickles/mcgillCorpusNgrams.noKey.tM' + str(int(triadMode)) + '.bM'+ str(int(beatMode)) +'.fM'+ str(int(formMode)) + '.pickle'
    if os.path.isfile(pickleFilename):
        sys.stderr.write("getting data from NGram pickle... ")
        start = time.clock()
        self.ngrams, self.songIDNgrams, self.maxLen = pickle.load(open(pickleFilename, 'rb'), encoding = 'latin-1')
        sys.stderr.write(str(time.clock()-start) + ' secs\n')
    else:
        sys.stderr.write("NGram data pickle not found, recalculating... ")
        start = time.clock()        
        self.ngrams = dict()
        self.songIDNgrams = dict()
        self.maxLen = 0
        songNumber = 0
        
        ###CREATE PRUNED LIST OF CHORDS FOR NGRAM FINDING  
        for theSongID, theSong in self.songs.items():
            #Song number counter for running testMode (must delete pickle)
            songNumber += 1
            if testMode == True and songNumber > 2:
                break
            ##############
            prunedList = self.chordPrune(theSong.chordsFlat, beatMode, formMode, triadMode)
            mList = prunedList[0]
            mListOrig = prunedList[3] #original mList without omissions 
            mListForms = prunedList[1]
            mListBeats = prunedList[2]
            songID = str(theSong.songID)
            mListLen = len(mList)
            if mListLen > self.maxLen: #keeps track of longest ngram length
                self.maxLen = mListLen
            
            #ITERATE THROUGH, CREATE LONGNGRAM to SPLIT (into len >= 1)
            #sp = starting point for analyzing ngram
            #ln = total length of ngram
            for ln in range(2, mListLen+1): #length of 2 to mListLen (inclusive)
                self.ngrams[ln] = dict()
                self.ngrams[ln]['total'] = 0
                self.songIDNgrams[ln] = dict()
                for sp in range(0, mListLen): #range of position 0 (first chord) to mListLen (non-inclusive)
                    print (mListLen, sp, ln)
                    if sp >= (mListLen - ln + 1): ##n is length of unit (ngram); adds one in order to account beyond all chords in song (ngram) --> if sp goes beyond, breaks loop 
                        break
                    longNgram = self.transToC(mList[sp:sp+ln], beatMode, formMode)#split song into one ngram based on location/length; transposes to C based on first chord of progression
                    prefixPos = mList[sp+ln-2]['pos'] #dummy variable to find ending position of ngram's prefix
                    suffixPos = mList[sp+ln-1]['pos'] #dummy variable to find ending position of ngram's suffix
                    print (prefixPos, suffixPos)
                    print (mListLen)
                    ngram = list() #create flat list of pruned, transposed chords
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
                    
                    #####NGRAM COUNTER CREATION##### Using prefix + suffix architecture
                    prefix = tuple(ngram[0:-1]) #prefix = all but the last element of ngram
                    suffix = tuple([ngram[-1]]) #suffix = last element of ngram
                    if prefix not in self.ngrams[ln]: #create prefix entry if not in dictionary
                        self.ngrams[ln][prefix] = dict()
                        self.ngrams[ln][prefix]['total'] = 0 
                        self.songIDNgrams[ln][prefix] = dict() #dict to keep track which songs this ngram appears in
                    if suffix in self.ngrams[ln][prefix]:
                        self.ngrams[ln][prefix][suffix] += 1 #adds one to number of times suffix follows the prefix
                        #script to encode the formal part in which a suffix chord occurs and if it's at a formal boundary
                        print (suffixPos)
                        print(mListForms)
                        suffixChordForm = mListForms[suffixPos]
                        suffixChordBeat = mListBeats[suffixPos]
                        prefixChordForm = mListForms[prefixPos]
                        #Add 'T' to list to denote that there is a form boundary between prefix and suffix chords
                        if suffixChordForm[1] == prefixChordForm[1]:
                            self.songIDNgrams[ln][prefix][suffix].add(songID +'.'+ str(suffixChordForm[1]))
                        else: #add True for boundary
                            self.songIDNgrams[ln][prefix][suffix].add(songID +'.'+ str(prefixChordForm[1])+str(suffixChordForm[1])+'.T')
                    else:
                        self.ngrams[ln][prefix][suffix] = 1 
                        self.songIDNgrams[ln][prefix][suffix] = set()
                        #script to encode the formal part in which a suffix chord occurs and if it's at a formal boundary
                        suffixChordForm = mListForms[suffixPos]
                        suffixChordBeat = mListBeats[suffixPos]
                        prefixChordForm = mListForms[prefixPos]
                        #Add 'T' to list to denote that there is a form boundary between prefix and suffix chords
                        if suffixChordForm[1] == prefixChordForm[1]:
                            self.songIDNgrams[ln][prefix][suffix].add(songID +'.'+ str(suffixChordForm[1]))
                        else:
                            self.songIDNgrams[ln][prefix][suffix].add(songID +'.'+ str(prefixChordForm[1])+str(suffixChordForm[1])+'.T')
                            
                    self.ngrams[ln][prefix]['total'] += 1 
                    self.ngrams[ln]['total'] += 1
        
        ########################################
        #########WRITE PICKLE #3 ###############
        ########################################
        pickle.dump([self.ngrams, self.songIDNgrams, self.maxLen], open(pickleFilename,'wb'))
        sys.stderr.write(str(time.clock()-start) + ' secs\n')

###################################################################
###METHOD FOR TRAVERSING NGRAM LIST AND CREATING OUTPUT###
###################################################################
def traverseNgramList (self, lick, outputList, beatMode, formMode, triadMode):

    print ("I'm here")    
    print (lick)

    ##################################################
    ######CALCULATIONS FOR TABLE OUTPUT###############
    ##################################################      
    n = len(lick)
    print ('*', n)
    
    #Print lick sorted backward
    revSortString = '' 
    for i in reversed(lick):
        revSortString += i
        
    #########COUNT EXCEEDS THRESHOLD, PROPAGATE ROW NFORMATION#########
    from collections import deque
    #dummy variables to keep track of previous & last chords, etc.
    prevRoot = ''
    lastChordInfo = ''
    sortedSongs = ''
    sortedForms = ''
    
    ####A. PROGRESSION CASE ID####
    self.nGramCounter += 1
    
    ####H-K. LICK'S SONG/FORM INFORMATION ###############
    #####METHOD TO GET SONGID INFORMATION####
    def songIDinfo(lick, n):
        ### create dicts that calls list of duplicates from RockPop-DupSongID.csv 
        dupSongID = dict()
        dupSongNum = dict()      
        dupSongOthers = dict()
        theReader = csv.reader(open('RockPop-DupSongID.csv', 'rU'))
        for row in theReader:
            dupSong = json.loads(row[1]) #identifies token duplicated ID
            dupSongID[row[0]] = dupSong #Finds duplicate (in row[0]) and translates to a token ID (from row[1])
            dupSongNum[row[0]] = row[2] #Number of total duplicated songs there are
            dupSongOthers[row[0]] = row[3] #Lists the other duplicated songs
        #Define set of songs for the lick
        lickSongs = set() #Set of total songs in which lick appears controlled for duplicates (duplicate songs included only once)
        songsCounter = set() #Set of total songs in which the lick appears (including duplicated songs counted as they appear)
        singleSongs = set() #Set of non-duplicated songs in which the lick appears (if a song is duplicated in corpus, not included here)
        dupSongs = set() #Set of duplicate songs in which lick appears (includes duplicates only for reference)
        songForms = set() #Set of form letters in which lick appears
        songFormRef = set() #Set of songs and forms in which lick appears
        formBound = dict()
        for s in sorted(self.songIDNgrams[n][lick[0:-1]][lick[-1:]]):
            #split songID from the formal marker, add to counter
            newS = s.split('.')
            sID = newS[0]
            sForm = newS[1]
            try:
                changeForm = newS[2] #dummy variable to track if suffix changes form from prefix
            except: 
                changeForm = 'F' 
            songsCounter.add(sID)
            songForms.add(sForm)
            #Add song+form for reference
            #identify if song is a duplicate using dupSongID dictionary
            if sID in dupSongID: #if song in duplicates dictionary: find other corresponding duplicates & add it to duplicates counter
                sName = str(dupSongID[sID])
                lickSongs.add(sName) #adds song to lick songs controlling for duplicates (uses token ID instead of actual song name)
                songID = sName + sForm
                songFormRef.add(songID) #Adds song+form to dictionary for ease of finding song+form part                        
                if changeForm == 'T': #Adds song to formBoundary if it has lick suffix at formal boundary
                    if sID not in formBound:
                        formBound[sID] = set()
                        formBound[sID].add(sForm)
                    else:
                        formBound[sID].add(sForm)
                #Finds other duplicate songs and adds to set:
                sDups = dupSongOthers[sName].split('_') 
                dups = set(sDups)
                for d in dups:
                    dupSongs.add(d)
            else: #if not duplicated, add song to single songs set
                lickSongs.add(sID)
                singleSongs.add(sID)
                songID = sID + sForm
                songFormRef.add(songID)
                if changeForm == 'T': #Adds song to formBoundary if it has lick suffix at formal boundary
                    if sID not in formBound:
                        formBound[sID] = set()
                        formBound[sID].add(sForm)
                    else:
                        formBound[sID].add(sForm)
        totalSongs = len(songsCounter) #finds total songs (inc. duplicates)
        totalNonDupSongs = len(lickSongs) #finds total of individual songs (non-duplicated)
        return totalSongs, totalNonDupSongs, lickSongs, songForms, formBound, songFormRef

    ###Song info for Licks:
    totalSongs = songIDinfo(lick, n)[0]
    totalNonDup = songIDinfo(lick, n)[1]

    ###Song IDs (no duplicates):
    lickSongs = songIDinfo(lick, n)[2]
    for y in sorted(lickSongs):
        sortedSongs = sortedSongs + y + ' '
    ###Song forms included in lick:
    songForms = songIDinfo(lick, n)[3]
    for f in sorted(songForms):
        sortedForms = sortedForms + f + ' '
        
    ###Does lick suffix occur at a form boundary?
    formBoundary = songIDinfo(lick, n)[4]
    sortedBoundaries = ''
    if len(formBoundary) > 0:
        for s in sorted(formBoundary):
            song = s
            sortedBoundaries = sortedBoundaries + '(' + str(song) + ': '
            for form in formBoundary[song]:
                sortedBoundaries = sortedBoundaries + str(form) + '; '
            sortedBoundaries = sortedBoundaries.strip('; ')
            sortedBoundaries = sortedBoundaries + ') '
    else:
        sortedBoundaries = 'NoBound'
    
    ####FIND IF PROGRESSION LOOPS(loop = recurrent portion of lick)####
    
    loopProgsOut = self.loopProgs(lick)
    loop = loopProgsOut[0] #Loop (min amt of chords)
    loopLen = loopProgsOut[1] #length of loop 
    repeats = loopProgsOut[2] #how many times loop repeats
    lastChord = loopProgsOut[3] #loop's last chord (not abstracted)
    lastChordSurr = loopProgsOut[4] #last chord's surrounding chords (3 last chords of loop)
    
    ####FIND ABSTRACTION OF LOOP (AKA CHAIN)####
    ####Turn abstract loop into quality_interval sets; calculate first interval if it's a rotating loop; fill in last chord information
    loopChain = collections.deque()
    firstChord = 1
    firstInt = 0
    end = 0
    interval = 0
    for i in range (0, loopLen): #iterate through chords in loop 
        testChord = str(loop[i])
        chordInfo = self.absChord(testChord, prevRoot, beatMode, formMode, triadMode) 
        prevRoot = chordInfo[2] #reset variable as current Root for next chord in sequence
        #calculate last chord information
        if i == (loopLen - 1): 
            lastChordInfo = str(chordInfo[1]) + ':' + str(chordInfo[3])
            lastChordInfo = lastChordInfo + '-->'
        #Calculate first interval
        if chordInfo[1] != '': 
            interval = interval + int(chordInfo[1])
        else:
            interval = interval + 0
        loopChain.append((chordInfo[1], chordInfo[3]))
    #Calculate value for first interval (subtracts all other interval values in loop, mod12)
    firstInt = (firstInt - interval) % 12
    if firstChord == 1: #replace beginning interval for the first chord ONLY
        interval = firstInt
        firstChordInfo = loopChain.popleft()[1]
        loopChain.appendleft((interval,firstChordInfo))
        firstchord = 0

    ###Find normal form of loop abstraction
    absLoop = self.loopNormalForm(loopChain)

    #####ROW OUTPUT######
    rowOutput = list()
    headerRow = list()
 
    #####Basic lick information:
    rowOutput.append(self.nGramCounter)                        ####A. Chord Progression ID
    if self.nGramCounter == 1: headerRow.append('nGramID')
    rowOutput.append(self.ngrams[n][lick[0:-1]][lick[-1:]])     ####B. Number of times a lick occurs
    if self.nGramCounter == 1: headerRow.append('Prog Count')
    rowOutput.append(n)                                             ####C. Number of chords in the lick 
    if self.nGramCounter == 1: headerRow.append('nGram Length')
    if self.nGramCounter == 1: headerRow.append('nGram')
    for c in lick:                                                  ####D. Output chords in the lick
        rowOutput.append(c)  
        if self.nGramCounter  == 1: headerRow.append('')                                        
    for i in range(n,self.maxLen-1):                             #### Print empty cells for alignment 
        rowOutput.append('')
    for i in range(n,self.maxLen-2):
        if self.nGramCounter == 1: headerRow.append('')      
    #rowOutput.append('_'+revSortString)                             ####E. Backward-sorted lick
    #headerRow.append('Reverse String')

    ####Song/Form Information:        
    rowOutput.append(totalSongs)                                    ####H. Total number of songs (including duplicates)
    if self.nGramCounter == 1: headerRow.append('ALL Songs (inc. Dups)')
    rowOutput.append(totalNonDup)                                   ####I. Total number of songs without duplicates
    if self.nGramCounter == 1: headerRow.append('Total Songs (no Dups)')
    rowOutput.append(sortedSongs)                                   ####J. Songs in which lick appears
    if self.nGramCounter == 1: headerRow.append('Sorted Songs')
    rowOutput.append(sortedForms)                                   ####K. Forms in which lick appears
    if self.nGramCounter == 1: headerRow.append('Forms')
    rowOutput.append(sortedBoundaries)                              ####K1. If suffix chord occurs at formal boundary, states where
    if self.nGramCounter == 1: headerRow.append('Boundary Cases')

    ####Loop Info
    loopList = ''
    for chord in loop:                                              ####L. Repeated Loop
        loopList = loopList + '_' + str(chord)
    rowOutput.append(loopList)                                          
    if self.nGramCounter  == 1: headerRow.append('Loop')
    rowOutput.append(loopLen)                                       ####M. Loop length
    if self.nGramCounter == 1: headerRow.append('Loop Length')
    rowOutput.append(repeats)                                       ####N. how many times loop repeats 
    if self.nGramCounter  == 1: headerRow.append('# Repeats')
    rowOutput.append(lastChordInfo)                                 ####O. Last chord in loop (Abstraction)
    if self.nGramCounter == 1: headerRow.append('Last Loop Chord')
    normLoop = ''                                                   ####P. Loop Abstraction (in Normal Form)
    if self.nGramCounter == 1: headerRow.append('LoopAbs')
    for i in absLoop:   #fix first interval of loop
        intBef = str(i[0])
        qual = str(i[1])
        normLoop += intBef + qual + '_'                      
    rowOutput.append(normLoop)
    ###APPEND ROW TO OUTPUT##
    if self.nGramCounter == 1: 
        outputList.append(headerRow)           
    outputList.append(rowOutput) 
    
    ###Finish output if reach end token    
    if lick[-1] == '>E':
       return
        
    ###Goes through the sorted suffixes for the ngram; traverses ngramTree only if prefix + suffix (entire ngram) appears over a certain number of times (countThreshold)
    for suffix in sorted(self.ngrams[n+1][lick], key = operator.itemgetter(0)): 
        if suffix == 'total':
            continue 
        if self.ngrams[n+1][lick][suffix] >= self.countThreshold:
            self.traverseNgramList (lick + suffix, outputList, beatMode, formMode, triadMode)

###############################################
###METHOD FOR STARTING SUFFIX TREE TRAVERSAL###
###############################################
def listNgrams (self, keyMode, beatMode, formMode, triadMode, countThreshold): 
    outputList = list()
    self.nGramCounter = 0 ###Set counter to create CASE IDs for each progression
    for pref in sorted(self.ngrams[2], key = operator.itemgetter(0)):
        print ('ngram', self.ngrams[2][pref])
        if pref == 'total': 
            continue
        self.traverseNgramList (pref, outputList, beatMode, formMode, triadMode)
    
    ###TO EDIT   
    #Method for comparing entropy results across many files
    def statsData(self, keyMode, beatMode, formMode, triadMode, countThreshold):
        finalRowOutput = list()
        totalProgs = len(outputList) - 1 
        finalRowOutput.append('keyMode: ' + str(keyMode))
        finalRowOutput.append('triadMode: ' + str(triadMode))
        finalRowOutput.append('beatMode: ' + str(beatMode))
        finalRowOutput.append('formMode: ' + str(formMode))
        finalRowOutput.append('Count Thresh: ' + str(countThreshold))
        finalRowOutput.append('Total # Cases: ' + str(totalProgs))
        return finalRowOutput
    finalRow = statsData (self, keyMode, beatMode, formMode, triadMode, countThreshold)
    
    outputList.append(finalRow)
    return outputList 

####IDENTIFY METHODS AS CLASS OBJECTS (SEE mcgilldata.py)    
mcgillCorpus.listNgrams = listNgrams
mcgillCorpus.traverseNgramList = traverseNgramList
mcgillCorpus.findNgramsNoKey = findNgramsNoKey