############################################################################################################
# This file is preparing final hourly releases and meta data
# Author: CAS
# Date: 17/07/2024
# Version: 1.0 Translated from Stata code
############################################################################################################
# IMPORTING PACKAGES #
import os
import config
import pandas as pd
from colorama import Fore
from datetime import date
from Housekeeping import ids_to_remove

#######################################################
# --- IMPORTING AND FORMATTING HOURLY OUTPUT FILE --- #
#######################################################
def formatting_hourly_file():
    hourly_output_file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, f'{config.HOUR_OUTPUT_FILE}.csv')
    if os.path.exists(hourly_output_file_path):
        hourly_df = pd.read_csv(hourly_output_file_path)

    # Generating id and filename
    hourly_df.rename(columns={'file_id': 'filename'}, inplace=True)
    hourly_df['id'] = hourly_df['filename'].apply(lambda x: x.split("_")[0])

    # Soring dataset by id
    hourly_df = hourly_df.sort_values(by=['id', 'DATETIME'])

    # Renaming calibration error variables
    hourly_df.rename(columns={'start_error': 'file_start_error', 'end_error': 'file_end_error'}, inplace=True)

    # Dropping variables that are not needed
    variables_to_drop = ['generic_first_timestamp', 'generic_last_timestamp', 'database_id']
    hourly_df.drop(columns=variables_to_drop, inplace=True)

    # Setting PWear to 0 if ENMO_mean is negativ
    hourly_df.loc[(hourly_df['ENMO_mean'] < 0), 'Pwear'] = 0

    # Changing order or variables in dataframe
    columns = ['id'] + [col for col in hourly_df.columns if col != 'id']
    hourly_df = hourly_df[columns]
    columns_order = list(hourly_df.columns)
    columns_order.insert(columns_order.index('ENMO_mean'), columns_order.pop(columns_order.index('Pwear')))
    hourly_df = hourly_df[columns_order]

    # Dropping variables if they exist
    drop_variables = ['DATETIME_ORIG', 'subject_code', 'processing_script', 'prestart', 'postend', 'valid', 'freeday_number', 'serial', 'ENMO_n', 'ENMO_missing']
    hourly_df.drop(columns=drop_variables, inplace=True, errors='ignore')

    # --- SECTION TO RUN HOUSEKEEPING AND DROP FILES NOT NEEDED IN FINAL RELEASE --- #
    if config.RUN_HOUSEKEEPING == 'Yes':
        print(Fore.GREEN + "RUNNING HOUSEKEEPING AND DROPPING FILES THAT ARE NOT NEEDED IN FINAL RELEASE" + Fore.RESET)
        hourly_df = hourly_df[(~hourly_df['id'].isin(ids_to_remove)) & (~hourly_df['filename'].isin(ids_to_remove))]

    # Counting number of files/IDs and print the IDs
    count_number_ids = hourly_df['id'].count()
    print(Fore.YELLOW + f'Total number of files/IDs: {count_number_ids}' + Fore.RESET)
    id_column = hourly_df['id']
    id_list = id_column.tolist()
    unique_ids = sorted(set(id_list))
    id_counts = hourly_df['id'].value_counts().sort_index()
    print(Fore.YELLOW + "IDs and number of files per ID:" + Fore.RESET)
    for id, count in zip(unique_ids, id_counts):
        print(Fore.YELLOW + f'{id:} {count}' + Fore.RESET)

    # Saving the release file with todays date
    today_date = date.today()
    formatted_date = today_date.strftime("%d%b%Y")
    output_folder = os.path.join(config.ROOT_FOLDER, config.RELEASES_FOLDER, f'{config.HOUR_OUTPUT_FILE}_FINAL_{formatted_date}.csv')
    hourly_df.to_csv(output_folder, index=False)

    return hourly_df



####################################
# --- CREATING DATA DICTIONARY --- #
####################################
def data_dictionary(hourly_df):

    variable_label = {
        "id": "Study ID",
        "filename": "Filename of original raw file",
        "timestamp": "Date & Time of index time period",
        "DATETIME": "Date & Time of index time period ",
        "DATE": "Date",
        "TIME": "Time",
        "dayofweek": "day of week for index time period",
        "hourofday": "Hour of day for index time period",
        "Pwear": "Time integral of wear probability based on ACC",
        "ENMO_mean": "Average acceleration (milli-g)",
        "ENMO_sum": "Sum of enmo (milli-g)"
    }


    if config.REMOVE_THRESHOLDS == 'No':
        enmo_variables = [col for col in hourly_df.columns if col.startswith("ENMO_") and col.endswith("plus")]

        for variables in enmo_variables:
            t1 = variables.replace("ENMO_", "")
            threshold = t1.replace("plus", "")
            label = f"Proportion of time spent above >= {threshold} milli-g"
            variable_label[variables] = label

    calibration_labels = {
        "temperature_mean": "Average temperature (degrees celsius)",
        "integrity_sum": "Calculated in Wave. -1=missing data; 0=passed integrity checks; 1=failed checks",
        "Battery_mean": "Average battery level",
        "device": "Device serial number",
        "file_start_error": "File error before calibration (single file cal) (mg)",
        "file_end_error": "File error after calibration (single file cal) (mg)",
        "calibration_method": "Calibration method applied (offset/scale/temp)",
        "noise_cutoff": "Threshold set for still bout detection (mg)",
        "processing_epoch": "Epoch setting used when processing data (sec)",
        "qc_first_battery_pct": "QC_first_battery_pct",
        "qc_last_battery_pct": "QC_last_battery_pct",
        "frequency": "Recording frequency in hz",
        "qc_anomalies_total": "1 = Anomaly flagged in file",
        "qc_anomaly_a": "1 = Anomaly a flagged in file. Dealt with during processing",
        "qc_anomaly_b": "1 = Anomaly b flagged in file. Dealt with during processing",
        "qc_anomaly_c": "1 = Anomaly c flagged in file. Dealt with during processing",
        "qc_anomaly_d": "1 = Anomaly d flagged in file. Dealt with during processing",
        "qc_anomaly_e": "1 = Anomaly e flagged in file. Dealt with during processing",
        "qc_anomaly_f": "1 = Anomaly f flagged in file. Dealt with during processing",
        "qc_anomaly_g": "1 = Anomaly g flagged in file. Dealt with during processing",
        "first_file_timepoint": "First date timestamp of hdf5 file",
        "last_file_timepoint": "Last date timestamp of hdf5 file",
        "FLAG_MECH_NOISE": "1 = Flagged as mechanical enmo values. Pwear set to 0"
        }

    variable_label.update(calibration_labels)


    df_labels = pd.DataFrame(list(variable_label.items()), columns=["Variable", "variabel_label"])

    # Determine if variable is numeric
    isnumeric = hourly_df.dtypes.apply(lambda x: 1 if pd.api.types.is_numeric_dtype(x) else 0).reset_index()
    isnumeric.columns = ['Variable', 'isnumeric']
    df_labels = pd.merge(df_labels, isnumeric, on='Variable', how='left')

    # Ordering columns
    df_labels = df_labels[['Variable', 'isnumeric', 'variabel_label']]

    file_path = os.path.join(config.ROOT_FOLDER, config.RELEASES_FOLDER)
    os.makedirs(file_path, exist_ok=True)
    file_name = os.path.join(file_path, f'Data_Dict_{config.HOUR_OUTPUT_FILE}.csv')
    df_labels.to_csv(file_name, index=False)

#################################
# --- Calling the functions --- #
#################################

if __name__ == "__main__":
    hourly_df = formatting_hourly_file()
    data_dictionary(hourly_df)