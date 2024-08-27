############################################################################################################
# Appending individual Daily files Together
# Author: CAS
# Date: 03/07/2024
# Version: 1.0 Translated from Stata code
############################################################################################################
# IMPORTING PACKAGES #
import config
import os
import pandas as pd


############################################################################################################
# PART B: This do file will append together all individual Daily files as well as join the files which have not produced an individual daily file
############################################################################################################

# CREATING A FILE LIST OF ALL FILES IN THE INDIVIDUAL DAILY FOLDER #
def create_filelist():

    # DELETE ALL PAST FILELISTS IN INDIVIDUAL DAILY FOLDER
    DAILY_FOLDER_PATH = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_DAILY_F, config.TIME_RES_FOLDER)

    if os.path.exists(os.path.join(DAILY_FOLDER_PATH, "filelist.txt")):  # If any filelist in the daily folder, this will be deleted.
        os.remove(os.path.join(DAILY_FOLDER_PATH, "filelist.txt"))

    # CREATING NEW FILELIST IN INDIVIDUAL DAILY FOLDER - CODE IS DIFFERENT FOR MAC AND WINDOWS, CHANGE PC TYPE IN THE BEGINNING OF SCRIPT
    os.chdir(DAILY_FOLDER_PATH)

    if config.PC_TYPE == "WINDOWS":
        os.system('dir /b *csv > filelist.txt')
    elif config.PC_TYPE == "MAC":
        os.system('ls /b *csv > filelist.txt')

# REMOVING FILES THAT SHOULD NOT BE APPENDED #
def remove_files():
    filelist_df = pd.read_csv('filelist.txt', header=None, names=['v1'])  # Reading in the filelist
    filelist_df = filelist_df.rename(columns={'v1': 'file_name'})

    # Dropping the data dictionary from the list and also the list of the main output file if saved in the same location so it is not looped through
    data_dictionary = 'dictionary'
    filelist_df = filelist_df[~filelist_df['file_name'].str.contains(data_dictionary, case=False, na=False)]
    filelist_df = filelist_df[~filelist_df['file_name'].str.contains(config.DAY_OUTPUT_FILE, case=False, na=False)]

    # Creating list with all filenames
    files_list = filelist_df['file_name'].tolist()
    return files_list

# Appending daily files
def appending_files(files_list):
    dataframes = []

    # Looping though each file and appending
    for file_name in files_list:
        file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_DAILY_F, config.TIME_RES_FOLDER, f"{file_name}")

        if os.path.exists(file_path):
            dataframe = pd.read_csv(file_path)
            dataframes.append(dataframe)

    if dataframes:
        appended_df = pd.concat(dataframes, ignore_index=True)
    else:
        appended_df = pd.DataFrame()

    # DROP ANY FILE WITH NO ID
    appended_df = appended_df.dropna(subset=['id'])

    # REMOVING THRESHOLDS FROM THE MAIN OUTPUT FILE IF THIS IS SPECIFIED IN CONFIG FILE
    if config.REMOVE_THRESHOLDS == 'Yes':
        variable_prefix = 'enmo_'
        variable_suffix = 'plus'

        columns_to_drop = []
        for column_name in appended_df.columns:
            if column_name.startswith(variable_prefix) and column_name.endswith(variable_suffix):
                columns_to_drop.append(column_name)

        appended_df = appended_df.drop(columns=columns_to_drop)
    return appended_df

# Creating filelist of any IDS that have not had an analysis file produced from post processing
def no_analysis_filelist():
    no_analysis_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.FILELIST_FOLDER, 'No_Analysis_Files.txt')
    if os.path.exists(no_analysis_path):

        no_analysis_filelist_df = pd.read_csv('No_Analysis_Files.txt', delimiter='\t')  # Reading in the filelist
        no_analysis_filelist_df = no_analysis_filelist_df.drop_duplicates(subset=['filename_temp'])
        no_analysis_filelist = no_analysis_filelist_df['filename_temp'].tolist()

        return no_analysis_filelist

    else:
        return []


# Appending any IDS that have not had an analysis file produced from post processing and outputting the dataset
def appending_no_analysis_files(no_analysis_filelist, appended_df):
    no_analysis_dataframes = []
    if not no_analysis_filelist:
        print("All files had a metadata and data file. No extra data to append")
        output_file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER)
        os.makedirs(output_file_path, exist_ok=True)
        file_name = os.path.join(output_file_path, f"{config.DAY_OUTPUT_FILE}.csv")
        appended_df.to_csv(file_name, index=False)

        return

    for file_id in no_analysis_filelist:

        metadata_file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, f"metadata_{file_id}.csv")
        if os.path.exists(metadata_file_path):
            no_analysis_metadata_df = pd.read_csv(metadata_file_path)

            # Specifying what variables to keep
            variables_to_keep = [
                '.*start_error*.', '.*end_error*.', 'calibration_method', 'noise_cutoff_mg',
                'generic_first_timestamp', 'generic_last_timestamp', 'device', 'processing_epoch',
                '.*anom*.', '.*batt*.'
            ]
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
            no_analysis_metadata_df.drop(columns=['first_battery', 'last_battery'], inplace=True)

            no_analysis_dataframes.append(no_analysis_metadata_df)

        # Appending dataframes if there are any
        if no_analysis_dataframes:
            appended_no_analysis_df = pd.concat(no_analysis_dataframes, ignore_index=True)
        else:
            appended_no_analysis_df = pd.DataFrame()

        # appending the dataset from no_analysis with the ones that have analysis data.
        merged_summary_df = pd.concat([appended_df, appended_no_analysis_df], ignore_index=True)

        # Outputting appended summary dataframe
        output_file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER)
        os.makedirs(output_file_path, exist_ok=True)
        file_name = os.path.join(output_file_path, f"{config.DAY_OUTPUT_FILE}.csv")

        merged_summary_df.to_csv(file_name, index=False)

if __name__ == '__main__':
    create_filelist()
    files_list = remove_files()
    appended_df = appending_files(files_list)
    no_analysis_filelist = no_analysis_filelist()
    appending_no_analysis_files(no_analysis_filelist, appended_df)
