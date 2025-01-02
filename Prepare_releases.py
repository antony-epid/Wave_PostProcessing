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
import numpy as np
import Wave_PostProcessingOrchestra

#########################################################
# --- IMPORTING AND FORMATTING SUMMARY RESULTS FILE --- #
#########################################################

def formatting_file(import_file_name, release_level, pwear, pwear_morning, pwear_quad, print_message, output_filename):
    # Make release directories if not already present
    try:
        os.makedirs(os.path.join(config.ROOT_FOLDER, config.RELEASES_FOLDER, config.PC_DATE))
    except FileExistsError:
        pass

    file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, import_file_name)
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        print(f"The file {file_path} does not exist. The release on {release_level} level could not be prepared.")
        df = pd.DataFrame()
        return df

    # Generating id and filename
    if 'id' in df.columns:
        df.rename(columns={'id': 'filename'}, inplace=True)
    else:
        df.rename(columns={'file_id': 'filename'}, inplace=True)
    df['id'] = df['filename'].apply(lambda x: x.split("_")[0])

    # For pampro output: Merging anomalies and axis anomaly info from qc_meta file
    if config.PROCESSING.lower() == 'pampro':
        collapsed_anomalies_path = os.path.join(config.ROOT_FOLDER, config.ANOMALIES_FOLDER, f'collapsed_anomalies.csv')
        if os.path.exists(collapsed_anomalies_path):
            collapsed_anomalies_df = pd.read_csv(collapsed_anomalies_path)
            df['file_id'] = df['filename']
            df = df.merge(collapsed_anomalies_df[['file_id', 'FLAG_ANOMALY']], on='file_id', how='left')
        else:
            df['FLAG_ANOMALY'] = np.nan

        # Flagging axis anomalies
        df['FLAG_AXIS_FAULT'] = 0
        df.loc[df['QC_axis_anomaly'] == 'True', 'FLAG_AXIS_FAULT'] = 1

        # Setting all variables to missing if confirmed axis issue
        columns_to_replace = [col for col in df.columns if any(pattern in col for pattern in ['Pwear', 'pwear', 'ENMO', 'enmo', 'HPFVM', 'hpfvm'])]
        for col in columns_to_replace:
            df.loc[df['FLAG_AXIS_FAULT'] == 1, col] = np.nan


    # Soring dataset by id and day_number for daily release file
    if release_level == 'summary':
        df = df.sort_values(by='id')
    if release_level == 'daily':
        df = df.sort_values(by=['id', 'day_number'])
    if release_level == 'hourly':
        df = df.sort_values(by=['id', 'DATETIME'])

    # Renaming timestamp variables
    if release_level == 'summary':
        df.rename(columns={'generic_first_timestamp': 'first_file_timepoint', 'generic_last_timestamp': 'last_file_timepoint'}, inplace=True)

    # Dropping variables that are not needed for hourly releases
    if release_level == 'hourly':
        variables_to_drop = ['generic_first_timestamp', 'generic_last_timestamp', 'database_id', 'DATETIME_ORIG', 'subject_code', 'processing_script',
                             'prestart', 'postend', 'valid', 'freeday_number', 'serial', 'ENMO_n', 'ENMO_missing']
        df.drop(columns=variables_to_drop, inplace=True, errors='ignore')

    # Setting PWear to 0 if ENMO_mean is negative for hourly releases
        df.loc[(df['ENMO_mean'] < 0), 'Pwear'] = 0

    # Generating include criteria
    df['include'] = 0


    if config.PROCESSING.lower() == 'wave':
        if release_level == 'summary' or release_level == 'daily':
            df.loc[
                (df['Pwear'] >= pwear) &
                (df['Pwear_morning'] >= pwear_morning) &
                (df['Pwear_noon'] >= pwear_quad) &
                (df['Pwear_afternoon'] >= pwear_quad) &
                (df['Pwear_night'] >= pwear_quad) &
                (df['file_end_error'] <= df['noise_cutoff']), 'include'] = 1

    if config.PROCESSING.lower() == 'pampro':
        if release_level == 'summary' or release_level == 'daily':

            # Checking if FLAG_NO_VALID_DAYS is a variable in the dataframe and otherwise it will give it the value 0
            FLAG_NO_VALID_DAYS_exists = 'FLAG_NO_VALID_DAYS' in df.columns
            FLAG_NO_VALID_DAYS_condition = (df['FLAG_NO_VALID_DAYS'] != 1) if FLAG_NO_VALID_DAYS_exists else True

            df.loc[
                (df['Pwear'] >= pwear) &
                (df['Pwear_morning'] >= pwear_morning) &
                (df['Pwear_noon'] >= pwear_quad) &
                (df['Pwear_afternoon'] >= pwear_quad) &
                (df['Pwear_night'] >= pwear_quad) &
                (df['calibration_type'] != 'fail') &
                (FLAG_NO_VALID_DAYS_condition) &
                (df['FLAG_AXIS_FAULT'] != 1), 'include'] = 1
            df.loc[
                (df['Pwear'] >= pwear) &
                (df['Pwear_morning'] < pwear_morning) &
                (df['Pwear_noon'] >= pwear_quad) &
                (df['Pwear_afternoon'] >= pwear_quad) &
                (df['Pwear_night'] >= pwear_quad) &
                (df['calibration_type'] != 'fail') &
                (FLAG_NO_VALID_DAYS_condition) &
                (df['include'] != 1) &
                (df['FLAG_AXIS_FAULT'] != 1), 'include'] = 2

            df.loc[(df['include'] == 2), 'imputed'] = 1

        if release_level == 'summary' or release_level == 'daily':

            # Consolidation of all intensity variables
            columns_to_change = [col for col in df.columns if ('enmo' in col or 'Pwear' in col) and not col.endswith('_IMP')]
            new_columns = {}
            for col in columns_to_change:
                new_columns[f'{col}_orig'] = df[col]
                imputed_col = f'{col}_IMP'
                if imputed_col in df.columns:
                    df.loc[df['include'] == 2, col] = df[imputed_col]

            df = pd.concat([df, pd.DataFrame(new_columns)], axis=1)

            # Generating sedentary, light and mvpa variables
            types = ['', '_IMP']
            for type_ in types:
                for x in range(25, 40, 5):
                    column_name = f'sed_{x}{type_}'
                    df[column_name] = (1 - df[f'enmo_{x}plus{type_}']) * 1400

                light_name = f'lpa{type_}'
                df[light_name] = (df[f'enmo_30plus{type_}'] - df[f'enmo_125plus{type_}']) * 1440

                for x in range(100, 175, 25):
                    mvpa_name = f'mvpa_{x}{type_}'
                    df[mvpa_name] = df[f'enmo_{x}plus{type_}'] * 1400

    # Changing order or variables in dataframe
    columns = ['id'] + [col for col in df.columns if col != 'id']
    df = df[columns]

    columns_order = list(df.columns)
    if config.PROCESSING.lower() == 'wave':
        columns_order.insert(columns_order.index('noise_cutoff'), columns_order.pop(columns_order.index('TIME_RESOLUTION')))
        columns_order.insert(columns_order.index('qc_anomaly_g'), columns_order.pop(columns_order.index('first_file_timepoint')))
        columns_order.insert(columns_order.index('first_file_timepoint'), columns_order.pop(columns_order.index('last_file_timepoint')))
        df = df[columns_order]
    if config.PROCESSING.lower() == 'pampro':
        pwear_columns = [col for col in df.columns if col.startswith('Pwear') and not (col.endswith('orig') or col.endswith('IMP'))]
        pwear_originals = [col for col in df.columns if col.startswith('Pwear') and col.endswith('orig')]
        pwear_imputed = [col for col in df.columns if col.startswith('Pwear') and col.endswith('IMP')]
        pwear_day_hour = [col for col in df.columns if col.startswith('pwear_day') or col.startswith('pwear_hour') and not (col.endswith('orig') or col.endswith('IMP'))]
        pwear_day_hour_orig = [col for col in df.columns if (col.startswith('pwear_day') or col.startswith('pwear_hour')) and col.endswith('orig')]
        pwear_day_hour_imp = [col for col in df.columns if (col.startswith('pwear_day') or col.startswith('pwear_hour')) and col.endswith('IMP')]
        enmo_variables = [col for col in df if col.startswith('enmo') and col.endswith('plus')]
        enmo_mean_orig = [col for col in df if col.startswith('enmo_mean') and col.endswith('orig')]
        enmo_plus_orig = [col for col in df if col.startswith('enmo') and col.endswith('plus_orig')]
        enmo_IMP = [col for col in df if col.startswith('enmo_mean') and col.endswith('IMP')]
        pampro_variables = ['id', 'filename']
        if release_level == 'summary':
            pampro_variables += ['startdate', 'RecordLength']
        pampro_column_order = [*pampro_variables, *pwear_columns, *pwear_originals, *pwear_imputed, *pwear_day_hour, *pwear_day_hour_orig, *pwear_day_hour_imp, *enmo_variables,
                               *enmo_mean_orig, *enmo_plus_orig, *enmo_IMP]
        remaining_columns = [col for col in df if col not in pampro_column_order]
        final_order = pampro_column_order + remaining_columns
        df = df[final_order]

    # --- SECTION TO RUN HOUSEKEEPING AND DROP FILES NOT NEEDED IN FINAL RELEASE --- #
    if config.RUN_HOUSEKEEPING.lower() == 'yes':
        print(Fore.GREEN + "RUNNING HOUSEKEEPING AND DROPPING FILES THAT ARE NOT NEEDED IN FINAL RELEASE" + Fore.RESET)
        df = df[(~df['filename'].isin(filenames_to_remove))]

    # Counting number of files/IDs and print the IDs
    count_number_ids = df['id'].count()
    print(Fore.YELLOW + f'Total number of {print_message} in {release_level} release file: {count_number_ids}' + Fore.RESET)
    if release_level == 'summary':
        id_column = df['id']
        id_list = id_column.tolist()
        print(Fore.YELLOW + "IDs:" + Fore.RESET)
        for id in id_list:
            print(Fore.YELLOW + id + Fore.RESET)
    if release_level == 'daily':
        filename_column = df['filename']
        filename_list = filename_column.tolist()
        unique_filename = sorted(set(filename_list))

        grouped = df.groupby('filename')['day_number'].count()
        print(Fore.YELLOW + "Filenames and rows/days per ID:" + Fore.RESET)
        for filename in unique_filename:
            count_days = grouped.get(filename, 0)
            print(Fore.YELLOW + f'{filename}:    {count_days} days' + Fore.RESET)

    if release_level == 'hourly':
        id_column = df['id']
        id_list = id_column.tolist()
        unique_ids = sorted(set(id_list))
        id_counts = df['id'].value_counts().sort_index()
        print(Fore.YELLOW + "IDs and number of rows/hours per ID:" + Fore.RESET)
        for id, count in zip(unique_ids, id_counts):
            print(Fore.YELLOW + f'{id:}   {count} files/hours' + Fore.RESET)

    # Saving the release file with todays date
    today_date = date.today()
    formatted_date = today_date.strftime("%d%b%Y")
    output_folder = os.path.join(config.ROOT_FOLDER, config.RELEASES_FOLDER, config.PC_DATE, f'{output_filename}_FINAL_{formatted_date}.csv')
    df.to_csv(output_folder, index=False)

    return df


####################################
# --- CREATING DATA DICTIONARY --- #
####################################
def data_dictionary(df, filename, release_level, pwear, pwear_quad):
    if df is not None and not df.empty:
        variable_label = {
            "id": "Study ID",
            "filename": "Filename of original raw file"}

        if release_level == 'summary':
            variable_label.update({
                "startdate": "Date of first day of free-living recording",
                "RecordLength": "Number of hours file was recording for"})
        if release_level == 'daily':
            variable_label.update({
                "DATE": "Daily date of wear",
                "day_number": "Consecutive day number in recording",
                "dayofweek": "day of week for index time period"
            })
        variable_label.update({
            "Pwear": "Time integral of wear probability based on ACC"
        })

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
            "Pwear_night": f"{label}; {quad_night_hours}"}
        if release_level == 'summary':
            pwear_labels.update({
                "Pwear_wkday": f"{label}; weekday",
                "Pwear_wkend": f"{label}; weekend day",
                "Pwear_morning_wkday": f"{label}; {quad_morning_hours}; weekday",
                "Pwear_noon_wkday": f"{label}; {quad_morning_hours}; weekday",
                "Pwear_afternoon_wkday": f"{label}; {quad_afternoon_hours} weekday",
                "Pwear_night_wkday": f"{label}; {quad_night_hours}; weekday",
                "Pwear_morning_wkend": f"{label}; {quad_morning_hours}; weekend day",
                "Pwear_noon_wkend": f"{label}; {quad_morning_hours}; weekend day",
                "Pwear_afternoon_wkend": f"{label}; {quad_afternoon_hours}; weekend day",
                "Pwear_night_wkend": f"{label}; {quad_night_hours}; weekend day"})
        pwear_labels.update({
            "enmo_mean": "Average acceleration (milli-g)"
        })

        variable_label.update(pwear_labels)

        if config.REMOVE_THRESHOLDS.lower() == 'no':
            enmo_variables = [col for col in df.columns if col.startswith("enmo_") and col.endswith("plus")]

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
            "last_file_timepoint": "Last date timestamp of hdf5 file"}

        if release_level == 'summary' or release_level == 'daily':
            calibration_labels.update({
            "include": f'1=Pwear>={pwear} & all Pwear_quads>={pwear_quad}'
            })

        variable_label.update(calibration_labels)


        df_labels = pd.DataFrame(list(variable_label.items()), columns=["Variable", "variabel_label"])

        # Determine if variable is numeric
        isnumeric = summary_df.dtypes.apply(lambda x: 1 if pd.api.types.is_numeric_dtype(x) else 0).reset_index()
        isnumeric.columns = ['Variable', 'isnumeric']
        df_labels = pd.merge(df_labels, isnumeric, on='Variable', how='left')

        # Ordering columns
        df_labels = df_labels[['Variable', 'isnumeric', 'variabel_label']]

        file_path = os.path.join(config.ROOT_FOLDER, config.RELEASES_FOLDER, config.PC_DATE)
        os.makedirs(file_path, exist_ok=True)
        file_name = os.path.join(file_path, f'Data_Dict_{filename}.csv')
        df_labels.to_csv(file_name, index=False)


#################################
# --- Calling the functions --- #
#################################
if __name__ == '__main__':
    # Preparing summary release file
    if Wave_PostProcessingOrchestra.RUN_PREPARE_SUMMARY_RELEASE.lower() == 'yes':
        Wave_PostProcessingOrchestra.print_message("PREPARING A SUMMARY RELEASE FILE")

        summary_df = formatting_file(import_file_name=f'{config.SUM_OUTPUT_FILE}.csv', release_level='summary',
                                     pwear=config.SUM_PWEAR, pwear_morning=config.SUM_PWEAR_MORNING, pwear_quad=config.SUM_PWEAR_QUAD, print_message='files/IDs',
                                     output_filename=config.SUM_OUTPUT_FILE)
        data_dictionary(df=summary_df, filename=config.SUM_OUTPUT_FILE, release_level='summary', pwear=config.SUM_PWEAR, pwear_quad=config.SUM_PWEAR_QUAD)

    # Preparing daily release file
    if Wave_PostProcessingOrchestra.RUN_PREPARE_DAILY_RELEASE.lower() == 'yes':
        Wave_PostProcessingOrchestra.print_message("PREPARING A DAILY RELEASE FILE")
        daily_df = formatting_file(import_file_name=f'{config.DAY_OUTPUT_FILE}.csv', release_level='daily',
                                   pwear=config.DAY_PWEAR, pwear_morning=config.DAY_PWEAR_MORNING, pwear_quad=config.DAY_PWEAR_QUAD, print_message='rows of data',
                                   output_filename=config.DAY_OUTPUT_FILE)
        data_dictionary(df=daily_df, filename=config.DAY_OUTPUT_FILE, release_level='daily', pwear=config.DAY_PWEAR, pwear_quad=config.DAY_PWEAR_QUAD)

    # Preparing hourly release file
    if Wave_PostProcessingOrchestra.RUN_PREPARE_HOURLY_RELEASE.lower() == 'yes':
        Wave_PostProcessingOrchestra.print_message("PREPARING A HOURLY RELEASE FILE")

        hourly_df = formatting_file(import_file_name=f'{config.HOUR_OUTPUT_FILE}.csv', release_level='hourly',
                                    pwear=None, pwear_morning=None, pwear_quad=None, print_message='rows of data', output_filename=config.HOUR_OUTPUT_FILE)
        data_dictionary(df=hourly_df, filename=config.HOUR_OUTPUT_FILE, release_level='hourly', pwear=None, pwear_quad=None)
