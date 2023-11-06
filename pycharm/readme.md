# This is a space for us to put any python scripts or other tools that we Techex develop related to Techex product troubleshooting/configuration

# Current dependencies:
   * Python (Tested/developed on 3.8) 
   * `pip install requests`
   * `pip install numpy` - Used for stbanalyse.py
# Installation and execution steps:
   ### Prefered option:
   * Reccomendation is to use Pycharm to update/run these scripts however this can be done without pycharm
   * If you need help setting this up talk with Jonathan, detailed guide pending 
   * #### Update:
      * git pull from within pycharm
   
   ### Option 2
   * `git clone https://github.com/techexltd/TechexTechnicalPythonScripts.git`
   * `cd TechexTechnicalPythonScripts/Techex/`
   * update /inputdata folder with csv's (examples from live projects exist, true examples pending)
   * `python mwcoreconfig.py -h`
   * #### Update:
      * `cd .../TechexTechnicalPythonScripts/`
      * `git pull`
   
   ### Option 3
   * Download Zip from github.com web ui under the reposity home page
   * unzip in the relevent location 
   * Run as above shows
   * #### Update: 
      * Re-Download Zip and replace files 
      
      
# V0.2.1 Change log (Version to support a range of STB focused functions) 
## stb analyse
  * New code to support input list of device ID's and will review grafana details for last x (default 24) hours of data
  * Based on Grafana data will remove anomily data and then write total and average counters based on the number of active data points grafana responds with.
    * Above supported only for Discontinuity and unrecovered counters, RTT and BW/bitrate are based on averages
  * Code will also ping the External IP to get an indication of RTT if not provided by Grafana data
  * Code will look up geo location 

## csvfunctions.py 
  * #### + Added support for writing a time serires set of data to CSV 
  
## Misc Functions 
  * #### + General get added without support for auth
  * #### + Geo Ip lookup function
  * #### + Ping latency function based on calling ping on OS level 
  * #### + Function to remove "null" values from a list
  * #### + Function to remove outliers from a list of data to support STB data normalization 

## MWfunctions 
  * #### * single re-try logic in mwGet/POST/PUT in case of transient issues
  * #### + Added function to get device/STB details json
  * #### + Function to get device/STB public/external IP
  * #### + Function to get Device/STB geo info based on IP, supports optional pass of IP to speed up function
  * #### + Specific function to simplify STB data and then write specific values back into a STB dictionary
  
## STBlist
  * #### + Querying all devices and printing to CSV if its online at time of query 
  * #### + Providing extra fields for version and serial numbers

# V0.1.3 Change log
## mwcoreconfig.py
  * #### + Added support for updating stream inputs 
  * #### + Added support for searching for stream source ID's 
  * #### + Added support for only creating config for specific entries for streams/sources/inputs/outputs,channel sources and passphrase updates in the input CSV provided to the scripts 
    * This specifically requires the field "action" and the entry "create" to trigger config creation
    * This will support use cases where you have a master CSV and want to add config to a system without having to add config for everything in the CSV or having to create a new set of CSV's
    * This also adds a level of saftey when working around a live system to ensure the scripting will only configure what you requested
    * Python will write back to the original CSV deleting the action entry of "create" or "update" to ensure if you trigger the script again it won't accidently re-configure
  * #### + Started to add frameworks for Create updates and deletes across all config 
## passphraseupdate.py
  * #### + Added support with input CSV to highight with Action field which channel to update
  * #### + Added function to go back and update mwedge output and channel sources csv's with the new passphrases


# V0.1.2 Change log
## mwcoreupdate.py
  * #### + Added support for rotating SRT passphrases 

## mwfunctions.py
  * #### + Exposed core functions from mwconfig to a mwfunctions code which are key functional peices of code 
  
## passphraseupdate.py
  * #### + Added some very specific functions for passphrase rotation for: 
      * MWEdge SRT outputs
      * MWCore Channel source updates

# V0.1.1 Change log
## mwcoreconfig 
 
 * #### + Added support for SRT/RTP input Buffer/Latency settings 
 * #### + Added support for configuring SRT channel sources to a channel list in MWCORE
 * #### + Added support for UDP outputs including Biss encryption variables following correct CSV variables aligning with API response e.g:
``` 
 UDP_data= {
      "stream": "822e35ba82dc52c4d36d6e98ae62773f1f78a522a1933271",
      "options": {
        "ttl": 5,
        "networkInterface": "195.181.164.33",
        "encryptionType": "BISS2 Mode-1",
        "address": "1.1.1.1",
        "port": 1,
        "encryptionPercentage": 10,
        "encryptionKeyParity": "odd",
        "encryptionOddKey": "00000000000000000000000000000000",
        "encryptionEvenKey": "10000000000000000000000000000000"
      },
      "name": "test",
      "protocol": "UDP",
      "id": "7b343d85963af89cb47d55c008ba5e371b85aac8a8c8d91a",
      "mwedge": "5f7de1627def3af9fff8a233"
    }
```
## channelsourcesduplicator.py

 * ### + Added support for duplicating SRT channel sources based on stream output CSV config, more details in: https://github.com/techexltd/TechexTechnicalPythonScripts/issues/14
 * ### + Added support for round robin priorities between origin servers
 * ### + Added support for static priorities between all servers/sources
 * ### + Added support for CLI driven server lists to duplicate config based on


# V0.1.0 change log:
## mwcoreconfig:

* #### Create Streams or Inputs/Outputs but only one option at a time

* #### Create Streams
    * Support for different failover methods
        * Static failover triggers right now, can be made dynamic in next version
    * support for thumbnail on/off
    * Will print out Stream config including stream ID which can be passed to CSV for In/output creation
    
* #### Create Inputs/outputs
    * #### Inputs:
        * Optional Passive option for all Inputs
        * RTP input
            * Optional Source interface and stream address
            * Optional preserve headers
            * optional enable correction
        
        * UDP input
            * Optional Source interface and stream address
            
        * SRT input
            * Optional encryption and passphrase (both needed)
            
        * 2x SRT inputs to 2022-7 input
            * Optional 
    * #### Outputs:
        * Only SRT supported
        * SRT output
            * Optional Encryption and passphrase (both needed)
            * Optional Max connections value 
            * Optional Max Bandwidth
                * This is a soft limit not a hard limit
            * Optional Output interface
            * Optional Chunk size otherwise default to RTP chunk size 

## srtlisteneroutputduplicator.py

* #### Duplicate CSV config ready for SRT outputs
    * Duplicates 2  outputs for each stream
    * Default 50 max connections
    * setting of chunk size to UDP if specified on origin protocol otherwise set to RTP as default
    * Optional encryption, pass phrase based on input passphrase





# Development:

* Expected development practice is to work under branches
* All work merged to development branch
* Work in progress work should be committed to feature/[FEATURE/BUGFIX/IMPLEMENTATION]
    * e.g feature/ReadmeUpdate
* Please keep branch names as short as possible
* Please work using Pycharm and ensure all errors/syntax issues are resolved before submitting pull request.
    * Pycharm will also help to run and debug code as well.
    * It makes life much easier when trying to write in Pycharm vs other programs.
    * It has specific style guidelines that we will follow in the code to ensure readability is preserved!Once ready and all committed within your feature branch then head to github to then create a pull request into the development branch.
* When a pull request is created assign to at least one other peer to review and comment on the code.
    * Treat these peer reviews as a driving lesson, if you forget your indicators its not the end of the world but if on the driving test (Real world execution) you forgot you'd fail!
    * Once you've started work on your feature branch, regardless of if its in a good state or not, submit a pull request.
        * This allows us to track progress through the implementation and comment on every commit rather than one big block of changes right at the end
        * It keeps feedback and personal improvement flowing as you're getting more consistent feedback
        * It ensures you don't end up having to re-write hundreds of lines of code.

    * The above only works though if you commit frequently and often:
        * Commit after implementing any level of functionality.
        * Done the initial scoping of functions or completed the function, commit
        * Updated a section of code that could be considered a discreet update, commit
        
        If we take the above behaviour it makes it really easy to keep track of changes.
        It also ensures you have a history on what changes you've made and can easily roll back if the change you made didn't work!

For any general guidance on the above reach out to Jonathan.
