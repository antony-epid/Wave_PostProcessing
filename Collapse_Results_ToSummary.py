############################################################################################################
# This file collapses hourly means to overall means
# Author: CAS
# Date: 26/06/2024
# Version: 1.0 Translated from Stata code
# Version: 2.0 - 21/11/2024: Updated to run on Pampro output
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

# Creating folder_paths in results folder:
def create_path(top_folder):
    path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, top_folder, config.TIME_RES_FOLDER)
    return path

# Creating individual summary resolution folder if not already there
def create_folders(folder_path):
    try:
        os.makedirs(folder_path)
    except FileExistsError:
        pass

# READING IN FILELIST
def reading_filelist(id=''):
    os.chdir(os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.FILELIST_FOLDER))
    #filelist_df = pd.read_csv('filelist.txt', delimiter='\t')  # Reading in the filelist
    filelist_df = pd.read_csv('filelist' + id + '.txt', delimiter='\t')  # Reading in the filelist    
    filelist_df = filelist_df.drop_duplicates(subset=['filename_temp'])
    file_list = filelist_df['filename_temp'].tolist()
    return file_list


# LOOPING THROUGH EACH FILE FOR COLLAPSING
def reading_part_proc(partPro_path, file_id, date_orig):
    part_proc_file_path = os.path.join(partPro_path, f"{file_id}_{config.OUTPUT_FILE_EXT}.csv")
    if os.path.exists(part_proc_file_path):
        df = pd.read_csv(part_proc_file_path)
        df.sort_values(by=['file_id', 'DATETIME'], inplace=True)
        df[date_orig] = pd.to_datetime(df[date_orig], format='%Y-%m-%d %H:%M:%S')
        time_difference = df[date_orig].iloc[1] - df[date_orig].iloc[0]
        time_resolution = time_difference.total_seconds() / 60

    return time_resolution, df

# REMOVING NON VALID HOURS
def remove_data(df):
    # If a wear log is provided with date and time for wear times the days will have been flagged as either valid or not
    # day_valid = 1: within valid time frame
    # day_valid = 2: No timeframe provided - everything kept
    # day_valid = 0: Outside valid time frame
    if config.USE_WEAR_LOG.lower() == 'yes':
        df = df[df['day_valid'] != 0]

    if config.USE_WEAR_LOG.lower() == 'no':
        if config.TRUNCATE_DATA.lower() == 'yes':
            threshold_datetime = df['DATETIME_ORIG'].iloc[0] + timedelta(days=config.NO_OF_DAYS)
            df = df[df['DATETIME_ORIG'] <= threshold_datetime]

    # Changing Pwear to 0 if flag mechanical noise is 1
    if config.REMOVE_MECH_NOISE.lower() == 'yes':
        df.loc[df['FLAG_MECH_NOISE'] == 1, 'Pwear'] = 0

    # Dropping last data point if file contains an anomaly F
    if config.DROP_END_ANOM_F.lower() == 'yes':
        if config.PROCESSING.lower() == 'wave':
            anom_F = 'QC_anomaly_F'
        if config.PROCESSING.lower() == 'pampro':
            anom_F = 'Anom_F'
        if df[anom_F].min() > 0:
            df['row'] = df.index + 1
            max_row = df['row'].max()
            df = df[df['row'] != max_row]
            df.drop(columns=['row'], inplace=True)

    return df

# CREATING "DUMMY" DATASET (EMPTY) IF ALL TIMES FALL OUTSIDE WEAR LOG TIMES OR LESS THAN 1 HOUR DATA
#def creating_dummy(df, file_id, time_resolution):
def creating_dummy(df, file_id, time_resolution, summary_files_path, partPro_path):    
    row_count = len(df)
    flag_valid_total = df['temp_flag_no_valid_days'].min()

    if row_count <= 1 or flag_valid_total == 1:
        dummy_df = pd.DataFrame({
            'file_id': file_id,
            'FLAG_NO_VALID_DAYS': [1]
        })
        part_proc_file_path = os.path.join(partPro_path, f"{file_id}_{config.OUTPUT_FILE_EXT}.csv")
        if os.path.exists(part_proc_file_path):
            part_proc_merge_df = pd.read_csv(part_proc_file_path)
        new_dummy_df = pd.merge(dummy_df, part_proc_merge_df, on='file_id', how='outer', validate='1:m', indicator=True)
        columns_to_keep = ['file_id', 'FLAG_NO_VALID_DAYS', 'device', 'calibration_method', 'noise_cutoff_mg', 'processing_epoch',
                           'generic_first_timestamp', 'generic_last_timestamp', 'QC_first_battery_pct', 'QC_last_battery_pct', 'frequency']
        if config.PROCESSING.lower() == 'wave':
            columns_to_keep += config.ANOM_VAR_WAVE + ['start_error', 'end_error', 'QC_anomalies_total', 'processing_script']
        if config.PROCESSING.lower() == 'pampro':
            columns_to_keep += config.ANOM_VAR_PAMPRO + ['calibration_type', 'file_start_error', 'file_end_error', 'mf_start_error', 'mf_end_error']
        if config.USE_WEAR_LOG.lower() == 'yes':
            columns_to_keep.extend(['start', 'end'])
        new_dummy_df = new_dummy_df[columns_to_keep]
        new_dummy_df['TIME_RESOLUTION'] = time_resolution

        var_to_convert = ['start', 'end']
        for variables in var_to_convert:
            if variables in new_dummy_df.columns:
                new_dummy_df[variables] = new_dummy_df[variables].astype(str)

        # Keep first row only
        new_dummy_df = new_dummy_df.head(1).rename(columns={'file_id': 'id'})
        new_dummy_df['id'] = new_dummy_df['id'].str.upper()

        # Outputting dummy dataset
        file_name = os.path.join(summary_files_path, f"{file_id}_{config.SUM_OVERALL_MEANS}.csv")
        new_dummy_df.to_csv(file_name, index=False)

    return row_count, flag_valid_total

#def trimmed_dataset(df, file_id, time_resolution):
def trimmed_dataset(df, file_id, time_resolution, trimmed_path):
    row_count = len(df)
    flag_valid_total = df['temp_flag_no_valid_days'].min()

    if row_count > 1 and flag_valid_total != 1:
        df.drop(columns='temp_flag_no_valid_days').sort_values(by=['file_id', 'DATETIME'])

        # Outputting dataset
        os.makedirs(trimmed_path, exist_ok=True)
        file_name = os.path.join(trimmed_path, f"{file_id}_TRIMMED_{config.count_prefixes}.csv")
        df.to_csv(file_name, index=False)

        # Generating day number and day change:
        df['day_number'] = 1
        df['day_change'] = 0
        df.loc[(df['hourofday'] == 1) & (df['hourofday'].shift(1) == 24) & (df['file_id'] == df['file_id'].shift(1)), 'day_change'] = 1
        day_number = 1
        for idx, row in df.iterrows():
            if row['day_change'] == 1:
                day_number += 1
            df.at[idx, 'day_number'] = day_number
        df.drop(columns=['day_change'], inplace=True)

        # Excluding data (based on local exclude_hours list) only if specified in header
        df['INCLUDE'] = 0
        df['awake_pwear'] = None

        # Sorting out the date/time variables
        df['wkend'] = 0
        df.loc[(df['dayofweek'] == 6) | (df['dayofweek'] == 7) & (df['dayofweek'].notna()), 'wkend'] = 1
        df['wkday'] = 0
        df.loc[(df['dayofweek'] <= 5) & (df['dayofweek'].notna()), 'wkday'] = 1

        # Generating the morning and midnight axes for purposes of diurnal adjustment
        df['MORNING'] = np.sin(2 * np.pi * (df['hourofday'] / 24))
        df['MIDNIGHT'] = np.cos(2 * np.pi * (df['hourofday'] / 24))

        df['index'] = df.groupby('file_id').cumcount() + 1

        # Generating PWEAR variables
        df['row'] = df.groupby('file_id').cumcount() + 1

        df['Pwear'] = pd.to_numeric(df['Pwear'])
        df['PWEAR_MORNING'] = df['Pwear'] * df['MORNING']
        df['PWEAR_MIDNIGHT'] = df['Pwear'] * df['MIDNIGHT']
        df['consecutive_hour'] = df['index'] * time_resolution / 60

    return df


# CREATING DATASET WITH JUST HEADERS, TO FILL IN WITH DATA LATER ON
#def creating_headers(file_id):
def creating_headers(file_id, summary_files_path):
    
    generic_variables = ['id', 'startdate', 'RecordLength',
                         'device', 'file_start_error', 'file_end_error', 'calibration_method', 'noise_cutoff', 'processing_epoch',
                         'generic_first_timestamp', 'generic_last_timestamp', 'qc_first_battery_pct', 'qc_last_battery_pct', 'frequency', 'TIME_RESOLUTION']

    enmo_variables = ['enmo_mean', 'enmo_0plus', 'enmo_1plus', 'enmo_2plus', 'enmo_3plus', 'enmo_4plus', 'enmo_5plus', 'enmo_10plus', 'enmo_15plus', 'enmo_20plus', 'enmo_25plus', 'enmo_30plus', 'enmo_35plus',
                         'enmo_40plus', 'enmo_45plus', 'enmo_50plus', 'enmo_55plus', 'enmo_60plus', 'enmo_65plus', 'enmo_70plus', 'enmo_75plus', 'enmo_80plus', 'enmo_85plus', 'enmo_90plus',
                         'enmo_95plus', 'enmo_100plus', 'enmo_105plus', 'enmo_110plus', 'enmo_115plus', 'enmo_120plus', 'enmo_125plus', 'enmo_130plus', 'enmo_135plus', 'enmo_140plus',
                         'enmo_145plus', 'enmo_150plus', 'enmo_160plus', 'enmo_170plus', 'enmo_180plus', 'enmo_190plus', 'enmo_200plus', 'enmo_210plus', 'enmo_220plus', 'enmo_230plus',
                         'enmo_240plus', 'enmo_250plus', 'enmo_260plus', 'enmo_270plus', 'enmo_280plus', 'enmo_290plus', 'enmo_300plus', 'enmo_400plus', 'enmo_500plus', 'enmo_600plus',
                         'enmo_700plus', 'enmo_800plus', 'enmo_900plus', 'enmo_1000plus', 'enmo_2000plus', 'enmo_3000plus', 'enmo_4000plus']

    hpfvm_variables = ['hpfvm_mean', 'hpfvm_0plus', 'hpfvm_1plus', 'hpfvm_2plus', 'hpfvm_3plus', 'hpfvm_4plus', 'hpfvm_5plus', 'hpfvm_10plus', 'hpfvm_15plus', 'hpfvm_20plus', 'hpfvm_25plus', 'hpfvm_30plus', 'hpfvm_35plus',
                         'hpfvm_40plus', 'hpfvm_45plus', 'hpfvm_50plus', 'hpfvm_55plus', 'hpfvm_60plus', 'hpfvm_65plus', 'hpfvm_70plus', 'hpfvm_75plus', 'hpfvm_80plus', 'hpfvm_85plus', 'hpfvm_90plus',
                         'hpfvm_95plus', 'hpfvm_100plus', 'hpfvm_105plus', 'hpfvm_110plus', 'hpfvm_115plus', 'hpfvm_120plus', 'hpfvm_125plus', 'hpfvm_130plus', 'hpfvm_135plus', 'hpfvm_140plus',
                         'hpfvm_145plus', 'hpfvm_150plus', 'hpfvm_160plus', 'hpfvm_170plus', 'hpfvm_180plus', 'hpfvm_190plus', 'hpfvm_200plus', 'hpfvm_210plus', 'hpfvm_220plus', 'hpfvm_230plus',
                         'hpfvm_240plus', 'hpfvm_250plus', 'hpfvm_260plus', 'hpfvm_270plus', 'hpfvm_280plus', 'hpfvm_290plus', 'hpfvm_300plus', 'hpfvm_400plus', 'hpfvm_500plus', 'hpfvm_600plus',
                         'hpfvm_700plus', 'hpfvm_800plus', 'hpfvm_900plus', 'hpfvm_1000plus', 'hpfvm_2000plus', 'hpfvm_3000plus', 'hpfvm_4000plus']

    pwear_variables = ['Pwear', 'Pwear_morning', 'Pwear_noon', 'Pwear_afternoon', 'Pwear_night', 'Pwear_wkday', 'Pwear_wkend',
                         'Pwear_morning_wkday', 'Pwear_noon_wkday', 'Pwear_afternoon_wkday', 'Pwear_night_wkday',
                         'Pwear_morning_wkend', 'Pwear_noon_wkend', 'Pwear_afternoon_wkend', 'Pwear_night_wkend']

    list_of_variables = generic_variables + enmo_variables + pwear_variables
    
    if not any(item.lower() == "hpfvm" for item in config.VARIABLES_TO_DROP):
        list_of_variables += hpfvm_variables

    if config.PROCESSING.lower() == 'pampro':
        list_of_variables += ['mf_start_error', 'mf_end_error', 'calibration_type']
        enmo_IMP_variables = [var + '_IMP' for var in enmo_variables]
        pwear_IMP_variables = [var + '_IMP' for var in pwear_variables]
        pwear_days = [f'pwear_day{day}' for day in range(1, 8)]
        pwear_hours = [f'pwear_hour{hour}' for hour in range(1, 25)]
        enmo_days = [f'enmo_mean_day{day}' for day in range(1, 8)]
        enmo_hours = [f'enmo_mean_hour{hour}' for hour in range(1, 25)]
        all_IMP = [pwear_days, pwear_hours, enmo_days, enmo_hours]
        if not any(item.lower() == "hpfvm" for item in config.VARIABLES_TO_DROP):
            hpfvm_IMP_variables = [var + '_IMP' for var in hpfvm_variables]
            hpfvm_days = [f'hpfvm_mean_day{day}' for day in range(1, 8)]
            hpfvm_hours = [f'hpfvm_mean_hour{hour}' for hour in range(1, 25)]
            all_IMP += [hpfvm_days, hpfvm_hours]
        IMP_variables = [var + '_IMP' for sublist in all_IMP for var in sublist]
        list_of_variables += config.ANOM_VAR_PAMPRO + enmo_IMP_variables + pwear_IMP_variables + pwear_days + pwear_hours + enmo_days + enmo_hours + IMP_variables

        if not any(item.lower() == "hpfvm" for item in config.VARIABLES_TO_DROP):

            list_of_variables += hpfvm_days + hpfvm_hours + hpfvm_IMP_variables

    if config.PROCESSING.lower() == 'wave':
        list_of_variables.extend(['qc_anomalies_total'])
        list_of_variables += config.ANOM_VAR_WAVE

    if config.USE_WEAR_LOG.lower() == 'yes':
        list_of_variables += ['start', 'end', 'flag_no_wear_info', 'flag_no_end_date', 'flag_missing_starthour', 'flag_missing_endhour']

    headers_df = pd.DataFrame(columns=list_of_variables)

    # Outputting empty dataframe
    os.makedirs(summary_files_path, exist_ok=True)
    file_name = os.path.join(summary_files_path, f"{file_id}_{config.SUM_OVERALL_MEANS}.csv")
    headers_df.to_csv(file_name, index=False)

    return headers_df

# INPUTTING DATA TO THE EMPTY DATAFRAME
def input_data(df, time_resolution):

    if df is not None and not df.empty:
        # Creating id variable if it doesn't already exist
        if 'id' not in df.columns:
            df['file_id'] = df['file_id'].astype(str)
            if df['file_id'].str.contains('_').any():
                df[['id', 'file_id2']] = df['file_id'].str.split('_', n=1, expand=True)
                df.drop(columns=['file_id2'], inplace=True)
            else:
                df['id'] = df['file_id']
        df['id'] = df['id'].str.upper()

        # Formatting timestamp variables:
        timestamp_variables = ['generic_first_timestamp', 'generic_last_timestamp']
        for timestamp_variable in timestamp_variables:
            df[timestamp_variable] = pd.to_datetime(df[timestamp_variable], dayfirst=True)
            df[timestamp_variable] = df[timestamp_variable].dt.strftime('%d/%m/%Y %H:%M:%S')

        # Creating variables to put into the dataframe later:
        first_row = df.index.min()
        first_row_data = df.loc[first_row]
        id_value = first_row_data['id']
        file_id_value = first_row_data['file_id']
        startdate_value = first_row_data['DATE']
        device_value = first_row_data['device']
        noise_cutoff_value = first_row_data['noise_cutoff_mg']
        processing_epoch_value = first_row_data['processing_epoch']
        calibration_method_value = first_row_data['calibration_method']
        if config.PROCESSING.lower() == 'wave':
            file_end_error_value = first_row_data['end_error']
            file_start_error_value = first_row_data['start_error']
        if config.PROCESSING.lower() == 'pampro':
            file_start_error_value = first_row_data['file_start_error']
            file_end_error_value = first_row_data['file_end_error']
            mf_start_error_value = first_row_data['mf_start_error']
            mf_end_error_value = first_row_data['mf_end_error']
            calibration_type_value = first_row_data['calibration_type']
        if config.USE_WEAR_LOG.lower() == 'yes':
            wear_log_start_value = first_row_data['start']
            wear_log_end_value = first_row_data['end']
            flag_no_wear_info_value = df['flag_no_wear_info'].max()
            flag_no_end_date_value = df['flag_no_end_date'].max()
            flag_missing_starthour_value = df['flag_missing_starthour'].max()
            flag_missing_endhour_value = df['flag_missing_endhour'].max()
        generic_first_timestamp_value = first_row_data['generic_first_timestamp']
        generic_last_timestamp_value = first_row_data['generic_last_timestamp']
        qc_first_battery_pct_value = first_row_data['QC_first_battery_pct']
        qc_last_battery_pct_value = first_row_data['QC_last_battery_pct']
        frequency_value = first_row_data['frequency']
        if config.PROCESSING.lower() == 'wave':
            qc_anomalies_total_value = first_row_data['QC_anomalies_total']
            qc_anomaly_a_value = first_row_data['QC_anomaly_A']
            qc_anomaly_b_value = first_row_data['QC_anomaly_B']
            qc_anomaly_c_value = first_row_data['QC_anomaly_C']
            qc_anomaly_d_value = first_row_data['QC_anomaly_D']
            qc_anomaly_e_value = first_row_data['QC_anomaly_E']
            qc_anomaly_f_value = first_row_data['QC_anomaly_F']
            qc_anomaly_g_value = first_row_data['QC_anomaly_G']
        if config.PROCESSING.lower() == 'pampro':
            qc_anomaly_a_value = first_row_data['Anom_A']
            qc_anomaly_b_value = first_row_data['Anom_B']
            qc_anomaly_c_value = first_row_data['Anom_C']
            qc_anomaly_d_value = first_row_data['Anom_D']
            qc_anomaly_e_value = first_row_data['Anom_E']
            qc_anomaly_f_value = first_row_data['Anom_F']

        # Adding the summary variables to the empty dataframe
        summary_dict = {
            'id': file_id_value,
            'startdate': startdate_value,
            'device': device_value,
            'noise_cutoff': noise_cutoff_value,
            'processing_epoch': processing_epoch_value,
            'file_start_error': file_start_error_value,
            'file_end_error': file_end_error_value,
            'generic_first_timestamp': generic_first_timestamp_value,
            'generic_last_timestamp': generic_last_timestamp_value,
            'qc_first_battery_pct': qc_first_battery_pct_value,
            'qc_last_battery_pct': qc_last_battery_pct_value,
            'frequency': frequency_value,
            'calibration_method': calibration_method_value,
            'TIME_RESOLUTION': time_resolution
        }
        if config.PROCESSING.lower() == 'wave':
            wave_dict = {
                'qc_anomalies_total': qc_anomalies_total_value,
                'qc_anomaly_a': qc_anomaly_a_value,
                'qc_anomaly_b': qc_anomaly_b_value,
                'qc_anomaly_c': qc_anomaly_c_value,
                'qc_anomaly_d': qc_anomaly_d_value,
                'qc_anomaly_e': qc_anomaly_e_value,
                'qc_anomaly_f': qc_anomaly_f_value,
                'qc_anomaly_g': qc_anomaly_g_value
            }
            summary_dict.update(wave_dict)

        if config.PROCESSING.lower() == 'pampro':
            pampro_dict = {
                'mf_start_error': mf_start_error_value,
                'mf_end_error': mf_end_error_value,
                'calibration_type': calibration_type_value,
                'Anom_A': qc_anomaly_a_value,
                'Anom_B': qc_anomaly_b_value,
                'Anom_C': qc_anomaly_c_value,
                'Anom_D': qc_anomaly_d_value,
                'Anom_E': qc_anomaly_e_value,
                'Anom_F': qc_anomaly_f_value,
            }
            summary_dict.update(pampro_dict)

        if config.USE_WEAR_LOG.lower() == 'yes':
            wear_log_dict = {
                'start': wear_log_start_value,
                'end': wear_log_end_value,
                'flag_no_wear_info': flag_no_wear_info_value,
                'flag_no_end_date': flag_no_end_date_value,
                'flag_missing_starthour': flag_missing_starthour_value,
                'flag_missing_endhour': flag_missing_endhour_value
            }
            summary_dict.update(wear_log_dict)

        return summary_dict


# CREATING PWEAR VARIABLES AND IMPUTTING TO THE EMPTY DATAFRAME
#def input_pwear_segment(df, summary_dict):
def input_pwear_segment(df, summary_dict, formula, quadrants,quad_variables):    
    if df is not None and not df.empty:

        variables = [
            'Pwear', 'RecordLength',
            'Pwear_morning', 'Pwear_noon', 'Pwear_afternoon', 'Pwear_night',
            'Pwear_morning_wkday', 'Pwear_noon_wkday', 'Pwear_afternoon_wkday', 'Pwear_night_wkday',
            'Pwear_morning_wkend', 'Pwear_noon_wkend', 'Pwear_afternoon_wkend', 'Pwear_night_wkend',
            'Pwear_wkday', 'Pwear_weekend'
            ]

        results = {var: np.nan for var in variables}

        results['PWear'] = df['Pwear'].sum() / formula
        PWear_count = df['Pwear'].notna().sum()
        RecordLength = PWear_count * formula
        summary_dict['RecordLength'] = RecordLength

        # PWear variables by quadrants
        Pwear_by_quad = {}

        for quad, variables in zip(quadrants, quad_variables):
            Pwear_sum = df.loc[variables, 'Pwear'].sum()
            quadrant = f'Pwear_{quad}'
            Pwear_by_quad[quadrant] = Pwear_sum/formula
            summary_dict[quadrant] = Pwear_by_quad[quadrant]

        # PWear variables by weekend/weekday
        PWear_wkday = df[df['wkday'] == 1]['Pwear'].sum()/formula
        PWear_wkend = df[df['wkend'] == 1]['Pwear'].sum()/formula

        summary_dict['Pwear_wkday'] = PWear_wkday
        summary_dict['Pwear_wkend'] = PWear_wkend

        #PWear variables by quadrant and weekend/weekday
        day_types = ['wkday', 'wkend']

        Pwear_by_quad_daytime = {}
        for day_type in day_types:
            for quad, variables in zip(quadrants, quad_variables):
                condition = variables & (df[day_type] == 1)
                Pwear_sum = df.loc[condition, 'Pwear'].sum()
                key = f'Pwear_{quad}_{day_type}'
                Pwear_by_quad_daytime[key] = Pwear_sum / formula

                summary_dict[key] = Pwear_by_quad_daytime[key]

        return summary_dict


# SUMMARISING HOURLY AND DAILY ENMO AND PWEAR VARIABLES
def input_hourly_daily(df, summary_dict):
    if df is not None and not df.empty:

        weighted_hourly_means = (
            df.assign(weighted_ENMO = df['ENMO_mean'] * df['Pwear']).groupby('hourofday')
            .apply(lambda x: x['weighted_ENMO'].sum() / x['Pwear'].sum(), include_groups=False)
        )
        hourly_enmo_variables = {
            f'enmo_mean_hour{hour}': weighted_hourly_means.get(hour, np.nan) for hour in range(1, 25)
        }
        summary_dict.update(hourly_enmo_variables)

        hourly_pwear_sums = df.groupby('hourofday')['Pwear'].sum()
        hourly_pwear_variables = {
            f'pwear_hour{hour}': hourly_pwear_sums.get(hour, np.nan) for hour in range(1, 25)
        }
        summary_dict.update(hourly_pwear_variables)


        weighted_daily_means = (
            df.assign(weighted_daily_ENMO = df['ENMO_mean'] * df['Pwear']).groupby('dayofweek')
            .apply(lambda x: x['weighted_daily_ENMO'].sum() / x['Pwear'].sum(), include_groups=False)
        )
        daily_enmo_variables = {
            f'enmo_mean_day{day}': weighted_daily_means.get(day, np.nan) for day in range(1, 8)
        }
        summary_dict.update(daily_enmo_variables)

        daily_pwear_sums = df.groupby('dayofweek')['Pwear'].sum()
        daily_pwear_variables = {
            f'pwear_day{day}': daily_pwear_sums.get(day, np.nan) for day in range(1, 8)
        }
        summary_dict.update(daily_pwear_variables)

        if not any(item.lower() == "hpfvm" for item in config.VARIABLES_TO_DROP):
            hourly_hpfvm_means = df.groupby('hourofday')['HPFVM_mean'].mean()
            hourly_hpfvm_variables = {
                f'hpfvm_mean_hour{hour}': hourly_hpfvm_means.get(hour, np.nan) for hour in range(1, 25)
            }
            summary_dict.update(hourly_hpfvm_variables)

            daily_hpfvm_means = df.groupby('dayofweek')['HPFVM_mean'].mean()
            daily_hpfvm_variables = {
                f'hpfvm_mean_day{day}': daily_hpfvm_means.get(day, np.nan) for day in range(1, 8)
            }
            summary_dict.update(daily_hpfvm_variables)


        return summary_dict


# SUMMARISING OUTPUT VARIABLES
#def input_output_variables(df, summary_dict, time_resolution):
def input_output_variables(df, summary_dict, time_resolution, formula):
    if df is not None and not df.empty:

        # ENMO MEAN
        filtered_df = df[(df['ENMO_mean'].notna()) & (df['Pwear'].notna()) & (df['Pwear'] > 0)]
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
        
        # HPFVM 
        if not any(item.lower() == "hpfvm" for item in config.VARIABLES_TO_DROP):
            # HPFVM MEAN
            filtered_df = df[(df['HPFVM_mean'].notna()) & (df['Pwear'].notna()) & (df['Pwear'] > 0)]
            Pwear_sum = filtered_df['Pwear'].sum()
            summary_dict['Pwear'] = Pwear_sum

            if Pwear_sum / formula >= config.SUM_MIN_HOUR_INCLUSION:
                X = filtered_df[['MORNING', 'MIDNIGHT']]
                Y = filtered_df['HPFVM_mean']
                X = sm.add_constant(X)
                weights = np.floor(time_resolution * filtered_df['Pwear'])
                model = sm.WLS(Y, X, weights=weights)
                results = model.fit()
                summary_dict['hpfvm_mean'] = results.params['const']

        # INTENSITY VARIABLES
        variable_prefix = 'ENMO_'
        variable_suffix = 'plus'

        # INTENSITY VARIABLES
        variable_prefixes = 'ENMO_'
        if not any(item.lower() == "hpfvm" for item in config.VARIABLES_TO_DROP):
            variable_prefixes += 'HPFVM_'
        variable_suffix = 'plus'

        for variable_prefix in variable_prefixes:
            for column_name in df.columns:
                if column_name.startswith(variable_prefix) and column_name.endswith(variable_suffix):
                    threshold_subset = df[(df['Pwear'] > 0) & (df[column_name].notna())]
                    PWEAR_sum = threshold_subset['Pwear'].sum()

                    if PWEAR_sum / formula >= config.SUM_MIN_HOUR_INCLUSION:
                        X = threshold_subset[['MORNING', 'MIDNIGHT']]
                        Y = threshold_subset[column_name]
                        X = sm.add_constant(X)
                        weights = np.floor(time_resolution * threshold_subset['Pwear'])
                        model = sm.WLS(Y, X, weights=weights)
                        results = model.fit()
                        column_name = column_name.lower()
                        summary_dict[column_name] = results.params['const']
        return summary_dict

# IMPUTING SLEEP DATA
#def impute_data(df, time_resolution):
def impute_data(df, time_resolution, summary_dict, formula, quadrants, quad_variables):
    if df is not None and not df.empty:

        max_days = df['day_number'].max()

        for dayNum in range(1, max_days + 1):
            subset_df = df[(df['day_number'] == dayNum) & (df['Pwear'] == 1)]
            Pwear_sum = subset_df['Pwear'].sum()
            if Pwear_sum > config.MIN_DAY_HOURS:
                for X in config.IMPUTE_HOURS:
                    condition = (
                            (df['hourofday'] == X) &
                            (df['Pwear'] == 0) &
                            (df['day_number'] == dayNum))

                    df.loc[condition, ['ENMO_mean', 'ENMO_0plus', 'Pwear']] = [0, 1, 1]

        # Calculating Pwear Imputed variables by quadrants
        summary_dict['Pwear_IMP'] = df['Pwear'].sum() / formula

        Pwear_IMP_by_quad = {}
        for quad, variables in zip(quadrants, quad_variables):
            Pwear_IMP_sum = df.loc[variables, 'Pwear'].sum()
            quadrant = f'Pwear_{quad}_IMP'
            Pwear_IMP_by_quad[quadrant] = Pwear_IMP_sum / formula
            summary_dict[quadrant] = Pwear_IMP_by_quad[quadrant]

        # PWear imputed variables by weekend/weekday
        PWear_wkday_IMP = df[df['wkday'] == 1]['Pwear'].sum() / formula
        PWear_wkend_IMP = df[df['wkend'] == 1]['Pwear'].sum() / formula

        summary_dict['Pwear_wkday_IMP'] = PWear_wkday_IMP
        summary_dict['Pwear_wkend_IMP'] = PWear_wkend_IMP

        # PWear imputed variables by quadrant and weekend/weekday
        day_types = ['wkday', 'wkend']
        Pwear_by_quad_daytime_IMP = {}
        for day_type in day_types:
            for quad, variables in zip(quadrants, quad_variables):
                condition = variables & (df[day_type] == 1)
                Pwear_sum_IMP = df.loc[condition, 'Pwear'].sum()
                key = f'Pwear_{quad}_{day_type}_IMP'
                Pwear_by_quad_daytime_IMP[key] = Pwear_sum_IMP / formula

                summary_dict[key] = Pwear_by_quad_daytime_IMP[key]

        # ENMO MEAN imputed
        impute_enmo_df = df[
            (df['ENMO_mean'].notna()) & (df['Pwear'].notna()) & (df['Pwear'] > 0)]
        Pwear_sum = impute_enmo_df['Pwear'].sum()

        if Pwear_sum / formula >= config.SUM_MIN_HOUR_INCLUSION:
            X = impute_enmo_df[['MORNING', 'MIDNIGHT']]
            Y = impute_enmo_df['ENMO_mean']
            X = sm.add_constant(X)
            weights = np.floor(time_resolution * impute_enmo_df['Pwear'])
            model = sm.WLS(Y, X, weights=weights)
            results = model.fit()
            summary_dict['enmo_mean_IMP'] = results.params['const']

        if not any(item.lower() == "hpfvm" for item in config.VARIABLES_TO_DROP):
            # HPFVM MEAN imputed
            impute_hpfvm_df = df[
                (df['HPFVM_mean'].notna()) & (df['Pwear'].notna()) & (df['Pwear'] > 0)]
            Pwear_sum = impute_hpfvm_df['Pwear'].sum()

            if Pwear_sum / formula >= config.SUM_MIN_HOUR_INCLUSION:
                X = impute_hpfvm_df[['MORNING', 'MIDNIGHT']]
                Y = impute_hpfvm_df['HPFVM_mean']
                X = sm.add_constant(X)
                weights = np.floor(time_resolution * impute_hpfvm_df['Pwear'])
                model = sm.WLS(Y, X, weights=weights)
                results = model.fit()
                summary_dict['hpfvm_mean_IMP'] = results.params['const']

        # INTENSITY VARIABLES
        variable_prefixes = 'ENMO_'
        if not any(item.lower() == "hpfvm" for item in config.VARIABLES_TO_DROP):
            variable_prefixes += 'HPFVM_'
        variable_suffix = 'plus'

        for variable_prefix in variable_prefixes:
            for column_name in df.columns:
                if column_name.startswith(variable_prefix) and column_name.endswith(variable_suffix):
                    threshold_subset = df[(df['Pwear'] > 0) & (df[column_name].notna())]
                    PWEAR_sum = threshold_subset['Pwear'].sum()

                    if PWEAR_sum / formula >= config.SUM_MIN_HOUR_INCLUSION:
                        X = threshold_subset[['MORNING', 'MIDNIGHT']]
                        Y = threshold_subset[column_name]
                        X = sm.add_constant(X)
                        weights = np.floor(time_resolution * threshold_subset['Pwear'])
                        model = sm.WLS(Y, X, weights=weights)
                        results = model.fit()
                        column_name = f'{column_name.lower()}_IMP'
                        summary_dict[column_name] = results.params['const']

        # Hourly and daily Enmo and Pwear variables
        weighted_hourly_means_IMP = (
            df.assign(weighted_ENMO_IMP=df['ENMO_mean'] * df['Pwear']).groupby('hourofday')
            .apply(lambda x: x['weighted_ENMO_IMP'].sum() / x['Pwear'].sum(), include_groups=False)
        )
        hourly_enmo_IMP_variables = {
            f'enmo_mean_hour{hour}_IMP': weighted_hourly_means_IMP.get(hour, np.nan) for hour in range(1, 25)
        }
        summary_dict.update(hourly_enmo_IMP_variables)

        hourly_pwear_sums = df.groupby('hourofday')['Pwear'].sum()
        hourly_pwear_IMP_variables = {
            f'pwear_hour{hour}_IMP': hourly_pwear_sums.get(hour, np.nan) for hour in range(1, 25)
        }
        summary_dict.update(hourly_pwear_IMP_variables)

        weighted_daily_means_IMP = (
            df.assign(weighted_daily_ENMO_IMP=df['ENMO_mean'] * df['Pwear']).groupby('dayofweek')
            .apply(lambda x: x['weighted_daily_ENMO_IMP'].sum() / x['Pwear'].sum(), include_groups=False)
        )
        daily_enmo_IMP_variables = {
            f'enmo_mean_day{day}_IMP': weighted_daily_means_IMP.get(day, np.nan) for day in range(1, 8)
        }
        summary_dict.update(daily_enmo_IMP_variables)

        daily_pwear_sums = df.groupby('dayofweek')['Pwear'].sum()
        daily_pwear_IMP_variables = {
            f'pwear_day{day}_IMP': daily_pwear_sums.get(day, np.nan) for day in range(1, 8)
        }
        summary_dict.update(daily_pwear_IMP_variables)

        if not any(item.lower() == "hpfvm" for item in config.VARIABLES_TO_DROP):
            # Hourly and daily hpfvm variables
            hourly_hpfvm_means = df.groupby('hourofday')['HPFVM_mean'].mean()
            hourly_hpfvm_IMP_variables = {
                f'hpfvm_mean_hour{hour}_IMP': hourly_hpfvm_means.get(hour, np.nan) for hour in range(1, 25)
            }
            summary_dict.update(hourly_hpfvm_IMP_variables)

            daily_hpfvm_means = df.groupby('dayofweek')['HPFVM_mean'].mean()
            daily_hpfvm_IMP_variables = {
                f'hpfvm_mean_day{day}_IMP': daily_hpfvm_means.get(day, np.nan) for day in range(1, 8)
            }
            summary_dict.update(daily_hpfvm_IMP_variables)

        return summary_dict

# Inputting data into headers dataframe and outputting summary_means dataset
#def output_summary_means(summary_dict, headers_df):
def output_summary_means(summary_dict, headers_df, df, summary_files_path, file_id):    
    if df is not None and not df.empty:
        # Adding the data from the summary dictionary into the empty dataframe (using the headers)
        summary_data = pd.DataFrame([summary_dict], columns=headers_df.columns)

        # Outputting summary dataframe
        os.makedirs(summary_files_path, exist_ok=True)
        file_name = os.path.join(summary_files_path, f"{file_id}_{config.SUM_OVERALL_MEANS}.csv")
        summary_data.to_csv(file_name, index=False)
        return summary_data


# Creating data dictionary for all variables:
#def data_dic(headers_df):
def data_dic(headers_df, summary_files_path):
    variable_label = {
        "id": "Study ID",
        "startdate": "Date of first day of free-living recording",
        "RecordLength": "Number of hours file was recording for",
        "Pwear": "Time integral of wear probability based on ACC",
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

    enmo_variables = [col for col in headers_df.columns if col.startswith("enmo_") and col.endswith("plus")]

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
    }

    variable_label.update(calibration_labels)

    if config.PROCESSING.lower() == 'pampro':
        pampro_labels = {
            "IMP": "IMP = Imputed.",
            "mf_start_error": "File error before calibration (multi file cal) (mg)",
            "mf_end_error": "File error after calibration (multi file cal) (mg)",
            "calibration_type": "Type of calibration used: Single or multi file or Fail",
        }
        variable_label.update(pampro_labels)

    if config.USE_WEAR_LOG.lower() == 'yes':
        wear_log_labels = {
            "start": "Start datetime of the wear log",
            "end": "End datetime of the wear log"
        }
        variable_label.update(wear_log_labels)


    df_labels = pd.DataFrame(list(variable_label.items()), columns=["Variable", "Label"])

    os.makedirs(summary_files_path, exist_ok=True)
    file_name = os.path.join(summary_files_path, "Data_dictionary_summary_means.csv")
    df_labels.to_csv(file_name, index=False)

# Calling the functions
def main():
    # Creating folder paths user for this script
    trimmed_path = create_path(config.INDIVIDUAL_TRIMMED_F)
    summary_files_path = create_path(config.INDIVIDUAL_SUM_F)
    partPro_path = create_path(config.INDIVIDUAL_PARTPRO_F)

    # Creating folder if they don't already exist
    create_folders(trimmed_path)
    create_folders(summary_files_path)

    # Creating filelist to loop through each file individually:
    #file_list = reading_filelist()
    task_id = os.environ.get('SLURM_ARRAY_TASK_ID')
    file_list = reading_filelist(str(int(task_id)-1))
    print(f"Task ID: {task_id}; file list: {file_list}")     

    for file_id in file_list:
        time_resolution, df = reading_part_proc(partPro_path, file_id, date_orig='DATETIME_ORIG')

        # Truncating data (depending on what is specified in config file) and creating dataframe if no valid data:
        df = remove_data(df)
        #row_count, flag_valid_total = creating_dummy(df, file_id, time_resolution)
        row_count, flag_valid_total = creating_dummy(df, file_id, time_resolution,summary_files_path, partPro_path)        
        #df = trimmed_dataset(df, file_id, time_resolution)
        df = trimmed_dataset(df, file_id, time_resolution, trimmed_path)        

        # Creating empty dataframe with headers, to fill in with data later
        #headers_df = creating_headers(file_id)
        headers_df = creating_headers(file_id, summary_files_path)

        # Summarizing data and inputting into dataframe
        formula = 60 / time_resolution   # Formula used when creating data for dataframe
        summary_dict = input_data(df, time_resolution)

        # Defining quad variables
        quad_morning_hours = (df['hourofday'] > 0) & (df['hourofday'] <= 6)
        quad_noon_hours = (df['hourofday'] > 6) & (df['hourofday'] <= 12)
        quad_afternoon_hours = (df['hourofday'] > 12) & (df['hourofday'] <= 18)
        quad_night_hours = (df['hourofday'] > 18) & (df['hourofday'] <= 24)
        quadrants = ['morning', 'noon', 'afternoon', 'night']

        # Summarizing data and inputting into dataframe
        quad_variables = [quad_morning_hours, quad_noon_hours, quad_afternoon_hours, quad_night_hours]
        #summary_dict = input_pwear_segment(df, summary_dict)
        summary_dict = input_pwear_segment(df, summary_dict, formula, quadrants,quad_variables)

        if config.PROCESSING.lower() == 'pampro':
            summary_dict = input_hourly_daily(df, summary_dict)
        #summary_dict = input_output_variables(df, summary_dict, time_resolution)
        summary_dict = input_output_variables(df, summary_dict, time_resolution, formula)

        # Impute hours
        if config.IMPUTE_DATA.lower() == 'yes':
            #summary_dict = impute_data(df, time_resolution)
            summary_dict = impute_data(df, time_resolution, summary_dict, formula, quadrants, quad_variables)    

        # Outputting summary means dataset
        #summary_data = output_summary_means(summary_dict, headers_df)
        summary_data = output_summary_means(summary_dict, headers_df, df, summary_files_path, file_id)
    
    # Outputting data dictionary
    #data_dic(headers_df)
    data_dic(headers_df, summary_files_path)


# Calling the functions
if __name__ == '__main__':
    main()
