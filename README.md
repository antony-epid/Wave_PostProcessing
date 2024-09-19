# Introduction
Wave Post Processing is a python project that can post process the output of accelerometery data that has been processed through Wave. The Wave Post Processing project can be run either through PyCharm or through a batch file. It is recommended to set up a virtual environment in a python interpreter (in MRC Epidemiology Unit PyCharm is used) and run the project through this. Follow the user guides on how to setup, prepare and run the project with the two different approaches.

Follow the repository [wiki](https://github.com/CAS254/Wave_PostProcessing/wiki) for detailed user guide on how to set up and run the script. 

# Prerequisites
- Output from accelerometer files that have been processed through Wave.
- Python version 3.12 or higher
- PyCharm Community Edition (If you wish to run the script through PyCharm, can also be run through a batch script and thus installation of PyCharm is not neccesary)

### Further notes 
- This process has been developed on Windows. It has NOT been tested for any other operating system type, e.g. macOS.
- The script has been tested on Python version 3.12. Future versions may be incompatible, although will be tested as they are released.
- The script has been tested on hourly (h) level data. It has NOT been tested on minute (m) level data. With current setup the SUB_SET_PREFIXES in the config file should remain as it is (keeping "1h", "metadata").
- The script has been tested to run on ENMO variables. It has NOT been tested on HPFVM, PITCH, ROLL. With current setup the VARIABLES_TO_DROP in the config file should remain as it is (dropping "HPFVM", "PITCH", "ROLL").


# Downloading and preparing the environment
### Set up folder structure
Set up the folder structure in your project folder on your computer:
- _analysis
- _data
- _feedback
- _logs
- _releases
- _results

The accelerometer files should be saved in the _data folder and the output from Wave processing should be saved in the _results folder (Should be set up when running Wave). 

### Download the code
1. Navigate to the Wave Post Processing repository [here](https://github.com/CAS254/Wave_PostProcessing). 
2. Click  ![image](https://github.com/user-attachments/assets/587012f2-735e-471e-b7c0-38e7977e36ee) and then Download ZIP.
3. Extract the ZIP file into the _analysis folder. Ensure it extracts to a single level of subfolders.

### Install dependencies
Certain python modules are needed to be able to run the code. A requirements.txt  it saved within the ZIP file that was downloaded when downloading the code. This text file contains all requirements needed to be able to run the code. See the User Guides on [GitHub wiki](https://github.com/CAS254/Wave_PostProcessing/wiki) for detailed guide on how to install the dependencies.

# Preparing script to run
For a description of the different part of the Wave Post Processing script see [Explanation of code](https://github.com/CAS254/Wave_PostProcessing/wiki/2.-Explanation-of-code). 

Some variables in the script needs editing to study specific setting before executing it. The 2 files that will need editing are the **config.py** and the **Wave_PostProcessingOrchestra.py**. See [GitHub Wiki](https://github.com/CAS254/Wave_PostProcessing/wiki) for in-depth instructions on how to edit and run the script.

# Output 
The process produces release files of the post processed accelerometer data. It will produce 3 release files with the data in hourly, daily and summary level and each of these files will contain the data for all files/participants appended. The release files will be outputted to the _releases folder together with a data dictionary for each file. All files will be in a CSV format. The project will also output a verification log (if this part of the script is specified to run in the Wave_PostProcessing_Orchestra.py file). The log will be outputted to the _logs folder and will display summaries of the post processed data as well as display if any issues occurred during processing of the accelerometer files. Go through the log to check if any files should be removed before releasing the release files.

