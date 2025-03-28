import sys
import os
import glob
import time

from pump_times_core import parameters_known
from pump_times_core import set_tty

def mydialog(title,buttons=["OK"],items=[],multi=False,default_pick=[0,1]):
    # adapted from "https://stackoverflow.com/questions/51874555/qpython3-and-androidhelper-droid-dialogsetsinglechoiceitems"
    title = str(title)
    droid.dialogCreateAlert(title)
    if len(items) > 0:
        if multi:
            droid.dialogSetMultiChoiceItems(items, default_pick)   # incl. list of defaults
        else:
            droid.dialogSetSingleChoiceItems(items, default_pick[0])
    if len(buttons) >= 1:
        droid.dialogSetPositiveButtonText(buttons[0])
    if len(buttons) >= 2:
        droid.dialogSetNegativeButtonText(buttons[1])
    if len(buttons) == 3:
        droid.dialogSetNeutralButtonText(buttons[2])
    droid.dialogShow()
    res0 = droid.dialogGetResponse().result
    res = droid.dialogGetSelectedItems().result
    if "which" in res0.keys():
        res0={"positive":0,"neutral":2,"negative":1}[res0["which"]]
    else:
        res0=-1
    return res0,res

def waitNextLoop(arg,varName):                  # arg = hh:mm:ss of last loop execution, optionally appended 'Z'
    #E started 05.Nov.2019
    if arg == 'Z':                              # no entry found for SMB loop
        waitSec = 310                           # this shoud include at leat 1 loop
    else:
        loophh = eval('1'+arg[0:2]) - 100       # handle leading '0'
        loopmm = eval('1'+arg[3:5]) - 100       # handle leading '0'
        loopss = eval('1'+arg[6:8]) - 100       # handle leading '0'
        LoopSec= loophh*3600 + loopmm*60 + loopss
        now = time.gmtime()
        now_hh = now[3]                         # tm_hour
        now_mm = now[4]                         # tm_min
        now_ss = now[5]                         # tm_sec
        if now_hh<loophh:
            now_hh = 24                         # past midnight
        nowSec = now_hh*3600 + now_mm*60 + now_ss
        waitSec = LoopSec + 300 + 10 - nowSec   # until next loop including 10 secs spare
        if waitSec<10:
            waitSec = 60                        # was even negative sometimes
    then = datetime.now() + timedelta(seconds=waitSec)
    thenStr = format(then, '%H:%M')
    print ('Variant "' + varName + '"\nwaiting ' + str(waitSec) + ' sec for next loop at '+ thenStr)
    return waitSec


###############################################
###    start of main                        ###
###############################################

#how_to_print = 'GUI'
how_to_print = 'print'
#et_tty(runframe, lfd,  how_to_print)            # export print settings to main routine
set_tty(0,        0,    how_to_print)            # export print settings to main routine


# try whether we are on Android:
test_dir  = '/storage/emulated/0/AAPS/logs/info.nightscout.androidaps/'
test_dir  = '/storage/emulated/0/AAPS/logs/info.nightscout.androidaps/'          # always find it even when starting new logfile
test_file = 'AndroidAPS.log'
inh = glob.glob(test_dir+'*')
#print (str(inh))
if len(inh) > 0:
    IsAndroid = True
    import androidhelper
    droid=androidhelper.Android()
    
    inh = glob.glob(test_dir+'*.log')
    fn = inh[0]

    myseek  = fn
    arg2 = 'Android/'+'ebbes'                       # the feature list what to find  #
    defaultStr = 'RhinoException'
    varFile = input('Enter string to search for (' + str(defaultStr) + ') ? ')
    if varFile == '':           varFile = defaultStr
    #varFile = 'dura_ISF adaptation'

    t_stoppLabel = '2099-00-00T00:00:00Z'           # defaults to end of centuary, i.e. open end
    t_startLabel = '2000-00-00T00:00:00Z'           # defaults to start of centuary, i.e. open start
else:                                                                               # we are not on Android
    IsAndroid = False
    #Settings for development on Windows with SMB events:
    #test_dir  = 'C:\Users\gerhard\Documents\Samsung\SmartSwitch\backup\SM-N950F\info.nightscout.androidaps\files\2020-10/'
    #test_file = 'AndroidAPS._2020-10-23_00-00-09_.6.zip'
    #fn = test_dir + test_file
    ClearScreenCommand = 'cls'
    maxItem = '144'    # shows all

    myseek  = sys.argv[1] #+ '\\'
    arg2    = 'Windows/' + sys.argv[2]              # the feature list what to plot; here dummy
    varDriver = sys.argv[3]                         # the variant labe; here output file label
    if len(sys.argv)>=6:
        t_stoppLabel = sys.argv[5]                  # last loop time to evaluate
    else:
        t_stoppLabel = '2099-00-00T00:00:00Z'       # defaults to end of centuary, i.e. open end
    if len(sys.argv)>=5:
        t_startLabel = sys.argv[4]                  # first loop time to evaluate
    else:
        t_startLabel = '2000-00-00T00:00:00Z'       # defaults to start of centuary, i.e. open start
#print ('evaluate from '+t_startLabel+' up to '+t_stoppLabel)

wdhl = 'yes'
entries = {}
lastTime = '0'
parameters_known(myseek, arg2, varDriver, t_startLabel, t_stoppLabel, entries)


if IsAndroid:       os._exit(os.EX_OK)              # terminate this script OK, but keep others alive
sys.exit()

