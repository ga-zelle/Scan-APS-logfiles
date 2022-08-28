# scan AdroidAPS logfile for latest loop decisions
# and present results in tabular format
#
# If last entry included "... carbs req" speak it loud
#
#   Author  Gerhard                 Started 01.Jul.2019
#
# save this py in the ".../qpython/scripts3/" folder

import json
import glob
import sys
import os
import time
import locale
from decimal import *
from datetime import datetime, timedelta
import copy

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
    droid.dialogDismiss()                       # important for Android12
    if "which" in res0.keys():
        res0={"positive":0,"neutral":2,"negative":1}[res0["which"]]
    else:
        res0=-1
    return res0,res

def waitNextLoop(arg):                      # arg = hh:mm:ss of last loop execution
    #E started 05.Nov.2019
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
        waitSec = 180                       # was even negative sometimes
    then = datetime.now() + timedelta(seconds=waitSec)
    thenStr = format(then, '%H:%M')
    print ('\nwaiting ' + str(waitSec) + ' sec for next loop at '+thenStr)
    return waitSec

def getReason(reason, keyword, ending, dezi):
    wo_key = reason.find(keyword)
    #print (wo_key, reason + '\n')
    if wo_key < 0:
        #print (keyword , 'nicht gefunden')
        return ''
    else:
        wo_com = reason[wo_key+len(keyword)+1:].find(ending) + wo_key+len(keyword)+1
        #print (reason[wo_key:])
        key_str = reason[wo_key+len(keyword)+0:wo_com]
        if key_str[len(key_str)-1:].isnumeric():
            #print('keyword='+keyword+'  key_str=['+key_str+']')
            if dezi==1:                                          # round to 1 decimal position
                getcontext().prec = 1
                #key_val = eval(key_str)
                key_str = str(Decimal(key_str) + Decimal(0))
        else:
            #print (keyword, 'vorher: '+key_str + ' endet mit ' + key_str[len(key_str)-1:])
            key_str = key_str[:len(key_str)-1]
        #print (keyword, key_str)
        return key_str

def basalFromReasonOnly(reason, lcount):
    # the method below is very difficult and still incomplete
    # obviously various programmers followed differnet logic how to declare the new rate    
    if reason.find('no temp required')>1 :
        tempReq = '0'
        tempSource = "no temp required"
    else :
        tempReq = getReason(reason, 'maxSafeBasal:',       ',', 3)
        tempSource = "maxSafeBasal:...,"
    if  tempReq == '':
        tempReq = getReason(reason, 'temp',    '~<', 3)
        tempSource = "temp...~<"
    if  tempReq == '':
        tempReq = getReason(reason, 'temp',    '>~', 3)
        tempSource = "temp...>~"
    if  tempReq == '':
        tempReq = getReason(reason, 'temp of', 'U', 3)
        tempSource = "temp of...U"
    if  tempReq == '':
        tempReq = getReason(reason, 'setting',       'U', 3)
        tempSource = "setting...U"
    if  tempReq == '':
        tempReq = getReason(reason, '~ req',   'U', 3)
    if  tempReq == '':
        tempReq = getReason(reason, '<',       'U', 3)
        tempSource = "<...U"
        tempSource = "~ req...U"
    if  tempReq == '':
        tempReq = getReason(reason, 'temp',    '<', 3)
        tempSource = "temp...<"
    print('tempReq in row '+str(lcount)+' from "'+tempSource+'" is ['+tempReq+']')
    if tempReq != '':   tempReq = str(round(eval(tempReq),4))
    else : tempReq = '0'
    #print('tempReq in row '+str(lcount)+' from "'+tempSource+'" is ['+tempReq+']')
    
    return tempReq

def scanLogfile(fn):
    #entries = {}                                                                   # keep recent history in case new logfile starts
    key_SMB = '[DetermineBasalAdapterSMBJS.invoke():1'                              # potential start of Result record, any version
    lcount  = 0
    lf = open(fn, 'r')

    for zeile in lf:
        lcount = lcount + 1
        was_SMB = zeile.find(key_SMB)
        was_Res = zeile.find(']: Result: ')
        if was_SMB>0 and was_Res>0 :
            Curly = zeile[was_SMB+len(key_SMB)+13:]                                 # all 3 keys have same length
            result = json.loads(Curly)
            if result['reason'][:10] == 'Error: CGM':
                break                                                               # like no CGM while loading transmitter
            if True :       #was_delivered>0:                                       # used in case of SMB
                thisTime = result['deliverAt']                                      # incl milliseconds
                if thisTime not in entries:
                    r_list = {}                                                     # restart with empty list
                    r_list['bg'] = result['bg']
                    r_list['iob'] = result['IOB']
                    reason = result['reason']
                    r_list['reason'] = reason
                    r_list['COB']         = result['COB']
                    CarbReqKey            =                   "add'l carbs req w\/in"
                    CarbReqTime           = getReason(reason, CarbReqKey,        'm', 0)
                    if CarbReqTime == '':
                        CarbReqKey        =                   "add'l carbs req w/in" # other spelling
                        CarbReqTime       = getReason(reason, CarbReqKey,        'm', 0)
                    if CarbReqTime == '':
                        CarbReqGram = ''
                    else:
                        wo_carb = reason.find(CarbReqKey)
                        wo_gram = reason[wo_carb-5:].find(' ') + wo_carb-5           # last BLANK before
                        CarbReqGram = reason[wo_gram+1:wo_carb-1]
                    r_list['CarbReqGram'] = CarbReqGram
                    r_list['CarbReqTime'] = CarbReqTime
                     
                    r_list['minPredBG']   = getReason(reason, 'minPredBG',       ' ', 0)
                    r_list['minGuardBG']  = getReason(reason, 'minGuardBG',      ' ', 0)
                    r_list['IOBpredBG']   = getReason(reason, 'IOBpredBG',       ' ', 0)
                    r_list['UAMpredBG']   = getReason(reason, 'UAMpredBG',       ' ', 0)
                    r_list['Eventual BG'] = getReason(reason, 'Eventual BG',     ' ', 0)
                    r_list['insulinReq']  = getReason(reason, 'insulinReq',      ' ', 1)
                    r_list['microBolus']  = getReason(reason, 'Microbolusing',   'U', 2)[1:]    # 2 digits, adds BLANK upfront
                    r_list['maxBolus']    = getReason(reason, 'maxBolus',        ' ', 1)
                    r_list['reqBasal']    = getReason(reason, 'adj. req. rate:', ' ', 1)
                    r_list['maxSafe']     = getReason(reason, 'maxSafeBasal:',   ' ', 1)
                    if 'rate' in result :
                        r_list['tempBasal'] = result['rate']
                    else :
                        r_list['tempBasal'] = eval(basalFromReasonOnly(reason, lcount))
                    
                    print ('\nrow '+str(lcount)+'\n'+str(r_list))
                    entries[thisTime] = r_list
            else:   #elif 1==0: #was_timestamp>was_reason:                          # used in case of AMA
                print (str(was_timestamp), zeile[was_reason:])
                thisTime = zeile[was_timestamp+13:was_timestamp+33]
                if thisTime not in entries:
                    was_bg = zeile.find('"bg":')
                    end_bg = zeile[was_bg:].find(',')
                    bg     = zeile[was_bg:was_bg+end_bg]

                    was_iBL= zeile.find('"IOB":[') + 7                              # position past this list
                    was_iob= zeile[was_iBL:].find('"IOB":') + was_iBL
                    end_iob = zeile[was_iob:].find(',')
                    iob     = zeile[was_iob:was_iob+end_iob]

                    reason = zeile[was_reason+10:]
                    end_reason = reason.find('"')
                    reason = reason[:end_reason]
                    entries[thisTime] = {'bg':bg, 'iob':iob, 'reason':reason}
    lf.close()
    return lcount #, entries

        
#Settings for usage on Android:
IsAndroid = False
test_dir  = '/storage/emulated/0/Android/data/info.nightscout.androidaps/files/'
test_file = 'AndroidAPS.log'
inh10     = glob.glob(test_dir+'*')             # for Android10 or less using AAPS 2.8.2
if len(inh10) > 0:
    IsAndroid = True
    fn = test_dir + test_file

test_dir  = '/storage/emulated/0/AAPS/logs/info.nightscout.androidaps/'
inh11     = glob.glob(test_dir+'*')             # for Android11+ using AAPS 3.0+
if len(inh11) > 0:
    IsAndroid = True
    fn = test_dir + test_file
    
if IsAndroid:
    IsAndroid = True
    import androidhelper
    droid = androidhelper.Android()

    btns = ["Next", "Exit", "Test"]
    items = ["Dieses Smartphon spricht Deutsch", "This smartphone speaks English"]
    pick = 0
    while True:    
        default_pick = [pick]
        pressed_button, selected_items_indexes = mydialog("Pick Language", btns, items, False, default_pick)
        pick = selected_items_indexes[0]
        if   pressed_button ==-1:           sys.exit()                      # external BREAK
        if   pressed_button == 0:           break
        elif pressed_button == 1:           sys.exit()
        elif pressed_button == 2:           droid.ttsSpeak(items[pick])
    if pick == 0:
        antw = 'Gut so, dann bleiben wir dabei,'
        both_ansage  = 'Prüf doch Mal die Lage.'
        carb_ansage0 = 'Du brauchst eventuell Kohlenhydrate,'
        both_ansage1 = 'und zwar circa'
        carb_ansage2 = 'Gramm in den nächsten'
        carb_ansage3 = 'Minuten'
        bolusansage0 = 'Du brauchst eventuell einen extra Bolus,'
        bolusansage2 = 'Einheiten'
        warteansage  = 'keine Änderung in den letzten 3 Minuten'
    else:
        antw = 'OK, I speak English during this session'
        both_ansage  = 'Houston, we may have a situation.'
        carb_ansage0 = 'You may need carbohydrates,'
        both_ansage1 = 'namely about'
        carb_ansage2 = 'grams during the next'
        carb_ansage3 = 'minutes'
        bolusansage0 = 'You may need an extra bolus'
        bolusansage2 = 'units'
        warteansage  = 'same procedure as last 3 minutes'

    #inh = glob.glob(test_dir+'files/*.log')
    #fn = inh[0]
    ClearScreenCommand = 'clear'
    maxItem = '12'    # shows last hour; was: maxItem = input('How many items to list (14)? ')
else:                                                                               # we are not on Android
    IsAndroid = False
    #Settings for development on Windows with SMB events:
    test_dir  = 'C:/gazelle/Dokumente/BZ/Looping/Dev_Last10/'
    #test_dir  = 'C:/gazelle/Dokumente/BZ/Looping/PID/'
    test_file = 'AndroidAPS seit 01Uhr45 mit WLAN NS_queue von 395 abgearbeitet.log'
    test_file = 'AndroidAPS._2019-12-06_00-00-00_.5'
    test_file = 'AndroidAPS28._2021-01-11_02-35-34_.3'
    test_file = 'AndroidAPS._2021-12-11_00-00-00_.2'
    #test_file = 'AndroidAPS_from261to27.log'                        # first use if AAPS 2.7
    #test_file = 'AndroidAPS._2020-09-30_00-00-01_.5'                # received no CGM data for a while
    #test_dir  = 'C:/gazelle/Dokumente/BZ/Looping/Dev Last10/'
    #test_file = 'AndroidAPS.log'
    #Settings for development on Windows with AMA and SMB events:
    #test_dir  = 'C:/gazelle/Dokumente/BZ/Looping/Test 31Mai ua Dev_Tests/'
    #test_file = 'AndroidAPS._2019-05-31_00-00-00_.2_EventTypeExamples.log'
    fn = test_dir + test_file
    ClearScreenCommand = 'cls'
    maxItem = '144'    # shows all

if maxItem == '':
    maxItem = '12'
if not maxItem.isnumeric():
    print (maxItem + ' was not numeric')
    sys.exit()
maxItems = eval(maxItem)

entries = {}
wdhl = 'yes'
lastTime = ''
while wdhl[0]=='y':                                                                 # use CANCEL to stop/exit
    lcount = scanLogfile(fn)
    
    #os.system(ClearScreenCommand)    
    sorted_entries = sorted(entries)
    top10 = min(maxItems, len(entries) )
    stLen = len(str(len(entries))) + len(str(top10))
    box = '+' + '---------------------------------------------------------'[:38+stLen] + '+\n'
    msg = box + '|  last '+str(top10)+' of '+str(len(entries))+' loop decisions & reasons  |\n' + box
    print (msg)
    for thisTime in sorted_entries[len(sorted_entries)-top10:]:                     # last 10 entries
        values = entries[thisTime]
        print ('\n=== timestamp: '+thisTime+' ===>"bg":'+str(values['bg'])+', "iob":'+str(values['iob'])+'\n'+values['reason'])
    
    print ("\n time      ---- predicted BG's ---  -carbs req-"
         +   "        ---Bolus requ--  ---Basal req--" 
         + "\nhh:mm   bg Pred Guard IOB UAM Evtl   [g]  [m]"
         + "    IOB   Req  maxSMB SMB  Req  Safe temp")

    for thisTime in sorted_entries[len(sorted_entries)-top10:]:                     # last 10 entries
        values = entries[thisTime]
        if values["maxSafe"] == '' : # in values:
            maxSafe = '     '
        else:
            maxSafe = values["maxSafe"]
            #print(str(len(maxSafe)), str(maxSafe))
            maxSafes= eval(maxSafe)
            maxSafe = round(maxSafes,2)
            maxSafe = f'{str(maxSafe):>5}'
        print (f'{thisTime[11:16]}Z {values["bg"]:>3}{values["minPredBG"]:>5} '
             + f'{values["minGuardBG"]:>5}{values["IOBpredBG"]:>4}'
             + f'{values["UAMpredBG"]:>4} {values["Eventual BG"]:>4}   '
             + f'{values["CarbReqGram"]:>3}  {values["CarbReqTime"]:>3}   '
             + f'{round(values["iob"],1):>4} '  # {round(values["COB"],1):>4}
             + f'{values["insulinReq"]:>6} {values["maxBolus"]:>5}  '
             + f'{values["microBolus"]:>3} {values["reqBasal"][:4]:>4} '
             +            maxSafe +f'{(str(round(values["tempBasal"]+0.00001,2))+"0")[0:4]:>5}' )

    if IsAndroid:     # tell user about the need to eat, NOW!
        #values = entries[thisTime]
        AlarmGram = values['CarbReqGram']
        lastCOB   = values['COB']
        if AlarmGram !='' and eval(AlarmGram)-lastCOB>6:                            # min 0,5BE missing
            AlarmTime = values['CarbReqTime']
            valTime = eval(AlarmTime)
            valGram = eval(AlarmGram)
            signif  = valTime / valGram
            if signif < 5:                                                          # above threshold of significance
                if thisTime!=lastTime:
                    droid.ttsSpeak(both_ansage)
                    droid.ttsSpeak(carb_ansage0)
                    droid.ttsSpeak(both_ansage1 + AlarmGram + carb_ansage2 + AlarmTime + carb_ansage3)
                else:
                    droid.ttsSpeak(warteansage)
        BolusReqStr = values['insulinReq']
        if BolusReqStr =='':
            BolusReq = 0
        else:
            BolusReq = eval(BolusReqStr)
        maxBolusStr = values['maxBolus']
        if maxBolusStr =='':
            maxBolus = 0
        else:
            maxBolus = eval(maxBolusStr)
        BolusSMBStr = values['microBolus']
        if BolusSMBStr =='':
            BolusSMB = 0
        else:
            BolusSMB = eval(BolusSMBStr)
        if int(BolusReq*0.7) > BolusSMB:                                            # BolusSMB limited by maxBolus
            if thisTime!=lastTime:
                getcontext().prec = 1
                AlarmBolus = str(Decimal(BolusReq) - Decimal(BolusSMB))
                droid.ttsSpeak(both_ansage)
                droid.ttsSpeak(bolusansage0)
                droid.ttsSpeak(both_ansage1 + AlarmBolus + bolusansage2)
            else:
                droid.ttsSpeak(warteansage)

    if False:                                                                       # no re-run on Windows
        droid.dialogShow()
        numb = droid.getInput('titel', 'message', '10').result
        if numb == '':      numb = '10'
        print (numb)
        maxItem = eval(numb)
        #res = droid.getSelectedItems().result
        print ('res0: ', res0)
        for button in res0:
            if button == 'which':
                if res0['which'] == 'negative':
                    wdhl = 'no'
        droid.dialogDismiss()
    if IsAndroid:
        #wdhl = input('\n' + str(lcount)+ ' rows scanned. Run again(y)? ') + 'yes'  # makes yes the default
        old_entries = copy.deepcopy(sorted_entries)
        for oldTime in old_entries:
            if oldTime not in sorted_entries[len(sorted_entries)-top10:]:
                del entries[oldTime]                                                # not in last 14 entries
        howLong = waitNextLoop(thisTime[11:19])        
        lastTime = thisTime
        time.sleep(howLong)
    else:   break


sys.exit()
