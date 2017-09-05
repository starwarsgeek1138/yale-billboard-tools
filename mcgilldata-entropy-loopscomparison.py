### THIS CODE DOES A MULTI-FILE ANALYSIS of of the loopsAnalysis

import mcgilldata, methods, functions, os, string, music21, sys, time, json, csv, collections, math, fractions, operator, pickle, re
from time import *
from mcgilldata import *
from methods import *
from functions import *

mcgillPath = 'mcgill-billboard' #define path for McGill Corpus Methods and Files
csvPath = 'csv-results/entropyResults/loopsAnalysis'  #define path of csv files
loopDict = dict() #Dictionary of loops (per individual analysis file) for output
###############################################
########### MAIN PARSING CODE #################
###############################################
#Open files from directory for data scraping
for fileName in os.listdir(csvPath):
    if fileName.startswith("loopsAnalysis_"):  #Looks at loops analysis files within directory
        #Create a directory of abstract loops from the relevant loopsAnalysis
        entropy = fileName.split('_')[7]
        fileName= csvPath + '/' + fileName #rename file to include csvPath info

        licksFile = open(fileName, 'r', newline = '').read().splitlines()
        #Identify row index for specific variables from header titles in licks output file
        header = licksFile[0].split(',')
        loopIndex = header.index('Abstract Loop')
        lickIndex = header.index('Abstract Lick')
        loopSongsIndex = header.index('Loop Song IDs')
        loopFormsIndex = header.index('Loop Forms')
        loopTotalIndex = header.index('Loop Total')
        lickCountIndex = header.index('Lick Total')
        lickLengthIndex = header.index('Lick Length')
        lickSongsIndex = header.index('Lick Song IDs')
        kModeIndex = header.index('keyMode')
        tModeIndex = header.index('triadMode')
        fModeIndex = header.index('formMode')
        bModeIndex = header.index('beatMode')
        
        #Propagate dictionary based on these variables (abstract loop is key)
        for row in licksFile[1:-1]: #ignores header and footer rows
            i = 1
            row = row.split(',')
            #extract keymode, triadmode, beatmode, formmode variables
            absLoop = row[loopIndex].rstrip('_')
            #Identify Analysis Modes for dictionary
            if i == 1:
                i = 0
                kMode = row[kModeIndex] 
                tMode = row[tModeIndex]
                bMode = row[bModeIndex]
                fMode = row[fModeIndex]
            absLick = row[lickIndex].rstrip('_')
            lickLength = len(absLick.split("_"))
            loopTotal = int(row[loopTotalIndex])
            lickCount = int(row[lickCountIndex])
            sortedSongs = row[loopSongsIndex].split(' ')
            sortedSongs = list(filter(None, sortedSongs))
            loopForms = row[loopFormsIndex].split(' ')
            loopForms = list(filter(None, loopForms))
            lickSongs = row[lickSongsIndex].split(' ')
            lickSongs = list(filter(None, lickSongs))
            
            
            #Create dictionary based on data
            if absLoop not in loopDict:
                loopDict[absLoop] = dict()
            if fileName not in loopDict[absLoop]:
                loopDict[absLoop][fileName] = dict()
                loopDict[absLoop][fileName]['keyMode'] = functions.boolean(kMode)
                loopDict[absLoop][fileName]['triadMode'] = int(tMode)
                loopDict[absLoop][fileName]['beatMode'] = functions.boolean(bMode)
                loopDict[absLoop][fileName]['formMode'] = functions.boolean(fMode)
                loopDict[absLoop][fileName]['licks'] = list()
                loopDict[absLoop][fileName]['songs'] = set()
                loopDict[absLoop][fileName]['forms'] = set()
                loopDict[absLoop][fileName]['lickLength'] = list()
                loopDict[absLoop][fileName]['loopTotal'] = 0
                loopDict[absLoop][fileName]['lickTotal'] = 0
                loopDict[absLoop][fileName]['lickSongs'] = set()
            loopDict[absLoop][fileName]['forms'].update(loopForms)
            loopDict[absLoop][fileName]['songs'].update(sortedSongs)
            loopDict[absLoop][fileName]['licks'].append(absLick)
            loopDict[absLoop][fileName]['lickLength'].append(lickLength)
            loopDict[absLoop][fileName]['loopTotal'] = loopTotal
            loopDict[absLoop][fileName]['lickTotal'] += lickCount
            loopDict[absLoop][fileName]['lickSongs'].update(lickSongs)

###############################################
########### OUTPUT ############################
###############################################
###############################################
########### OUTPUT HEADER #####################
###############################################
outputList = list()
#Create spreadsheet header  
headerRow = list()
headerRow.append('Abstract Loop')
headerRow.append('Loop Length')
#Append triadMode 0 Info
headerRow.append('TM0 - BMT Count')
headerRow.append('TM0 - BMT Songs')
headerRow.append('TM0 - FMT Count')
headerRow.append('TM0 - FMT Songs')
headerRow.append('TM0 - BFMT Count')
headerRow.append('TM0 - BFMT Songs')
headerRow.append('TM0 - BFMF Count')
headerRow.append('TM0 - BFMF Songs')
#Append triadMode7 Info
headerRow.append('TM7 - BMT Count')
headerRow.append('TM7 - BMT Songs')
headerRow.append('TM7 - FMT Count')
headerRow.append('TM7 - FMT Songs')
headerRow.append('TM7 - BFMT Count')
headerRow.append('TM7 - BFMT Songs')
headerRow.append('TM7 - BFMF Count')
headerRow.append('TM7 - BFMF Songs')
#Append triadMode1 Info
headerRow.append('TM1 - BMT Count')
headerRow.append('TM1 - BMT Songs')
headerRow.append('TM1 - FMT Count')
headerRow.append('TM1 - FMT Songs')
headerRow.append('TM1 - BFMT Count')
headerRow.append('TM1 - BFMT Songs')
headerRow.append('TM1 - BFMF Count')
headerRow.append('TM1 - BFMF Songs')
headerRow.append('Total All Songs')


#Append Form Info - If it appears in these forms or not
headerRow.append('Forms')
headerRow.append('Boundary Forms')
headerRow.append('# Abstract Licks')
headerRow.append('Average Licks Length')
headerRow.append('Min Lick Length')
headerRow.append('Max Lick Length')
headerRow.append('Average Reps')
headerRow.append('Song IDs')
headerRow.append('Files')
outputList.append(headerRow)

###############################################
########### OUTPUT DATA #######################
###############################################        

#Populate row info from directory
for abstractLoop in sorted(loopDict, key = lambda abstractLoop: len(abstractLoop), reverse = True):
    #create variables for output
    tm0BMT = 0
    tm0FMT = 0
    tm0BFMT = 0
    tm0BFMF = 0
    tm1BMT = 0
    tm1FMT = 0
    tm1BFMT = 0
    tm1BFMF = 0
    tm7BMT = 0
    tm7FMT = 0
    tm7BFMT = 0
    tm7BFMF = 0
    tm0BMTsongs = 0
    tm0FMTsongs = 0
    tm0BFMTsongs = 0
    tm0BFMFsongs = 0
    tm1BMTsongs = 0
    tm1FMTsongs = 0
    tm1BFMTsongs = 0
    tm1BFMFsongs = 0
    tm7BMTsongs = 0
    tm7FMTsongs = 0
    tm7BFMTsongs = 0
    tm7BFMFsongs = 0
    allSongs = set()
    totalLicks = 0
    singleForms = set()
    boundaryForms = set()
    fileNames = list()    
    avgLickLens = 0
    fileCounter = 0
    totalAbsLicks = 0
    totalRepAvgs = 0

    ###populate row information for loop
    outputRow = list()
    outputRow.append(abstractLoop)
    loopLen = len(abstractLoop.split('_'))
    outputRow.append(loopLen)

    for fileName in loopDict[abstractLoop]:
        directory = loopDict[abstractLoop][fileName]
        fileNames.append(fileName)
        ##Propagate counts for TriadMode, formMode and beatMode licks and songs
        if directory['triadMode'] == 0:
            if directory['beatMode'] == True:
                if directory['formMode'] == True:
                    tm0BFMT = directory['lickTotal']
                    tm0BFMTsongs = len(directory['lickSongs'])
                else: 
                    tm0BMT = directory['lickTotal']
                    tm0BMTsongs = len(directory['lickSongs'])
            else:
                if directory['formMode'] == True:
                    tm0FMT = directory['lickTotal']
                    tm0FMTsongs = len(directory['lickSongs'])
                else: 
                    tm0BFMF = directory['lickTotal']
                    tm0BFMFsongs = len(directory['lickSongs']) 
        elif directory['triadMode'] == 1:
            if directory['beatMode'] == True:
                if directory['formMode'] == True:
                    tm1BFMT = directory['lickTotal']
                    tm1BFMTsongs = len(directory['lickSongs'])
                else: 
                    tm1BMT = directory['lickTotal']
                    tm1BMTsongs = len(directory['lickSongs'])       
            else:
                if directory['formMode'] == True:
                    tm1FMT = directory['lickTotal']
                    tm1FMTsongs = len(directory['lickSongs'])
                else: 
                    tm1BFMF = directory['lickTotal'] 
                    tm1BFMFsongs = len(directory['lickSongs']) 
        elif directory['triadMode'] == 7:
            if directory['beatMode'] == True:
                if directory['formMode'] == True:
                    tm7BFMT = directory['lickTotal']
                    tm7BFMTsongs = len(directory['lickSongs'])
                else: 
                    tm7BMT = directory['lickTotal']
                    tm7BMTsongs = len(directory['lickSongs'])        
            else:
                if directory['formMode'] == True:
                    tm7FMT = directory['lickTotal']
                    tm7FMTsongs = len(directory['lickSongs'])
                else: 
                    tm7BFMF = directory['lickTotal'] 
                    tm7BFMFsongs = len(directory['lickSongs']) 
                             
        #Store total number of songs for loop across files
        allSongs.update(directory['songs'])
        #Store form info for loop across files
        for item in directory['forms']:
            if len(item) == 1:
                singleForms.update(item)
            else:
                boundaryForms.add(item)
        maxLen = 0
        minLen = 100
        for lick in directory['licks']:
            lickLen = len(lick.split('_'))
            avgLickLen = lickLen/len(directory['licks']) #Average lick length
            avgLickLens += avgLickLen
            if lickLen > maxLen:                         #Min and max lick length
                maxLen = lickLen
            if lickLen < minLen:
                minLen = lickLen
            rep = lickLen/loopLen                       #average repeats
            totalRepAvgs += rep
        totalAbsLicks += len(directory['licks'])
        fileNames.append(fileName)
        totalLicks += directory['lickTotal']
        
    ##OUTPUT ROW INFO
    ##SONG LICK INFO PER LOOP
    outputRow.append(tm0BMT)
    outputRow.append(tm0BMTsongs)
    outputRow.append(tm0FMT)
    outputRow.append(tm0FMTsongs)
    outputRow.append(tm0BFMT)
    outputRow.append(tm0BFMTsongs)    
    outputRow.append(tm0BFMF)
    outputRow.append(tm0BFMFsongs)
    outputRow.append(tm7BMT)
    outputRow.append(tm7BMTsongs)
    outputRow.append(tm7FMT)
    outputRow.append(tm7FMTsongs)
    outputRow.append(tm7BFMT)
    outputRow.append(tm7BFMTsongs)
    outputRow.append(tm7BFMF)
    outputRow.append(tm7BFMFsongs)
    outputRow.append(tm1BMT)
    outputRow.append(tm1BMTsongs)
    outputRow.append(tm1FMT)
    outputRow.append(tm1FMTsongs)
    outputRow.append(tm1BFMT)
    outputRow.append(tm1BFMTsongs)
    outputRow.append(tm1BFMF)
    outputRow.append(tm1BFMFsongs)
    
    #Rest of Loop info 
    outputRow.append(len(allSongs))                 #Total Songs
    outputRow.append(sorted(singleForms))           #Single Forms
    outputRow.append(sorted(boundaryForms))         #Boundary Forms
    outputRow.append(totalAbsLicks)                 # Number abstract licks
    try:
        averageLickLen = avgLickLens/totalAbsLicks  #Average length of lick
    except:
        averageLickLen = 0
    outputRow.append(str(averageLickLen))           ###
    outputRow.append(str(minLen))                   ###Min Lick Length
    outputRow.append(str(maxLen))                   ###Max Lick Length
    averageReps = totalRepAvgs/totalAbsLicks        #Average repetitions of loop
    outputRow.append(averageReps)                   ### 
    outputRow.append(sorted(allSongs))             #Sorted Song Loops
    outputRow.append(fileNames)                     #File Names
    outputList.append(outputRow)
    #write rows
    analysisFile = csvPath + '/loopsAnalysisMulti.csv'
    w = csv.writer(open(analysisFile, 'w'))
    for row in outputList:
        w.writerow(row)