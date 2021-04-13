# Scan-APS-logfiles
various tools for extracting information out of the AAPS logfiles

- **Tabulate_APS_results.py** 
  
  Lists key results and parameters per loop execution
  
  Main purpose ist to run on loop phone, monitor the active loop, speak alarm notification for missing carbs
  
  Can run an Windows, too. Needs editing the source for the name of the logfile copied to the Windows system

- **find_string_batch.py**

  search a group of logfiles for occurence of a search string
  
  usage:
  ```
  find_string_batch.py  <wild-card-AAPS-logfile(s)>  <dummy-text>  "search string including BLANKS"
  ```
  requires *find_string_core.py* to be installed in the same folder
