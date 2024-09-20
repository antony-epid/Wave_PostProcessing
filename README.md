# Introduction
Wave Post Processing is a Python project designed to post-process accelerometry data that has been processed through Wave. The Wave Post Processing project can be executed either through PyCharm or via a batch file. It is recommended to set up a virtual environment in a Python interpreter (PyCharm is used within the MRC Epidemiology Unit) and run the project through this. Follow the user guides for instructions on how to setup, prepare and run the project using both approaches.

For detailed user guides on setting up and running the script, refer to the repository [wiki](https://github.com/CAS254/Wave_PostProcessing/wiki). 

# Prerequisites
- Output from accelerometer files processed through Wave.
- Python version 3.12 or higher
- PyCharm Community Edition (optional; while the script can also be run through a batch file, installation of PyCharm is recommended as it facilitates setting up a virtual environment and managing dependencies more easily).

### Further notes 
- This process has been developed on Windows and has **NOT** been tested on other operating systems, such as macOS.
- The script has been tested on Python version 3.12. Future versions may be incompatible, but testing will occur as new versions are released.
- The script has been tested on hourly (h) level data and has **NOT** been tested on minute (m) level data. With current setup the ```SUB_SET_PREFIXES``` in the config file should remain as they are (keeping "1h", "metadata").
- The script has been tested to run on ENMO variables and has **NOT** been tested on HPFVM, PITCH or ROLL. With current setup the ```VARIABLES_TO_DROP``` in the config file should remain as is (dropping "HPFVM", "PITCH", "ROLL").
- The script assumes that **ID** will be the first part of filename. It can extra the ID from filenames formatted as either **ID** or **ID_DeviceNumber** (It can be other details than the device number, but it is importaint that ID and additional details are seperated by an underscore). If you filename differs, you will need to edit the code to accomodate this. The section to modify can be found in ```Collapse_Results_ToSummary.py``` under **Creating id variable if it doesn't already exist**. 


# Downloading and preparing the environment
### Set up folder structure
Create the following folder structure in your project directory:
- _analysis
- _data
- _feedback
- _logs
- _releases
- _results

Store the accelerometer files in the ```_data``` folder, while the output from Wave processing should be placed in the ```_results``` folder (Which should be set up when running Wave). 

### Download the code
1. Navigate to the Wave Post Processing repository [here](https://github.com/CAS254/Wave_PostProcessing). 
2. Click  ![image](https://github.com/user-attachments/assets/587012f2-735e-471e-b7c0-38e7977e36ee) and select **Download ZIP**.
3. Extract the ZIP file into the ```_analysis``` folder, ensuring it extracts to a single level of subfolders.

### Install dependencies
Certain Python modules are required to run the code. A **requirements.txt**  it included within the downloaded ZIP file, which contains all necessary dependencies for the project. See the User Guides on [GitHub wiki](https://github.com/CAS254/Wave_PostProcessing/wiki) for detailed instructions on installing these dependencies.

# Preparing script to run
For a description of the different parts of the Wave Post Processing script see [Explanation of code](https://github.com/CAS254/Wave_PostProcessing/wiki/2.-Explanation-of-code). 

Before executing the script, some variables must be edited to study specific setting. The two files that require editing are **config.py** and the **Wave_PostProcessingOrchestra.py**. For in-depth instructions on how to edit and run the script, see the [GitHub Wiki](https://github.com/CAS254/Wave_PostProcessing/wiki).

# Output 
The process generates release files of the post-processed accelerometer data. It will produce three release files containing the data in hourly, daily and summary level. Each file will include data for all files/participants appended together. These files will be saved in the ```_releases``` folder. Each file will have an accompanying data dictionary. All files will be in CSV format. 

If the ```RUN_VERIFICATION_CHECKS``` is activated to run in the ```Wave_PostProcessing_Orchestra.py``` file, a verification log will be produced. The log will be saved in the ```_logs``` folder. It provides summaries of the post processed data and notes any issues encountered during the processing of accelerometer files. Review the log to identify any files that may need removal before finalising the release files.

