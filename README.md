# Scan-APS-logfiles
various tools for extracting information out of the AAPS logfiles

Those tools running on the phone need a python environment, e.g.
   - From the playstore download and install qpthon3 („QPython 3L – Python for Android“ by QpythonLab). 
   - This should create a folder „qpython“ at the top level
   - Go to its subfolder „scripts3“
   - Download the python programmes to this subfolder
 
 On Windows it uses python 3.7 upwards.
 
 
 
 **Tabulate_APS_results.py** 
  
  Lists key results and parameters per loop execution
  
  Main purpose ist to run on loop phone, monitor the active loop, speak alarm notification for missing carbs
  
  Can run an Windows, too. Needs editing the source for the name of the logfile copied to the Windows system



**find_string_batch.py**

  requires *find_string_core.py* to be installed in the same folder    
 
  usage on Windows: search a group of logfiles for occurence of a search string
  ``` 
  find_string_batch.py  <wild-card-AAPS-logfile(s)>  <dummy-text>  "search string including BLANKS"
  ```

  usage on Android12: search active logfile for occurence of a search string
  ``` 
  find_string_batch.py 
  >"search string including BLANKS" will be prompted for
  ``` 



**pump_times_batch.py**

   extracts command execution times for various pump actions like issue SMB or change TBR.
   The result is a tsv-file which you import into a spreadsheet where you can filter for action types.
   With a bit of additional maths you can plot execution time distributions.

   requires *pump_times_core.py* to be installed in the same folder    
 
   usage on Windows: extract pump command execution times from a group of logfiles
   ``` 
   pump_times_batch.py  <wild-card-AAPS-logfile(s)>  <dummy-text>  label_included_in_resulting_tsv_file_name
   ```

   Limitation: the script works for logfiles from ASP3.2 verions up to early AAPS3.3 logs. It needs to be adapted to the more recent AAPS3.3.2.0 logfiles for which in its current state it delivers imcomplete output and is therefore not usable yet.
               
