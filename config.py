########################################################################################################################
# This file contains all global variables across the different .py files.
# Once updated these variables should not need altering again (unless any post processing decisions change)
# Any variable that read EDIT: Edit to study specific settings unless you are happy with what it is already specified to.
# Any variable that read DO NOT EDIT: Does not need editing unless you want to use different naming of folders, files etc.
# Author: CAS
# Date: 03/06/2024
# Version: 1.0
########################################################################################################################

# --- IMPORT PACKAGES --- #
from datetime import date

########################################################################################################################
# --- OVERALL VARIABLES, FOLDERS AND FILES --- #
# Variables below will need adjusting to fit the study being post processed #
# Follow the comments at each variable to check which variables to edit and which do not need editing #
########################################################################################################################

# --- OVERALL VARIABLES THAT WORK ACROSS PYTHON FILES --- #
PROJECT = "example_project_name"                # EDIT: Name of the project going through post processing. Do not use space (replace with _) E.g., study_name
REMOVE_THRESHOLDS = 'No'                        # EDIT: Set to 'Yes' if you want to remove ENMO thresholds (Wave produces these automatically. If not needed for study these can be removed). Set to 'No' if you want to keep them.
PC_TYPE = "WINDOWS"                             # EDIT: Choice of "WINDOWS" or "MAC". Code runs slightly different on windows and mac.
count_prefixes = "1h"                           # DO NOT EDIT: Processing resolution. Specify what time resolutions you want. Normally "1h" (1m is not tested)
PC_DATE = date.today().strftime("%d%b%Y")       # DO NOT EDIT.
PROCESSING = 'Pampro'                             # EDIT: 'Wave' if files were processed through Wave or 'Pampro' if files were processed through Pampro.


# --- FOLDERS --- #
ROOT_FOLDER = 'example_file_path_project_folder'                                                    # EDIT: Root folder for the project
ANALYSIS_FOLDER = '_analysis/Wave_PostProcessing-master'                                            # EDIT: Where the post-processing .py files are saved
RESULTS_FOLDER = '_results'                                                                         # DO NOT EDIT BUT MAKE SURE _results FOLDER EXISTS IN ROOT_FOLDER: Where the wave outputs / results are saved
RELEASES_FOLDER = '_releases'                                                                       # DO NOT EDIT BUT MAKE SURE _releases FOLDER EXISTS: Where the release files will be saved
FEEDBACK_FOLDER = '_feedback'                                                                       # DO NOT EDIT BUT MAKE SURE _feedback FOLDER EXISTS: For the csv files used to create the feedback plot
LOG_FOLDER = '_logs'                                                                                # DO NOT EDIT BUT MAKE SURE _logs FOLDER EXISTS. Where the verification and QC data log files will be saved.
ANOMALIES_FOLDER = '_anomalies'                                                                     # DO NOT EDIT BUT MAKE SURE _anomalies FOLDER EXISTS. Any anomalies.csv files created when files were processed through pampro should be saved here.
FILELIST_FOLDER = 'Filelists'                                                                       # DO NOT EDIT: Auto generated folder where post processing filelist is saved (Found within _results folder)
SUMMARY_FOLDER = 'Summary_Files'                                                                    # DO NOT EDIT: Auto generated folder where all summary files are saved (Found within _results folder)
INDIVIDUAL_PARTPRO_F = 'Individual_PartPro_files'                                                   # DO NOT EDIT: Auto generated folder for individual part processed files (found within _Summary_Files folder)
INDIVIDUAL_SUM_F = 'Individual_Summary_files'                                                       # DO NOT EDIT: Auto generated folder to contain all individual summary files (found within _Summary_Files folder)
INDIVIDUAL_DAILY_F = 'Individual_Daily_files'                                                       # DO NOT EDIT: Auto generated folder to contain all individual daily files (found within _Summary_Files folder)
INDIVIDUAL_TRIMMED_F = 'Individual_Trimmed_files'                                                   # DO NOT EDIT: Auto generated folder to contain all individual hourly trimmed files (found within _Summary_Files folder)
TIME_RES_FOLDER = f"{count_prefixes}_level"                                                         # DO NOT EDIT: Auto generated folder for the specified time resolution (within each summary/daily/hourly folder)
WEAR_LOG_FOLDER = '_analysis/trim_times'                                                           # EDIT: Name of folder were the wear log is saved in, if a wear log is used. Add the name of the sub-folder as well if the wear log is saved within a sub-folder in the root folder for the project.


# --- HOUSEKEEPING --- #

RUN_HOUSEKEEPING = 'Yes'        # EDIT: Set to 'Yes' if you have housekeeping script to drop any duplicates etc. Set to 'No' if you don't have a housekeeping script to run.
RUN_CORRUPTIONS_HOUSEKEEPING = 'Yes'  # EDIT: Set to 'yes' if you have a corruptions housekeeping file to adjust pwear based on verification checks
CORRUPTION_CONDITION_FILE_PATH = 'C:/Users/cas254/PycharmProjects/PostProcessing/corruptions_conditions.csv'  # EDIT: Edit to the file path for the corruptions_conditions filepath, this should include the name and file extension of the file itself. (e.g., corruptions_conditions.csv)

###########################################################################
# --- VARIABLES BELOW ARE SPECIFIC TO EACH PART OF THE POSTPROCESSING --- #
###########################################################################

# --- FILELIST GENERATION ADDITIONAL VARIABLES --- #
# EDIT: Variables below can be adapted depending on the Wave output. Can also be changed if wanting to post process all files again or just newly added files.
SUB_SET_PREFIXES = ['1h', 'metadata']                # DO NOT EDIT: File resolution and meta files to look for when creating filelist. (Add each in the format ['1h', 'metadata']). Not tested on minute level data.
ONLY_NEW_FILES = 'Yes'                               # EDIT: Set to 'No' if you want to process all files. If running a dataset as continue processing throughout the study can be set to "Yes" so only new files are processed.


# --- GENERIC EXH POSTPROCESSING ADDITIONAL VARIABLES --- #
# EDIT: Variables below can be adapted if you want to specify other variables to drop and if you wish to adjust for daylight saving times.
VARIABLES_TO_DROP = []     # DO NOT EDIT: Specify what variables to drop (Normally this will be ["HPFVM", "PITCH", "ROLL"]). Not tested to run on HPFVM, PITCH and ROLL yet.
CLOCK_CHANGES = 'Yes'                               # EDIT: If set 'Yes' it will adjust data for daylight savings. Swith to 'No' if in a country without clock changes
TIMEZONE = 'Europe/London'                          # EDIT: Change to the timezone data is collected in. To find correct name for timezone, in google type "pytz timezone" followed by the country (Or see list herehttps://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568)
USE_WEAR_LOG = 'Yes'                              # EDIT: Set to 'Yes' if there is a wear log and to use only certain days (specified in wear log).
WEAR_LOG = 'example_wear_log'                           # EDIT: Name of wear log file if MERGE_WEAR_LOG is Yes.
# DO NOT EDIT: Variables below do not need editing if you are happy with the standard file naming output.
ANOMALIES_FILE = 'collapsed_anomalies.csv'          # DO NOT EDIT: Filename for collapsed anomalies files. This file is generated if data were processed through Pampro and if the Pampro_Collate_Anomalies are run (only if any anomalies are present in dataset)
OUTPUT_FILE_EXT = f"{count_prefixes}_part_proc"     # DO NOT EDIT: Extension for the output files from exhaustive post processing.


# --- COLLAPSE RESULTS TO SUMMARY AND/OR DAILY LEVEL ADDITIONAL VARIABLES --- #
# Variables in here are used to define inclusion criteria for post processing on summary and daily level. It is possible to truncate data and remove noise/anomaly f end hour.
# SUMMARY
SUM_OVERALL_MEANS = 'SUMMARY_MEANS'                 # DO NOT EDIT: Suffix for the summary level output filename, found on the end of each individual file. Do not need editing if you are happy with the standard file naming output.
SUM_MIN_HOUR_INCLUSION = 18                         # EDIT: How many hours overall need to be present for that specific volunteer for values to be included in the output.

# DAILY
DAY_OVERALL_MEAN = 'DAILY_MEANS'                    # DO NOT EDIT: Suffix for the daily level output filename, found on the end of each individual file. Do not need editing if you are happy with the standard file naming output.
DAY_MIN_HOUR_INCLUSION = 8                          # EDIT: How many daily hours need to be present for that specific volunteer for values to be included in the output.

# BOTH
TRUNCATE_DATA = 'No'                                # EDIT: Set to 'Yes' if want to truncate data to X days rather than leaving the whole file in. Set to 'No' if you want to leave whole file in.
NO_OF_DAYS = 7                                      # EDIT: Set to number of days to be added to the start data if have start but no end date (taken from wearing time).
REMOVE_MECH_NOISE = 'Yes'                           # EDIT: Set to 'Yes' if you want to set Pwear to 0 for hours that have been flagged as potential mechanical noise. Flag produced at Generic_exh_postprocessing. Set to 'No' if you want to keep Pwear as it is.
DROP_END_ANOM_F = 'Yes'                             # EDIT: Set to 'Yes' to drop the last data point of the file if the file contain an Anomaly F. Set to 'No' if you want to keep the last data point.
IMPUTE_DATA = 'Yes'                                 # EDIT: If the monitor was worn for 6+ hours during the day but not during night you can impute sleep data. Change to 'Yes' if you want to impute sleep data and no if you don't want to. You can't impute sleep data on days where monitor was not worn.
IMPUTE_HOURS = [1, 2, 3, 4, 5, 6]                   # DO NOT EDIT: Which hours of day you want to impute (e.g., 1=00:00-01:00, 2=01:00-02:00)
MIN_DAY_HOURS = 6                                   # EDIT: Number of hours within a day that has to be worn before sleep can be imputed (for that day)

# List of anomaly variables as the naming are different from wave and pampro - DO NOT EDIT THIS:
ANOM_VAR_PAMPRO = ['Anom_A', 'Anom_B', 'Anom_C', 'Anom_D', 'Anom_E', 'Anom_F']
ANOM_VAR_WAVE = ['QC_anomaly_A', 'QC_anomaly_B', 'QC_anomaly_C', 'QC_anomaly_D', 'QC_anomaly_E', 'QC_anomaly_F', 'QC_anomaly_G']

# --- APPENDING SUMMARY / DAILY / HOURLY DATASETS --- #
# DO NOT EDIT: Variables below do not need editing if you are happy with the standard file naming output. Will use project name specified previously.
# SUMMARY
SUM_OUTPUT_FILE	= f'{PROJECT}_SUMMARY_MEANS'        # DO NOT EDIT: Output filename for the summary appended dataset.
# DAILY
DAY_OUTPUT_FILE	= f'{PROJECT}_DAILY_MEANS' 	        # DO NOT DIT: Output filename for the daily appended dataset.
# HOURLY
HOUR_OUTPUT_FILE = f'{PROJECT}_HOURLY_TRIMMED_MEANS' # DO NOT EDIT: Output filename for the hourly appended dataset.


# --- VERIFICATION CHECKS --- #
# DO NOT EDIT: All variables below do not need editing if you are happy with the name of verification log and using ENMO as standard variables to verify.
VER_PWEAR = 72                                      # DO NOT EDIT: The minimum number of hours of wear to signify the file contains enough data to be included (on summary data). Will be outputted to verification log if less.
VER_PWEAR_MORN = 9                                  # DO NOT EDIT: The minimum hours of wear needed within the morning quadrant to show monitor was worn overnight (on summary data). Will be outputted to verification log if less.
VER_PWEAR_QUAD = 9                                  # DO NOT EDIT: The minimum hours of wear needed within each of noon, afternoon and night quadrants to be included (on summary data). Will be outputted to verification log if less.

VERIF_NAME = 'Verification_Log'                     # DO NOT EDIT: Name of the verification log to be outputted in the _results folder. Edit if you wish a different name.
VERIFY_VARS = ['enmo']                              # DO NOT EDIT: Variables used in verification, e.g. ['enmo', 'hpfvm']. Only tested on ENMO variables.

MIN_INCLUSION_HRS = 96                              # EDIT: Minimum number of hours recorded --> If below this it will be flagged as device stopped recording early
PROTOCOL_FREQUENCY = 100                            # EDIT: Frequency the devices are set up to record data at for the study/ project. Keep as 100 if device is recording at 100 hz.


# --- PREPARING SUMMARY/HOURLY/DAILY RELEASES -- #
# EDIT: In the variables below you can specify how many hours of wear a file need to be on summary and daily basis to count as valid.
# SUMMARY
SUM_PWEAR = 72                                      # EDIT: Minimum number of hours to signify a summary file contains enough data to be included in final release.
SUM_PWEAR_MORNING = 9                               # EDIT: Minimum number of hours needed within the morning quadrant to show the monitor worn overnight.
SUM_PWEAR_QUAD = 9                                  # EDIT: Minumum number of hours needed within each of noon, afternoon and night quadrants to be included in final release.

# DAILY
DAY_PWEAR = 12                                      # EDIT: Minimum number of hours to signify each day contains enough data to be included in final release.
DAY_PWEAR_MORNING = 3                               # EDIT: Minimum number of hours needed each day within morning quadrant to show monitor worn overnight
DAY_PWEAR_QUAD = 3                                  # EDIT: Minumum number of hours needed each day within each of noon, afternoon and night quadrant to be included in final release.
