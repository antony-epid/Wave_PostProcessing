# This script merge the meta data files from files that have been processed through Pampro and merges them into 1 metadata file
# Author: cas254
# Date: 07/10/2024
# Version 1

import os
import pandas as pd

RESULTS_FOLDER = '/rfs/project/rfs-Bl26eNcUDB8/users_writeable/antony_runs/TestWave/_results/'

# Get list of files
def list_files(folder_path):
    '''
    The function creates a filelist, keeps files with meta in, extract filetype and id and then group the files by id.
    :param results_folder:
    :return: groups
    '''
    files = os.listdir(folder_path)
    df = pd.DataFrame(files, columns=['filename'])
    df = df[df['filename'].str.contains('meta')]
    df[['file_type', 'id']] = df['filename'].str.split(r'(?<=meta)', expand=True)
    df['id'] = df['id'].str.lstrip('_').str.replace('.csv', '', regex=False)

    # Grouping files with same id
    groups = df.groupby('id')
    return groups

# Merge meta files with same id
def merge_meta(groups, folder_path, variables):
    for id, group in groups:
        file_paths = {}
        for var in variables:
            file_name = group[group['file_type'].str.contains(var)]['filename'].values[0]
            file_paths[f'{var}_file'] = os.path.join(folder_path, file_name)

        # Reading analysis_meta file
        analysis_df = pd.read_csv(file_paths['analysis_meta_file'])

        # Merge with qc_meta
        qc_meta_df = pd.read_csv(file_paths['qc_meta_file'])
        columns_to_keep = [col for col in qc_meta_df.columns if col.startswith('QC')] + ['file_filename']
        qc_meta_df = qc_meta_df[columns_to_keep]
        merged_df = pd.merge(analysis_df, qc_meta_df, how='outer', on='file_filename')

        output_file = os.path.join(folder_path, f'metadata_{id}.csv')
        merged_df.to_csv(output_file, index=False)


if __name__ == '__main__':
    groups = list_files(RESULTS_FOLDER)
    merge_meta(groups, RESULTS_FOLDER, ['analysis_meta', 'file_meta', 'qc_meta'])