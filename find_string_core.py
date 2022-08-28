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



def scanLogfile(fn, entries):
    global fn_base                              # keep first match in case of wild card file list
    global log
    global varlog
    global newLoop
    global loopCount
    
    if filecount == 0 :                         # initalize file loop
        fn_base =      fn + '.' + var_Name      # mod V3
        log     = open(fn_base + '.found', 'w')
    #log.write('AAPS logfile scan for string"'+varLabel+'"n created on ' + formatdate(localtime=True) + '\n')
    log.write('FILE='+fn + '\n')
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
    
    cont = 'MORE'                               # in case nothing found
    while notEOF:                               # needed because "for zeile in lf" does not work with AAPS 2.5
        try:                                    # needed because "for zeile in lf" does not work with AAPS 2.5
            zeile = lf.readline()               # needed because "for zeile in lf" does not work with AAPS 2.5
            if isZip:   zeile = str(zeile)[2:-3]# strip off the "'b....'\n" remaining from the bytes to str conversion
            if zeile == '':                     # needed because "for zeile in lf" does not work with AAPS 2.5
                notEOF = False                  # needed because "for zeile in lf" does not work with AAPS 2.5
                break                           # needed because "for zeile in lf" does not work with AAPS 2.5
            lcount +=  1
            #print(zeile)
            if zeile.find(varLabel) >=0:  
                log.write('row'+f'{str(lcount):>6} '+zeile+'\n')
                print('row'+f'{str(lcount):>6} '+zeile)
                loopCount += 1

        except UnicodeDecodeError:              # needed because "for zeile in lf" does not work with AAPS 2.5 containing non-printing ASCII codes
            lcount +=  1                        # skip this line, it contains non-ASCII characters!
            
    lf.close()
    return cont


def parameters_known(myseek, arg2, variantFile, startLabel, stoppLabel, entries):
    #   start of top level analysis
    
    global fn
    global varLabel, var_Name                       # mod V3
    global fn_first

    global  filecount, loopCount
    global  t_startLabel, t_stoppLabel
    global  varFile
    
    global  isAndroid                               # flag for running on Android
    global  isZip                                   # flag for input file type
    global  newLoop                                 # flag whether data collection for new loop started
    #global  entries
    
    
    t_startLabel= startLabel
    t_stoppLabel= stoppLabel
    filecount   = 0
    loopCount   = 0
    oldloopCount= 0
        
    myfile = ''
    #arg2 = arg2.replace('_', ' ')                  # get rid of the UNDERSCOREs
    #doit = arg2.split('/')
    varFile = variantFile                           # on Windows
    varLabel = os.path.basename(varFile)            # do not overwrite the calling arg value
    if varLabel[len(varLabel)-4:] == '.dat' :       # drop the tail coming from DOS type ahead
        varLabel = varLabel[:-4]
    print('initially:', varLabel)
    var_Name = varLabel.replace('"', '_')           # mod V3
    var_Name = var_Name.replace(':', '_')           # mod V3
    var_Name = var_Name.replace('{', '_')           # mod V3
    var_Name = var_Name.replace('}', '_')           # mod V3
    var_Name = var_Name.replace('[', '_')           # mod V3
    var_Name = var_Name.replace(']', '_')           # mod V3
    print('finally  :', varLabel)
    
    logListe = glob.glob(myseek+myfile, recursive=False)
    if arg2[:7] == 'Android' :
        isAndroid = True
    else:
        isAndroid = False
        
    for fn in logListe:
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
    if loopCount == 0 :
        log_msg ('no entries found in logfile(s): "'+myseek+'"')
        #return     #sys.exit()
    log.write('ENDE\n')
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
    print('Found', str(loopCount),'occurences in', str(filecount),'files\nresults saved in file "'+ fn_base + '.found"')
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
