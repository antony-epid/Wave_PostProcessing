############################################################################################################
# This file is preparing daily releases
# Author: CAS
# Date: 15/07/2024
# Version: 1.0 Translated from Stata code
############################################################################################################
# IMPORTING PACKAGES #
import os
import config
import pandas as pd
from colorama import Fore
from datetime import date
from Housekeeping import filenames_to_remove


######################################################
# --- IMPORTING AND FORMATTING DAILY OUTPUT FILE --- #
######################################################
def formatting_daily_file():
    daily_output_file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, f'{config.DAY_OUTPUT_FILE}.csv')
    if os.path.exists(daily_output_file_path):
        daily_df = pd.read_csv(daily_output_file_path)

    # Generating id and filename
    daily_df.rename(columns={'id': 'filename'}, inplace=True)
    daily_df['id'] = daily_df['filename'].apply(lambda x: x.split("_")[0])

    # Soring dataset by id
    daily_df = daily_df.sort_values(by=['id', 'day_number'])

    # Generating include criteria
    daily_df['include'] = 0
    daily_df.loc[
        (daily_df['Pwear'] >= config.DAY_PWEAR) &
        (daily_df['Pwear_morning'] >= config.DAY_PWEAR_MORNING) &
        (daily_df['Pwear_noon'] >= config.DAY_PWEAR_QUAD) &
        (daily_df['Pwear_afternoon'] >= config.DAY_PWEAR_QUAD) &
        (daily_df['Pwear_night'] >= config.DAY_PWEAR_QUAD) &
        (daily_df['file_end_error'] <= daily_df['noise_cutoff']), 'include'] = 1

    # Changing order or variables in dataframe
    columns = ['id'] + [col for col in daily_df.columns if col != 'id']
    daily_df = daily_df[columns]

    # --- SECTION TO RUN HOUSEKEEPING AND DROP FILES NOT NEEDED IN FINAL RELEASE --- #
    if config.RUN_HOUSEKEEPING == 'Yes':
        print(Fore.GREEN + "RUNNING HOUSEKEEPING AND DROPPING FILES THAT ARE NOT NEEDED IN FINAL RELEASE" + Fore.RESET)
        daily_df = daily_df[(~daily_df['filename'].isin(filenames_to_remove))]

    # Counting number of files/IDs and print the IDs
    count_number_ids = daily_df['id'].count()
    print(Fore.YELLOW + f'Total number of files/IDs: {count_number_ids}' + Fore.RESET)
    filename_column = daily_df['filename']
    filename_list = filename_column.tolist()
    unique_filename = sorted(set(filename_list))

    grouped = daily_df.groupby('filename')['day_number'].count()
    print(Fore.YELLOW + "Filenames:" + Fore.RESET)
    for filename in unique_filename:
        count_days = grouped.get(filename, 0)
        print(Fore.YELLOW + f'{filename}:    {count_days} days' + Fore.RESET)


    # Saving the release file with todays date
    today_date = date.today()
    formatted_date = today_date.strftime("%d%b%Y")
    output_folder = os.path.join(config.ROOT_FOLDER, config.RELEASES_FOLDER, f'{config.DAY_OUTPUT_FILE}_FINAL_{formatted_date}.csv')
    daily_df.to_csv(output_folder, index=False)

    return daily_df

####################################
# --- CREATING DATA DICTIONARY --- #
####################################
def data_dictionary(daily_df):

    variable_label = {
        "id": "Study ID",
        "filename": "Filename of original raw file",
        "DATE": "Daily date of wear",
        "day_number": "Consecutive day number in recording",
        "dayofweek": "day of week for index time period",
        "Pwear": "Time integral of wear probability based on ACC"
    }

    quadrants = ['morning', 'noon', 'afternoon', 'night']
    quad_morning_hours = ">0 & <=6 hours"
    quad_noon_hours = ">6 & <=12 hours"
    quad_afternoon_hours = ">12 & <=18 hours"
    quad_night_hours = ">18 & <=24 hours"
    label = "Number of valid hrs during free-living;"

    pwear_labels = {
        "Pwear_morning": f"{label} {quad_morning_hours}",
        "Pwear_noon": f"{label} {quad_noon_hours}",
        "Pwear_afternoon": f"{label} {quad_afternoon_hours}",
        "Pwear_night": f"{label} {quad_night_hours}",
        "enmo_mean": "Average acceleration (milli-g)"
    }

    variable_label.update(pwear_labels)

    if config.REMOVE_THRESHOLDS == 'No':
        enmo_variables = [col for col in daily_df.columns if col.startswith("enmo_") and col.endswith("plus")]

        for variables in enmo_variables:
            t1 = variables.replace("enmo_", "")
            threshold = t1.replace("plus", "")
            label = f"Proportion of time spent above >= {threshold} milli-g"
            variable_label[variables] = label

    calibration_labels = {
        "device": "Device serial number",
        "file_start_error": "File error before calibration (single file cal) (mg)",
        "file_end_error": "File error after calibration (single file cal) (mg)",
        "calibration_method": "Calibration method applied (offset/scale/temp)",
        "noise_cutoff": "Threshold set for still bout detection (mg)",
        "processing_epoch": "Epoch setting used when processing data (sec)",
        "TIME_RESOLUTION": "Time resolution of processed data (minutes)",
        "qc_anomalies_total": "Total number of anomalies detected in the file",
        "include": f'1=Pwear>={config.DAY_PWEAR} & all Pwear_quads>={config.DAY_PWEAR_QUAD}'
        }

    variable_label.update(calibration_labels)


    df_labels = pd.DataFrame(list(variable_label.items()), columns=["Variable", "variabel_label"])

    # Determine if variable is numeric
    isnumeric = daily_df.dtypes.apply(lambda x: 1 if pd.api.types.is_numeric_dtype(x) else 0).reset_index()
    isnumeric.columns = ['Variable', 'isnumeric']
    df_labels = pd.merge(df_labels, isnumeric, on='Variable', how='left')

    # Ordering columns
    df_labels = df_labels[['Variable', 'isnumeric', 'variabel_label']]

    file_path = os.path.join(config.ROOT_FOLDER, config.RELEASES_FOLDER)
    os.makedirs(file_path, exist_ok=True)
    file_name = os.path.join(file_path, f'Data_Dict_{config.DAY_OUTPUT_FILE}.csv')
    df_labels.to_csv(file_name, index=False)



#################################
# --- Calling the functions --- #
#################################

if __name__ == "__main__":
    daily_df = formatting_daily_file()
    data_dictionary(daily_df)