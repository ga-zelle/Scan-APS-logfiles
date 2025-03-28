#
"""
	Scan APS logfile and extract relevant items
"""
#	Version INIT		Started	08.Dec.2019			Author	Gerhard Zellermann
#   - adapted from scanAPSlog.py
#   Version 3           Status  30.Nov.2021
#   - convert characters fom search text to '_' if not allowed in path name

import sys
import os
import glob
from email.utils import formatdate
import datetime
from datetime import timezone
import time
import zipfile
from decimal import *
import binascii
import copy

global  clockStart, task, subtask
clockStart = 0

def hole(sLine, Ab, Auf, Zu):
    #E extrahiere Substring ab der Stelle "ab"
    #E	beginnend mit dem Zeichen "Auf" bis zum Zeichen "Zu"
    #E	wobei Level gezählt werden wie in "...[xxx[yy]]..."
    offsetAnf = 0
    offsetEnd = 0
    Anf_pos = sLine[Ab:].find(Auf) + Ab
    while Anf_pos>=0:
        End_pos = sLine[Anf_pos+offsetEnd+1:].find(Zu) + Anf_pos+offsetEnd+1
        if End_pos == Anf_pos+offsetEnd+1*0:    break
        Zw_Anf = sLine[Anf_pos+offsetAnf+1:End_pos].find(Auf) + Anf_pos+offsetAnf+1
        if Zw_Anf==Anf_pos+offsetAnf:   #+1  or  Zw_Anf>End_pos:
            return sLine[Anf_pos:End_pos+1]
            break
        offsetAnf = Zw_Anf  - Anf_pos
        offsetEnd = End_pos - Anf_pos #+ 1
    return ''

def getUTC(zeile, baseUTC):
    hours = eval('1'+zeile[:2]  +'-100')
    mins  = eval('1'+zeile[3:5] +'-100')
    secs  = eval('1'+zeile[6:13]+'-100')
    utc = baseUTC + (hours*3600 + mins*60 + secs)*1000
    return str(utc)[:-2]
    
def receiveBg(zeile):
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    wo = zeile.find('Extras.Time') + 11 +3
    bgStamp= hole(zeile, wo,     ' ', ';')[1:-1]    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab +tab +tab+bgStamp +tab+str(lcount) +'\n')

def gotXdrip(zeile):
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    wo = zeile.find('Extras.Time') + 11
    bgStamp= hole(zeile, wo,     '=', ',')[1:-1]    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab +tab +tab+bgStamp +tab+str(lcount) +'\n')

def doneXdrip(zeile):
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    wo = zeile.find('Worker result')
    other  = zeile[wo:]    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab +tab +tab+str(lcount) +'\n')

def doneLoadBg(zeile):
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    wo = zeile.find('Worker result')
    other  = zeile[wo:]    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab +tab +tab+str(lcount) +'\n')

def insertBg(zeile):
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    wo = zeile.find('dateCreated') + 11
    created= hole(zeile, wo,     '=', ',')[1:-1]
    wo = zeile.find('timestamp') + 9
    bgStamp= hole(zeile, wo,     '=', ',')[1:-1]    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab +tab+created +tab+bgStamp +tab+str(lcount) +'\n')

def inBgReadings(zeile):
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    wo = zeile.find(' stamp=') + 6
    bgStamp= hole(zeile, wo,     '=', ';')[1:-1]    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab +tab +tab+bgStamp +tab+str(lcount) +'\n')

def sendEventNewBg(zeile):
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    other  = 'Sending EventNewBG'    
    wo = zeile.find('Timestamp') + 9
    bgStamp= hole(zeile, wo,     '=', ']')[1:-1]    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab +tab+bgStamp +tab+str(lcount) +'\n')

def sendEventNewHistoryData(zeile):
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    wo = zeile.find('oldDataTimestamp') + 16
    bgStamp= hole(zeile, wo,     '=', ',')[1:-1]
    wo = zeile.find('reloadBgData') + 13
    reload = hole(zeile, wo,     '=', ']')[1:-1]
    other  = 'Sending EventNewHistoryData, - reloadBgData=' + reload      
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab +tab+bgStamp +tab+str(lcount) +'\n')

def calcNewBg(zeile):
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    other  = 'Starting calculation worker: EventNewBG'    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab +tab +tab+str(lcount) +'\n')

def sendNewBg(zeile):
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    other  = 'Sending EventBucketedDataCreated'    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab +tab +tab+str(lcount) +'\n')

def invokeLoop(zeile):
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    wo = zeile.find(']:')
    other  = zeile[wo+3:]
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab +tab +tab+str(lcount) +'\n')

def doneIobCalc(zeile):
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    wo = zeile.find(']:')
    other  = zeile[wo+3:]
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab +tab +tab+str(lcount) +'\n')

def startLoop(zeile):
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    other  = '>>> Invoking determine_basal <<<'    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab +tab +tab+str(lcount) +'\n')

def elapsed(utc):
    global clockStart
    delta = ( eval(utc) - clockStart ) / 1000
    return str(delta).replace('.', ',')
    
def finishConnect(zeile):
    if clockStart == 0:     return
    global varDriver
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    other  = 'finished '+ varDriver + ' connect'    
    global task, subtask
    subtask = 'finish connect'    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab+task +tab+subtask +tab+str(lcount) +tab+elapsed(utc) +'\n')

def triggerConnect(zeile):
    if clockStart == 0:     return
    global varDriver
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    other  = 'finished '+ varDriver + ' connect'    
    global task, subtask
    subtask = 'connect'    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab+task +tab+subtask +tab+str(lcount) +tab+elapsed(utc) +'\n')
                                                                
def triggerNewTBR(zeile):
    utc = getUTC(zeile, baseUTC)
    global clockStart
    global varDriver
    clockStart = eval(utc)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    other  = 'triggered '+ varDriver + ' new TBR'    
    global task, subtask
    task = 'new TBR'
    subtask = 'trigger'    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab+task +tab+subtask +tab+str(lcount) +tab+elapsed(utc) +'\n')
                                                                
def triggerSMB(zeile):
    utc = getUTC(zeile, baseUTC)
    global clockStart
    global varDriver
    clockStart = eval(utc)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    other  = 'triggered '+ varDriver + ' new SMB'    
    global task, subtask
    task = 'new SMB'
    subtask = 'trigger'    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab+task +tab+subtask +tab+str(lcount) +tab+elapsed(utc) +'\n')
                                                                
def finishNewTBR(zeile):
    if clockStart == 0:     return
    global varDriver
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    other  = 'finished '+ varDriver + ' new TBR'    
    global task, subtask
    subtask = 'finish'    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab+task +tab+subtask +tab+str(lcount) +tab+elapsed(utc) +'\n')
                                                               
def readStatus(zeile):
    utc = getUTC(zeile, baseUTC)
    global clockStart, varDriver
    clockStart = eval(utc)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    other  = varDriver + ' get status'    
    global task, subtask
    task = 'read status'
    subtask = 'trigger'    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab+task +tab+subtask +tab+str(lcount) +tab+elapsed(utc) +'\n')
                                                              
def threadEnd(zeile):
    if clockStart == 0:     return
    global varDriver
    utc = getUTC(zeile, baseUTC)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    other  = ''+ varDriver + ' thread end'    
    global task, subtask
    subtask = 'end thread'    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab+task +tab+subtask +tab+str(lcount) +tab+elapsed(utc) +'\n')

def triggerCancelTBR(zeile):
    utc = getUTC(zeile, baseUTC)
    global clockStart, varDriver
    clockStart = eval(utc)
    offset = 12
    action = hole(zeile, offset, '[', ']')[1:-1]
    offset += len(action) + 2
    phase  = hole(zeile, offset, ' ', ':')[1:-1]
    offset += len(phase) + 2
    module = hole(zeile, offset, '[', ']')[1:-1]
    other  = 'triggered '+ varDriver + ' camcel TBR'    
    global task, subtask
    task = 'cancel TBR'
    subtask = 'trigger'    
    log.write(zeile[:12] +tab+utc +tab+action +tab+phase +tab+module +tab+other +tab+task +tab+subtask +tab+str(lcount) +tab+elapsed(utc) +'\n')
    
def scanLogfile(fn, entries):
    global fn_base                              # keep first match in case of wild card file list
    global log, tab, lcount, baseUTC
    global varlog, varDriver
    global newLoop
    global loopCount
    tab = chr(9)
    baseUTC = 1720562400000
    
    if filecount == 0 :                         # initalize file loop
        fn_base = os.path.basename(fn)+'.'+varDriver # var_Name      # fn + '.' + ....
        log     = open(fn_base + '.tsv', 'w')
        log.write('LOG_STAMP' +tab+'UTC' +tab+'ACTION' +tab+'PHASE' +tab+'MODULE' +tab+'OTHER' +tab+'TASK' + tab+'SUBTASK' +tab+'ZEILE' +tab+'ELAPSED' +'\n')
    #log.write('AAPS logfile scan for string"'+varLabel+'"n created on ' + formatdate(localtime=True) + '\n')
    #og.write('LOG_STAMP' +tab+'UTC' +tab+'ACTION' +tab+'PHASE' +tab+'MODULE' +tab+'OTHER' +tab+'CREATED' +tab+'SOURCE_STAMP' +tab+'ZEILE' +'\n')
    global lcount
    lcount  = 0
    if isZip:
        with zipfile.ZipFile(fn) as z:
            for filename in z.namelist():
                lf = z.open(filename)                               # has only 1 member file
    else:
        lf = open(fn, 'r')
    #lf = open(fn, 'r')
    notEOF = True                               # needed because "for zeile in lf" does not work with AAPS 2.5
    blankRows = 0
    cont = 'MORE'                               # in case nothing found
    while notEOF:                               # needed because "for zeile in lf" does not work with AAPS 2.5
        try:                                    # needed because "for zeile in lf" does not work with AAPS 2.5
            zeile = lf.readline()               # needed because "for zeile in lf" does not work with AAPS 2.5
            if isZip:   zeile = str(zeile)[2:-3]# strip off the "'b....'\n" remaining from the bytes to str conversion
            lcount +=  1
            if zeile == '':                     # needed because "for zeile in lf" does not work with AAPS 2.5
                blankRows += 1
                print(str(lcount), str(blankRows), end='\r')
                if blankRows>30000:
                    notEOF = False                  # needed because "for zeile in lf" does not work with AAPS 2.5
                    break                           # needed because "for zeile in lf" does not work with AAPS 2.5
            #print(zeile)
            if   zeile.find('D/PUMPQUEUE: [CommandQueueImplementation.add():') >0:
                if    zeile.find('TEMP BASAL') >0 :                                         triggerNewTBR(zeile)
                elif  zeile.find('CANCEL TEMPBASAL') >0 :                                   triggerCancelTBR(zeile)
                elif  zeile.find('SMB BOLUS') >0 :                                          triggerSMB(zeile)
                elif  zeile.find('READSTATUS') >0 :                                         readStatus(zeile)
                elif  zeile.find('SET PROFILE') >0 :                                        pass
                else:   print('anderes Kommando in zeile', str(lcount))
            elif zeile.find('D/PUMPQUEUE: [QueueThread.run():114]: connect') >0:            triggerConnect(zeile) 
            elif zeile.find('D/PUMPQUEUE: [QueueThread.run():121]: connection time ') >0:   finishConnect(zeile)    # older ruffy
            elif zeile.find('D/PUMPQUEUE: [QueueThread.run():123]: connection time ') >0:   finishConnect(zeile)
            elif zeile.find('D/PUMPQUEUE: [QueueThread.run():161]: thread end') > 0:        threadEnd(zeile)        # older ruffy
            elif zeile.find('D/PUMPQUEUE: [QueueThread.run():163]: thread end') > 0:        threadEnd(zeile)


        except UnicodeDecodeError:              # needed because "for zeile in lf" does not work with AAPS 2.5 containing non-printing ASCII codes
            lcount +=  1                        # skip this line, it contains non-ASCII characters!
            
    lf.close()
    print('\n')
    return cont

def parameters_known(myseek, arg2, variantDriver, startLabel, stoppLabel, entries):
    #   start of top level analysis
    
    global fn
    global varLabel, var_Name                       # mod V3
    global fn_first

    global  filecount, loopCount
    global  t_startLabel, t_stoppLabel
    global  varDriver
    
    global  isAndroid                               # flag for running on Android
    global  isZip                                   # flag for input file type
    global  newLoop                                 # flag whether data collection for new loop started
    #global  entries
    
    varDriver = variantDriver
    t_startLabel= startLabel
    t_stoppLabel= stoppLabel
    filecount   = 0
    loopCount   = 0
    oldloopCount= 0
        
    myfile = ''
    #arg2 = arg2.replace('_', ' ')                  # get rid of the UNDERSCOREs
    #doit = arg2.split('/')
    #varFile = variantFile                           # on Windows
    #varLabel = os.path.basename(varFile)            # do not overwrite the calling arg value
    #if varLabel[len(varLabel)-4:] == '.dat' :       # drop the tail coming from DOS type ahead
    #    varLabel = varLabel[:-4]
    #print('initially:', varLabel)
    #var_Name = varLabel.replace('"', '_')           # mod V3
    #var_Name = var_Name.replace(':', '_')           # mod V3
    #var_Name = var_Name.replace('{', '_')           # mod V3
    #var_Name = var_Name.replace('}', '_')           # mod V3
    #var_Name = var_Name.replace('[', '_')           # mod V3
    #var_Name = var_Name.replace(']', '_')           # mod V3
    #print('finally  :', varLabel)
    
    logListe = glob.glob(myseek+myfile, recursive=False)
    if arg2[:7] == 'Android' :
        isAndroid = True
    else:
        isAndroid = False
        
    # ---   add sorting info    -----------------------------------
    sorted_fn = {}
    for fn in logListe:
        lenfn = len(fn)
        basefn= os.path.basename(fn)
        basefn= basefn.replace('AndroidAPS._', '')          # default starting with YYYY-MM-TT
        if basefn[4]+basefn[7]+basefn[10] == '--_' :        # assume regular date sting
            #print('checking for fit of '+ basefn)
            if (basefn[:10]>=t_startLabel[:10]):    # undo: and (basefn[:10]<=t_stoppLabel[:10]):   # otherwise date outside window
                ftype = fn[lenfn-3:]
                if ftype=='zip' or ftype=='log' or ftype.find(".")>=0:
                    if fn[lenfn-6:lenfn-5] == '.':
                        #print('pseud ist einstellig')
                        fnpseudo = fn[:lenfn-5] + '0' + fn[lenfn-5:]
                    else:
                        #print('pseud ist zweistellig')
                        fnpseudo = fn
                    fcounter = fn[lenfn-6:-4]
                    sorted_fn[fnpseudo] = fn    #os.path.basename(fn)
                #print(str(sorted_fn))
                pass
    if len(sorted_fn) == 0:
        sorted_fn[myseek] = myseek              # in case of special naming use just that file

    for ps in sorted(sorted_fn):
        fn = sorted_fn[ps]
        ftype = fn[len(fn)-3:]
        useFile = False
        if isAndroid and ftype=='log':                                                  useFile = True
        elif not isAndroid and (ftype=='zip' or ftype=='log' or ftype.find('.')>0) :    useFile = True      # valid logfiles should end with "_.0" thru "_.99" or "zip"
        #print(ftype, str(useFile))
        if useFile:
            isZip = ( ftype == 'zip')
            if filecount == 0 :                     # initalize file loop
                #ce_file = fn + '.' + varLabel + '.txt'
                #cel = open(ce_file, 'w')
                #cel.write('AAPS scan from ' + varLabel + ' for SMB comparison created on ' + formatdate(localtime=True) + '\n')
                #cel.write('FILE='+fn + '\n')
                #cel.close()
                #my_ce_file(ce_file)                 # exports name to determine_basal.py
                fn_first = fn
            if not isAndroid:        log_msg ('Scanning logfile '+fn)
            cont = scanLogfile(fn, entries)
            #print('returned to parameters_known:', CarbReqGram, 'when:', CarbReqTime)
            if oldloopCount < loopCount:
                log_msg('         contained ' + str(loopCount-oldloopCount) + ' occurences')
                oldloopCount = loopCount
            filecount += 1
            if cont == 'STOP':      break           # end of time window reached
    
    if filecount == 0 :
        log_msg ('no such logfile: "'+myseek+'"')
        return 
    #loopCount = len(loop_mills)
    #if loopCount == 0 :
        #log_msg ('no entries found in logfile(s): "'+myseek+'"')
        #return     #sys.exit()
    #log.write('ENDE\n')
    log.close()
    #varlog.close()
    
    if loopCount > 0 :   # ---   save the results from current logfile   --------------
        sepLine = ''
        for i in range(177):
            sepLine += '-'
        #tabz = 'Totals:'+ f'{round(origSMBsum,1):>116} {round(emulSMBsum,1):>4} {round(origBasalint,2):>10} {round(emulBasalint,2):>7}'
        #print(sepLine + '\n' + tabz)
        #xyf.write(sepLine + '\n' + tabz + '\n')
    #xyf.close()
    #print('Found', str(loopCount),'occurences in', str(filecount),'files\nresults saved in file "'+ fn_base + '.tsv')
    pass  
    
def set_tty(printframe, txtbox, channel):               # for GIU
    global how_to_print
    how_to_print = channel
    global runframe
    runframe = printframe
    global lfd
    lfd = txtbox
        
def log_msg(msg):                                       # for GUI
    if how_to_print == 'GUI':
        lfd['state'] = 'normal'
        lfd.insert('end', msg + '\n')
        lfd.see('end')
        lfd['state'] = 'disabled'
        runframe.update()                                                       # update frame display
    else:
        print(msg)
