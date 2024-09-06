############################################################################################################
# This file collapses hourly means to overall means
# Author: CAS
# Date: 26/06/2024
# Version: 1.0 Translated from Stata code
############################################################################################################
# IMPORTING PACKAGES #
import os
import pandas as pd
import config
from datetime import timedelta
import numpy as np
import statsmodels.api as sm

##################
# Processing #
##################

# Creating individual summary resolution folder if not already there
def create_folders():
    try:
        os.makedirs(os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_TRIMMED_F, config.TIME_RES_FOLDER))
        os.makedirs(os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_SUM_F, config.TIME_RES_FOLDER))
    except FileExistsError:
        pass


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
            part_proc_df['serial'] = part_proc_df.groupby('file_id').ngroup() + 1
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
        if config.TRUNCATE_DATA == 'Yes':
            threshold_datetime = dataframe['DATETIME_ORIG'].iloc[0] + timedelta(days=config.NO_OF_DAYS)
            dataframe = dataframe[dataframe['DATETIME_ORIG'] <= threshold_datetime]

        # Changing Pwear to 0 if flag mechanical noise is 1
        if config.REMOVE_MECH_NOISE == 'Yes':
            dataframe.loc[dataframe['FLAG_MECH_NOISE'] == 0, 'Pwear'] = 0

        # Dropping last data point if file contains an anomaly F
        if config.DROP_END_ANOM_F == 'Yes':
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
            file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_SUM_F, config.TIME_RES_FOLDER)
            os.makedirs(file_path, exist_ok=True)
            file_name = os.path.join(file_path, f"{file_list}_{config.SUM_OVERALL_MEANS}.csv")

            new_dummy_df.to_csv(file_name, index=False)


def trimmed_dataset(truncated_dataframes, files_list, time_resolutions):
    trimmed_dfs = []
    for truncated_dataframe, file_list, time_resolution in zip(truncated_dataframes, files_list, time_resolutions):
        row_count = len(truncated_dataframe)
        flag_valid_total = truncated_dataframe['temp_flag_no_valid_days'].min()

        if row_count > 1 or flag_valid_total != 1:
            truncated_dataframe.drop(columns='temp_flag_no_valid_days', inplace=True)
            truncated_dataframe.sort_values(by=['file_id', 'DATETIME'], inplace=True)

            # Outputting dataset
            file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_TRIMMED_F, config.TIME_RES_FOLDER)
            os.makedirs(file_path, exist_ok=True)
            file_name = os.path.join(file_path, f"{file_list}_TRIMMED_{config.count_prefixes}.csv")

            truncated_dataframe.to_csv(file_name, index=False)

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
            truncated_dataframe['wkend'] = 0
            truncated_dataframe.loc[(truncated_dataframe['dayofweek'] == 6) | (truncated_dataframe['dayofweek'] == 7) & (truncated_dataframe['dayofweek'].notna()), 'wkend'] = 1
            truncated_dataframe['wkday'] = 0
            truncated_dataframe.loc[(truncated_dataframe['dayofweek'] <= 5) & (truncated_dataframe['dayofweek'].notna()), 'wkday'] = 1

            # Generating the morning and midnight axes for purposes of diurnal adjustment
            truncated_dataframe['MORNING'] = np.sin(2 * np.pi * (truncated_dataframe['hourofday'] / 24))
            truncated_dataframe['MIDNIGHT'] = np.cos(2 * np.pi * (truncated_dataframe['hourofday'] / 24))


            truncated_dataframe['index'] = truncated_dataframe.groupby('file_id').cumcount() + 1

            # Generating PWEAR variables
            truncated_dataframe['row'] = truncated_dataframe.groupby('file_id').cumcount() + 1

            truncated_dataframe['Pwear'] = pd.to_numeric(truncated_dataframe['Pwear'])
            truncated_dataframe['PWEAR_MORNING'] = truncated_dataframe['Pwear'] * truncated_dataframe['MORNING']
            truncated_dataframe['PWEAR_MIDNIGHT'] = truncated_dataframe['Pwear'] * truncated_dataframe['MIDNIGHT']
            truncated_dataframe['consecutive_hour'] = truncated_dataframe['index'] * time_resolution / 60

            trimmed_dfs.append(truncated_dataframe)
    return trimmed_dfs

# CREATING DATASET WITH JUST HEADERS, TO FILL IN WITH DATA LATER ON
def creating_headers(files_list):
    summary_dataframes = []

    for file in files_list:
        list_of_variables = ['id', 'startdate', 'RecordLength', 'Pwear', 'Pwear_morning', 'Pwear_noon', 'Pwear_afternoon', 'Pwear_night', 'Pwear_wkday', 'Pwear_wkend',
                             'Pwear_morning_wkday', 'Pwear_noon_wkday', 'Pwear_afternoon_wkday', 'Pwear_night_wkday',
                             'Pwear_morning_wkend', 'Pwear_noon_wkend', 'Pwear_afternoon_wkend', 'Pwear_night_wkend',
                             'enmo_mean',
                             'enmo_0plus', 'enmo_1plus', 'enmo_2plus', 'enmo_3plus', 'enmo_4plus', 'enmo_5plus', 'enmo_10plus', 'enmo_15plus', 'enmo_20plus', 'enmo_25plus', 'enmo_30plus', 'enmo_35plus',
                             'enmo_40plus', 'enmo_45plus', 'enmo_50plus', 'enmo_55plus', 'enmo_60plus', 'enmo_65plus', 'enmo_70plus', 'enmo_75plus', 'enmo_80plus', 'enmo_85plus', 'enmo_90plus',
                             'enmo_95plus', 'enmo_100plus', 'enmo_105plus', 'enmo_110plus', 'enmo_115plus', 'enmo_120plus', 'enmo_125plus', 'enmo_130plus', 'enmo_135plus', 'enmo_140plus',
                             'enmo_145plus', 'enmo_150plus', 'enmo_160plus', 'enmo_170plus', 'enmo_180plus', 'enmo_190plus', 'enmo_200plus', 'enmo_210plus', 'enmo_220plus', 'enmo_230plus',
                             'enmo_240plus', 'enmo_250plus', 'enmo_260plus', 'enmo_270plus', 'enmo_280plus', 'enmo_290plus', 'enmo_300plus', 'enmo_400plus', 'enmo_500plus', 'enmo_600plus',
                             'enmo_700plus', 'enmo_800plus', 'enmo_900plus', 'enmo_1000plus', 'enmo_2000plus', 'enmo_3000plus', 'enmo_4000plus',
                             'device', 'file_start_error', 'file_end_error', 'calibration_method', 'noise_cutoff', 'processing_epoch',
                             'generic_first_timestamp', 'generic_last_timestamp', 'qc_first_battery_pct', 'qc_last_battery_pct', 'frequency', 'TIME_RESOLUTION', 'qc_anomalies_total',
                             'qc_anomaly_a', 'qc_anomaly_b', 'qc_anomaly_c', 'qc_anomaly_d', 'qc_anomaly_e', 'qc_anomaly_f', 'qc_anomaly_g', 'FLAG_MECH_NOISE']
        headers_df = pd.DataFrame(columns=list_of_variables)
        summary_dataframes.append(headers_df)

        # Outputting empty dataframe
        file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_SUM_F, config.TIME_RES_FOLDER)
        os.makedirs(file_path, exist_ok=True)
        file_name = os.path.join(file_path, f"{file}_{config.SUM_OVERALL_MEANS}.csv")

        headers_df.to_csv(file_name, index=False)
    return summary_dataframes


# CREATING VARIABLES FOR SUMMARY DATASET
def summarise_variables(files_list, trimmed_dfs, time_resolutions, summary_dataframes):
    summary_dfs = []

    for file, trimmed_df, time_resolution, summary_df in zip(files_list, trimmed_dfs, time_resolutions, summary_dataframes):

        # Creating id variable if it doesn't already exist
        if 'id' not in trimmed_df.columns:
            trimmed_df[['id', 'file_id2']] = trimmed_df['file_id'].str.split('_', n=1, expand=True)
            trimmed_df.drop(columns=['file_id2'], inplace=True)
        trimmed_df['id'] = trimmed_df['id'].str.upper()

        # Formatting timestamp variables:
        trimmed_df['generic_first_timestamp'] = pd.to_datetime(trimmed_df['generic_first_timestamp'], dayfirst=True)
        trimmed_df['generic_first_timestamp'] = trimmed_df['generic_first_timestamp'].dt.strftime('%d/%m/%Y %H:%M:%S')
        trimmed_df['generic_last_timestamp'] = pd.to_datetime(trimmed_df['generic_last_timestamp'], dayfirst=True)
        trimmed_df['generic_last_timestamp'] = trimmed_df['generic_last_timestamp'].dt.strftime('%d/%m/%Y %H:%M:%S')


        # Creating variables to put into the dataframe later:
        first_row = trimmed_df.index.min()
        first_row_data = trimmed_df.loc[first_row]
        id_value = first_row_data['id']
        file_id_value = first_row_data['file_id']
        startdate_value = first_row_data['DATE']
        device_value = first_row_data['device']
        noise_cutoff_value = first_row_data['noise_cutoff_mg']
        processing_epoch_value = first_row_data['processing_epoch']
        file_end_error_value = first_row_data['end_error']
        file_start_error_value = first_row_data['start_error']
        calibration_method_value = first_row_data['calibration_method']
        generic_first_timestamp_value = first_row_data['generic_first_timestamp']
        generic_last_timestamp_value = first_row_data['generic_last_timestamp']
        qc_first_battery_pct_value = first_row_data['QC_first_battery_pct']
        qc_last_battery_pct_value = first_row_data['QC_last_battery_pct']
        frequency_value = first_row_data['frequency']
        qc_anomalies_total_value = first_row_data['QC_anomalies_total']
        qc_anomaly_a_value = first_row_data['QC_anomaly_A']
        qc_anomaly_b_value = first_row_data['QC_anomaly_B']
        qc_anomaly_c_value = first_row_data['QC_anomaly_C']
        qc_anomaly_d_value = first_row_data['QC_anomaly_D']
        qc_anomaly_e_value = first_row_data['QC_anomaly_E']
        qc_anomaly_f_value = first_row_data['QC_anomaly_F']
        qc_anomaly_g_value = first_row_data['QC_anomaly_G']
        flag_mech_noise = first_row_data['FLAG_MECH_NOISE']

        # Adding the summary variables to the empty dataframe
        summary_dict = {
            'id': file_id_value,
            'startdate': startdate_value,
            'device': device_value,
            'noise_cutoff': noise_cutoff_value,
            'processing_epoch': processing_epoch_value,
            'file_end_error': file_end_error_value,
            'file_start_error': file_start_error_value,
            'generic_first_timestamp': generic_first_timestamp_value,
            'generic_last_timestamp': generic_last_timestamp_value,
            'qc_first_battery_pct': qc_first_battery_pct_value,
            'qc_last_battery_pct': qc_last_battery_pct_value,
            'frequency': frequency_value,
            'qc_anomalies_total': qc_anomalies_total_value,
            'qc_anomaly_a': qc_anomaly_a_value,
            'qc_anomaly_b': qc_anomaly_b_value,
            'qc_anomaly_c': qc_anomaly_c_value,
            'qc_anomaly_d': qc_anomaly_d_value,
            'qc_anomaly_e': qc_anomaly_e_value,
            'qc_anomaly_f': qc_anomaly_f_value,
            'qc_anomaly_g': qc_anomaly_g_value,
            'calibration_method': calibration_method_value,
            'TIME_RESOLUTION': time_resolution,
            'FLAG_MECH_NOISE': flag_mech_noise
        }

        ##################################
        ### SUMMARISING PWEAR SEGMENTS ###
        ##################################
        variables = [
            'Pwear', 'RecordLength',
            'Pwear_morning', 'Pwear_noon', 'Pwear_afternoon', 'Pwear_night',
            'Pwear_morning_wkday', 'Pwear_noon_wkday', 'Pwear_afternoon_wkday', 'Pwear_night_wkday',
            'Pwear_morning_wkend', 'Pwear_noon_wkend', 'Pwear_afternoon_wkend', 'Pwear_night_wkend',
            'Pwear_wkday', 'Pwear_weekend'
            ]

        results = {var: np.nan for var in variables}

        formula = 60/time_resolution

        results['PWear'] = trimmed_df['Pwear'].sum() / formula
        PWear_count = trimmed_df['Pwear'].notna().sum()
        RecordLengt = PWear_count * formula
        #results['RecordLength'] = PWear_count * formula
        summary_dict['RecordLength'] = RecordLengt

        # PWear variables by quadrants
        quad_morning_hours = (trimmed_df['hourofday'] > 0) & (trimmed_df['hourofday'] <= 6)
        quad_noon_hours = (trimmed_df['hourofday'] > 6) & (trimmed_df['hourofday'] <= 12)
        quad_afternoon_hours = (trimmed_df['hourofday'] > 12) & (trimmed_df['hourofday'] <= 18)
        quad_night_hours = (trimmed_df['hourofday'] > 18) & (trimmed_df['hourofday'] <= 24)

        quadrants = ['morning', 'noon', 'afternoon', 'night']
        quad_variables = [quad_morning_hours, quad_noon_hours, quad_afternoon_hours, quad_night_hours]
        Pwear_by_quad = {}

        for quad, variables in zip(quadrants, quad_variables):
            Pwear_sum = trimmed_df.loc[variables, 'Pwear'].sum()
            quadrant = f'Pwear_{quad}'
            Pwear_by_quad[quadrant] = Pwear_sum/formula
            summary_dict[quadrant] = Pwear_by_quad[quadrant]


        #PWear variables by weekend/weekday
        PWear_wkday = trimmed_df[trimmed_df['wkday'] == 1]['Pwear'].sum()/formula
        PWear_wkend = trimmed_df[trimmed_df['wkend'] == 1]['Pwear'].sum()/formula

        summary_dict['Pwear_wkday'] = PWear_wkday
        summary_dict['Pwear_wkend'] = PWear_wkend

        #PWear variables by quadrant and weekend/weekday
        day_types = ['wkday', 'wkend']
        Pwear_by_quad_daytime = {}
        for day_type in day_types:
            for quad, variables in zip(quadrants, quad_variables):
                condition = variables & (trimmed_df[day_type] == 1)
                Pwear_sum = trimmed_df.loc[condition, 'Pwear'].sum()
                key = f'Pwear_{quad}_{day_type}'
                Pwear_by_quad_daytime[key] = Pwear_sum / formula

                summary_dict[key] = Pwear_by_quad_daytime[key]


        ####################################
        ### SUMMARISING OUTPUT VARIABLES ###
        ####################################

        # ENMO MEAN
        filtered_df = trimmed_df[(trimmed_df['ENMO_mean'].notna()) & (trimmed_df['Pwear'].notna()) & (trimmed_df['Pwear'] > 0)]
        Pwear_sum = filtered_df['Pwear'].sum()
        summary_dict['Pwear'] = Pwear_sum

        if Pwear_sum / formula >= config.SUM_MIN_HOUR_INCLUSION:

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
                filtered_df = trimmed_df[(trimmed_df['Pwear'] > 0) & (trimmed_df[column_name].notna())]
                ENMO_sum = filtered_df['Pwear'].sum()

                if ENMO_sum / formula >= config.SUM_MIN_HOUR_INCLUSION:
                    X = filtered_df[['MORNING', 'MIDNIGHT']]
                    Y = filtered_df[column_name]
                    X = sm.add_constant(X)
                    weights = np.floor(time_resolution * filtered_df['Pwear'])
                    model = sm.WLS(Y, X, weights=weights)
                    results = model.fit()
                    column_name = column_name.lower()
                    summary_dict[column_name] = results.params['const']

        summary_df = pd.concat([summary_df, pd.DataFrame([summary_dict])], ignore_index=True)

        # Rounding all numeric columns to 4 decimal places
        numeric_columns = summary_df.select_dtypes(include=['float64', 'float32']).columns
        summary_df[numeric_columns] = summary_df[numeric_columns].round(4)

        # Outputting summary dataframe
        file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_SUM_F, config.TIME_RES_FOLDER)
        os.makedirs(file_path, exist_ok=True)
        file_name = os.path.join(file_path, f"{file}_{config.SUM_OVERALL_MEANS}.csv")

        summary_df.to_csv(file_name, index=False)
        summary_dfs.append(summary_df)
    return summary_dfs

# Creating data dictionary for all variables:
def data_dic(summary_dfs):
    for summary_df in summary_dfs:

        variable_label = {
            "id": "Study ID",
            "startdate": "Date of first day of free-living recording",
            "RecordLength": "Number of hours file was recording for",
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
            "Pwear_wkday": f"{label}, weekday",
            "Pwear_wkend": f"{label}, weekend day",
            "Pwear_morning_wkday": f"{label}, {quad_morning_hours}, weekday",
            "Pwear_noon_wkday": f"{label}, {quad_morning_hours}, weekday",
            "Pwear_afternoon_wkday": f"{label}, {quad_afternoon_hours}, weekday",
            "Pwear_night_wkday": f"{label}, {quad_night_hours}, weekday",
            "Pwear_morning_wkend": f"{label}, {quad_morning_hours}, weekend day",
            "Pwear_noon_wkend": f"{label}, {quad_morning_hours}, weekend day",
            "Pwear_afternoon_wkend": f"{label}, {quad_afternoon_hours}, weekend day",
            "Pwear_night_wkend": f"{label}, {quad_night_hours}, weekend day",
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
            "generic_first_timestamp": "Generic first data timestamp of collection",
            "generic_last_timestamp": "Generic last data timestamp of download",
            "qc_first_battery_pct": "Battery percentage of device at beginning of data collection",
            "qc_last_battery_pct": "Battery percentage of device at end of data collection",
            "frequency": "Recording frequency in hz",
            "TIME_RESOLUTION": "Time resolution of processed data (minutes)",
            "qc_anomalies_total": "",
            "qc_anomalies_a": "",
            "qc_anomalies_b": "",
            "qc_anomalies_c": "",
            "qc_anomalies_d": "",
            "qc_anomalies_e": "",
            "qc_anomalies_f": "",
            "qc_anomalies_g": ""
        }

        variable_label.update(calibration_labels)


        df_labels = pd.DataFrame(list(variable_label.items()), columns=["Variable", "Label"])

        file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, config.INDIVIDUAL_SUM_F, config.TIME_RES_FOLDER)
        os.makedirs(file_path, exist_ok=True)
        file_name = os.path.join(file_path, "Data_dictionary_summary_means.csv")
        df_labels.to_csv(file_name, index=False)



# Calling the functions
if __name__ == '__main__':
    create_folders()
    files_list = reading_filelist()
    time_resolutions, dataframes = reading_part_proc(files_list)
    truncated_dataframes = remove_data(dataframes)
    creating_dummy(truncated_dataframes, files_list, dataframes, time_resolutions)
    trimmed_dfs = trimmed_dataset(truncated_dataframes, files_list, time_resolutions)
    summary_dataframes = creating_headers(files_list)
    summary_dfs = summarise_variables(files_list, trimmed_dfs, time_resolutions, summary_dataframes)
    data_dic(summary_dfs)