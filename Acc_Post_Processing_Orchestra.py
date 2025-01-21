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
import sys
import config
from colorama import Fore

################
### SWITCHES ###
################
# These switches can be turned on/off depending on which part of the code is wanted to run. Providing all information is correct in config.py, the code should run without any issues
# Change to 'Yes' to run script, change to 'No' if you don't want to run script.
RUN_PAMPRO_MERGE_METAFILES = 'Yes'           # This needs running if accelerometer files are processed through Pampro to merge metafiles into 1 for each person.
RUN_PAMPRO_COLLATE_ANOMALIES = 'Yes'         # This needs running to include information on anomalies if files are processed through Pampro.
RUN_FILELIST_GENERATION = 'Yes'              # Create a filelist of all Wave output files. Depending on what is specified in the config.py, this might be all available or only the new files (that are not in the appended summary file)
RUN_GENERIC_EXH_POSTPROCESSING = 'Yes'       # Generic exhaustive post processing works through generic updates to the Wave output. This needs to be completed before collapsing any data.
RUN_COLLAPSE_RESULTS_TO_SUMMARY = 'Yes'      # Takes the file created from exhaustive post processing and collapses it down to a summary (1 line) file. These are saved as individual files.
RUN_COLLAPSE_RESULTS_TO_DAILY = 'Yes'        # Takes the file created from exhaustive post processing and collapses it down to a daily (1 line per day) file. These are saved as individual files.
RUN_APPEND_SUMMARY_FILES = 'Yes'             # Appends together the individual summary level data files (created within the collapse results to summary file)
RUN_APPEND_DAILY_FILES = 'Yes'               # Appends together the daily level data files (created within the collapse results to summary file)
RUN_APPEND_HOURLY_FILES = 'Yes'              # Appends together the hourly level data files (created within the collapse results to summary file)
RUN_VERIFICATION_CHECKS = 'Yes'              # Verification code will run some basic checks on the summary and hourly level data looking for potential issues (i.e. duplicate/ extreme outliers). Does not need to be ran to prepare release files, but useful to fully check data. Will be outputted in the _logs folder.
RUN_PREPARE_SUMMARY_RELEASE = 'Yes'          # Prepares summary releases. Will be outputted in the _releases folder together with a data dictionary.
RUN_PREPARE_DAILY_RELEASE = 'Yes'            # Prepares daily releases. Will be outputted in the _releases folder together with a data dictionary.
RUN_PREPARE_HOURLY_RELEASE = 'Yes'           # Prepares hourly releases. Will be outputted in the _releases folder together with a data dictionary.

# Python executable used in the virtual environment
venv_python = sys.executable

# Running script:
def run_script(script):
    filelist_script_path = os.path.join(config.ROOT_FOLDER, config.ANALYSIS_FOLDER, script)
    if not os.path.exists(filelist_script_path):
        print(f"Error: The script {filelist_script_path} does not exist.")
        return
    subprocess.run([venv_python, filelist_script_path], check=True)

# Print message that script is being run:
def print_message(message):
    print(Fore.GREEN + message + Fore.RESET)

if __name__ == '__main__':
    # Running Pampro_Merge_MetaFiles script if files were processed through Wave:
    if config.PROCESSING.lower() == 'pampro':
        if RUN_PAMPRO_MERGE_METAFILES.lower() == 'yes':
            print_message("MERGING METAFILES")
            run_script("Pampro_Merge_MetaFiles.py")
        if RUN_PAMPRO_COLLATE_ANOMALIES.lower() == 'yes':
            print_message("COLLATING ANOMALIES")
            run_script("Pampro_Collate_Anomalies.py")

    # Running the Filelist_Generation script:
    if RUN_FILELIST_GENERATION.lower() == 'yes':
        print_message("CREATING FILELIST")
        run_script("Filelist_Generation.py")

    # Running the GENERIC_EXH_POSTPROCESSING script:
    if RUN_GENERIC_EXH_POSTPROCESSING.lower() == 'yes':
        print_message("COMPLETING GENERIC EXHAUSTIVE ANALYSIS")
        run_script("GENERIC_exh_postprocessing.py")

    # Running the Collapse_Results script (to Summary and/or Daily:
    if RUN_COLLAPSE_RESULTS_TO_SUMMARY.lower() == 'yes' or RUN_COLLAPSE_RESULTS_TO_DAILY.lower() == 'yes':
        run_script("Collapse_Results.py")

    # Running the Append_Files script (Appending summary and/or daily and/or hourly):
    if RUN_APPEND_SUMMARY_FILES.lower() == 'yes' or RUN_APPEND_DAILY_FILES.lower() == 'yes' or RUN_APPEND_HOURLY_FILES.lower() == 'yes':
        run_script("Appending_Files.py")

    # Running the Verification_Checks script:
    if RUN_VERIFICATION_CHECKS.lower() == 'yes':
        print_message("COMPLETING VERIFICATION CHECKS ON SUMMARY AND HOURLY DATA")
        run_script("Verification_Checks.py")

    # Preparing releases
    if RUN_PREPARE_SUMMARY_RELEASE.lower() == 'yes' or RUN_PREPARE_DAILY_RELEASE.lower() == 'yes' or RUN_PREPARE_HOURLY_RELEASE.lower() == 'yes':
        run_script("Prepare_releases.py")

    print_message(Fore.BLUE + "The Wave Post Processing code has finished running successfully. \n If ran in PyCharm you can now close PyCharm. \n If ran as batch file: Press Enter to close the script." + Fore.RESET)


