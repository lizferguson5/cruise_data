#!/usr/bin/env python
"""
Created on Apr 20 2018

@author: Lori Garzio
@brief: update https://github.com/seagrinch/data-team-python/tree/master/cruise_data/platform_CTDcast_mapping.csv
with the latest information from the asset management deployment sheets:
https://github.com/ooi-integration/asset-management/tree/master/deployment. Currently only updates Pioneer and Global
platforms.

@usage:
AMdir: deployment directory in a clone of the OOI asset management repo on local machine
(https://github.com/ooi-integration/asset-management/tree/master/deployment)
sDir: directory where output is saved
"""

import pandas as pd
import os
from collections import OrderedDict
import datetime


def append_deploymentsheet_info(dct, var, date, lat, lon, CUID):
    dct[var] = OrderedDict()
    dct[var]['deploymentNumber'] = int(var.split('_')[-1][1:])
    dct[var]['lat'] = str(lat).strip('[]').strip(" '' ")
    dct[var]['lon'] = str(lon).strip('[]').strip(" '' ")
    dct[var]['CUID'] = str(CUID).strip('[]').strip(" '' ")
    dct[var]['AM_Date'] = str(date).strip('[]')


def define_array(key):
    code = key[0:2]
    code_mapping = {'GA': 'Global_Argentine_basin',
                    'GI': 'Global_Irminger',
                    'GP': 'Global_Papa',
                    'GS': 'Global_Southern_Ocean',
                    'CP': 'Coastal_Pioneer',
                    'CE': 'Coastal_Endurance'}
    for c, a in code_mapping.iteritems():
        if code == c:
            array = a
    return array


def format_deploy_str(d):
    dd = '%05d' % (d,)
    deploys = [''.join(('D', dd)), ''.join(('R', dd))]
    return deploys


def update_dataframe(match, df, var, am_info):
    if str(match.iloc[0][var]) != am_info[var]:
        df.loc[match.index, var] = am_info[var]  # update the variable
        i = match.index[0]
        if df['update_notes'][i] == '':
            df.loc[match.index, 'update_notes'] = 'Manually check cruise CTD info. Updated {}'.format(var)
        else:
            df.loc[match.index, 'update_notes'] = df['update_notes'][i] + ', {}'.format(var)


def main(rootdir, sDir):
    dfile_dict = {}
    for root, dirs, files in os.walk(rootdir):
        for f in files:
            if f.startswith(('CP', 'G')):
                print f
                dfile = pd.read_csv(os.path.join(root,f)).fillna('')
                platform = f.split('_')[0]
                deployments = dfile['deploymentNumber'].unique().tolist()
                stimes = dfile['startDateTime'].unique().tolist()
                etimes = dfile['stopDateTime'].unique().tolist()

                # Check to make sure there is the same number of deployment numbers, startDateTimes, stopDateTimes
                # in asset management
                length = len(deployments)
                if any(len(lst) != length for lst in [stimes, etimes]):
                    raise ValueError("The number of unique entries in one or more asset management fields doesn't match. "
                                     "Check {}: deploymentNumber, startDate, stopDate".format(f))

                for i in range(len(deployments)):
                    d = deployments[i]
                    # filter on deployment and get rid of lines that are commented out
                    dfile_filtered = dfile[(dfile['deploymentNumber'] == d) & (~dfile['CUID_Deploy'].str.startswith('#'))]
                    lat = dfile_filtered['lat'].astype(str).unique().tolist()
                    lon = dfile_filtered['lon'].astype(str).unique().tolist()
                    dCUID = dfile_filtered['CUID_Deploy'].unique().tolist()
                    rCUID = dfile_filtered['CUID_Recover'].unique().tolist()
                    deploys = format_deploy_str(d)
                    for x in deploys:
                        if x.startswith('D'):
                            d_platform_deploy = '_'.join((platform, x))
                            append_deploymentsheet_info(dfile_dict, d_platform_deploy, stimes[i], lat, lon, dCUID)
                        if x.startswith('R'):
                            d_platform_deploy = '_'.join((platform, x))
                            append_deploymentsheet_info(dfile_dict, d_platform_deploy, etimes[i], lat, lon, rCUID)

    cruisedata_repo = 'https://raw.githubusercontent.com/seagrinch/data-team-python/master/cruise_data'
    df = pd.read_csv('/'.join((cruisedata_repo, 'platform_CTDcast_mapping.csv'))).fillna('')
    df['update_notes'] = ''

    for key in dfile_dict.keys():
        am_info = dfile_dict[key]
        match = df.loc[(df['platform'] == key.split('_')[0]) & (df['Deployment'] == key.split('_')[1])]

        # if the record in asset management doesn't exist in platform_CTDcast_mapping, add it
        if match.empty:
            print 'Adding row to platform_CTDcast_mapping.csv'
            cols = ['Array', 'platform', 'deploymentNumber', 'Deployment', 'lat', 'lon', 'CUID', 'AM_Date', 'update_notes']
            newrow = key.split('_')
            newrow.insert(0, define_array(key))

            for ii, value in dfile_dict[key].iteritems():
                if ii == 'deploymentNumber':
                    newrow.insert(2, value)
                else:
                    newrow.append(value)

            newrow.append('New entry. Need to manually check cruise CTD info')
            new_row = pd.DataFrame([newrow], columns=cols)
            df = df.append(new_row)[df.columns.tolist()]

        # if the record in asset management exists in platform_CTDcast_mapping, update it if necessary
        else:
            update_vars = ['CUID', 'AM_Date', 'lat', 'lon']
            for u in update_vars:
                update_dataframe(match, df, u, am_info)

    dfs = df.sort_values(['platform', 'deploymentNumber', 'Deployment'])
    fname = 'platform_CTDcast_mapping_{}.csv'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S'))
    dfs.to_csv(os.path.join(sDir, fname), index=False)


if __name__ == '__main__':
    AMdir = '/Users/lgarzio/Documents/repo/lgarzio/ooi-integration-fork/asset-management/deployment'
    sDir = '/Users/lgarzio/Documents/repo/lgarzio/seagrinch-fork/data-team-python/cruise_data/'
    main(AMdir, sDir)
