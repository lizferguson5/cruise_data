#!/usr/bin/env python
"""
Created on Apr 24 2018

@author: Lori Garzio
@brief: update https://github.com/seagrinch/data-team-python/tree/master/cruise_data/cruise_CTDs.csv with the time, lat,
lon from the cruise .cnv files. Requires server connection to alfresco.ooi.rutgers.edu on local machine to directly 
access the shipboard CTD files.

@usage:
sDir: directory where output is saved
"""

import pandas as pd
from seabird.cnv import fCNV
import os
import datetime


def main(sDir):
    file = 'https://raw.githubusercontent.com/seagrinch/data-team-python/master/cruise_data/cruise_CTDs.csv'
    df = pd.read_csv(file).fillna('')
    df['update_notes'] = ''
    for row in df.iterrows():
        if row[-1]['CTD_rawdata_filepath'].endswith('.cnv'):
            if row[-1]['CTD_Date'] == '' or row[-1]['CTD_lat'] == '' or row[-1]['CTD_lon'] == '':
                f = ''.join((row[-1]['filepath_primary'], row[-1]['CTD_rawdata_filepath']))
                profile = fCNV(f)

                if row[-1]['CTD_Date'] == '':
                    df.loc[row[0], 'CTD_Date'] = profile.attributes['datetime'].strftime('%Y-%m-%dT%H:%M:%S')
                    df.loc[row[0], 'update_notes'] = 'Updated row'
                if row[-1]['CTD_lat'] == '':
                    df.loc[row[0], 'CTD_lat'] = profile.attributes['LATITUDE']
                    df.loc[row[0], 'update_notes'] = 'Updated row'
                if row[-1]['CTD_lon'] == '':
                    df.loc[row[0], 'CTD_lon'] = profile.attributes['LONGITUDE']
                    df.loc[row[0], 'update_notes'] = 'Updated row'

    fname = 'cruise_CTDs_{}.csv'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S'))
    df.to_csv(os.path.join(sDir,fname), index=False)


if __name__ == '__main__':
    sDir = '/Users/lgarzio/Documents/repo/lgarzio/seagrinch-fork/data-team-python/cruise_data/'
    main(sDir)
