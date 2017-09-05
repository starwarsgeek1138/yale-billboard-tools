import mcgilldata, string, os, sys, collections, csv, music21
from mcgilldata import *

#Gives spreadsheet of information by song:
    #Each song's tonic, mode, meter, instrumentation (including tonic/mode/meter change
#Mode includes ambiguous, major, and minor

mcgillPath = 'mcgill-billboard'
theCorpus = mcgilldata.mcgillCorpus(mcgillPath, testMode = False)

#create spreadsheet with basic song information metadata
outputCsv = csv.writer(open('csv-results/corpusStatsBySong.csv', 'wb'))

#Create spreadsheet            
headerRow = list()
headerRow.append('SongID')
headerRow.append('Title')
headerRow.append('Artist')
headerRow.append('Beg. Tonic') 
headerRow.append('Beg. Mode')
headerRow.append('Beg. Meter')
headerRow.append('Meter Change?')
headerRow.append('Tonic Change?')
headerRow.append('Mode Change?')
outputCsv.writerow(headerRow)

####CODE INFORMATION

for theSongid, theSong in theCorpus.songs.iteritems():
    thisRow = list()
#Build metadata spreadsheet
    songID = theSongid
    thisRow.append(songID)
    songTitle = theSong.title
    thisRow.append(songTitle)
    songArtist = theSong.artist
    thisRow.append(songArtist)
    begTonicTrack = 0
    modeChange = 0
    meterChange = 0
    tonicChange = 0
    for thePhrase in theSong.phrases:
        #FIND BEGINNING SONG VALUES ONLY (TONIC, METER, MODE)
        for theMeasure in thePhrase.measures:
            if begTonicTrack == 0:
                if theMeasure.measureNumber == 1:
                    begTonic = theMeasure.tonic
                    thisRow.append(begTonic)
                    begMode = thePhrase.mode
                    thisRow.append(begMode)
                    begMeter = theMeasure.meter
                    thisRow.append(begMeter)
                    begTonicTrack += 1
            if meterChange == 0:
                thisRow.append(meterChange)
                if theMeasure.changeMeter == True:
                    meterChange = 1
                    thisRow[-1] = meterChange
            if tonicChange == 0:
                thisRow.append(tonicChange)
                if theMeasure.changeTonic == True:
                    tonicChange = 1
                    thisRow[-1] = tonicChange
#             if phraseMode == currentMode:
#                 modeChange = 0
#                 thisRow.append(modeChange)
#                 currentMode = phraseMode
#             else:
#                 modeChange = 1
#                 thisRow.append(modeChange)
    outputCsv.writerow(thisRow)

