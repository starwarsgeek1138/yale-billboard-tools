import os, string, sys, time, json, csv, collections, numpy

#This Module will compare all CSV results for entropy ngram analyses

#This script does two things:
    #1) It outputs a summary of all the Abstract Loops for each CSV results entropy file (that is, each trial): summary file
    #2) It outputs a comparison of all the CSV data files available in the csv-results folder: comparison file

#METHOD TO ITERATE THROUGH FILES AND PROPAGATE DICTIONARY OF CHAINS
def analyzeCSVResults (theFile, fileName):    
    #create a list of lists for row output for summary file
    rowOutput = list() 
    #create row output for comparison file
    rowOutput2 = list()
    #create dictionary to keep track of abstract loops
    absFormDict = dict()
    #Variables
    entList = list()
    maxEntropy = 0
    summedEntropy = 0
    countEnt = 0
    #create header based on CSV information (for variable attribution)
    header = theFile[0].split(',')
    #Find indexes of list items based on header row
    progIDIndex = header.index('progID')
    absLengthIndex = header.index('Loop Length')
    absFormIndex = header.index('LoopAbs')
    totalSongsIndex = header.index('Total Songs (no Dups)')
    formsIndex = header.index('Forms')
    sortedSongsIndex = header.index('Sorted Songs')
    formBoundaryIndex = header.index('Boundary Cases')
    entropyIndex = header.index('H')
    
    #Get information for each row of CSV file (each progression in file)
    for row in theFile[1:-1]:
        row = row.split(',')
        absForm = row[absFormIndex]
        progID = row[progIDIndex]
        absLength = row[absLengthIndex]
        totalSongs = row[totalSongsIndex]
        entropy = float(row[entropyIndex])
        entList.append(entropy)
        
        #Calculate entropy values
        if entropy > maxEntropy:
            maxEntropy = entropy
        summedEntropy += entropy
        countEnt += 1
        stdEnt = numpy.std(entList)
        
        forms = list(filter(None, row[formsIndex].split(' '))) #filters out empty items and splits output into list by space separators
        sortedSongs = list(filter(None, row[sortedSongsIndex].split(' '))) 
        formBoundary = row[formBoundaryIndex]
        #print (absForm, progID, absLength, totalSongs, forms, sortedSongs, formBoundary)
        #Store in dictionary
        if absForm not in absFormDict:
            absFormDict[absForm] = dict()
            absFormDict[absForm]['Length'] = absLength
            absFormDict[absForm]['Total Count'] = 1
            absFormDict[absForm]['Prog IDs'] = list()
            absFormDict[absForm]['Prog IDs'].append(progID)
            absFormDict[absForm]['Sorted Songs'] = set()
            for song in sortedSongs:
                absFormDict[absForm]['Sorted Songs'].add(song)
            absFormDict[absForm]['Total Songs'] = len(absFormDict[absForm]['Sorted Songs'])
            absFormDict[absForm]['Forms'] = set()
            for form in forms:
                absFormDict[absForm]['Forms'].add(form)
            if formBoundary == 'NoBound':
                absFormDict[absForm]['Boundary'] = False
            else:
                absFormDict[absForm]['Boundary'] = True
        else:
            absFormDict[absForm]['Prog IDs'].append(progID)
            absFormDict[absForm]['Total Count'] += 1
            for song in sortedSongs:
                absFormDict[absForm]['Sorted Songs'].add(song)
            absFormDict[absForm]['Total Songs'] = len(absFormDict[absForm]['Sorted Songs'])
            for form in forms:
                absFormDict[absForm]['Forms'].add(form)
            if absFormDict[absForm]['Boundary'] == False and formBoundary == 'NoBound':
                absFormDict[absForm]['Boundary'] = False
            else:
                absFormDict[absForm]['Boundary'] = True
        
                
    #Define CSV case variables  
    lastRowIndex = len(theFile) - 1                     #Total # of progressions
    lastRow = theFile[lastRowIndex].split(',')          
    entropy = float(lastRow[4].split(' ')[2])           
    probability = float(lastRow[5].split(' ')[2])      
    totalCount = int(lastRow[6].split(' ')[3])   
             
    #Set up row output for each abstract loop for summary output
    for case in absFormDict:
        eachRow = list()
        eachRow.append(case)
        eachRow.append(absFormDict[case]['Length']) 
        eachRow.append(absFormDict[case]['Total Songs'])
        songs = ''
        for piece in sorted(list(absFormDict[case]['Sorted Songs'])):
            songs = songs + ' ' + str(piece)
        eachRow.append(songs)
        progIDs = ''
        for number in sorted(list(absFormDict[case]['Prog IDs'])):
            progIDs = progIDs + ' ' + str(number)
        eachRow.append(progIDs)
        eachRow.append(absFormDict[case]['Total Count'])
        eachRow.append(absFormDict[case]['Boundary'])
        eachRow.append(len(absFormDict[case]['Forms']))
        for structure in sorted(list(absFormDict[case]['Forms'])):
            eachRow.append(structure)
        rowOutput.append(eachRow)
        
    #Set up row output for comparison of CSVs Results
    rowOutput2.append(fileName)
    rowOutput2.append(entropy)
    rowOutput2.append(probability)
    rowOutput2.append(totalCount)
    rowOutput2.append(lastRow[0].split(' ')[1])
    rowOutput2.append(lastRow[1].split(' ')[1])
    rowOutput2.append(lastRow[2].split(' ')[1])
    rowOutput2.append(lastRow[3].split(' ')[1])
    rowOutput2.append(len(absFormDict))
    rowOutput2.append(maxEntropy)
    rowOutput2.append(summedEntropy/countEnt)
    rowOutput2.append(stdEnt)
    return rowOutput, rowOutput2

entropyPath = 'csv-results/entropyResults' # establish folder as entropyPath to parse files
os.chdir(entropyPath)

###HEADERS - make headers for files (both each individual summary list and comparison file) - Make sure to align with fields in METHOD
###Set up header for summary list 
#Set up header for summary output (each file individually) 
headerOutput = list()
headerOutput.append('Abstract Loop')
headerOutput.append('Loop Length')
headerOutput.append('Total Songs')
headerOutput.append('Sorted Songs')
headerOutput.append('Prog IDs')
headerOutput.append('Prog Counts')
headerOutput.append('Boundary?')
headerOutput.append('Form Count')
headerOutput.append('Forms')  

###Output header for comparison file 
headerOutput2 = list()
headerOutput2.append('File Name')
headerOutput2.append('Entropy Threshold')
headerOutput2.append('Prob Threshold')
headerOutput2.append('# Progressions')
headerOutput2.append('Keymode')
headerOutput2.append('Triad Mode')
headerOutput2.append('beatMode')
headerOutput2.append('formMode')
headerOutput2.append('# Abstract Forms')
headerOutput2.append('Max Entropy')
headerOutput2.append('Average Entropy')
headerOutput2.append('Entropy STD')

outputList2 = list() #Output list for comparison file (all analyses combined)

#########CALL FOR ITERATION THROUGH FILES IN GIVEN DIRECTORY
for fileName in os.listdir():  #iterate through CSV output files
    outputList = list() #Output list for summary file (each individual analysis) - needs to clear every iteration
    if fileName.startswith("ngrams-entropy_"):  #ONLY LOOKS at files in directory with "ngrams_entropy" as starting name
        theFile = open(fileName, 'r', newline = '').read().splitlines()
        ##Run METHOD to propagate summary and comparison fields
        fileResults = analyzeCSVResults(theFile, fileName)
        fileRes = fileResults[0] 
        fileRes1 = fileResults[1]
        outputList.append(fileRes)
        outputList2.append(fileRes1)

        #Output Summary Analysis for each file individually
        filenameSum = 'entropyStats' + '_' + fileName
        #Write entropy File Stats
        w = csv.writer(open(filenameSum, 'w'))
        w.writerow(headerOutput)
        for row in outputList:
            for col in sorted(row):
                w.writerow(col)
    else:
        continue
    
#Output Multi-File Comparison information
filenameComp = 'multFileAnalysis'
filenameComp = filenameComp + '.csv'
w = csv.writer(open(filenameComp, 'w'))
w.writerow(headerOutput2)
for thing in outputList2:
    w.writerow(thing)