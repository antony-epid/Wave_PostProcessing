############################################################################################################
# This file is preparing summary releases
# Author: CAS
# Date: 12/07/2024
# Version: 1.0 Translated from Stata code
############################################################################################################
# IMPORTING PACKAGES #
import os
import config
import pandas as pd
from colorama import Fore
from datetime import date
from Housekeeping import filenames_to_remove

#########################################################
# --- IMPORTING AND FORMATTING SUMMARY RESULTS FILE --- #
#########################################################

def formatting_summary_file():
    summary_means_file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, f'{config.SUM_OUTPUT_FILE}.csv')
    if os.path.exists(summary_means_file_path):
        summary_df = pd.read_csv(summary_means_file_path)


    # Generating id and filename
    summary_df.rename(columns={'id': 'filename'}, inplace=True)
    summary_df['id'] = summary_df['filename'].apply(lambda x: x.split("_")[0])

    # Soring dataset by id
    summary_df = summary_df.sort_values(by='id')

    # Renaming timestamp variables
    summary_df.rename(columns={'generic_first_timestamp': 'first_file_timepoint', 'generic_last_timestamp': 'last_file_timepoint'}, inplace=True)

    # Generating include criteria
    summary_df['include'] = 0
    summary_df.loc[
        (summary_df['Pwear'] >= config.SUM_PWEAR) &
        (summary_df['Pwear_morning'] >= config.SUM_PWEAR_MORNING) &
        (summary_df['Pwear_noon'] >= config.SUM_PWEAR_QUAD) &
        (summary_df['Pwear_afternoon'] >= config.SUM_PWEAR_QUAD) &
        (summary_df['Pwear_night'] >= config.SUM_PWEAR_QUAD) &
        (summary_df['file_end_error'] <= summary_df['noise_cutoff']), 'include'] = 1

    # Changing order or variables in dataframe
    columns = ['id'] + [col for col in summary_df.columns if col != 'id']
    summary_df = summary_df[columns]

    columns_order = list(summary_df.columns)
    columns_order.insert(columns_order.index('noise_cutoff'), columns_order.pop(columns_order.index('TIME_RESOLUTION')))
    columns_order.insert(columns_order.index('qc_anomaly_g'), columns_order.pop(columns_order.index('first_file_timepoint')))
    columns_order.insert(columns_order.index('first_file_timepoint'), columns_order.pop(columns_order.index('last_file_timepoint')))
    summary_df = summary_df[columns_order]

    # --- SECTION TO RUN HOUSEKEEPING AND DROP FILES NOT NEEDED IN FINAL RELEASE --- #
    if config.RUN_HOUSEKEEPING.lower() == 'yes':
        print(Fore.GREEN + "RUNNING HOUSEKEEPING AND DROPPING FILES THAT ARE NOT NEEDED IN FINAL RELEASE" + Fore.RESET)
        summary_df = summary_df[(~summary_df['filename'].isin(filenames_to_remove))]

    # Counting number of files/IDs and print the IDs
    count_number_ids = summary_df['id'].count()
    print(Fore.YELLOW + f'Total number of files/IDs in summary release file: {count_number_ids}' + Fore.RESET)
    id_column = summary_df['id']
    id_list = id_column.tolist()
    print(Fore.YELLOW + "IDs:" + Fore.RESET)
    for id in id_list:
        print(Fore.YELLOW + id + Fore.RESET)


    # Saving the release file with todays date
    today_date = date.today()
    formatted_date = today_date.strftime("%d%b%Y")
    output_folder = os.path.join(config.ROOT_FOLDER, config.RELEASES_FOLDER, f'{config.SUM_OUTPUT_FILE}_FINAL_{formatted_date}.csv')
    summary_df.to_csv(output_folder, index=False)

    return summary_df


####################################
# --- CREATING DATA DICTIONARY --- #
####################################
def data_dictionary(summary_df):

    variable_label = {
        "id": "Study ID",
        "filename": "Filename of original raw file",
        "startdate": "Date of first day of free-living recording",
        "RecordLength": "Number of hours file was recording for",
        "Pwear": "Time integral of wear probability based on ACC"
    }

    quadrants = ['morning', 'noon', 'afternoon', 'night']
    quad_morning_hours = ">0 & <=6 hours"
    quad_noon_hours = ">6 & <=12 hours"
    quad_afternoon_hours = ">12 & <=18 hours"
    quad_night_hours = ">18 & <=24 hours"
    label = "Number of valid hrs during free-living"

    pwear_labels = {
        "Pwear_morning": f"{label}; {quad_morning_hours}",
        "Pwear_noon": f"{label}; {quad_noon_hours}",
        "Pwear_afternoon": f"{label}; {quad_afternoon_hours}",
        "Pwear_night": f"{label}; {quad_night_hours}",
        "Pwear_wkday": f"{label}; weekday",
        "Pwear_wkend": f"{label}; weekend day",
        "Pwear_morning_wkday": f"{label}; {quad_morning_hours}; weekday",
        "Pwear_noon_wkday": f"{label}; {quad_morning_hours}; weekday",
        "Pwear_afternoon_wkday": f"{label}; {quad_afternoon_hours} weekday",
        "Pwear_night_wkday": f"{label}; {quad_night_hours}; weekday",
        "Pwear_morning_wkend": f"{label}; {quad_morning_hours}; weekend day",
        "Pwear_noon_wkend": f"{label}; {quad_morning_hours}; weekend day",
        "Pwear_afternoon_wkend": f"{label}; {quad_afternoon_hours}; weekend day",
        "Pwear_night_wkend": f"{label}; {quad_night_hours}; weekend day",
        "enmo_mean": "Average acceleration (milli-g)"
    }

    variable_label.update(pwear_labels)

    if config.REMOVE_THRESHOLDS.lower() == 'no':
        enmo_variables = [col for col in summary_df.columns if col.startswith("enmo_") and col.endswith("plus")]

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
        "TIME_RESOLUTION": "Time resolution of processed data (minutes)",
        "noise_cutoff": "Threshold set for still bout detection (mg)",
        "processing_epoch": "Epoch setting used when processing data (sec)",
        "qc_first_battery_pct": "Battery percentage of device at beginning of data collection",
        "qc_last_battery_pct": "Battery percentage of device at end of data collection",
        "frequency": "Recording frequency in hz",
        "qc_anomalies_total": "Total number of anomalies detected in the file",
        "qc_anomaly_a": "1 = Anomaly a flagged in file. Dealt with during processing.",
        "qc_anomaly_b": "1 = Anomaly b flagged in file. Dealt with during processing.",
        "qc_anomaly_c": "1 = Anomaly c flagged in file. Dealt with during processing.",
        "qc_anomaly_d": "1 = Anomaly d flagged in file. Dealt with during processing.",
        "qc_anomaly_e": "1 = Anomaly e flagged in file. Dealt with during processing.",
        "qc_anomaly_f": "1 = Anomaly f flagged in file. Dealt with during processing.",
        "qc_anomaly_g": "1 = Anomaly g flagged in file. Dealt with during processing.",
        "first_file_timepoint": "First date timestamp of hdf5 file",
        "last_file_timepoint": "Last date timestamp of hdf5 file",
        "include": f'1=Pwear>={config.SUM_PWEAR} & all Pwear_quads>={config.SUM_PWEAR_QUAD}'
        }

    variable_label.update(calibration_labels)


    df_labels = pd.DataFrame(list(variable_label.items()), columns=["Variable", "variabel_label"])

    # Determine if variable is numeric
    isnumeric = summary_df.dtypes.apply(lambda x: 1 if pd.api.types.is_numeric_dtype(x) else 0).reset_index()
    isnumeric.columns = ['Variable', 'isnumeric']
    df_labels = pd.merge(df_labels, isnumeric, on='Variable', how='left')

    # Ordering columns
    df_labels = df_labels[['Variable', 'isnumeric', 'variabel_label']]

    file_path = os.path.join(config.ROOT_FOLDER, config.RELEASES_FOLDER)
    os.makedirs(file_path, exist_ok=True)
    file_name = os.path.join(file_path, f'Data_Dict_{config.SUM_OUTPUT_FILE}.csv')
    df_labels.to_csv(file_name, index=False)


#################################
# --- Calling the functions --- #
#################################
if __name__ == '__main__':
    summary_df = formatting_summary_file()
    data_dictionary(summary_df)

