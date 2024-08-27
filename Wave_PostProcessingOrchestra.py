########################################################################################################################################################################
# WAVE POST PROCESSING ORCHESTRA FILE
########################################################################################################################################################################
# This do file will run each section of the post processing for the Wave outputs for Axivity files. Each of the stata scripts have been specially adapted to work with
# a slimmed down dataset as well as having any reference to clock changes removed (due to use in Countries that do not have clock changes.)
# Author: CAS
# Date: 03/06/2024 (Started)
# Version: 1.0
########################################################################################################################################################################

# Importing packages
import os
import subprocess
import config
from colorama import Fore

################
### SWITCHES ###
################
# These switches can be turned on/off depending on which part of the code is wanted to run. Providing all information is correct in  config.py, the code should run without any issues
RUN_FILELIST_GENERATION = 'No' # Create a filelist of all Wave output files. Depending on what is specified in the config.py, this might be all available or only the new files (that are not in the appended summary file)
RUN_GENERIC_EXH_POSTPROCESSING = 'No' # Generic exhaustive post processing works through generic updates to the Wave output. This needs to be completed before collapsing any data.
RUN_COLLAPSE_RESULTS_TO_SUMMARY = 'No' # Takes the file created from exhaustive post processing and collapses it down to a summary (1 line) file. These are save individual files.
RUN_COLLAPSE_RESULTS_TO_DAILY = 'No' # Takes the file created from exhaustive post processing and collapses it down to a daily (1 line per day) file. These are save individual files.
RUN_APPEND_SUMMARY_FILES = 'No' # Appends together the individual summary level data files (created within the collapse to summary do file)
RUN_APPEND_DAILY_FILES = 'No'  # Appends together the daily level data files (created within the collapse to summary do file)
RUN_APPEND_HOURLY_FILES = 'No' # Appends together the hourly level data files (created within the collapse to summary do file)
RUN_VERIFICATION_CHECKS = 'No' # Verification code will run some basic checks on the summary and hourly level data looking for potential issues (i.e. duplicate/ extreme outliers). Does not need to be ran to prepare release files, but useful to fully check data
RUN_PREPARE_SUMMARY_RELEASE = 'No' # Prepares summary releases
RUN_PREPARE_DAILY_RELEASE = 'No'  # Prepares daily releases
RUN_PREPARE_HOURLY_RELEASE = 'No'  # Prepares hourly releases
RUN_DATA_QC = 'Yes' # Running data QC


# Running the Filelist_Generation script:
def filelist_generation_execution():
    filelist_script_path = os.path.join(config.PYTHON_CODE, "Filelist_Generation.py")
    if not os.path.exists(filelist_script_path):
        print(f"Error: The script {filelist_script_path} does not exist.")
        return
    subprocess.run(["python", filelist_script_path], check=True)

# Running the GENERIC_EXH_POSTPROCESSING script:
def generic_exh_postprocessing():
    generic_script_path = os.path.join(config.PYTHON_CODE, "GENERIC_exh_postprocessing.py")
    if not os.path.exists(generic_script_path):
        print(f"Error: The script {generic_script_path} does not exist.")
        return
    subprocess.run(["python", generic_script_path], check=True)

# Running the Collapse_Results_ToSummary script:
def collapse_results_to_summary():
    collapse_to_summary_script_path = os.path.join(config.PYTHON_CODE, "Collapse_Results_ToSummary.py")
    if not os.path.exists(collapse_to_summary_script_path):
        print(f"Error: The script {collapse_to_summary_script_path} does not exist.")
        return
    subprocess.run(["python", collapse_to_summary_script_path], check=True)

# Running the Collapse_Results_ToDaily script:
def collapse_results_to_daily():
    collapse_to_daily_script_path = os.path.join(config.PYTHON_CODE, "Collapse_Results_ToDaily.py")
    if not os.path.exists(collapse_to_daily_script_path):
        print(f"Error: The script {collapse_to_daily_script_path} does not exist.")
        return
    subprocess.run(["python", collapse_to_daily_script_path], check=True)

# Running the Append_Summary_Files script:
def append_summary_files():
    append_summary_files_script_path = os.path.join(config.PYTHON_CODE, "Appending_Summary_Files.py")
    if not os.path.exists(append_summary_files_script_path):
        print(f"Error: The script {append_summary_files_script_path} does not exist.")
        return
    subprocess.run(["python", append_summary_files_script_path], check=True)

# Running the Append_Daily_Files script:
def append_daily_files():
    append_daily_files_script_path = os.path.join(config.PYTHON_CODE, "Appending_Daily_Files.py")
    if not os.path.exists(append_daily_files_script_path):
        print(f"Error: The script {append_daily_files_script_path} does not exist.")
        return
    subprocess.run(["python", append_daily_files_script_path], check=True)


# Running the Append_Hourly_Files script:
def append_hourly_files():
    append_hourly_files_script_path = os.path.join(config.PYTHON_CODE, "Appending_Hourly_Files.py")
    if not os.path.exists(append_hourly_files_script_path):
        print(f"Error: The script {append_hourly_files_script_path} does not exist.")
        return
    subprocess.run(["python", append_hourly_files_script_path], check=True)

# Running the Verification_Checks script:
def verification_checks():
    verification_checks_script_path = os.path.join(config.PYTHON_CODE, "Verification_Checks_v1.2.py")
    if not os.path.exists(verification_checks_script_path):
        print(f"Error: The script {verification_checks_script_path} does not exist.")
        return
    subprocess.run(["python", verification_checks_script_path], check=True)

# Preparing summary releases
def prepare_summary_release():
    prepare_summary_release_path = os.path.join(config.PYTHON_CODE, "Prepare_Summary_Releases.py")
    if not os.path.exists(prepare_summary_release_path):
        print(f"Error: The script {prepare_summary_release_path} does not exist.")
        return
    subprocess.run(["python", prepare_summary_release_path], check=True)


# Preparing daily releases
def prepare_daily_release():
    prepare_daily_release_path = os.path.join(config.PYTHON_CODE, "Prepare_Daily_Releases.py")
    if not os.path.exists(prepare_daily_release_path):
        print(f"Error: The script {prepare_daily_release_path} does not exist.")
        return
    subprocess.run(["python", prepare_daily_release_path], check=True)

# Preparing hourly releases
def prepare_hourly_release():
    prepare_hourly_release_path = os.path.join(config.PYTHON_CODE, "Prepare_Hourly_Releases.py")
    if not os.path.exists(prepare_hourly_release_path):
        print(f"Error: The script {prepare_hourly_release_path} does not exist.")
        return
    subprocess.run(["python", prepare_hourly_release_path], check=True)

# Data QC
def data_qc():
    data_qc_path = os.path.join(config.PYTHON_CODE, "Data_QC.py")
    if not os.path.exists(data_qc_path):
        print(f"Error: The script {data_qc_path} does not exist.")
        return
    subprocess.run(["python", data_qc_path], check=True)



if __name__ == '__main__':
    if RUN_FILELIST_GENERATION == 'Yes':
        print(Fore.GREEN + "CREATING FILELIST" + Fore.RESET)
        filelist_generation_execution()
    if RUN_GENERIC_EXH_POSTPROCESSING == 'Yes':
        print(Fore.GREEN + "COMPLETING GENERIC EXHAUSTIVE ANALYSIS" + Fore.RESET)
        generic_exh_postprocessing()
    if RUN_COLLAPSE_RESULTS_TO_SUMMARY == 'Yes':
        print(Fore.GREEN + "COLLAPSING DATA TO INDIVIDUAL SUMMARY FILES" + Fore.RESET)
        collapse_results_to_summary()
    if RUN_COLLAPSE_RESULTS_TO_DAILY == 'Yes':
        print(Fore.GREEN + "COLLAPSING DATA TO INDIVIDUAL DAILY FILES" + Fore.RESET)
        collapse_results_to_daily()
    if RUN_APPEND_SUMMARY_FILES == 'Yes':
        print(Fore.GREEN + "APPENDING ALL INDIVIDUAL SUMMARY FILES TOGETHER" + Fore.RESET)
        append_summary_files()
    if RUN_APPEND_DAILY_FILES == 'Yes':
        print(Fore.GREEN + "APPENDING ALL INDIVIDUAL DAILY FILES TOGETHER" + Fore.RESET)
        append_daily_files()
    if RUN_APPEND_HOURLY_FILES == 'Yes':
        print(Fore.GREEN + "APPENDING ALL INDIVIDUAL HOURLY FILES TOGETHER" + Fore.RESET)
        append_hourly_files()
    if RUN_VERIFICATION_CHECKS == 'Yes':
        print(Fore.GREEN + "COMPLETING VERIFICATION CHECKS ON SUMMARY AND HOURLY DATA" + Fore.RESET)
        verification_checks()
    if RUN_PREPARE_SUMMARY_RELEASE == 'Yes':
        print(Fore.GREEN + "PREPARING A SUMMARY RELEASE FILE" + Fore.RESET)
        prepare_summary_release()
    if RUN_PREPARE_DAILY_RELEASE == 'Yes':
        print(Fore.GREEN + "PREPARING A DAILY RELEASE FILE" + Fore.RESET)
        prepare_daily_release()
    if RUN_PREPARE_HOURLY_RELEASE == 'Yes':
        print(Fore.GREEN + "PREPARING A HOURLY RELEASE FILE" + Fore.RESET)
        prepare_hourly_release()
    if RUN_DATA_QC == 'Yes':
        print(Fore.GREEN + "RUN THE DATA QC FROM WAVE" + Fore.RESET)
        data_qc()
