import os, string, sys, time, json, csv, collections, math, fractions, operator, music21, pickle

#Main parser code for sorting through .txt files of McGill Corpus.
#Organized as set of classes, in hierarchical structure (Song: Phrase: Measure: Chord all input from Corpus)
#Dictionaries for function translations

mcgillPath = 'mcgill-billboard'

beatsPerMeasure = { #lookup table for beat definitions per meter
    '1/4': 1,
    '2/4': 2,  
    '3/4': 3,
    '4/4': 4,
    '5/4': 5,
    '6/4': 6,
    '7/4': 7,
    '9/4': 9,
    '3/8': 1,
    '5/8': 2,
    '6/8': 2,
    '9/8': 3,
    '12/8': 4 } 

beatStrengthByMeter = { #lookup table for beat strengths by meter
    '1/4': [3],
    '2/4': [3,1],
    '3/4': [3,1,1],
    '4/4': [3,1,2,1],
    '5/4': [3,1,1,1,1],
    '6/4': [3,1,1,2,1,1],
    '7/4': [3,1,1,1,1,1,1],
    '9/4': [3,1,1,2,1,1,2,1,1],
    '3/8': [3],
    '5/8': [3],
    '6/8': [3,1],
    '9/8': [3,1,1],
    '12/8': [3,1,2,1] }
    
formTranslateDict = { #lookup/standardization table for form functions
    'applause': '',   
    'bridge': 'bridge', #shortened as b
    'coda': 'outro', #shortened as o
    'chorus': 'chorus', #shortened as c
    'chorusa': 'chorus',
    'chorusb': 'chorus',
    'end': '',
    'ending': 'outro',
    'fadein': 'fadein', #shortened as n (think: in)
    'fadeout': 'fadeout',   #changed to d (think: decay)
    'flute)': '',
    'instrumental': 'instrumental', #shortened as s
    'instrumentalbreak': 'instrumental',
    'interlude': 'interlude', #shortened as u
    'intro': 'intro', #shortened as i
    'introa': 'intro',
    'introb': 'intro',
    'keychange': 'transition', #shortened as t
    'maintheme': 'theme',  #shortened as h
    'modulation': 'transition',
    'noise': '',
    'outro': 'outro',
    'prechorus': 'prechorus', #shortened as p
    'prechorustwo': 'prechorus',
    'preintro': '', 
    'preverse': 'interlude',
    'refrain': 'refrain', #shortened as r
    '(secondary)theme': 'theme',
    'secondarytheme': 'theme',
    'silence': '',
    'solo': 'solo', #shortened as l
    'spoken': '',
    'spokenverse': '',
    'talking': '',
    'theme': 'theme',
    'trans': 'transition',
    'transition': 'transition',
    'verse': 'verse', #shortened as v
    'versefive': 'verse',
    'versefour': 'verse',
    'verseone': 'verse',
    'versethree': 'verse',
    'versetwo': 'verse',
    'vocal': ''}

shortFormDict = { #Short one-letter versions for chord functions  
    'bridge': 'b',
    'chorus': 'c', 
    'fadein': 'n', #shortened as n (think: in)
    'fadeout': 'd',   #changed to d (think: decay) 
    'instrumental': 's', 
    'interlude': 'u',
    'intro': 'i',
    'outro': 'o',
    'prechorus': 'p', 
    'refrain': 'r',
    'solo': 'l',
    'theme': 'h',
    'transition': 't',
    'verse': 'v',
    '': ' '}
    

# Lazy class for used for lazy evaluation of chordsFlat and begTonic
# from http://stackoverflow.com/questions/3012421/python-lazy-property-decorator

class lazy_property(object):
    '''
    meant to be used for lazy evaluation of an object attribute.
    property should represent non-mutable data, as it replaces itself.
    '''

    def __init__(self,fget):
        self.fget = fget
        self.__name__ = fget.__name__


    def __get__(self,obj,cls):
        if obj is None:
            return None
        value = self.fget(obj)
        setattr(obj,self.__name__,value)
        return value


#Following are classes defined for mcgill data Corpus, Song, Phrase, Measure, Chord.
#Main parser for McGill data Corpus
    
class mcgillSong:
    def __init__(self):
        self.songID = ''
        self.title = ''
        self.artist = ''
        self.phrases = list() 
        self.numPhrases = '' #number of phrases in song with harmonic content ONLY
        self.measuresFlat = list() #for ease of parsing measure content without opening mcgillPhrase and mcgill Measure
        self.form = list() #gives form of the song
        self.begTonic = '' #gives beginning tonic of song
        self.begMeter = '' #gives beginning tonic of song
        self.songLength = 0 #identifies number of measures in song
        self.chordsFlat = list()
              
    @lazy_property
    def begTonic(self):
        begTonic = ''
        for thePhrase in self.phrases:
            for theMeasure in thePhrase.measures:
                if theMeasure.measureNumber == 1:
                    begTonic = theMeasure.tonic
                    break
            if begTonic != '':
                break
        return begTonic
             
class mcgillPhrase:
    def __init__(self):
        self.time = -1. #watch emptyMeasure variable for timestamp purposes
        self.measures = list() 
        self.measureLength = 0 #identifies how long phrase is
        self.phraseNumber = 0 #identifies phrase number
        self.formLetter = '' #identifies formal letter label of phrase
        self.formFunction = list() #identifies formal function of phrase
        self.changeForm = False #determines if change in formal section
        self.theLine = ''
        self.mode = ''
        self.splitLine = list()
    #NEW INFO FOR PRINTING FORM INFO
    def __str__(self):
        output = str(self.time) + ': '
        if self.changeForm: 
            output += '*' #Outputs an asterisk whenever the form changes at the beginning of the phrase
        output += self.formLetter + ' ( '
        for item in self.formFunction:
            output += item + ' '
        output += ')'
        
        return output
        
class mcgillMeasure:
    def __init__(self):
        self.meter = ''
        self.tonic = ''
        self.chords = list()
        self.formFunction = list() #identifies formal function of the measure's phrase
        self.changeMeter = False #determines change of meter within song structure
        self.changeTonic = False #determines change of song within song structure
        self.measureNumber = 0 #determines measure number within the phrase
    def __str__(self): #function for printing measure information
        if len(self.chords) == 0 :
            return 'empty measure' + '\n' #if no chords (i.e. 'N' or *), print as empty measure
        else :
            output = 'Measure: ' + str(self.measureNumber) + ' - ' + '\n'
            if self.changeMeter : #print meter change info if there's a change
                output += 'Time Change: ' + self.meter + '\n'
            for theChord in self.chords: #print information for each chord from mcgillChord.__str__
                output += theChord.__str__() + '\n'
            return output
        
class mcgillChord:
    def __init__(self):
        self.rootPC = ''
        self.rootSD = ''
        self.quality = '' #quality as it appears in corpus (includes inversions)
        self.qualityNormalForm = '' #quality NF (without added inversion tones)
        self.qualityReduced = '' #reduced quality - only 7ths, sus, no3s, no5s, 6s, no-chords (nc)
        self.qualityReducedNF = '' #reduced qual as NF
        self.qualityTriad = '' #reduced quality including only triads & mct (missing-chord-tones)
        self.qualityTriadNF = '' #triad quality as NF
        #self.fullQualityNF = '' #quality NF including added inversion tones (not part of the chord)
        self.beat = ''
        self.beatStrength = '' 
        self.beatDuration = ''
        self.formFunction = '' #identifies formal function of the chord's phrase
        self.secsDuration = '' #determines chord length in seconds -  - TO DO AT A LATER TIME
    def __str__(self): #function for printing chord: gives beat, rootPC and quality information
        return 'b=' + str(self.beat) + ' d=' + str(self.beatDuration) + ' sd=' + self.rootSD + ' q=' + self.quality + ' bs=' + str(self.beatStrength)
        
class mcgillCorpus:
    def __init__(self, mcgillPath, triadMode, keyMode, testMode): #set variable for testing parameters (shorten time!)
        
        ##################
        #  PICKLE        #
        ##################
        ### Define quality2NF as dictionary that calls normal chord list from RockPop-ChordTo-NF.csv for conversion       
        global quality2NF
        global reducedQuality
        global triadQuality
        #global fullQuality2NF
        quality2NF = dict()
        #fullQuality2NF = dict()
        reducedQuality = dict()
        triadQuality = dict()        
        theReader = csv.reader(open('RockPop-ChordToNF.csv', 'rU'))
        for row in theReader:
            normalChord = json.loads(row[1]) #json will read text from NFchord .csv as list data  
            quality2NF[row[0]] = normalChord
            reducedQuality[row[0]] = row[2] #translates quality of chord to reduced triad or 7th chord
            triadQuality[row[0]] = row[3] #translates quality of chord to maximally reduced name (triad)
            #fullQuality2NF[row[0]] = row[5] #translates quality of chord into normal form, including non-chord-member inversions
        
        pickleFilename = 'pickles/mcgillCorpusData.tM' + str(triadMode) + '.pickle'
        if os.path.isfile(pickleFilename):
            sys.stderr.write("getting data from Song Corpus pickle... ")
            start = time.clock()
            self.songs = pickle.load(open(pickleFilename, 'rb'), encoding = 'latin-1')
            sys.stderr.write(str(time.clock()-start) + ' secs\n')
        else:
            sys.stderr.write("Song Corpus data pickle not found, recalculating... ")
            start = time.clock()
            self.songs = dict() #songs is a dictionary of songs instances
            for j,theFolder in enumerate(os.listdir(mcgillPath)): # establish folder as mcgillPath to parse files
                if testMode == True and j > 2:
                    break
                if theFolder == '.DS_Store': 
                    continue #ignore .DS_Store as a folder
                theSong = mcgillSong() #class for song information
                theFileName = mcgillPath + '/' + theFolder + '/' + 'salami_chords.txt' #find data file for each song
                theFile = open(theFileName, 'r') #theFile is each song: read-only
                #Establish variables for tonic, meter and potential changes
                currentTonic = '' 
                if theFolder[0] == '0':
                    if theFolder[1] == '0':
                        if theFolder[2] == '0':
                            theFolder = theFolder[3:]
                        else:
                            theFolder = theFolder[2:]
                    else:
                        theFolder = theFolder[1:]
                else:
                    theFolder = theFolder                   
                theSong.songID = theFolder
                
                #SET BEGINNING DUMMY VARIABLES
                prevTonic = ''
                currentMeter = ''
                prevMeter = ''
                currentFormLetter = ''
                currentFormFunction = list()
                begMeterCounter = 0
                begTonicCounter = 0
        
                #SONG METADATA: Populate classes with individual file data, enumerating through each salami_chords.txt line
                songPhraseLength = 0 #start phrase counter  
                for i, theLine in enumerate(theFile):
                    #find title metadata for each song, store as theSong.title
                    if theLine[0:9] == '# title: ':
                        #if the title line is longer than 9 characters, emit error
                        if theLine[9] == ' ':
                            raise RuntimeError('theLine contains too many spaces')  
                        theSong.title = theLine[9:-1]
                
                    #find artist metadata, store as theSong.artist 
                    elif theLine[0:10] == '# artist: ':
                        #if the line is longer than 10 characters, emit error
                        if theLine[10] == ' ':
                            raise RuntimeError('theLine contains too many spaces')  
                        theSong.artist = theLine[10:-1]
            
                    #find meter metadata, store as currentMeter
                    elif theLine[0:9] == '# metre: ':
                        begMeterCounter += 1
                        #if the line is longer than 9 characters, emit error
                        if theLine[9] == ' ':
                            raise RuntimeError('theLine contains too many spaces')  
                        if begMeterCounter < 2:
                            prevMeter = theLine[9:-1]
                            theSong.begMeter = theLine[9:-1]
                        else:
                            prevMeter = currentMeter #identify prevMeter for future use
                        currentMeter = theLine[9:-1]
  
                    #find tonic metadata, store as currentTonic
                    elif theLine[0:9] == '# tonic: ':
                        begTonicCounter += 1
                        #if the line is longer than 9 characters, emit error
                        if theLine[9] == ' ':
                            raise RuntimeError('theLine contains too many spaces')  
                        if begTonicCounter < 2:
                            prevTonic = theLine[9:-1]
                            theSong.begTonic = theLine[9:-1]
                        else:
                            prevTonic = currentTonic #identify prevTonic for future use
                        currentTonic = theLine[9:-1]
                        
                    #Parse data line-by-line; start with timespan data, parse into measures, then into individual chords
                    elif theLine[0] in string.digits: #If a line begins with a digit, assume it's a time marker
                        thePhrase = mcgillPhrase() #store thePhrase as mcgillPhrase
                        splitLine = theLine.split() #split the line by whitespaces
                        thePhrase.time = float(splitLine[0]) #Set/store timestamp information as float
                        thePhrase.theLine = theLine #Store the entire phrase as thePhrase.theLine
                        theLine = ' '.join(splitLine[1:]) #rejoin theLine without timestamp information
                                
                        #FORM/MODE INFORMATION (== splitLine[0])
                        ##Create blank variables to tally chord-score for phrase MODE INFORMATION 
                        minorScore = 0
                        majorScore = 0
                        splitLine = theLine.split('|') #resplit the new line (without timestamps) by '|' --> Gets rid of measure marks
                        thePhrase.splitLine = splitLine #store phrase information without measure dividers
                        if theLine[0] == '|' : #If the phrase has no form information (theLine starts with '|'):
                            thePhrase.formLetter = currentFormLetter #Set form info as previous phrase's form information
                            thePhrase.formFunction = currentFormFunction #Set form function as previous phrase's form function
                        else: #find and parse form information if phrase begins with form information
                            formInfo = splitLine[0].split(',')  #form = first part of splitLine, split by commas
                            currentFormFunction = list() #create list of items for form info
                            thePhrase.formLetter = currentFormLetter #Set form letter as current form Letter (for other cases)
                            for item in formInfo: #iterate through items in forminfo, format to get rid of spaces/dashes/etc.
                                if item[0] == ' ': #if item begins blank, get rid of space
                                    item = item[1:]
                                if len(item) == 0 or item == ' ' or item == '': #if item length is zero or blank (no form info), ignore
                                    continue
                                if item.find('-') != -1: #if item contains dash, get rid of dash
                                    item = item.replace('-', '')
                                if item[0] in string.ascii_uppercase: #if item starts with capital letter, it is a letter label -- store as formLetter
                                    thePhrase.formLetter = item
                                    currentFormLetter = item #reset currentFormLetter
                                    thePhrase.changeForm = True
                                else:   #if item is lowercase, then it is a formFunction: standardize using translation dictionary
                                    function = formTranslateDict[item.replace(' ', '')] #use translation chart to identify proper form function label
                                    if function == '': #if the translation chart is blank, ignores
                                        continue
                                    else:  #identifies proper translation as form function   
                                        thePhrase.formFunction.append(function) #store function label as formFunction
                                        currentFormFunction.append(function)

                        #MEASURE DATA POPULATION: 
                        #Split line information by '|' to identify measure spans
                        #Populate measure information (based on split entities 1 to lineend AKA all data after line's timestamp)
                        measureCounter = 0 #establish measure counter to keep track of # of measures
                        for theMeasureText in splitLine[1:-1]:
                            measureCounter += 1
                            theMeasure = mcgillMeasure() #identify measure data as mcgillMeasure class 
                            theMeasure.meter = currentMeter #set current meter variable as theMeasure data
                            theMeasure.tonic = currentTonic #set current tonic variable as theMeasure data
                            theMeasure.formFunction = function #set current function as form function variable in theMeasure data
                            if currentMeter != prevMeter: #if currentMeter doesn't equal prevMeter, then signal change
                                theMeasure.changeMeter = True
                                prevMeter = currentMeter
                            if currentTonic != prevTonic: #if currentTonic doesn't equal prevTonic, then signal change
                                theMeasure.changeTonic = True
                                prevTonic = currentTonic
                            chords = theMeasureText.split() #define chords as measureText split by spaces
                            emptyMeasure = False #set default value of emptyMeasure as false
                            currentBeat = 0
                            
                            #CHORDS: parse the split measure text (within each measure - identify if it's an empty or complete measure)  
                            for i,eachItem in enumerate(chords):
                                eachItem = eachItem.replace(' ', '') #replace any blank spaces with nothing
                                if eachItem == '':
                                    continue
                                theChord = mcgillChord() #identify theChord as mcgillChord class
                        
                                #set split measure contents as s - otherwise, identify type of measure content for the following cases:
                                    #1. (__) signifies time change (no musical measure) - set new meter, change prevMeter variables, delete measure from counter, continue
                                    #2. '*' signifies music with no clear harmony - set measure as emptyMeasure, delete measure from counter
                                    #3. '&pause' signifies arbitrary pause in song - set measure as emptyMeasure
                                    #4. 'N' signifies no chord data for that beat - add beat value, no harmony information added
                                    #5. '.' signifies chord carried over from previous beat - add beat value, implement quality/root of previous chord
                        
                                #store harmony contents of chords if no problems found
                                s = eachItem.split(':') #split s by ':' (identifies chords from other entities) - s is a list which contains root and quality information
                                if len(s) == 2: #Is this a chord? Only is a chord if there are two elements (in the list) when split by ":"
                                    theChord.formFunction = function #set function of the chord as the function defined for the measure/phrase
                                    rootPC = s[0].strip() #set rootPC as first element of the list
                                    theChord.rootPC = rootPC.replace('b','-')
                                    if s[0] == ' ':
                                      print ('rootPC', theChord.rootPC)
                                    ###DERIVE ROOT INFORMATION (INTO PC, SD, ETC.)
                                    p = music21.pitch.Pitch(s[0].replace('b','-')+'4') #pitch of the root of the chord
                                    x = music21.pitch.Pitch(currentTonic.replace('b','-')) #pitch of the current tonic 
                                    y = music21.pitch.Pitch('C') #pitch of 'C' (reference for transposition)
                                    ivl = music21.interval.Interval(noteStart = x, noteEnd = y) #interval between reference 'C' and SD root of chord    
                                    theChord.rootSD = p.transpose(ivl).name #Set root SD relevant to current tonic
                                    ####DERIVE CHORD QUALITY INFORMATION (NF, QUALITY, ETC.)
                                    theChord.quality = s[1] #Set quality of chord as stuff after colon in splitList
                                    #theChord.quality = fullQuality2NF[theChord.quality]
                                    theChord.qualitySplit = theChord.quality.split('/') #Split the quality of the chord into quality versus inversion (denoted with '/')
                                    theChord.qualityReduced = reducedQuality[theChord.qualitySplit[0]] #Sets chord quality as only 7ths, triads, no3, no5, sus, and no-chords
                                    theChord.qualityTriad = triadQuality[theChord.qualitySplit[0]] #Sets chord quality as only triad or mct (missing-chord-tone)
                                    theChord.qualityNormalForm = quality2NF[theChord.qualitySplit[0]] #transform first part of quality into Normal Form
                                    ###Identify normal forms for reduced, triad, and normal qualities; if not able to (especial labels: nc, no3, no5, mct), sets NF as original normal form
                                    try:
                                        theChord.qualityReducedNF = quality2NF[theChord.qualityReduced]
                                    except:
                                        theChord.qualityReducedNF = theChord.qualityNormalForm
                                    try: 
                                        theChord.qualityTriadNF = quality2NF[theChord.qualityTriad]
                                    except:
                                        theChord.qualityTriadNF = theChord.qualityNormalForm
                                    theChord.beat = currentBeat
                                    #identify and store current beat strength 
                                    meterStrengths = beatStrengthByMeter[theMeasure.meter]
                                    theChord.beatStrength = meterStrengths[currentBeat]
                                    currentBeat += 1 #add count for next beat
                                    
                                    #MODE identification: Store chord information for identifying phrase mode                              
                                    try:  #turn chordRoot into a pitch object 
                                        chordRoot = music21.pitch.Pitch(theChord.rootSD).pitchClass
                                    except: #assume rootSD is empty
                                        print ('blank', theChord.rootSD)
                                    cquality = theChord.qualityNormalForm #turn the quality of the chord into a normalForm   
                                    for theNote in cquality: #find if the notes of the chord include b3, b6, b7 in the home tonic
                                        if (theNote + chordRoot) % 12 in [3,8,10]:
                                            minorScore += 1 #if b3, b6, b7 are present, add 1 to minorScore
                                        elif (theNote + chordRoot) % 12 in [4,9,11]:
                                            majorScore += 1 #if 3, 6, and 7 are present, add 1 to majorScore
                                            
                                else: #If no colon is present, there is no chord present: take special cases as above
                                    if eachItem[0] == '(' and eachItem[-1] == ')' : #Case 1 - meter change
                                        theMeasure.meter = eachItem[1:-1]
                                        theMeasure.changeMeter = True
                                        prevMeter = theMeasure.meter
                                        continue
                                    if eachItem == '*' or eachItem == '&pause' : #Case 2 and 3 - emptyMeasure
                                        emptyMeasure = True #flags empty measures (be careful with TIMESTAMPS)
                                        measureCounter -= 1
                                        continue                                     
                                    if eachItem == 'N' : #case 4 - no chord for the beat
                                        theChord.beat = currentBeat
                                        currentBeat += 1
                                    if eachItem == '.' : #case 5 - carry previous chord to current beat
                                        theChord.formFunction = function
                                        theChord.beat = currentBeat
                                        theChord.rootPC = '.'
                                        currentBeat += 1
                                theMeasure.chords.append(theChord) #append chord data to theMeasure class
                                theMeasure.measureNumber = measureCounter   #appends # of measure (within phrase)
                                                                
                            ##FIND BEAT DURATION FOR MEASURES WITH *, N, ' ' or other values   
                            if emptyMeasure : #keeps empty measures from being in analysis
                                continue
                                
                            #SET BEAT COUNTS FOR WEIRD METERS   
                            #Beat count when metric signature doesn't align with # of chords annotated (MUST redo if new release of Billboard data!)                                    
                            #Only done for 12/8 and 4/4, when only two chords per measure
                            beats = len(theMeasure.chords) #establishes the number of beats as the length of the measure (number of splits)
                            if currentMeter in ['12/8', '4/4'] and beats == 2:
                                theMeasure.chords[1].beat = 2 #sets the beat of the second chord as '2'
                            
                            #IDENTIFY BLANK CHORD ROOTS ('.'), change duration of previous chord to accomodate these chords
                            w = 0
                            while w < (len(theMeasure.chords)): #go through measure, identify '.' and take out (for replacement with duration) at location w
                                if theMeasure.chords[w].rootPC == '.':
                                    theMeasure.chords.pop(w) #deleting chord item w (aka '.') from list of chords within this measure
                                else: #no '.' at location 'w'
                                    w += 1
                            for w in range(len(theMeasure.chords)):
                                if w < (len(theMeasure.chords) - 1):
                                    theMeasure.chords[w].beatDuration = theMeasure.chords[w+1].beat - theMeasure.chords[w].beat
                                else:
                                    theMeasure.chords[w].beatDuration = beatsPerMeasure[currentMeter] - theMeasure.chords[w].beat   
                                                                    
                            thePhrase.measureLength = int(measureCounter) * 1.0 #stores length of Phrase (in measures) information 
                            thePhrase.measures.append(theMeasure) #append theMeasure information to thePhrase class
                            theSong.measuresFlat.append(theMeasure) #append theMeasure information to theSong class
                        
                        if int(thePhrase.measureLength) > 0:  # Gets # of phrases in song and # of measures in song                     
                            songPhraseLength += 1
                            thePhrase.phraseNumber = songPhraseLength #Store current phraseNumber as phrase # ID     
                        theSong.numPhrases = songPhraseLength #Store length of song (in phrases)                    
                        theSong.songLength += int(thePhrase.measureLength)  #store total number of measures in song
                        
                        ##MODE: Calculate Phrase Mode Information
                        ##Mode is determined by: 
                        ##  1) Identifying tonic of each song 
                        ##  2) Identifying normal form of each chord within a phrase *using external Rockpop-NSF list*
                        ##  3) Identify if chord tones are b3, b6, and b7 in tonic key (add to a minor-key counter)
                        ##  4) If the minor-key counter outweighs the counter for major key, codify phrase as minor (if equal, ambiguous mode)

                        if minorScore == majorScore:
                            thePhrase.mode = 'ambiguous' 
                        elif minorScore > majorScore: #identify whether majorScore or minorScore prevails in phrase
                            #if minorScore prevails, phrase encoded as minor, chords added to minor dictionary tally
                            thePhrase.mode = 'minor'
                        else:
                            thePhrase.mode = 'major'       
                        theSong.phrases.append(thePhrase) #append thePhrase information to theSong class
                        
                self.songs[theFolder] = theSong #define theFolder item number as dictionary key for theSong
                
                ####CREATE CHORDSFLAT LIST FOR ENTROPY ALGORITHM
                ###NOTE: This chordsflat list will skip any beats without harmonic information (i.e. silences, or ambiguous 'N' moments as noted above)
                chordsFlatList = list() #create list of dictionaries (each chord = dictionary)
                chordDict = {  #set start token
                    'root': '>S',
                    'position': 0 }  
                chordsFlatList.append(chordDict)
                chordPos = 1 #dummy variable to tally chord position
                for thePhrase in theSong.phrases:
                    for theMeasure in thePhrase.measures:
                        for theChord in theMeasure.chords:
                            if theChord.rootPC == '': #omits any beats without harmonic information/roots
                                continue
                            splitQual = theChord.quality.split("/")[0].replace(',', '|')
                            print (splitQual)
                            chordDict = {
                                'root': theChord.rootPC,                     #Chord Root
                                'qual': theChord.quality,                    #Chord Quality - Full as appears in corpus (triadMode = 2)
                                'triadQual': theChord.qualityTriad,          #Chord Quality - Triad only (triadMode = 0)
                                'redQual': theChord.qualityReduced,          #Chord Quality - Reduced to only 7ths, triads, no3 & 5, sus, 6 (triadMode = 7)
                                'splitQual': splitQual, #Chord Quality - Full without inversions (triadMode = 1)
                                'beat': theChord.beat,                       #Chord beat within measure
                                'form': shortFormDict[theChord.formFunction], #Formal section in which chord appears
                                'phrase': thePhrase.phraseNumber,            #Phrase in which chord appears
                                'measure': theMeasure.measureNumber,         #Measure in which chord appears
                                'position': chordPos                        #Chord position
                                }
                            print (chordDict)
                            chordsFlatList.append(chordDict)
                            chordPos += 1
                chordDict = {   #set end token
                    'root': '>E',
                    'position': chordPos } 
                chordsFlatList.append(chordDict)
                theSong.chordsFlat = chordsFlatList           
                
            #write pickle
            pickle.dump(self.songs, open(pickleFilename,'wb'))
            sys.stderr.write(str(time.clock()-start) + ' secs\n')