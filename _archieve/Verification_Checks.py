############################################################################################################
# Verification of SUMMARY_MEANS and part_processed hourly files
# Author: CAS
# Date: 04/07/2024 (started)
# Version: 1.0 Translated from Stata code
############################################################################################################
# IMPORTING PACKAGES #
import pandas as pd
import config
import os
import xlsxwriter

###########################################################
# SECTION 1: VERIFICATION OF OUTPUT SUMMARY OVERALL MEANS #
###########################################################
# Creating xlsx output sheet:
def create_summary_output_file():
    verif_log_path = os.path.join(config.ROOT_FOLDER, config.ANALYSIS_FOLDER, config.VERIF_LOG_SUMMARY)
    outWorkbook = xlsxwriter.Workbook(verif_log_path)

    return outWorkbook


# --- CHECKING IF OUTPUT SUMMARY OVERALL MEANS EXISTS AND THEN READING IT IN --- #
def summary_df():
    summary_means_file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, f'{config.SUM_OUTPUT_FILE}.csv')
    if os.path.exists(summary_means_file_path):
        summary_df = pd.read_csv(summary_means_file_path)
        summary_file_exists = True

    if not os.path.exists(summary_means_file_path):
        summary_df = None
        summary_file_exists = False

    return summary_df, summary_file_exists

def sum_startdate(outWorkbook, summary_df):

    # Converting startdate to datetime format
    summary_df['startdate'] = pd.to_datetime(summary_df['startdate'])

    # Calculating the summary statistics
    obs = summary_df['startdate'].count()
    mean_date = summary_df['startdate'].mean()
    min_date = summary_df['startdate'].min()
    max_date = summary_df['startdate'].max()

    # Formatting the dates for readability
    mean_date_str = mean_date.strftime('%d%b%Y')
    min_date_str = min_date.strftime('%d%b%Y')
    max_date_str = max_date.strftime('%d%b%Y')

    # Create a DataFrame to store the results
    summary_stats_df = pd.DataFrame({
        'Variable': ['startdate'],
        'Obs': [obs],
        'Mean': [mean_date_str],
        'Min': [min_date_str],
        'Max': [max_date_str]
    })

    # Outputting the summary details of the startdate variable to the verification log
    worksheet = outWorkbook.add_worksheet('Date_Summary')
    header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

    headers_list = list(summary_stats_df.columns)
    for col_num, header in enumerate(headers_list):
        worksheet.write(3, col_num, header, header_format)

    for row_num, row_data in enumerate(summary_stats_df.values):
        for col_num, cell_data in enumerate(row_data):
            worksheet.write(row_num + 4, col_num, cell_data)

    # Writing messages to verification log
    bold_format = outWorkbook.add_format({'bold': True})
    worksheet.write(0, 0, "Summarising start date:", bold_format)
    worksheet.write(1, 0, "Check that the minimum and maximum start date falls within the expected testing dates.")

# --- SUMMARISING STARTDATE TO CHECK THEY FALL INSIDE THE EXPECTED TESTING DATES --- #
def check_calibration(outWorkbook, summary_df):
    # Generate cal_flag variable to tag those with calibration issues
    summary_df['cal_flag'] = 0
    summary_df.loc[(summary_df['file_end_error'] > 10), 'cal_flag'] = 1

    # Summarising cal_flag and listing files with calibration end errors over 10 in the verification log
    cal_flag_max = summary_df['cal_flag'].max()
    if cal_flag_max > 0:
        worksheet = outWorkbook.add_worksheet('Calibration_Check')
        header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

        # Specifying the headers the will be printed in the verification log
        headers = ['id', 'file_start_error', 'file_end_error']
        for col_num, header in enumerate(headers):
            worksheet.write(3, col_num, header, header_format)

        # Filter rows with calibration error above 10
        filtered_df = summary_df[summary_df['cal_flag'] == 1]
        for row_num, row_data in enumerate(filtered_df[['id', 'file_start_error', 'file_end_error']].values):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num + 4, col_num, cell_data)

        # Writing messages to verification log
        red_format = outWorkbook.add_format({'bold': True, 'font_color': 'red'})
        worksheet.write(0, 0, "Some files have not calibrated - check file end errors.", red_format)
        worksheet.write(1, 0, "Uncalibrated data will be set to missing during post-processing.", red_format)

    # If no calibration error print message to verification log:
    else:
        worksheet = outWorkbook.add_worksheet('Calibration_Check')
        header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

        green_format = outWorkbook.add_format({'bold': True, 'font_color': 'green'})
        worksheet.write(0, 0, "All files have calibrated.", green_format)


# --- CHECKING FOR CALIBRATION ISSUES --- #
# --- GENERATING INCLUDE CRITERIA --- ~
def include_criteria(outWorkbook, summary_df):

    # Generating the include criteria
    summary_df['include'] = 0
    summary_df.loc[
        (summary_df['Pwear'] > config.VER_PWEAR) &
        (summary_df['Pwear'].notnull()) &
        (summary_df['Pwear_morning'] >= config.VER_PWEAR_MORN) &
        (summary_df['Pwear_noon'] >= config.VER_PWEAR_QUAD) &
        (summary_df['Pwear_afternoon'] >= config.VER_PWEAR_QUAD) &
        (summary_df['Pwear_night'] >= config.VER_PWEAR_QUAD), 'include'] = 1

    # Summarising the include variable
    include_freq = summary_df['include'].value_counts()
    include_percent = summary_df['include'].value_counts(normalize=True) * 100
    include_cum_percent = include_percent.cumsum()

    # Creating dataframe with the summary details of the include variable
    results_df = pd.DataFrame({
        'include': include_freq.index,
        'frequency': include_freq.values,
        'percent': include_percent.values,
        'cumulative percent': include_cum_percent.values
    })

    total_frequency = results_df['frequency'].sum()
    total_percent = results_df['percent'].sum()

    total_row_df = pd.DataFrame({
        'include': 'Totalt',
        'frequency': [total_frequency],
        'percent': [total_percent],
        'cumulative percent': ['']
    })

    results_df = pd.concat([results_df, total_row_df], ignore_index=True)

    # Outputting the summary details of the include variable to the verification log
    header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

    worksheet = outWorkbook.add_worksheet('Include_Criteria')

    # Specifying the headers the will be printed in the verification log
    headers = list(results_df.columns)
    for col_num, header in enumerate(headers):
        worksheet.write(3, col_num, header, header_format)

    for row_num, row_data in enumerate(results_df.values):
        for col_num, cell_data in enumerate(row_data):
            worksheet.write(row_num + 4, col_num, cell_data)


    # Writing messages to verification log
    bold_format = outWorkbook.add_format({'bold': True})
    worksheet.write(0, 0, "Summarising include variable:", bold_format)
    worksheet.write(1, 0, "Include = 0 (include criteria are met), Include = 1 (include criteria are not met).")

    return summary_df

# --- CHECKING FOR DUPLICATES IN DATA --- #
def check_duplicates(summary_df):
    # Tagging duplicates
    summary_df['dup_device_date'] = summary_df.duplicated(subset=['device', 'generic_first_timestamp', 'generic_last_timestamp'], keep=False).astype(int)
    dup_max = summary_df['dup_device_date'].max()


    if dup_max > 0:
        worksheet = outWorkbook.add_worksheet('Duplicates_Check')
        header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

        # Specifying the headers the will be printed in the verification log
        headers = ['id', 'device', 'generic_first_timestamp', 'generic_last_timestamp']
        for col_num, header in enumerate(headers):
            worksheet.write(3, col_num, header, header_format)

        # Filter rows that are duplicated
        filtered_df = summary_df[summary_df['dup_device_date'] == 1]
        for row_num, row_data in enumerate(filtered_df[['id', 'device', 'generic_first_timestamp', 'generic_last_timestamp']].values):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num + 4, col_num, cell_data)

        # Writing messages to verification log
        red_format = outWorkbook.add_format({'bold': True, 'font_color': 'red'})
        worksheet.write(0, 0, "There are duplicates in this summary dataset", red_format)
        worksheet.write(1, 0, "Add the duplicate file to the Housekeeping file to remove data from final dataset.", red_format)

    else:
        worksheet = outWorkbook.add_worksheet('Duplicates_Check')

        # Writing messages to verification log
        green_format = outWorkbook.add_format({'bold': True, 'font_color': 'green'})
        worksheet.write(0, 0, "There are no duplicates in this summary dataset", green_format)


# --- SUMMARISING EMMO_MEAN --- #
def sum_enmo_mean(summary_df):

    # Summarising ENMO_mean
    enmo_mean_min = summary_df['enmo_mean'].min()

    if enmo_mean_min < 0:
        worksheet = outWorkbook.add_worksheet('ENMO_Mean')
        header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

        # Specifying the headers that will be printed in the verification log
        headers = ['id', 'enmo_mean', 'Pwear', 'RecordLength']
        for col_num, header in enumerate(headers):
            worksheet.write(2, col_num, header, header_format)

        # Filter rows where enmo_mean < 0 and include == 1:
        filtered_df = summary_df[(summary_df['enmo_mean'] < 0) & (summary_df['include'] == 1)]
        for row_num, row_data in enumerate(
                filtered_df[['id', 'enmo_mean', 'Pwear', 'RecordLength']].values):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num + 4, col_num, cell_data)

        # Writing messages to verification log
        red_format = outWorkbook.add_format({'bold': True, 'font_color': 'red'})
        worksheet.write(0, 0, "There are negative values of ENMO_mean in this summary dataset.", red_format)

    else:
        worksheet = outWorkbook.add_worksheet('ENMO_Mean')

        # Writing messages to verification log
        green_format = outWorkbook.add_format({'bold': True, 'font_color': 'green'})
        worksheet.write(0, 0, "There are no negative values of ENMO_mean in this summary dataset", green_format)


# --- LOOKING AT OUTLIERS IN DATA --- #
def outliers(summary_df):
    if config.REMOVE_THRESHOLDS == 'No':
        worksheet = outWorkbook.add_worksheet('Outliers')
        header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

        # Specifying the headers that will be printed in the verification log
        headers = ['id', 'enmo_mean', 'enmo_0plus']
        for col_num, header in enumerate(headers):
            worksheet.write(3, col_num, header, header_format)

        # Filter rows where enmo_mean != -1 and not missing
        filtered_df = summary_df[(summary_df['enmo_mean'] != -1) & (~summary_df['enmo_mean'].isna())]
        filtered_df = filtered_df.sort_values(by='enmo_mean')
        for row_num, row_data in enumerate(
                filtered_df[['id', 'enmo_mean', 'enmo_0plus']].values):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num + 4, col_num, cell_data)

        # Writing messages to verification log
        bold_format = outWorkbook.add_format({'bold': True})
        worksheet.write(0, 0, "When threshold is not set to be removed", bold_format)
        worksheet.write(1, 0, "Look through the data for potential outliers (both smallest and largest)", bold_format)

    if config.REMOVE_THRESHOLDS == 'Yes':
        worksheet = outWorkbook.add_worksheet('Outliers')
        header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

        # Specifying the headers that will be printed in the verification log
        headers = ['id', 'enmo_mean']
        for col_num, header in enumerate(headers):
            worksheet.write(3, col_num, header, header_format)

        # Filter rows where enmo_mean != -1 and not missing
        filtered_df = summary_df[(summary_df['enmo_mean'] != -1) & (~summary_df['enmo_mean'].isna())]
        filtered_df = filtered_df.sort_values(by='enmo_mean')
        for row_num, row_data in enumerate(
                filtered_df[['id', 'enmo_mean']].values):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num + 4, col_num, cell_data)

        # Writing messages to verification log
        bold_format = outWorkbook.add_format({'bold': True})
        worksheet.write(0, 0, "When threshold is set to be removed", bold_format)
        worksheet.write(1, 0, "Look through the data for potential outliers (both smallest and largest)", bold_format)


# --- VERIFICATION OF PWEAR --- #

# Checking that PWear is equal to the sum of Pwear of the quad times
def verif_pwear_quad_times(summary_df):

    # Creating pwear - pwear_quad_times variable:
    summary_df['Pwear_quad_diff'] = summary_df['Pwear'] - (summary_df['Pwear_morning'] + summary_df['Pwear_noon'] + summary_df['Pwear_afternoon'] + summary_df['Pwear_night'])
    max_Pwear_quad_diff = summary_df['Pwear_quad_diff'].max()

    if max_Pwear_quad_diff >= 0.0001 and summary_df['Pwear'].isna().any():

        worksheet = outWorkbook.add_worksheet('Pwear')
        header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

        # Specifying the headers that will be printed in the verification log
        headers = ['id', 'Pwear', 'Pwear_quad_diff']
        for col_num, header in enumerate(headers):
            worksheet.write(3, col_num, header, header_format)

        # Filtering rows
        filtered_df = summary_df[(summary_df['Pwear_quad_diff'] >= 0.0001) & (summary_df['Pwear'].isna())]
        for row_num, row_data in enumerate(filtered_df[['id', 'Pwear', 'Pwear_quad_diff']].values):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num + 4, col_num, cell_data)

        # Writing messages to verification log
        red_format = outWorkbook.add_format({'bold': True, 'font_color': 'red'})
        worksheet.write(0, 0, "Checking Pwear = sum of Pwear quad times:", red_format)


    else:
        worksheet = outWorkbook.add_worksheet('Pwear')

        # Writing messages to verification log
        green_format = outWorkbook.add_format({'bold': True, 'font_color': 'green'})
        worksheet.write(0, 0, "Pwear = sum of Pwear quad times for all IDs", green_format)


# Checking that PWear is equal to the sum of Pwear of weekdays and weekends
def verif_pwear_wkend_wkday(summary_df):

    # Creating pwear - pwear_wkday_wkend variable:
    summary_df['Pwear_wk_wkend_diff'] = summary_df['Pwear'] - (summary_df['Pwear_wkend'] + summary_df['Pwear_wkday'])
    max_Pwear_wk_wkend_diff = summary_df['Pwear_wk_wkend_diff'].max()


    if max_Pwear_wk_wkend_diff >= 0.0001 and summary_df['Pwear'].isna().any():

        # Creating Pwear worksheet if not already there, if already there continue writing in this
        if 'Pwear' in outWorkbook.sheetnames:
            worksheet = outWorkbook.get_worksheet_by_name('Pwear')
        else:
            worksheet = outWorkbook.add_worksheet('Pwear')

        header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

        # Specifying the headers that will be printed in the verification log
        headers = ['id', 'Pwear', 'Pwear_wk_wkend_diff']
        for col_num, header in enumerate(headers):
            worksheet.write(3, col_num + 4, header, header_format)

        # Filtering rows
        filtered_df = summary_df[(summary_df['Pwear_wk_wkend_diff'] >= 0.0001) & (summary_df['Pwear'].isna())]
        for row_num, row_data in enumerate(filtered_df[['id', 'Pwear', 'Pwear_wk_wkend_diff']].values):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num + 4, col_num + 4, cell_data)

        # Writing messages to verification log
        red_format = outWorkbook.add_format({'bold': True, 'font_color': 'red'})
        worksheet.write(0, 4, "Checking Pwear = sum of Pwear weekday + weekend day:", red_format)

    else:
        if 'Pwear' in outWorkbook.sheetnames:
            worksheet = outWorkbook.get_worksheet_by_name('Pwear')
        else:
            worksheet = outWorkbook.add_worksheet('Pwear')

        # Writing messages to verification log
        green_format = outWorkbook.add_format({'bold': True, 'font_color': 'green'})
        worksheet.write(0, 4, "Pwear = sum of Pwear weekday + weekend day for all IDs", green_format)


# Checking that PWear weekend and weekday is equal to the sum of Pwear quads on weekdays and weekends
def verif_pwear_wkend_wkday_quad(summary_df):

    variables = ['wkend', 'wkday']

    for index, variable in enumerate(variables):
        # Creating pwear weekend/weekday - pwear weekend/weekday quad variable:
        summary_df[f'Pwear_{variable}_quads_diff'] = summary_df[f'Pwear_{variable}'] - (summary_df[f'Pwear_morning_{variable}'] + summary_df[f'Pwear_noon_{variable}'] + summary_df[f'Pwear_afternoon_{variable}'] + summary_df[f'Pwear_night_{variable}'])
        max_Pwear_diff = summary_df[f'Pwear_{variable}_quads_diff'].max()

        # defining start column to print out the message to verification log
        start_column = {}
        if variable == 'wkend':
            start_column = 8
        if variable == 'wkday':
            start_column = 12

        if max_Pwear_diff >= 0.0001 and summary_df['Pwear'].isna().any():

            # Creating Pwear worksheet if not already there, if already there continue writing in this
            if 'Pwear' in outWorkbook.sheetnames:
                worksheet = outWorkbook.get_worksheet_by_name('Pwear')
            else:
                worksheet = outWorkbook.add_worksheet('Pwear')

            header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

            # Specifying the headers that will be printed in the verification log
            headers = ['id', 'Pwear', f'Pwear_{variable}_quads_diff']
            for col_num, header in enumerate(headers):
                worksheet.write(3, start_column, header, header_format)

            # Filtering rows
            filtered_df = summary_df[(summary_df[f'Pwear_{variable}_quads_diff'] >= 0.0001) & (summary_df['Pwear'].isna())]
            for row_num, row_data in enumerate(filtered_df[['id', 'Pwear', f'Pwear_{variable}_quads_diff']].values):
                for col_num, cell_data in enumerate(row_data):
                    worksheet.write(row_num + 4, start_column, cell_data)

            # Writing messages to verification log
            red_format = outWorkbook.add_format({'bold': True, 'font_color': 'red'})
            worksheet.write(0, start_column, f"Checking Pwear_{variable} = sum of Pwear_{variable} for each quad:", red_format)

        else:
            if 'Pwear' in outWorkbook.sheetnames:
                worksheet = outWorkbook.get_worksheet_by_name('Pwear')
            else:
                worksheet = outWorkbook.add_worksheet('Pwear')

            # Writing messages to verification log
            green_format = outWorkbook.add_format({'bold': True, 'font_color': 'green'})
            worksheet.write(0, start_column, f"Pwear_{variable} = sum of Pwear_{variable} for each quad for all IDs", green_format)

# --- VERIFICATION THAT THE PROPORTION OF TIME SPENT IN CATEGORIES IS EQUAL TO THE TOTAL PROPORTION --- #
def proportion_categories(summary_df):

    if config.REMOVE_THRESHOLDS == 'No':

        # Finding the differences in all variable different thresholds (so the difference between e.g., enmo_1plus and enmo_2plus and so on)
        for variable in config.VERIFY_VARS:
            for i in range(0, 5):
                l = i + 1
                summary_df[f'{variable}_prop_cat_{i}_{l}'] = summary_df[f'{variable}_{i}plus'] - summary_df[f'{variable}_{l}plus']

            for i in range(5, 150, 5):
                l = i + 5
                summary_df[f'{variable}_prop_cat_{i}_{l}'] = summary_df[f'{variable}_{i}plus'] - summary_df[f'{variable}_{l}plus']

            for i in range(150, 300, 10):
                l = i + 10
                summary_df[f'{variable}_prop_cat_{i}_{l}'] = summary_df[f'{variable}_{i}plus'] - summary_df[f'{variable}_{l}plus']

            for i in range(300, 1000, 100):
                l = i + 100
                summary_df[f'{variable}_prop_cat_{i}_{l}'] = summary_df[f'{variable}_{i}plus'] - summary_df[f'{variable}_{l}plus']

            for i in range(1000, 4000, 1000):
                l = i + 1000
                summary_df[f'{variable}_prop_cat_{i}_{l}'] = summary_df[f'{variable}_{i}plus'] - summary_df[f'{variable}_{l}plus']

            summary_df[f'{variable}_prop_cat_4000plus'] = summary_df[f'{variable}_4000plus']

            # Checking the total proportions of all categories equals the proportion of time spent above 0mg
            prop_cat_columns = [col for col in summary_df.columns if col.startswith(f'{variable}_prop_cat_')]
            summary_df[f'{variable}_total_prop'] = summary_df[prop_cat_columns].sum(axis=1)
            summary_df[f'{variable}_total_diff'] = (summary_df[f'{variable}_total_prop'] - summary_df[f'{variable}_0plus']).abs()

            max_total_difference = summary_df[f'{variable}_total_diff'].max()

            # If the difference between the sum of proportions and e.g., enmo_0plus is too big it will print it to the verification log
            if max_total_difference >= 0.0001 and summary_df[f'{variable}_0plus'].isna().any():

                worksheet = outWorkbook.add_worksheet('Sum_Proportions')
                header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

                # Specifying the headers that will be printed in the verification log
                headers = ['id', f'{variable}_0plus', f'{variable}_total_prop']
                for col_num, header in enumerate(headers):
                    worksheet.write(3, col_num, header, header_format)

                # Filtering rows
                filtered_df = summary_df[(summary_df[f'{variable}_total_prop'] >= 0.0001) & (summary_df[f'{variable}_0plus'].isna())]
                for row_num, row_data in enumerate(filtered_df[['id', f'{variable}_0plus', f'{variable}_total_prop']].values):
                    for col_num, cell_data in enumerate(row_data):
                        worksheet.write(row_num + 4, col_num, cell_data)

                # Writing messages to verification log
                red_format = outWorkbook.add_format({'bold': True, 'font_color': 'red'})
                worksheet.write(0, 0, f"List of sum of {variable} proportions does not equal total proportion:", red_format)

            else:
                # Writing message to verification log if everything is good (no big difference between sum of proportion and e.g., enmo_0plus)
                worksheet = outWorkbook.add_worksheet('Sum_Proportions')
                green_format = outWorkbook.add_format({'bold': True, 'font_color': 'green'})
                worksheet.write(0, 0, f"List of sum of {variable} proportions is equal to the total proportion:", green_format)

            columns_to_drop = [col for col in summary_df.columns if col.startswith(f'{variable}_prop_cat') or col.endswith('_diff')]
            summary_df.drop(columns=columns_to_drop, inplace=True)


# --- Checking the total proportion in ENMO_0PLUS --- #
# Summarising enmo_0 plus (should be ~1).
def check_total_proportion(summary_df):
    if config.REMOVE_THRESHOLDS == 'No':
        su_enmo_0plus = summary_df['enmo_0plus'].describe()
        su_include_enmo_0plus = summary_df[summary_df['include'] == 1]['enmo_0plus'].describe()

        worksheet = outWorkbook.add_worksheet('Proportion_Enmo_0plus')
        header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

        # Adding summary statistics to verification log (if any observations)
        worksheet.write(0, 0, "Overall summary statistics for enmo_0plus", header_format)
        if su_enmo_0plus['count'] > 0:
            for i, (stat_name, value) in enumerate(su_enmo_0plus.items(), start=1):
                worksheet.write(i, 0, stat_name)
                worksheet.write(i, 1, value)


        # Adding summary statistics when include == 1 to  verification log (if any observations)
        worksheet.write(0, 3, "Summary statistics for enmo_0plus where include==1", header_format)
        if su_include_enmo_0plus['count'] > 0:
            for i, (stat_name, value) in enumerate(su_include_enmo_0plus.items(), start=1):
                worksheet.write(i, 3, stat_name)
                worksheet.write(i, 4, value)
        else:
            red_format = outWorkbook.add_format({'font_color': 'red'})
            worksheet.write(2, 3, "No observations (include == 1) to summarize", red_format)

# Summarising all enmo_*plus variables to check for any negative values
def checking_enmo_negative_values(summary_df):
    if config.REMOVE_THRESHOLDS == 'No':

        enmo_columns = [col for col in summary_df.columns if col.startswith('enmo_') and col.endswith('plus')]
        su_enmo_stats = summary_df[enmo_columns].describe()
        su_include_enmo_stats = summary_df[summary_df['include'] == 1][enmo_columns].describe()

        worksheet = outWorkbook.add_worksheet('Su_Enmo_variables')
        header_format = outWorkbook.add_format({'bold': True, 'bottom': 2})

        # Adding summary statistics to verification log (if any observations)
        worksheet.write(0, 0, "Summary statistics for enmo_*plus variables to check for any negative values", header_format)

        # Writing headers
        for col_num, stat_name in enumerate(su_enmo_stats.index, start=1):
            worksheet.write(1, col_num, stat_name, header_format)

        # Transposing the data to be able to write it to verification log
        for row_num, (variable, stats) in enumerate(su_enmo_stats.transpose().iterrows(), start=2):
            worksheet.write(row_num, 0, variable)
            for col_num, value in enumerate(stats, start=1):
                worksheet.write(row_num, col_num, value)

        # Adding summary statistics when include == 1 to  verification log (if any observations)
        worksheet.write(0, 11, "Summary statistics for enmo_*plus variables where include==1, to check for any negative values ", header_format)
        if 'count' in su_include_enmo_stats.index and su_include_enmo_stats.loc['count'].sum() > 0:

            # Writing headers
            for col_num, stat_name in enumerate(su_include_enmo_stats.index, start=11):
                worksheet.write(1, col_num, stat_name, header_format)

            # Transposing the data to be able to write it to verification log
            for row_num, (variable, stats) in enumerate(su_include_enmo_stats.transpose().iterrows(), start=2):
                worksheet.write(row_num, 11, variable)
                for col_num, value in enumerate(stats, start=10):
                    worksheet.write(row_num, col_num, value)

        else:
            red_format = outWorkbook.add_format({'font_color': 'red'})
            worksheet.write(2, 11, "No observations (include == 1) to summarize", red_format)

    outWorkbook.close()



#############################################
# SECTION 2: VERIFICATION OF HOURLY FILE(S) #
#############################################
# --- Creating xlsx output sheet --- #
def create_hourly_output_file():
    verif_log_path = os.path.join(config.ROOT_FOLDER, config.ANALYSIS_FOLDER, config.VERIF_LOG_HOURLY)
    outWorkbook2 = xlsxwriter.Workbook(verif_log_path)

    return outWorkbook2

# --- CHECKING IF HOURLY OUTPUT FILE EXISTS AND THEN READING IT IN --- #
def hourly_df():
    hourly_file_path = os.path.join(config.ROOT_FOLDER, config.RESULTS_FOLDER, config.SUMMARY_FOLDER, f'{config.HOUR_OUTPUT_FILE}.csv')
    if os.path.exists(hourly_file_path):
        hourly_df = pd.read_csv(hourly_file_path)
        hourly_file_exists = True

    if not os.path.exists(hourly_file_path):
        hourly_df = None
        hourly_file_exists = False

    return hourly_df, hourly_file_exists


# --- INVESTIGATING DUPLICATES --- #
def hourly_duplicates(hourly_df, outWorkbook2):

    # Filtering dataframe based on conditions
    condition = (hourly_df['ENMO_mean'] != 1) & (hourly_df['ENMO_mean'] != 0) & (~hourly_df['ENMO_mean'].isnull())
    filtered_df = hourly_df[condition].copy()

    # Tagging duplicates
    filtered_df['dup_enmo_date'] = hourly_df.duplicated(subset=['timestamp', 'ENMO_mean', 'ENMO_sum', 'Battery_mean'], keep=False).astype(int)
    dup_max = filtered_df['dup_enmo_date'].max()

    if dup_max > 0:
        worksheet = outWorkbook2.add_worksheet('Duplicates_Check')
        header_format = outWorkbook2.add_format({'bold': True, 'bottom': 2})

        # Specifying the headers the will be printed in the verification log
        headers = ['file_id', 'timestamp', 'ENMO_mean', 'ENMO_sum', 'Battery_mean']
        for col_num, header in enumerate(headers):
            worksheet.write(3, col_num, header, header_format)

        # Filter rows that are duplicated
        duplicates_df = filtered_df[filtered_df['dup_enmo_date'] == 1]
        filter = (duplicates_df['ENMO_mean'] != -1)
        duplicates_df = duplicates_df[filter]

        for row_num, row_data in enumerate(filtered_df[['file_id', 'timestamp', 'ENMO_mean', 'ENMO_sum', 'Battery_mean']].values):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num + 4, col_num, cell_data)

        # Writing messages to verification log
        red_format = outWorkbook2.add_format({'bold': True, 'font_color': 'red'})
        worksheet.write(0, 0, "There are duplicates in this hourly dataset", red_format)
        worksheet.write(1, 0, "Add the duplicate file to the Housekeeping file to remove data from final dataset.", red_format)

    else:
        worksheet = outWorkbook2.add_worksheet('Duplicates_Check')

        # Writing messages to verification log
        green_format = outWorkbook2.add_format({'bold': True, 'font_color': 'green'})
        worksheet.write(0, 0, "There are no duplicates in this hourly dataset", green_format)


# --- COMPARING ENMO_N AND ENMO_0_99999 --- #
def compare_enmo(hourly_df, outWorkbook2):
    if config.REMOVE_THRESHOLDS == 'No':
        hourly_df['ENMO_0plus_check'] = hourly_df['ENMO_0plus'] * 720

        # Generating difference between ENMO_n and ENMO_0plus_check
        hourly_df['ENMO_n_0plus_diff'] = hourly_df.apply(lambda x: abs(x['ENMO_n'] - x['ENMO_0plus_check']) if x['ENMO_n'] != x['ENMO_0plus_check'] else 0, axis=1)

        # Summarising the difference
        su_enmo_n_0plus_diff = hourly_df[hourly_df['ENMO_n_0plus_diff'] > 1]['ENMO_n_0plus_diff'].describe()

        # Outputting to verification log
        worksheet = outWorkbook2.add_worksheet('Comparing_Enmo')
        header_format = outWorkbook2.add_format({'bold': True, 'bottom': 2})

        # Adding summary statistics to verification log (if any observations)
        worksheet.write(0, 0, "Summarising the difference between ENMO_n and ENMO_0plus * 720, if these are not equal to each other", header_format)
        if su_enmo_n_0plus_diff['count'] > 0:
            for i, (stat_name, value) in enumerate(su_enmo_n_0plus_diff.items(), start=1):
                worksheet.write(i, 0, stat_name)
                worksheet.write(i, 1, value)

        else:
            red_format = outWorkbook.add_format({'bold': True, 'font_color': 'red'})
            worksheet.write(2, 0, "No observations to summarise: ENMO_n and ENMO_0plus * 720 are equal to each other for all observations ", red_format)


# --- COUNTING DIFFERENCES IN ENMO_N AND ENMO_OPLUS NOT DUE TO FIRST OR LAST TIMEPOINT IN THE FILE --- #
def differences_enmo_enmo0plus(hourly_df, outWorkbook2):

    # Converting timestamps to datetime format
    hourly_df['first_file_timepoint'] = pd.to_datetime(hourly_df['first_file_timepoint'])
    hourly_df['last_file_timepoint'] = pd.to_datetime(hourly_df['last_file_timepoint'])
    hourly_df['DATETIME_ORIG'] = pd.to_datetime(hourly_df['DATETIME_ORIG'])

    # Generating difference between the first file timepoint and the DATETIME_ORIG
    hourly_df['diff_first_file_timepoint'] = abs(hourly_df['first_file_timepoint'] - hourly_df['DATETIME_ORIG']) / pd.Timedelta(hours=1)

    # Generating difference between the last file timepoint and the DATETIME_ORIG
    hourly_df['diff_last_file_timepoint'] = abs(hourly_df['last_file_timepoint'] - hourly_df['DATETIME_ORIG']) / pd.Timedelta(hours=1)

    if config.REMOVE_THRESHOLDS == 'No':
        # If count is 0, differences are accounted for by the datapoint being next to the first or last in the file
        count = hourly_df[(hourly_df['ENMO_n_0plus_diff'] > 0.01) & (hourly_df['diff_first_file_timepoint'] > 1) & (hourly_df['diff_last_file_timepoint'] > 1)].shape[0]

        if count > 0:
            # Outputting to verification log
            worksheet = outWorkbook2.add_worksheet('Differences_Enmo')
            red_format = outWorkbook2.add_format({'bold': True, 'font_color': 'red'})

            # Adding count to verification log (if count > 0)
            worksheet.write(0, 0, "Count if diff in enmo_n & enmo_0plus NOT due to first or last timepoint in the file:", red_format)
            worksheet.write(1, 0, "Count")
            worksheet.write(1, 1, count)

        else:
            worksheet = outWorkbook2.add_worksheet('Differences_Enmo')
            green_format = outWorkbook2.add_format({'font_color': 'green'})

            worksheet.write(0, 0, "There are no observations with differences between ENMO_n and ENMO_0plus * 720", green_format)


# --- SUMMARISE VARIABLES - OUTLIERS --- #
# Summarising enmo_0 plus (should be ~1).
def check_enmo_0plus(hourly_df):
    if config.REMOVE_THRESHOLDS == 'No':
        su_enmo_0plus = hourly_df['ENMO_0plus'].describe()

        worksheet = outWorkbook2.add_worksheet('Summary_Enmo_0plus')
        header_format = outWorkbook2.add_format({'bold': True, 'bottom': 2})

        if su_enmo_0plus['count'] > 0:

            # Adding summary statistics to verification log (if any observations)
            worksheet.write(0, 0, "Overall summary statistics for enmo_0plus.", header_format)
            worksheet.write(1, 0, "ENMO_0plus should be ~1")
            for i, (stat_name, value) in enumerate(su_enmo_0plus.items(), start=2):
                worksheet.write(i, 0, stat_name)
                worksheet.write(i, 1, value)

        else:
            red_format = outWorkbook2.add_format({'font_color': 'red'})
            worksheet.write(0, 0, "No observations to summarize", red_format)


# Summarising all enmo_* variables to check for any negative values
def summarise_all_enmo(hourly_df):
    if config.REMOVE_THRESHOLDS == 'No':

        # Filtering data
        enmo_columns = [col for col in hourly_df.columns if col.startswith('ENMO_')]
        filtered_df = hourly_df[(hourly_df['ENMO_mean'] != -1) & (~hourly_df['ENMO_mean'].isna())]

        su_enmo_stats = filtered_df[enmo_columns].describe()

        worksheet = outWorkbook2.add_worksheet('Su_Enmo_variables')
        header_format = outWorkbook2.add_format({'bold': True, 'bottom': 2})

        # Adding summary statistics to verification log (if any observations)
        worksheet.write(0, 0, "Summary statistics for all enmo_* variables to check for any negative values", header_format)

        # Writing headers
        for col_num, stat_name in enumerate(su_enmo_stats.index, start=1):
            worksheet.write(1, col_num, stat_name, header_format)

        # Transposing the data to be able to write it to verification log
        for row_num, (variable, stats) in enumerate(su_enmo_stats.transpose().iterrows(), start=2):
            worksheet.write(row_num, 0, variable)
            for col_num, value in enumerate(stats, start=1):
                worksheet.write(row_num, col_num, value)


# Summarising enmo_mean if REMOVE_THRESHOLD == YES).
def hourly_sum_enmo_mean(hourly_df):
    if config.REMOVE_THRESHOLDS == 'Yes':

        # Filtering data
        filtered_df = hourly_df[(hourly_df['ENMO_mean'] != -1) & (~hourly_df['ENMO_mean'].isna())]

        su_enmo_mean = filtered_df['ENMO_mean'].describe()

        worksheet = outWorkbook2.add_worksheet('Summary_Enmo_mean')
        header_format = outWorkbook2.add_format({'bold': True, 'bottom': 2})

        if su_enmo_mean['count'] > 0:

            # Adding summary statistics to verification log (if any observations)
            worksheet.write(0, 0, "Overall summary statistics for enmo_mean if thresholds removed.", header_format)
            worksheet.write(1, 0, "Check for any negative values")
            for i, (stat_name, value) in enumerate(su_enmo_mean.items(), start=2):
                worksheet.write(i, 0, stat_name)
                worksheet.write(i, 1, value)

        else:
            red_format = outWorkbook2.add_format({'font_color': 'red'})
            worksheet.write(0, 0, "No observations to summarize", red_format)


# Summarise ENMO_mean to check for any negative values
def hourly_enmo_negative_values(hourly_df):
    # Finding the minimum ENMO_mean in dataframe
    enmo_mean_min = hourly_df['ENMO_mean'].min()

    # Creating sheet in verification log
    worksheet = outWorkbook2.add_worksheet('Summary_Negative_Enmo_mean')

    if enmo_mean_min < 0:
        filtered_df = hourly_df[(hourly_df['ENMO_mean'] < 0)]


        header_format = outWorkbook2.add_format({'bold': True})

        # Specifying the headers that will be printed in the verification log
        headers = ['file_id', 'ENMO_mean', 'Pwear']
        for col_num, header in enumerate(headers):
            worksheet.write(3, col_num, header, header_format)

        # Printing data to verification log
        for row_num, row_data in enumerate(filtered_df[['file_id', 'ENMO_mean', 'Pwear']].values):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num + 4, col_num, cell_data)

        # Writing messages to verification log
        red_format = outWorkbook2.add_format({'bold': True, 'font_color': 'red'})
        worksheet.write(0, 0, "There are negative values of ENMO_mean", red_format)

    else:
        # Writing messages to verification log
        green_format = outWorkbook2.add_format({'bold': True, 'font_color': 'green'})
        worksheet.write(0, 0, "There are no negative values of ENMO_mean", green_format)

# --- LOOKING AT OUTLIERS IN DATA --- #
def hourly_outliers(hourly_df):
    worksheet = outWorkbook2.add_worksheet('Outliers')
    header_format = outWorkbook2.add_format({'bold': True, 'bottom': 2})

    # Specifying the headers that will be printed in the verification log
    headers = ['file_id', 'DATETIME_ORIG', 'ENMO_mean', 'ENMO_n', 'ENMO_missing', 'ENMO_sum', 'QC_anomalies_total']
    for col_num, header in enumerate(headers):
        worksheet.write(3, col_num, header, header_format)

    # Filter rows where enmo_mean != -1 and not missing
    filtered_df = hourly_df[(hourly_df['ENMO_mean'] != -1) & (~hourly_df['ENMO_mean'].isna())]
    filtered_df = filtered_df.sort_values(by='ENMO_mean')
    for row_num, row_data in enumerate(filtered_df[['file_id', 'DATETIME_ORIG', 'ENMO_mean', 'ENMO_n', 'ENMO_missing', 'ENMO_sum', 'QC_anomalies_total']].values):
        for col_num, cell_data in enumerate(row_data):
            worksheet.write(row_num + 4, col_num, cell_data)

    # Writing messages to verification log
    bold_format = outWorkbook2.add_format({'bold': True})
    worksheet.write(0, 0, "Look through the data for potential outliers (both smallest and largest)", bold_format)


# Creating ENMO_mean flag to pick out files for checking
def hourly_enmo_flag(hourly_df):

    # Creating enmo_mean_flag. 600 is chosen after looking at other study data - to pick out files for checking.
    enmo_mean_flag = 600

    # Counting number of files with ENMO_mean > enmo_mean_flag
    count = hourly_df[(hourly_df['ENMO_mean'] > enmo_mean_flag) & (~hourly_df['ENMO_mean'].isna()) & (hourly_df['QC_anomalies_total'] == 0)].shape[0]

    worksheet = outWorkbook2.add_worksheet('Enmo_flag')
    header_format = outWorkbook2.add_format({'bold': True, 'bottom': 2})

    # Adding count to verification log
    worksheet.write(0, 0, "Number of files with ENMO_mean > enmo_mean_flag (600):", header_format)
    worksheet.write(1, 0, "Count")
    worksheet.write(1, 1, count)

    outWorkbook2.close()

if __name__ == '__main__':
    # VERIFICATION SUMMARY OVERALL MEANS FILE
    outWorkbook = create_summary_output_file()
    summary_df, summary_file_exists = summary_df()
    # Only running the functions if the summary overall means file exists
    if summary_file_exists:
        summary_df = include_criteria(outWorkbook, summary_df)
        sum_startdate(outWorkbook, summary_df)
        check_calibration(outWorkbook, summary_df)
        check_duplicates(summary_df)
        sum_enmo_mean(summary_df)
        outliers(summary_df)
        verif_pwear_quad_times(summary_df)
        verif_pwear_wkend_wkday(summary_df)
        verif_pwear_wkend_wkday_quad(summary_df)
        proportion_categories(summary_df)
        check_total_proportion(summary_df)
        checking_enmo_negative_values(summary_df)

    # VERIFICATION HOURLY FILE(S)
    outWorkbook2 = create_hourly_output_file()
    hourly_df, hourly_file_exists = hourly_df()
    # only running functions if the hourly output file exists
    if hourly_file_exists:
        hourly_duplicates(hourly_df, outWorkbook2)
        compare_enmo(hourly_df, outWorkbook2)
        differences_enmo_enmo0plus(hourly_df, outWorkbook2)
        check_enmo_0plus(hourly_df)
        summarise_all_enmo(hourly_df)
        hourly_sum_enmo_mean(hourly_df)
        hourly_enmo_negative_values(hourly_df)
        hourly_outliers(hourly_df)
        hourly_enmo_flag(hourly_df)