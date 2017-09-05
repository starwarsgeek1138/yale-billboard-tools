import os, string, music21, sys, time, json, csv, collections, math, fractions, operator, pickle, mcgilldata, methods, functions
from mcgilldata import *
from methods import *
from functions import *

##This module defines methods for finding entropy-end-bounded progressions (using imported mcgilldata.py classes)
#Requires setting dummy variables in running script (mcgilldata-progression-entropy-default.py)
#testMode = True (parses whole corpus) or False (parses ten first songs)
#keyMode = True (based on tonic key) or False (key-blind: progressions are all transposed to that C M/m = the first chord)
#triadMode = 0 (parses only using triads) or 1 (parses all chord-tones) or 7 (parses only triads and 7ths); or 2 (parses all quality including inversion, not implemented yet)
#beatMode = True (includes chord Beat info) or False (no beat info included)
#formMode = True (include form value for each chord) or False (no form info included)

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

##################################################################################################             
###METHOD FOR FINDING LICKS NAIVE TO TONIC/RN (BASED ON CHORD QUALITY AND INTERVAL MOTION ONLY)###
##################################################################################################
def findLicksNoKey(self, keyMode, beatMode, formMode, triadMode, treeDepth, countThreshold, entropyThreshold, probThreshold):
    
    ###CREATE SUFFIX TREE###
    self.songIDLicks = dict()
    self.treeDepth = treeDepth
    self.countThreshold = countThreshold
    self.entropyThreshold = entropyThreshold
    self.probThreshold = probThreshold
    ########################################
    #########PICKLE #2 #####################
    ########################################
    pickleFilename = 'pickles/mcgillCorpusSuffixTree.noKey.tM' + str(triadMode) + '.bM'+ str(int(beatMode)) +'.fM'+ str(int(formMode)) + '.pickle'
    if os.path.isfile(pickleFilename):
        sys.stderr.write("getting data from Suffix Tree pickle... ")
        start = time.clock()
        self.suffixTree, self.songIDLicks = pickle.load(open(pickleFilename, 'rb'), encoding = 'latin-1')
        sys.stderr.write(str(time.clock()-start) + ' secs\n')
    else:
        sys.stderr.write("Suffix Tree data pickle not found, recalculating... ")
        start = time.clock()        
        self.suffixTree = dict()
        for n in range(1, self.treeDepth+1):
            self.suffixTree[n] = dict() #sets up suffix tree - a dict of dict for progressions of various lengths (n)
            self.suffixTree[n]['total'] = 0
            self.songIDLicks[n] = dict() #create dictionary of songIDs for specific licks
            
        ###CREATE PRUNED LIST OF CHORDS FOR TREE CREATION  
        for theSongID, theSong in self.songs.items():
            prunedList = self.chordPrune(theSong.chordsFlat, beatMode, formMode, triadMode)
            mList = prunedList[0]
            mListOrig = prunedList[3] #original mList without omissions 
            mListForms = prunedList[1]
            mListBeats = prunedList[2]
            songID = str(theSong.songID)
            
            for n in range(1, self.treeDepth+1):
                ##Create ngrams (for suffix tree) from pruned list 
                for loc in range(len(mList)):
                    if loc >= (len(mList) - n + 1): ##n is length of unit (ngram); adds one in order to account beyond all chords in song (ngram) --> if loc goes beyond, breaks loop 
                        break
                    longNgram = self.transToC(mList[loc:loc+n], beatMode, formMode) #split into ngram based on location; transposes to C based on first chord of progression
                    prefixPos = mList[loc+n-2]['pos'] #dummy variable to find ending position of ngram's prefix
                    suffixPos = mList[loc+n-1]['pos'] #dummy variable to find ending position of ngram's suffix
                    ngram = self.ngramCreate(longNgram)
                    
                    #####SUFFIX TREE CREATION#####
                    prefix = tuple(ngram[0:-1]) #prefix = all but the last element of ngram
                    suffix = tuple([ngram[-1]]) #suffix = last element of ngram
                    if prefix not in self.suffixTree[n]: #create prefix entry if not in dictionary
                        self.suffixTree[n][prefix] = dict()
                        self.suffixTree[n][prefix]['total'] = 0 
                        self.songIDLicks[n][prefix] = dict() #dict to keep track which songs this ngram appears in
                    if suffix in self.suffixTree[n][prefix]:
                        self.suffixTree[n][prefix][suffix] += 1 #adds one to number of times suffix follows the prefix
                        #script to encode the formal part in which a suffix chord occurs and if it's at a formal boundary
                        suffixChordForm = mListForms[suffixPos]
                        suffixChordBeat = mListBeats[suffixPos]
                        prefixChordForm = mListForms[prefixPos]
                        #Add 'T' to list to denote that there is a form boundary between prefix and suffix chords
                        if suffixChordForm[1] == prefixChordForm[1]:
                            self.songIDLicks[n][prefix][suffix].add(songID +'.'+ str(suffixChordForm[1]))
                        else: #add True for boundary
                            self.songIDLicks[n][prefix][suffix].add(songID +'.'+ str(prefixChordForm[1])+str(suffixChordForm[1])+'.T')
                    else:
                        self.suffixTree[n][prefix][suffix] = 1 
                        self.songIDLicks[n][prefix][suffix] = set()
                        #script to encode the formal part in which a suffix chord occurs and if it's at a formal boundary
                        suffixChordForm = mListForms[suffixPos]
                        suffixChordBeat = mListBeats[suffixPos]
                        prefixChordForm = mListForms[prefixPos]
                        #Add 'T' to list to denote that there is a form boundary between prefix and suffix chords
                        if suffixChordForm[1] == prefixChordForm[1]:
                            self.songIDLicks[n][prefix][suffix].add(songID +'.'+ str(suffixChordForm[1]))
                        else:
                            self.songIDLicks[n][prefix][suffix].add(songID +'.'+ str(prefixChordForm[1])+str(suffixChordForm[1])+'.T')
                            
                    self.suffixTree[n][prefix]['total'] += 1 
                    self.suffixTree[n]['total'] += 1
        
        ########################################
        #########WRITE PICKLE #2 ###############
        ########################################
        pickle.dump([self.suffixTree, self.songIDLicks], open(pickleFilename,'wb'))
        sys.stderr.write(str(time.clock()-start) + ' secs\n')

###################################################################
###METHOD FOR TRAVERSING SUFFIX TREE/ENTROPY AND CREATING OUTPUT###
###################################################################
def traverseSuffixTree (self, lick, chainLength, outputList, beatMode, formMode, triadMode):

    #####METHOD TO FIND SUFFIX PROBABILITIES#####
    def suffixProb (lick): #probability that, given the first n-1 elements of lick, the last element will follow (when n is the number of elements of lick)
        n = len(lick) #determines number of chords in the lick
        branch = self.suffixTree[n][lick[0:-1]] #identifies the lick elements from first to last (the last becomes the "suffix")
        prob = branch[(lick[-1],)] * 1.00 / branch['total'] #finds total number of times last element of lick appears, multiplies by 1/total branches
        return prob
        
    ######METHOD TO CALCULATE PROGRESSION ENTROPY########     
    def suffixEntropy(lick): #treats WHOLE lick as prefix; calculates the entropy of the distribution of all possible suffixes (after the WHOLE lick)
        n = len(lick) + 1
        H = 9.99 #set ceiling on H (entropy)
        if n <= self.treeDepth and lick[-1] != '>E':
            #prevents calculation if tree doesn't have enough levels or if there's an endtoken (H = 9.99)
            H = 0.00 #reset entropy at 0
            branch = self.suffixTree[n][lick]
            #calculate entropy for all possible cases of suffixes following this lick
            for leaf in branch:
                if leaf == 'total': continue
                P = branch[leaf] * 1.00 / branch['total']
                H -= P * math.log2(P) 
        return H
            
    ##################################################
    ######CALCULATIONS FOR TABLE OUTPUT###############
    ##################################################      
    n = len(lick)
    
    ##F. Calculate entropy and probability (print/store in dict if there is an error)
    theSuffixEntropy = suffixEntropy(lick)
    
    #E. Print lick sorted backward
    revSortString = '' 
    sortString = ''
    for i in reversed(lick):
        i = i + '_'
        revSortString += i
    for i in lick:
        i = i + '_'
        sortString += i 

    #####G. METHOD TO CALCULATE HASHES FOR NESTED LICKS####
    ###chainLength = variable to count hashes
    ###No hashes if: probability of suffix is less than 0.5 (that given n-1 events in lick, the probability of n is less than 50%)
    ###Add hashes to chainLength (which will get transferred across nested levels): Low entropy after entire lick (Entropy < threshold  - low entropy following the entire lick, or high certainty of next event: this will get added to the next lick up)
    ###Hashes printed if: there are hashes (chainLength != 0) and the entropy reaches above the threshold
    hashes = ''
    prob = suffixProb(lick)
    if prob < self.probThreshold: chainLength = 0
    if theSuffixEntropy < self.entropyThreshold: 
        chainLength += 1
    if chainLength != 0 and theSuffixEntropy >= self.entropyThreshold:
        if theSuffixEntropy >= self.entropyThreshold: 
            for i in range(chainLength):
                hashes += '#'
        chainLength = 0
        
    #########IF HASHES EXIST FOR LICK: PROPAGATE ROW NFORMATION#########
    #Row is only appended to the table if the row has hashes  & there was no error in finding the entropy (otherwise, the row is thrown out)
    if hashes != '': 
        from collections import deque
        #dummy variables to keep track of previous & last chords, etc.
        prevRoot = ''
        lastChordInfo = ''
        sortedSongs = ''
        sortedForms = ''
    
        ####A. PROGRESSION CASE ID####
        self.suffixTreeCounter += 1
    
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
            for s in sorted(self.songIDLicks[n][lick[0:-1]][lick[-1:]]):
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
        rowOutput.append(self.suffixTreeCounter)                        ####A. Chord Progression ID
        if self.suffixTreeCounter == 1: headerRow.append('progID')
        rowOutput.append(self.suffixTree[n][lick[0:-1]][lick[-1:]])     ####B. Number of times a lick occurs
        if self.suffixTreeCounter == 1: headerRow.append('Prog Count')
        rowOutput.append(n)                                             ####C. Number of chords in the lick 
        if self.suffixTreeCounter == 1: headerRow.append('Prog Length')
        if self.suffixTreeCounter == 1: headerRow.append('Lick')
        for c in lick:                                                  ####D. Output chords in the lick
            rowOutput.append(c)  
            if self.suffixTreeCounter == 1: headerRow.append('')                                        
        for i in range(n,self.treeDepth-1):                             #### Print empty cells for alignment 
            rowOutput.append('')
        for i in range(n,self.treeDepth-2):
            if self.suffixTreeCounter == 1: headerRow.append('')      
        #rowOutput.append('_'+revSortString)                            ####E. Print reversed lick as string
        #headerRow.append('Reverse String')
        rowOutput.append(sortString)                                    ####E.2. Print lick as a string
        headerRow.append('Lick String')                                
    
        rowOutput.append(theSuffixEntropy)                              ####F. Entropy at end of lick
        if self.suffixTreeCounter == 1: headerRow.append('H')
        rowOutput.append(hashes)                                        ####G. Output hashes
        if self.suffixTreeCounter == 1: headerRow.append('Hashes')
    
        ####Song/Form Information:        
        rowOutput.append(totalSongs)                                    ####H. Total number of songs (including duplicates)
        if self.suffixTreeCounter == 1: headerRow.append('ALL Songs (inc. Dups)')
        rowOutput.append(totalNonDup)                                   ####I. Total number of songs without duplicates
        if self.suffixTreeCounter == 1: headerRow.append('Total Songs (no Dups)')
        rowOutput.append(sortedSongs)                                   ####J. Songs in which lick appears
        if self.suffixTreeCounter == 1: headerRow.append('Sorted Songs')
        rowOutput.append(sortedForms)                                   ####K. Forms in which lick appears
        if self.suffixTreeCounter == 1: headerRow.append('Forms')
        rowOutput.append(sortedBoundaries)                              ####K1. If suffix chord occurs at formal boundary, states where
        if self.suffixTreeCounter == 1: headerRow.append('Boundary Cases')

        ####Loop Info
        loopList = ''
        for chord in loop:                                              ####L. Repeated Loop
            loopList = loopList + '_' + str(chord)
        rowOutput.append(loopList)                                          
        if self.suffixTreeCounter == 1: headerRow.append('Loop')
        rowOutput.append(loopLen)                                       ####M. Loop length
        if self.suffixTreeCounter == 1: headerRow.append('Loop Length')
        rowOutput.append(repeats)                                       ####N. how many times loop repeats 
        if self.suffixTreeCounter == 1: headerRow.append('# Repeats')
        rowOutput.append(lastChordInfo)                                 ####O. Last chord in loop (Abstraction)
        if self.suffixTreeCounter == 1: headerRow.append('Last Loop Chord')
        normLoop = ''                                                   ####P. Loop Abstraction (in Normal Form)
        if self.suffixTreeCounter == 1: headerRow.append('LoopAbs')
        for i in absLoop:   #fix first interval of loop
            intBef = str(i[0])
            qual = str(i[1])
            normLoop += intBef + qual + '_'                      
        rowOutput.append(normLoop)
        ###APPEND ROW TO OUTPUT##
        if self.suffixTreeCounter == 1: 
            outputList.append(headerRow)           
        outputList.append(rowOutput) 

        
    ###Finish output if reach end token or full tree-Depth    
    if lick[-1] == '>E' or n+1 == self.treeDepth:
        return
        
    ###Goes through the sorted suffixes for the lick; traverses suffixTree only if lick + suffix appears over a certain number of times (countThreshold)
    for suffix in sorted(self.suffixTree[n+1][lick], key = operator.itemgetter(0)): 
        if suffix == 'total':
            continue 
        if self.suffixTree[n+1][lick][suffix] >= self.countThreshold:
            self.traverseSuffixTree ( lick + suffix, chainLength, outputList, beatMode, formMode, triadMode)

###############################################
###METHOD FOR STARTING SUFFIX TREE TRAVERSAL###
###############################################
def listLicks (self, keyMode, beatMode, formMode, triadMode, entropyThreshold, probThreshold): 
    outputList = list()
    self.suffixTreeCounter = 0 ###Set counter to create CASE IDs for each progression
    for note in sorted(self.suffixTree[2], key = operator.itemgetter(0)):
        if note == 'total': 
            continue
        self.traverseSuffixTree(note, 0, outputList, beatMode, formMode, triadMode)
    #Method for comparing entropy results across many files
    def statsData(self, keyMode, beatMode, formMode, triadMode, entropyThreshold, probThreshold):
        finalRowOutput = list()
        totalProgs = len(outputList) - 1 
        finalRowOutput.append('keyMode: ' + str(keyMode))
        finalRowOutput.append('triadMode: ' + str(triadMode))
        finalRowOutput.append('beatMode: ' + str(beatMode))
        finalRowOutput.append('formMode: ' + str(formMode))
        finalRowOutput.append('Entropy Thresh: ' + str(entropyThreshold))
        finalRowOutput.append('Prob Thresh: ' + str(probThreshold))
        finalRowOutput.append('Total # Cases: ' + str(totalProgs))
        return finalRowOutput
    finalRow = statsData (self, keyMode, beatMode, formMode, triadMode, entropyThreshold, probThreshold)
    
    outputList.append(finalRow)
    return outputList 

####IDENTIFY METHODS AS CLASS OBJECTS (SEE mcgilldata.py)   
mcgillCorpus.listLicks = listLicks
mcgillCorpus.traverseSuffixTree = traverseSuffixTree
mcgillCorpus.findLicksNoKey = findLicksNoKey