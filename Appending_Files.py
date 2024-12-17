############################################################################################################
# This file appends the summary, daily and hourly datasets
# Author: CAS
# Date: 03/07/2024
# Version: 1.0 Translated from Stata code
############################################################################################################
# IMPORTING PACKAGES #
import config
import os
import pandas as pd
import Wave_PostProcessingOrchestra


############################################################################################################
# PART A: This do file will append together all individual Summary files as well as join the files which have not produced an individual summary file
############################################################################################################

# CREATING A FILE LIST OF ALL FILES IN THE RESULTS FOLDER #
def create_filelist(folder):

    # DELETE ALL PAST FILELISTS IN INDIVIDUAL SUMMARY FOLDER
    file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, folder, config.TIME_RES_FOLDER)

    if os.path.exists(os.path.join(file_path, "filelist.txt")):  # If any filelist in the summary folder, this will be deleted.
        os.remove(os.path.join(file_path, "filelist.txt"))

    # CREATING NEW FILELIST IN INDIVIDUAL SUMMARY FOLDER - CODE IS DIFFERENT FOR MAC AND WINDOWS, CHANGE PC TYPE IN THE BEGINNING OF SCRIPT
    os.chdir(file_path)

    if config.PC_TYPE.lower() == "windows":
        os.system('dir /b *.csv > filelist.txt')
    elif config.PC_TYPE.lower() == "mac":
        os.system('ls /b *csv > filelist.txt')

    return file_path

# REMOVING FILES THAT SHOULD NOT BE APPENDED #
def remove_files(output_file):
    filelist_df = pd.read_csv('filelist.txt', header=None, names=['v1'])  # Reading in the filelist
    filelist_df = filelist_df.rename(columns={'v1': 'file_name'})

    # Dropping the data dictionary from the list and also the list of the main output file if saved in the same location so it is not looped through
    data_dictionary = 'dictionary'
    filelist_df = filelist_df[~filelist_df['file_name'].str.contains(data_dictionary, case=False, na=False)]
    filelist_df = filelist_df[~filelist_df['file_name'].str.contains(output_file, case=False, na=False)]

    # Creating list with all filenames
    files_list = filelist_df['file_name'].tolist()
    return files_list

# Appending summary files
def appending_files(files_list, file_path, append_level):
    dataframes = []

    # Looping though each file and appending
    if files_list:
        for file_name in files_list:
            full_file_path = os.path.join(file_path, f"{file_name}")

            if os.path.exists(full_file_path):
                dataframe = pd.read_csv(full_file_path)
                dataframes.append(dataframe)

    if dataframes:
        appended_df = pd.concat(dataframes, ignore_index=True)
    else:
        appended_df = pd.DataFrame()

    if append_level == 'hourly':
        appended_df['id'] = appended_df['file_id']

    # DROP ANY FILE WITH NO ID
    appended_df = appended_df.dropna(subset=['id'])

    # REMOVING THRESHOLDS FROM THE MAIN OUTPUT FILE IF THIS IS SPECIFIED IN CONFIG FILE
    if config.REMOVE_THRESHOLDS.lower() == 'yes':
        variable_prefixes = 'enmo_'
        if not any(item.lower() == "hpfvm" for item in config.VARIABLES_TO_DROP):
            variable_prefixes += 'HPFVM_'
        variable_suffix = 'plus'

        columns_to_drop = []
        for variable_prefix in variable_prefixes:
            for column_name in appended_df.columns:
                if column_name.startswith(variable_prefix) and column_name.endswith(variable_suffix):
                    columns_to_drop.append(column_name)

        appended_df = appended_df.drop(columns=columns_to_drop)
    return appended_df

# Creating filelist of any IDS that have not had an analysis file produced from post processing
def no_analysis_filelist():
    no_analysis_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.FILELIST_FOLDER, 'No_Analysis_Files.txt')
    if os.path.exists(no_analysis_path):

        no_analysis_filelist_df = pd.read_csv(no_analysis_path)  # Reading in the filelist
        no_analysis_filelist_df = no_analysis_filelist_df.drop_duplicates(subset=['filename_temp'])
        no_analysis_files = no_analysis_filelist_df['filename_temp'].tolist()

        return no_analysis_files

    else:
        return []


# Appending any IDS that have not had an analysis file produced from post processing and outputting the dataset
def appending_no_analysis_files(no_analysis_files, appended_df, file_name):
    no_analysis_dataframes = []
    if not no_analysis_files:
        print("All files had a metadata and data file. No extra data to append.")
        output_file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER)
        os.makedirs(output_file_path, exist_ok=True)
        file_name = os.path.join(output_file_path, f"{file_name}.csv")
        appended_df.to_csv(file_name, index=False)

        return

    for file_id in no_analysis_files:

        metadata_file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, f"metadata_{file_id}.csv")
        if os.path.exists(metadata_file_path):
            no_analysis_metadata_df = pd.read_csv(metadata_file_path)

            # Specifying what variables to keep
            variables_to_keep = [
                '.*start_error*.', '.*end_error*.', 'calibration_method', 'noise_cutoff_mg',
                'generic_first_timestamp', 'generic_last_timestamp', 'device', 'processing_epoch'
            ]
            # Variables to keep if processed through Wave
            if config.PROCESSING.lower() == 'wave':
                variables_to_keep.extend(['.*anom*.', '.*batt*.'])
            # Variables to keep if processed through Pampro
            if config.PROCESSING.lower() == 'pampro':
                variables_to_keep.extend(['calibration_type'])

            # Joining the variables to be able to use regular expression
            combined_variables = '|'.join(variables_to_keep)
            no_analysis_metadata_df = no_analysis_metadata_df.filter(regex=combined_variables)
            no_analysis_metadata_df['id'] = file_id

            # Renaming variables
            no_analysis_metadata_df = no_analysis_metadata_df.rename(columns={'end_error': 'file_end_error', 'start_error': 'file_start_error', 'noise_cutoff_mg': 'noise_cutoff'})
            variables_to_lower_case = [col for col in no_analysis_metadata_df.columns if col.startswith('QC_')]
            lower_case_mapping = {col: col.lower() for col in variables_to_lower_case}
            no_analysis_metadata_df = no_analysis_metadata_df.rename(columns=lower_case_mapping)

            # Dropping variables:
            if config.PROCESSING.lower() == 'wave':
                no_analysis_metadata_df.drop(columns=['first_battery', 'last_battery'], inplace=True)

            # Formatting time stamp variables:
            generic_timestamps = ['generic_first_timestamp', 'generic_last_timestamp']
            no_analysis_metadata_df[generic_timestamps] = no_analysis_metadata_df[generic_timestamps].apply(lambda x: x.str[:19])

            no_analysis_dataframes.append(no_analysis_metadata_df)

        # Appending dataframes if there are any
        if no_analysis_dataframes:
            appended_no_analysis_df = pd.concat(no_analysis_dataframes, ignore_index=True)
        else:
            appended_no_analysis_df = pd.DataFrame()

        # appending the dataset from no_analysis with the ones that have analysis data.
        merged_df = pd.concat([appended_df, appended_no_analysis_df], ignore_index=True)

        # Outputting appended summary dataframe
        output_file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER)
        os.makedirs(output_file_path, exist_ok=True)
        file_name = os.path.join(output_file_path, f"{file_name}.csv")

        merged_df.to_csv(file_name, index=False)



if __name__ == '__main__':
    # Appending summary files
    if Wave_PostProcessingOrchestra.RUN_APPEND_SUMMARY_FILES.lower() == 'yes':
        summary_file_path = create_filelist(folder=config.INDIVIDUAL_SUM_F)
        summary_files_list = remove_files(output_file=config.SUM_OUTPUT_FILE)
        summary_appended_df = appending_files(summary_files_list, file_path=summary_file_path, append_level='summary')
        no_analysis_files = no_analysis_filelist()
        appending_no_analysis_files(no_analysis_files, summary_appended_df, file_name=config.SUM_OUTPUT_FILE)

    # Appending hourly trimmed files
    if Wave_PostProcessingOrchestra.RUN_APPEND_HOURLY_FILES.lower() == 'yes':
        hourly_file_path = create_filelist(folder=config.INDIVIDUAL_TRIMMED_F)
        hourly_files_list = remove_files(output_file=config.HOUR_OUTPUT_FILE)
        hourly_appended_df = appending_files(hourly_files_list, file_path=hourly_file_path, append_level='hourly')
        no_analysis_files = no_analysis_filelist()
        appending_no_analysis_files(no_analysis_files, hourly_appended_df, file_name=config.HOUR_OUTPUT_FILE)

    # Appending daily files
    if Wave_PostProcessingOrchestra.RUN_APPEND_DAILY_FILES.lower() == 'yes':
        daily_file_path = create_filelist(folder=config.INDIVIDUAL_DAILY_F)
        daily_files_list = remove_files(output_file=config.DAY_OUTPUT_FILE)
        daily_appended_df = appending_files(daily_files_list, file_path=daily_file_path, append_level='daily')
        no_analysis_files = no_analysis_filelist()
        appending_no_analysis_files(no_analysis_files, daily_appended_df, file_name=config.DAY_OUTPUT_FILE)
