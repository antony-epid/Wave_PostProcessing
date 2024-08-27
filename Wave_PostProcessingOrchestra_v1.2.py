############################################################################################################
# This do file will run each section of the post processing for the Wave outputs for Axivity files. Each of the stata scripts have been specially adapted to work with
# a slimmed down dataset as well as having any reference to clock changes removed (due to use in Countries that do not have clock changes.)
# Author: CAS
# Date: 23/08/2024
# Version: 1.2 Edited to one function that is called multiple times
############################################################################################################

# --- Importing packages --- #
import os
import subprocess
import config
from colorama import Fore

################
### SWITCHES ###
################
# These switches can be turned on/off depending on which part of the code is wanted to run. Providing all information is correct in config.py, the code should run without any issues
# Change to 'Yes' to run script, change to 'No' if you don't want to run script.
RUN_FILELIST_GENERATION = 'No'              # Create a filelist of all Wave output files. Depending on what is specified in the config.py, this might be all available or only the new files (that are not in the appended summary file)
RUN_GENERIC_EXH_POSTPROCESSING = 'No'       # Generic exhaustive post processing works through generic updates to the Wave output. This needs to be completed before collapsing any data.
RUN_COLLAPSE_RESULTS_TO_SUMMARY = 'No'      # Takes the file created from exhaustive post processing and collapses it down to a summary (1 line) file. These are saved as individual files.
RUN_COLLAPSE_RESULTS_TO_DAILY = 'No'        # Takes the file created from exhaustive post processing and collapses it down to a daily (1 line per day) file. These are saved as individual files.
RUN_APPEND_SUMMARY_FILES = 'No'             # Appends together the individual summary level data files (created within the collapse results to summary file)
RUN_APPEND_DAILY_FILES = 'No'               # Appends together the daily level data files (created within the collapse results to summary file)
RUN_APPEND_HOURLY_FILES = 'No'              # Appends together the hourly level data files (created within the collapse results to summary file)
RUN_VERIFICATION_CHECKS = 'No'              # Verification code will run some basic checks on the summary and hourly level data looking for potential issues (i.e. duplicate/ extreme outliers). Does not need to be ran to prepare release files, but useful to fully check data. Will be outputted in the _logs folder.
RUN_PREPARE_SUMMARY_RELEASE = 'No'          # Prepares summary releases. Will be outputted in the _releases folder together with a data dictionary.
RUN_PREPARE_DAILY_RELEASE = 'No'            # Prepares daily releases. Will be outputted in the _releases folder together with a data dictionary
RUN_PREPARE_HOURLY_RELEASE = 'No'           # Prepares hourly releases. Will be outputted in the _releases folder together with a data dictionary.
RUN_DATA_QC = 'Yes'                          # Running data QC. QC log will be outputted in the _logs folder.


# Running script:
def run_script(script):
    filelist_script_path = os.path.join(config.ROOT_FOLDER, config.ANALYSIS_FOLDER, script)
    if not os.path.exists(filelist_script_path):
        print(f"Error: The script {filelist_script_path} does not exist.")
        return
    subprocess.run(["python", filelist_script_path], check=True)

# Print message that script is being run:
def print_message(message):
    print(Fore.GREEN + message + Fore.RESET)

if __name__ == '__main__':

    # Running the Filelist_Generation script:
    if RUN_FILELIST_GENERATION == 'Yes':
        print_message("CREATING FILELIST")
        run_script("Filelist_Generation.py")

    # Running the GENERIC_EXH_POSTPROCESSING script:
    if RUN_GENERIC_EXH_POSTPROCESSING == 'Yes':
        print_message("COMPLETING GENERIC EXHAUSTIVE ANALYSIS")
        run_script("GENERIC_exh_postprocessing.py")

    # Running the Collapse_Results_ToSummary script:
    if RUN_COLLAPSE_RESULTS_TO_SUMMARY == 'Yes':
        print_message("COLLAPSING DATA TO INDIVIDUAL SUMMARY FILES")
        run_script("Collapse_Results_ToSummary.py")

    # Running the Collapse_Results_ToDaily script:
    if RUN_COLLAPSE_RESULTS_TO_DAILY == 'Yes':
        print_message("COLLAPSING DATA TO INDIVIDUAL DAILY FILES")
        run_script("Collapse_Results_ToDaily.py")

    # Running the Append_Summary_Files script:
    if RUN_APPEND_SUMMARY_FILES == 'Yes':
        print_message("APPENDING ALL INDIVIDUAL SUMMARY FILES TOGETHER")
        run_script("Appending_Summary_Files.py")

    # Running the Append_Daily_Files script:
    if RUN_APPEND_DAILY_FILES == 'Yes':
        print_message("APPENDING ALL INDIVIDUAL DAILY FILES TOGETHER")
        run_script("Appending_Daily_Files.py")

    # Running the Append_Hourly_Files script:
    if RUN_APPEND_HOURLY_FILES == 'Yes':
        print_message("APPENDING ALL INDIVIDUAL HOURLY FILES TOGETHER")
        run_script("Appending_Hourly_Files.py")

    # Running the Verification_Checks script:
    if RUN_VERIFICATION_CHECKS == 'Yes':
        print_message("COMPLETING VERIFICATION CHECKS ON SUMMARY AND HOURLY DATA")
        run_script("Verification_Checks_v1.2.py")

    # Preparing summary releases
    if RUN_PREPARE_SUMMARY_RELEASE == 'Yes':
        print_message("PREPARING A SUMMARY RELEASE FILE")
        run_script("Prepare_Summary_Releases.py")

    # Preparing daily releases
    if RUN_PREPARE_DAILY_RELEASE == 'Yes':
        print_message("PREPARING A DAILY RELEASE FILE")
        run_script("Prepare_Daily_Releases.py")

    # Preparing hourly releases
    if RUN_PREPARE_HOURLY_RELEASE == 'Yes':
        print_message("PREPARING A HOURLY RELEASE FILE")
        run_script("Prepare_Hourly_Releases.py")

    # Data QC
    if RUN_DATA_QC == 'Yes':
        print_message("RUN THE DATA QC FROM WAVE")
        run_script("Data_QC.py")

    print_message("The Wave Post Processing code has finished running successfully. Press any key to close the script.")


