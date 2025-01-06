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
import Filelist_Generation
import GENERIC_exh_postprocessing
import Collapse_Results_ToSummary
import Collapse_Results_ToDaily

################
### SWITCHES ###
################
# These switches can be turned on/off depending on which part of the code is wanted to run. Providing all information is correct in config.py, the code should run without any issues
# Change to 'Yes' to run script, change to 'No' if you don't want to run script.
RUN_PAMPRO_MERGE_METAFILES = 'No'           # This needs running if accelerometer files are processed through Pampro to merge metafiles into 1 for each person.
RUN_PAMPRO_COLLATE_ANOMALIES = 'No'         # This needs running to include information on anomalies if files are processed through Pampro.
RUN_FILELIST_GENERATION = 'No'              # Create a filelist of all Wave output files. Depending on what is specified in the config.py, this might be all available or only the new files (that are not in the appended summary file)
RUN_GENERIC_EXH_POSTPROCESSING = 'No'       # Generic exhaustive post processing works through generic updates to the Wave output. This needs to be completed before collapsing any data.
RUN_COLLAPSE_RESULTS_TO_SUMMARY = 'Yes'      # Takes the file created from exhaustive post processing and collapses it down to a summary (1 line) file. These are saved as individual files.
RUN_COLLAPSE_RESULTS_TO_DAILY = 'No'        # Takes the file created from exhaustive post processing and collapses it down to a daily (1 line per day) file. These are saved as individual files.
RUN_APPEND_SUMMARY_FILES = 'No'             # Appends together the individual summary level data files (created within the collapse results to summary file)
RUN_APPEND_DAILY_FILES = 'No'               # Appends together the daily level data files (created within the collapse results to summary file)
RUN_APPEND_HOURLY_FILES = 'No'              # Appends together the hourly level data files (created within the collapse results to summary file)
RUN_VERIFICATION_CHECKS = 'No'              # Verification code will run some basic checks on the summary and hourly level data looking for potential issues (i.e. duplicate/ extreme outliers). Does not need to be ran to prepare release files, but useful to fully check data. Will be outputted in the _logs folder.
RUN_PREPARE_SUMMARY_RELEASE = 'No'          # Prepares summary releases. Will be outputted in the _releases folder together with a data dictionary.
RUN_PREPARE_DAILY_RELEASE = 'No'            # Prepares daily releases. Will be outputted in the _releases folder together with a data dictionary.
RUN_PREPARE_HOURLY_RELEASE = 'No'           # Prepares hourly releases. Will be outputted in the _releases folder together with a data dictionary.

# Python executable used in the virtual environment
venv_python = sys.executable

# Running script:
def run_script(script):
    filelist_script_path = os.path.join(config.ANALYSIS_FOLDER, script)
    if not os.path.exists(filelist_script_path):
        print(f"Error: The script {filelist_script_path} does not exist.")
        return
    subprocess.run([venv_python, filelist_script_path], check=True)

# Print message that script is being run:
def print_message(message):
    print(Fore.GREEN + message + Fore.RESET)


def get_cmd_args(budgacc, arrsize, num_cpu, num_files_per_job, time_in_batch):
    return [f"--account={budgacc}", f"--array=1-{str(arrsize)}", f"--cpus-per-task={num_cpu}", f"--time={time_in_batch}"]

def submit_jobs(func, arrsize=10,num_cpu=1, jid=None, budgacc='BRAGE-SL3-CPU'):
    #cmdargs = get_cmd_args(func_name, budgacc, nfiles, num_files_per_job, bool7d)
    #cmdargs = get_cmd_args(budgacc, arrsize, num_cpu, num_files_per_job, time_in_batch):
    cmdargs = get_cmd_args(budgacc, arrsize, num_cpu, 50, '00:20:00')    

    if jid:
        #sbatch_command = ['sbatch'] + cmdargs +  ['submit_jobs.sh', a1, f"--depend=afterany:{a2}", settings_file, jobfile, 'rfs-Bl26eNcUDB8-users']
        sbatch_command = ['sbatch'] + cmdargs + [f"--depend=afterany:{jid}"] + ['submit_wavejobs.sh', func] 
    else:
        #sbatch_command = ['sbatch'] + cmdargs +  ['submit_jobs.sh', a1, settings_file, jobfile, 'rfs-Bl26eNcUDB8-users']    
        sbatch_command = ['sbatch'] + cmdargs +  ['submit_wavejobs.sh', func]            
    try:
            # Submit the job and capture the output
            output = subprocess.check_output(sbatch_command).decode().strip()
            # Extract the job ID from the output
            job_id = output.split()[-1]
            print(f"Job array submitted successfully with job ID: {job_id}")
            return job_id
    except subprocess.CalledProcessError as e:
            print(f"Error submitting job: {e}")

if __name__ == '__main__':

   #config_file = str(sys.argv[1])
   #jobs_dir = str(sys.argv[2])
   #job_num = int(sys.argv[3])
   #num_jobs = int(sys.argv[4])

    jid = None

    # Running Pampro_Merge_MetaFiles script if files were processed through Wave:
    if config.PROCESSING.lower() == 'pampro':
        if RUN_PAMPRO_MERGE_METAFILES.lower() == 'yes':
            print_message("MERGING METAFILES")
            run_script("Pampro_Merge_MetaFiles.py")
        if RUN_PAMPRO_COLLATE_ANOMALIES.lower() == 'yes':
            print_message("COLLATING ANOMALIES")
            run_script("Pampro_Collate_Anomalies.py")

    # Running the Filelist_Generation script:
    #!!!! use optional argument num_jobs, and make several filelists
    if RUN_FILELIST_GENERATION.lower() == 'yes':
        print_message("CREATING FILELIST")
        #run_script("Filelist_Generation.py")
        Filelist_Generation.create_folders()
        Filelist_Generation.create_filelist()
        Filelist_Generation.remove_files()

    # Running the GENERIC_EXH_POSTPROCESSING script:
    if RUN_GENERIC_EXH_POSTPROCESSING.lower() == 'yes':
        print_message("COMPLETING GENERIC EXHAUSTIVE ANALYSIS")
        #run_script("GENERIC_exh_postprocessing.py")
        # create the command line
        # then check if the number of files are satisfied
        # then create a conditional script; conditioned on the number of script         
        #GENERIC_exh_postprocessing.main()
        #jid = submit_jobs('GENERIC_exh_postprocessing.py', 'rfs-Bl26eNcUDB8-users', 1, 1, False) 
        #jid = submit_jobs('GENERIC_exh_postprocessing.py', 10, jid=jid, budgacc='BRAGE-SL3-CPU') 
        jid = submit_jobs('GENERIC_exh_postprocessing.py', arrsize=10,num_cpu=1, jid=None, budgacc='BRAGE-SL3-CPU')

    # Running the Collapse_Results_ToSummary script:
    if RUN_COLLAPSE_RESULTS_TO_SUMMARY.lower() == 'yes':
        print_message("COLLAPSING DATA TO INDIVIDUAL SUMMARY FILES")
        #run_script("Collapse_Results_ToSummary.py")
        #Collapse_Results_ToSummary.main()
        jid = submit_jobs('Collapse_Results_ToSummary.py', arrsize=10,num_cpu=1, jid=None, budgacc='BRAGE-SL3-CPU')


    # Running the Collapse_Results_ToDaily script:
    if RUN_COLLAPSE_RESULTS_TO_DAILY.lower() == 'yes':
        print_message("COLLAPSING DATA TO INDIVIDUAL DAILY FILES")
        #run_script("Collapse_Results_ToDaily.py")
        Collapse_Results_ToDaily.main()

    # Running the Append_Summary_Files script:
    if RUN_APPEND_SUMMARY_FILES.lower() == 'yes':
        print_message("APPENDING ALL INDIVIDUAL SUMMARY FILES TOGETHER")
        run_script("Appending_Summary_Files.py")

    # Running the Append_Daily_Files script:
    if RUN_APPEND_DAILY_FILES.lower() == 'yes':
        print_message("APPENDING ALL INDIVIDUAL DAILY FILES TOGETHER")
        run_script("Appending_Daily_Files.py")

    # Running the Append_Hourly_Files script:
    if RUN_APPEND_HOURLY_FILES.lower() == 'yes':
        print_message("APPENDING ALL INDIVIDUAL HOURLY FILES TOGETHER")
        run_script("Appending_Hourly_Files.py")

    # Running the Verification_Checks script:
    if RUN_VERIFICATION_CHECKS.lower() == 'yes':
        print_message("COMPLETING VERIFICATION CHECKS ON SUMMARY AND HOURLY DATA")
        run_script("Verification_Checks.py")

    # Preparing summary releases
    if RUN_PREPARE_SUMMARY_RELEASE.lower() == 'yes':
        print_message("PREPARING A SUMMARY RELEASE FILE")
        run_script("Prepare_Summary_Releases.py")

    # Preparing daily releases
    if RUN_PREPARE_DAILY_RELEASE.lower() == 'yes':
        print_message("PREPARING A DAILY RELEASE FILE")
        run_script("Prepare_Daily_Releases.py")

    # Preparing hourly releases
    if RUN_PREPARE_HOURLY_RELEASE.lower() == 'yes':
        print_message("PREPARING A HOURLY RELEASE FILE")
        run_script("Prepare_Hourly_Releases.py")


    print_message(Fore.BLUE + "The Wave Post Processing code has finished running successfully. \n If ran in PyCharm you can now close PyCharm. \n If ran as batch file: Press Enter to close the script." + Fore.RESET)


