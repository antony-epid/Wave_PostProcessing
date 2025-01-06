############################################################################################################
# This file collapses hourly means to daily means
# Author: CAS
# Date: 02/07/2024
# Version: 1.0 Translated from Stata code
############################################################################################################
# IMPORTING PACKAGES #
import os
import pandas as pd
import config
from datetime import timedelta
import numpy as np
import statsmodels.api as sm
import warnings

##################
# Processing #
##################

# READING IN FILELIST
def reading_filelist():
    os.chdir(os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.FILELIST_FOLDER))
    filelist_df = pd.read_csv('filelist.txt', delimiter='\t')  # Reading in the filelist
    filelist_df = filelist_df.drop_duplicates(subset=['filename_temp'])
    files_list = filelist_df['filename_temp'].tolist()
    return files_list

# LOOPING THROUGH EACH FILE FOR COLLAPSING
def reading_part_proc(files_list):
    time_resolutions = []
    dataframes = []

    for file_id in files_list:
        part_proc_file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_PARTPRO_F, config.TIME_RES_FOLDER, f"{file_id}_{config.OUTPUT_FILE_EXT}.csv")
        if os.path.exists(part_proc_file_path):
            part_proc_df = pd.read_csv(part_proc_file_path)
            part_proc_df.sort_values(by=['file_id', 'DATETIME'], inplace=True)

            part_proc_df['DATETIME_ORIG'] = pd.to_datetime(part_proc_df['DATETIME_ORIG'])
            time_difference = part_proc_df['DATETIME_ORIG'].iloc[1] - part_proc_df['DATETIME_ORIG'].iloc[0]
            time_resolution = time_difference.total_seconds() / 60
            time_resolutions.append(time_resolution)

            dataframes.append(part_proc_df)
    return time_resolutions, dataframes


# REMOVING NON VALID HOURS
def remove_data(dataframes):
    truncated_dataframes = []

    for dataframe in dataframes:
        if config.TRUNCATE_DATA.lower() == 'yes':
            threshold_datetime = dataframe['DATETIME_ORIG'].iloc[0] + timedelta(days=config.NO_OF_DAYS)
            dataframe = dataframe[dataframe['DATETIME_ORIG'] <= threshold_datetime]

        # Changing Pwear to 0 if flag mechanical noise is 1
        if config.REMOVE_MECH_NOISE.lower() == 'yes':
            dataframe.loc[dataframe['FLAG_MECH_NOISE'] == 0, 'Pwear'] = 0

        # Dropping last data point if file contains an anomaly F
        if config.DROP_END_ANOM_F.lower() == 'yes':
            if dataframe['QC_anomaly_F'].min() > 0:
                dataframe['row'] = dataframe.index + 1
                max_row = dataframe['row'].max()
                dataframe = dataframe[dataframe['row'] != max_row]
                dataframe.drop(columns=['row'], inplace=True)

        truncated_dataframes.append(dataframe)
    return truncated_dataframes

# CREATING "DUMMY" DATASET (EMPTY) IF ALL TIMES FALL OUTSIDE WEAR LOG TIMES OR LESS THAN 1 HOUR DATA
def creating_dummy(truncated_dataframes, files_list, dataframes, time_resolutions):
    for truncated_dataframe, dataframe, file_list, time_resolution in zip(truncated_dataframes, dataframes, files_list, time_resolutions):
        row_count = len(truncated_dataframe)
        flag_valid_total = truncated_dataframe['temp_flag_no_valid_days'].min()

        if row_count <= 1 or flag_valid_total == 1:
            dummy_df = pd.DataFrame({
                'file_id': [file_list],
                'FLAG_NO_VALID_DAYS': [1]
            })
            new_dummy_df = dataframe.merge(dummy_df, on='file_id', how='left', suffixes=('', '_y'))
            columns_to_keep = ['file_id', 'FLAG_NO_VALID_DAYS', 'device', 'start_error', 'end_error', 'calibration_method', 'noise_cutoff_mg', 'processing_epoch', 'generic_first_timestamp', 'generic_last_timestamp', 'QC_first_battery_pct', 'QC_last_battery_pct', 'frequency', 'QC_anomalies_total', 'QC_anomaly_A', 'QC_anomaly_B', 'QC_anomaly_C', 'QC_anomaly_D', 'QC_anomaly_E', 'QC_anomaly_F', 'QC_anomaly_G', 'processing_script']
            new_dummy_df = new_dummy_df[columns_to_keep]
            new_dummy_df['TIME_RESOLUTION'] = time_resolution

            if 'START' in new_dummy_df.columns:
                new_dummy_df['START'] = new_dummy_df['START'].astype(str)
            if 'END' in new_dummy_df.columns:
                new_dummy_df['END'] = new_dummy_df['END'].astype(str)

            # Keep first row only
            new_dummy_df = new_dummy_df.head(1)

            new_dummy_df = new_dummy_df.rename(columns={'file_id': 'id'})
            new_dummy_df['id'] = new_dummy_df['id'].str.upper()

            # Outputting dummy dataset
            file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_DAILY_F, config.TIME_RES_FOLDER)
            os.makedirs(file_path, exist_ok=True)
            file_name = os.path.join(file_path, f"{file_list}_{config.DAY_OVERALL_MEAN}.csv")

            new_dummy_df.to_csv(file_name, index=False)

def trimmed_dataset(truncated_dataframes, files_list, time_resolutions):
    trimmed_dfs = []
    for truncated_dataframe, file_list, time_resolution in zip(truncated_dataframes, files_list, time_resolutions):
        row_count = len(truncated_dataframe)
        flag_valid_total = truncated_dataframe['temp_flag_no_valid_days'].min()

        if row_count > 1 or flag_valid_total != 1:
            truncated_dataframe.drop(columns='temp_flag_no_valid_days', inplace=True)

            # Generating day number and day change:
            truncated_dataframe['day_number'] = 1
            truncated_dataframe['day_change'] = 0
            truncated_dataframe.loc[(truncated_dataframe['hourofday'] == 1) & (truncated_dataframe['hourofday'].shift(1) == 24) & (truncated_dataframe['file_id'] == truncated_dataframe['file_id'].shift(1)), 'day_change'] = 1
            day_number = 1
            for idx, row in truncated_dataframe.iterrows():
                if row['day_change'] == 1:
                    day_number += 1
                truncated_dataframe.at[idx, 'day_number'] = day_number
            truncated_dataframe.drop(columns=['day_change'], inplace=True)

            # Excluding data (based on local exclude_hours list) only if specified in header
            truncated_dataframe['INCLUDE'] = 0
            truncated_dataframe['awake_pwear'] = None

            # Sorting out the date/time variables
            truncated_dataframe['weekend'] = 0
            truncated_dataframe.loc[(truncated_dataframe['dayofweek'] == 6) | (truncated_dataframe['dayofweek'] == 7) & (truncated_dataframe['dayofweek'].notna()), 'weekend'] = 1
            truncated_dataframe['dayofyear'] = truncated_dataframe['DATETIME_ORIG'].dt.dayofyear

            # Generating the morning and midnight axes for purposes of diurnal adjustment
            truncated_dataframe['MORNING'] = np.sin(2 * np.pi * (truncated_dataframe['hourofday'] / 24))
            truncated_dataframe['MIDNIGHT'] = np.cos(2 * np.pi * (truncated_dataframe['hourofday'] / 24))

            # Generating spring and winter variables:
            hemisphere = 1 # Northern = 1, Southern = -1
            truncated_dataframe['SPRING'] = np.sin(2 * np.pi * (truncated_dataframe['dayofyear'] / 365.25)) * hemisphere
            truncated_dataframe['WINTER'] = np.cos(2 * np.pi * (truncated_dataframe['dayofyear'] / 365.25)) * hemisphere

            # Generating PWEAR variables
            truncated_dataframe['row'] = truncated_dataframe.groupby('file_id').cumcount() + 1

            truncated_dataframe['Pwear'] = pd.to_numeric(truncated_dataframe['Pwear'])
            truncated_dataframe['PWEAR_MORNING'] = truncated_dataframe['Pwear'] * truncated_dataframe['MORNING']
            truncated_dataframe['PWEAR_MIDNIGHT'] = truncated_dataframe['Pwear'] * truncated_dataframe['MIDNIGHT']

            trimmed_dfs.append(truncated_dataframe)
    return trimmed_dfs

def creating_headers(files_list):
    summary_dataframes = []

    for file in files_list:
        list_of_variables = ['id', 'DATE', 'day_number', 'dayofweek', 'Pwear', 'Pwear_morning', 'Pwear_noon', 'Pwear_afternoon', 'Pwear_night',
                             'enmo_mean',
                             'enmo_0plus', 'enmo_1plus', 'enmo_2plus', 'enmo_3plus', 'enmo_4plus', 'enmo_5plus', 'enmo_10plus', 'enmo_15plus', 'enmo_20plus', 'enmo_25plus', 'enmo_30plus', 'enmo_35plus',
                             'enmo_40plus', 'enmo_45plus', 'enmo_50plus', 'enmo_55plus', 'enmo_60plus', 'enmo_65plus', 'enmo_70plus', 'enmo_75plus', 'enmo_80plus', 'enmo_85plus', 'enmo_90plus',
                             'enmo_95plus', 'enmo_100plus', 'enmo_105plus', 'enmo_110plus', 'enmo_115plus', 'enmo_120plus', 'enmo_125plus', 'enmo_130plus', 'enmo_135plus', 'enmo_140plus',
                             'enmo_145plus', 'enmo_150plus', 'enmo_160plus', 'enmo_170plus', 'enmo_180plus', 'enmo_190plus', 'enmo_200plus', 'enmo_210plus', 'enmo_220plus', 'enmo_230plus',
                             'enmo_240plus', 'enmo_250plus', 'enmo_260plus', 'enmo_270plus', 'enmo_280plus', 'enmo_290plus', 'enmo_300plus', 'enmo_400plus', 'enmo_500plus', 'enmo_600plus',
                             'enmo_700plus', 'enmo_800plus', 'enmo_900plus', 'enmo_1000plus', 'enmo_2000plus', 'enmo_3000plus', 'enmo_4000plus',
                             'device', 'file_start_error', 'file_end_error', 'calibration_method', 'noise_cutoff', 'processing_epoch',
                             'TIME_RESOLUTION', 'qc_anomalies_total']
        headers_df = pd.DataFrame(columns=list_of_variables)
        summary_dataframes.append(headers_df)

        # Outputting empty dataframe
        file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_DAILY_F, config.TIME_RES_FOLDER)
        os.makedirs(file_path, exist_ok=True)
        file_name = os.path.join(file_path, f"{file}_{config.DAY_OVERALL_MEAN}.csv")

        headers_df.to_csv(file_name, index=False)
    return summary_dataframes


# CREATING VARIABLES FOR SUMMARY DATASET
def summarise_variables(files_list, trimmed_dfs, time_resolutions, summary_dataframes):
    summary_dfs = []

    for file, trimmed_df, time_resolution, summary_df in zip(files_list, trimmed_dfs, time_resolutions, summary_dataframes):

        # Looping through each day and creating summarized variables:
        DAYS = trimmed_df['day_number'].max()
        for dayNum in range (1, DAYS + 1):
            day_df = trimmed_df[trimmed_df['day_number'] == dayNum]

            if not day_df.empty:
                first_row = day_df.index.min()
                first_row_data = trimmed_df.loc[first_row]
                file_id_value = first_row_data['file_id']
                startdate_value = first_row_data['DATE']
                day_number_value = first_row_data['day_number']
                day_of_week = first_row_data['dayofweek']
                device_value = first_row_data['device']
                noise_cutoff_value = first_row_data['noise_cutoff_mg']
                processing_epoch_value = first_row_data['processing_epoch']
                file_end_error_value = first_row_data['end_error']
                file_start_error_value = first_row_data['start_error']
                calibration_method_value = first_row_data['calibration_method']
                qc_anomalies_total_value = first_row_data['QC_anomalies_total']


                summary_dict = {
                    'id': file_id_value,
                    'DATE': startdate_value,
                    'day_number': day_number_value,
                    'dayofweek': day_of_week,
                    'device': device_value,
                    'noise_cutoff': noise_cutoff_value,
                    'processing_epoch': processing_epoch_value,
                    'file_end_error': file_end_error_value,
                    'file_start_error': file_start_error_value,
                    'qc_anomalies_total': qc_anomalies_total_value,
                    'calibration_method': calibration_method_value,
                    'TIME_RESOLUTION': time_resolution
                }

                ##################################
                ### SUMMARISING PWEAR SEGMENTS ###
                ##################################
                formula = 60 / time_resolution
                PWear_sum = day_df['Pwear'].sum()
                PWear = PWear_sum / formula

                # PWear variables by quadrants
                quad_morning_hours = (day_df['hourofday'] > 0) & (day_df['hourofday'] <= 6)
                quad_noon_hours = (day_df['hourofday'] > 6) & (day_df['hourofday'] <= 12)
                quad_afternoon_hours = (day_df['hourofday'] > 12) & (day_df['hourofday'] <= 18)
                quad_night_hours = (day_df['hourofday'] > 18) & (day_df['hourofday'] <= 24)

                quadrants = ['morning', 'noon', 'afternoon', 'night']
                quad_variables = [quad_morning_hours, quad_noon_hours, quad_afternoon_hours, quad_night_hours]
                Pwear_by_quad = {}

                for quad, variables in zip(quadrants, quad_variables):
                    Pwear_sum = day_df.loc[variables, 'Pwear'].sum()
                    quadrant = f'Pwear_{quad}'
                    Pwear_by_quad[quadrant] = Pwear_sum / formula
                    summary_dict[quadrant] = Pwear_by_quad[quadrant]

                ####################################
                ### SUMMARISING OUTPUT VARIABLES ###
                ####################################
                # ENMO MEAN
                filtered_df = day_df[(day_df['ENMO_mean'].notna()) & (day_df['Pwear'].notna()) & (day_df['Pwear'] > 0)]
                Pwear_sum = filtered_df['Pwear'].sum()
                summary_dict['Pwear'] = Pwear_sum
                if Pwear_sum / formula >= config.DAY_MIN_HOUR_INCLUSION:
                    X = filtered_df[['MORNING', 'MIDNIGHT']]
                    Y = filtered_df['ENMO_mean']
                    X = sm.add_constant(X)
                    weights = np.floor(time_resolution * filtered_df['Pwear'])
                    model = sm.WLS(Y, X, weights=weights)
                    results = model.fit()
                    summary_dict['enmo_mean'] = results.params['const']

                # INTENSITY VARIABLES
                variable_prefix = 'ENMO_'
                variable_suffix = 'plus'

                for column_name in trimmed_df.columns:
                    if column_name.startswith(variable_prefix) and column_name.endswith(variable_suffix):
                        filtered_df = day_df[(day_df['Pwear'] > 0) & (day_df[column_name].notna())]
                        ENMO_sum = filtered_df['Pwear'].sum()

                        if ENMO_sum / formula >= config.DAY_MIN_HOUR_INCLUSION:
                            X = filtered_df[['MORNING', 'MIDNIGHT']]
                            Y = filtered_df[column_name]
                            X = sm.add_constant(X)
                            weights = np.floor(time_resolution * filtered_df['Pwear'])
                            model = sm.WLS(Y, X, weights=weights)
                            results = model.fit()
                            column_name = column_name.lower()
                            summary_dict[column_name] = results.params['const']

                # In future pandas might filter out any rows with only NaN data. This turns of a warning message about this. Code will need editing in the future.
                with warnings.catch_warnings():
                    warnings.simplefilter(action='ignore', category=FutureWarning)
                    summary_df = pd.concat([summary_df, pd.DataFrame([summary_dict])], ignore_index=True)

        # Rounding all numeric columns to 4 decimal places
        numeric_columns = summary_df.select_dtypes(include=['float64', 'float32']).columns
        summary_df[numeric_columns] = summary_df[numeric_columns].round(4)

        # Outputting summary dataframe
        file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_DAILY_F, config.TIME_RES_FOLDER)
        os.makedirs(file_path, exist_ok=True)
        file_name = os.path.join(file_path, f"{file}_{config.DAY_OVERALL_MEAN}.csv")

        summary_df.to_csv(file_name, index=False)
        summary_dfs.append(summary_df)
    return summary_dfs

# Creating data dictionary for all variables:
def data_dic(summary_dfs):
    for summary_df in summary_dfs:

        variable_label = {
            "id": "Study ID",
            "DATE": "Daily date of wear",
            "day_number": "Consecutive day number in recording",
            "dayofweek": "day of week for index time period",
            #"RecordLength": "Number of hours file was recording for",
            "Pwear": "Time integral of wear probability based on ACC"
        }

        quadrants = ['morning', 'noon', 'afternoon', 'night']
        quad_morning_hours = "hourofday>0 & hourofday<=6"
        quad_noon_hours = "hourofday>6 & hourofday<=12"
        quad_afternoon_hours = "hourofday>12 & hourofday<=18"
        quad_night_hours = "hourofday>18 & hourofday<=24"
        label = "Number of valid hrs during free-living"

        pwear_labels = {
            "Pwear_morning": f"{label}, {quad_morning_hours}",
            "Pwear_noon": f"{label}, {quad_noon_hours}",
            "Pwear_afternoon": f"{label}, {quad_afternoon_hours}",
            "Pwear_night": f"{label}, {quad_night_hours}",
            "enmo_mean": "Average acceleration (milli-g)"
        }

        variable_label.update(pwear_labels)

        enmo_variables = [col for col in summary_df.columns if col.startswith("enmo_") and col.endswith("plus")]

        for variables in enmo_variables:
            t1 = variables.replace("enmo_", "")
            treshold = t1.replace("plus", "")
            label = f"Proportion of time spent above >= {treshold} milli-g"
            variable_label[variables] = label

        calibration_labels = {
            "device": "Device serial number",
            "file_start_error": "File error before calibration (single file cal) (mg)",
            "file_end_error": "File error after calibration (single file cal) (mg)",
            "calibration_method": "Calibration method applied (offset/scale/temp)",
            "noise_cutoff": "Treshold set for still bout detection (mg)",
            "processing_epoch": "Epoch setting used when processing data (sec)",
            "TIME_RESOLUTION": "Time resolution of processed data (minutes)",
            "qc_anomalies_total": ""
        }

        variable_label.update(calibration_labels)

        df_labels = pd.DataFrame(list(variable_label.items()), columns=["Variable", "Label"])

        file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_DAILY_F, config.TIME_RES_FOLDER)
        os.makedirs(file_path, exist_ok=True)
        file_name = os.path.join(file_path, "Data_dictionary_daily_means.csv")
        df_labels.to_csv(file_name, index=False)

def main():
    files_list = reading_filelist()
    time_resolutions, dataframes = reading_part_proc(files_list)
    truncated_dataframes = remove_data(dataframes)
    creating_dummy(truncated_dataframes, files_list, dataframes, time_resolutions)
    trimmed_dfs = trimmed_dataset(truncated_dataframes, files_list, time_resolutions)
    summary_dataframes = creating_headers(files_list)
    summary_dfs = summarise_variables(files_list, trimmed_dfs, time_resolutions, summary_dataframes)
    data_dic(summary_dfs)    

# Calling the functions
if __name__ == '__main__':
    main()



