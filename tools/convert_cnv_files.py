#!/usr/bin/env python
"""
Created on Apr 18 2018

@author: Lori Garzio
@brief: Convert OOI cruise shipboard CTD .cnv files to .csv files. Requires server connection to 
alfresco.ooi.rutgers.edu on local machine if directly accessing the OOI shipboard CTD files.
@usage:
sDir: Directory where output files are saved
CTDfiles: two acceptable formats: 1) path to an individual *.cnv file, or 2) .csv file containing CTD files to be
converted (e.g. https://github.com/seagrinch/data-team-python/blob/master/cruise_data/cruise_CTDs.csv)
"""

import pandas as pd
from io import StringIO
import os


def create_dir(new_dir):
    # Check if dir exists.. if it doesn't... create it.
    if not os.path.isdir(new_dir):
        try:
            os.makedirs(new_dir)
        except OSError:
            if os.path.exists(new_dir):
                pass
            else:
                raise


def ctd_files_lst(CTD_files):
    flist = []
    if CTD_files.endswith('.csv'):
        CTDfiles = pd.read_csv(CTD_files).fillna('')
        for row in CTDfiles.iterrows():
            if row[-1]['CTD_rawdata_filepath'].endswith('.cnv'):
                f = ''.join((row[-1]['filepath_primary'], row[-1]['CTD_rawdata_filepath']))
                flist.append(f)
    elif CTD_files.endswith('.cnv'):
        flist.append(CTD_files)
    else:
        print 'CTD_files input not in correct format'
    return flist


def main(sDir, CTD_files):
    flist = ctd_files_lst(CTD_files)
    for i, f in enumerate(flist):
        print 'Converting {} of {} files'.format(i, len(flist))
        save_dir = '/'.join((sDir, '/'.join(f.split('/')[4:-1])))
        create_dir(save_dir)

        # open the file and write to .csv
        ctdfile = open(f, 'rb')
        ctdfile = StringIO(ctdfile.read().decode(encoding='utf-8', errors='replace'))
        header1, header2 = [], []
        for k, line in enumerate(ctdfile.readlines()):
            if '# name ' in line:
                line = line.rstrip('\r\n')
                name, desc = line.split('=')[1].split(':')
                if name in [u' sigma-\ufffd00', u' sigma-\ufffd11']:
                    name = 'sigma'
                header1.append(str(name).lstrip())
                header2.append(str(desc).lstrip())

            if '*END*' in line:
                skiprows = k + 1

        ctdfile.seek(0)
        df = pd.read_table(ctdfile, header=None, names=header1, index_col=None, skiprows=skiprows, delim_whitespace=True)
        df.columns = pd.MultiIndex.from_tuples(zip(df.columns, header2))
        fname = '.'.join((f.split('/')[-1].split('.')[0], 'csv'))
        df.to_csv(os.path.join(save_dir, fname), index=False)
        ctdfile.close()


if __name__ == '__main__':
    sDir = '/Users/lgarzio/Documents/OOI/CruiseData/processed_files'
    CTD_files = 'https://raw.githubusercontent.com/seagrinch/data-team-python/master/cruise_data/cruise_CTDs.csv'
    #CTD_files = '/Volumes/webdav/OOI/Global Argentine Basin Array/Cruise Data/Argentine_Basin-01_AT-26-30_2015-03-08/Ship Data/at26-30/ctd/process/at2630007.cnv'
    main(sDir, CTD_files)
