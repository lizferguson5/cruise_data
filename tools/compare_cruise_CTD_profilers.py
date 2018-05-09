#!/usr/bin/env python
"""
Created on Apr 12 2018

@author: Lori Garzio
@brief: Compare profiler CTD or FLORT data in uFrame to the cruise shipboard CTD casts. Uses the platform-to-CTD-cast
mapping files in the OOI Datateam Database (https://github.com/seagrinch/data-team-python/tree/master/cruise_data).
Requires server connection to alfresco.ooi.rutgers.edu on local machine to directly access the shipboard CTD files.

@usage:
sDir: directory where output is saved
api_key: OOI API username
api_token: OOI API password
refdes: reference designator of interest
deployment: deployment of interest (e.g. D00001 = compare data from the instrument to the CTD cast that  was done at
deployment #1; R00001 = compare data from the instrument to the CTD cast that was done at recovery #1)
"""

import pandas as pd
import sys
from seabird.cnv import fCNV
import requests
import datetime
import matplotlib.pyplot as plt
import os
from geopy.distance import geodesic
from collections import OrderedDict


def data_request_url(session, rd):
    API_BASE_URL = 'https://ooinet.oceanobservatories.org/api/m2m/12576/sensor/inv/'
    refdes_url = '{:s}{:s}/{:s}/{:s}-{:s}'.format(API_BASE_URL, rd[0], rd[1], rd[2], rd[3])

    mlist = return_uframe_response(refdes_url, session, api_key, api_token)
    mlist = filter(lambda k: 'bad' not in k, mlist)  # don't show 'bad' delivery methods
    print 'Delivery methods listed in uFrame for {}: '.format(refdes)
    print mlist
    method = raw_input('\nPlease choose one delivery method for your data request: ')
    murl = '{:s}/{:s}'.format(refdes_url, method)

    slist = return_uframe_response(murl, session, api_key, api_token)
    print 'Streams listed in uFrame for {}-{}'.format(refdes, method)
    print slist
    stream = raw_input('\nPlease choose one stream for your data request: ')
    request_url = '{:s}/{:s}'.format(murl, stream)

    return method, stream, request_url


def format_str(input):
    if input == '':
        output = [input]
        length = len(output)
    else:
        if ',' in input:
            input1 = input.replace(" ", "")  # remove any whitespace
            output = input1.split(',')
            length = len(output)
        else:
            output = [input]
            length = len(output)
    return output, length


def ntp_seconds_to_datetime(ntp_seconds):
    ntp_epoch = datetime.datetime(1900, 1, 1)
    unix_epoch = datetime.datetime(1970, 1, 1)
    ntp_delta = (unix_epoch - ntp_epoch).total_seconds()
    return datetime.datetime.utcfromtimestamp(ntp_seconds - ntp_delta).replace(microsecond=0)


def profile_plot_panel(cast_args, uF_args, units, labels, ptitle, sfile, uFdate):
    fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
    ax1.plot(cast_args[1], cast_args[0], 'b')
    ax1.plot(uF_args[1], uF_args[0], 'r.', markersize=.75)
    ax1.set_ylabel('Pressure ({})'.format(units[0]))
    ax1.set_xlabel(labels[0] + ' ({})'.format(units[1]))
    ax1.invert_yaxis()
    ax1.grid()

    ax2.plot(cast_args[2], cast_args[0], 'b', label='Cruise CTD')
    ax2.plot(uF_args[2], uF_args[0], 'r.', markersize=.75, label='Profiler')
    ax2.set_xlabel(labels[1] + ' ({})'.format(units[2]))
    ax2.legend()
    ax2.grid()

    fig.suptitle(('{} vs. Shipboard CTD'.format(refdes) + '\n' + ptitle + '\n' + 'uFrame Profiler data: {}'.format(uFdate)), fontsize=10)
    fig.subplots_adjust(top=0.875)
    plt.savefig(str(sfile))
    plt.close()


def profile_plot_single(cast_args, uF_args, units, label, ptitle, sfile, uFdate):
    fix, ax = plt.subplots()
    ax.plot(cast_args[1], cast_args[0], 'b', label='Cruise CTD')
    ax.plot(uF_args[1], uF_args[0], 'r.', markersize=1.5, label='Profiler')
    ax.set_ylabel('Pressure ({})'.format(units[0]))
    ax.set_xlabel(label + ' ({})'.format(units[1]))
    #plt.xlim(0, 1.5)
    #plt.ylim(0, 150)
    ax.invert_yaxis()
    ax.legend()
    ax.grid()

    ax.set_title(('{} vs. Shipboard CTD'.format(refdes) + '\n' + ptitle + '\n' + 'uFrame Profiler data: {}'.format(uFdate)), fontsize=10)
    plt.savefig(str(sfile))
    plt.close()


def return_uframe_response(url, session, username, token):
    r = session.get(url, auth=(username, token))
    if r.status_code == 200:
        response = r.json()
        return response
    else:
        print 'Request failed'


def main(sDir, api_key, api_token, refdes, deployment):
    rd = refdes.split('-')
    summary = OrderedDict()

    # Get information from the cruise CTD-to-platform mapping files to grab the cruise CTD data that would overlap
    # with some data from the selected platform
    cruisedata_repo = 'https://raw.githubusercontent.com/seagrinch/data-team-python/master/cruise_data'
    p_CTD_map = pd.read_csv('/'.join((cruisedata_repo, 'platform_CTDcast_mapping.csv'))).fillna('')
    CTDcasts = pd.read_csv('/'.join((cruisedata_repo, 'cruise_CTDs.csv'))).fillna('')

    info = p_CTD_map.loc[(p_CTD_map.platform == rd[0]) & (p_CTD_map.Deployment == deployment)]
    ploc = [info.iloc[0]['lat'], info.iloc[0]['lon']]  # platform deployment location from asset management

    if info.iloc[0]['CTDcast'] == '':
        print 'No CTD cast identified for {} {}. Ending program'.format(rd[0], deployment)
        sys.exit()

    cruise, cruise_len = format_str(info.iloc[0]['CTD_CruiseName'])
    cruiseleg, cruiseleg_len = format_str(info.iloc[0]['CTD_CruiseLeg'])
    cast, cast_len = format_str(info.iloc[0]['CTDcast'])

    if cruise_len == cruiseleg_len == cast_len:
        cast_info_list = zip(cruise, cruiseleg, cast)
    else:
        if cruise_len != cruiseleg_len and cruiseleg_len == cast_len:
            cast_info_list = zip(cruise * cruiseleg_len, cruiseleg, cast)
        if cruise_len == cruiseleg_len and cruiseleg_len != cast_len:
            cast_info_list = zip(cruise * cast_len, cruiseleg * cast_len, cast)
        if cruiseleg == [''] and cruise_len == cast_len:
            cast_info_list = zip(cruise, cruiseleg * cruise_len, cast)
        else:
            print "!! Check CTD_CruiseName, CTD_CruiseLeg, CTDcast info. Lengths of lists don't match up !!"

    for i, c in enumerate(cast_info_list):
        # select the information from the CTD cast identified in the mapping table
        CTDcast_info = CTDcasts.loc[(CTDcasts.CTD_CruiseName == c[0]) & (CTDcasts.CTD_CruiseLeg == c[1]) & (CTDcasts.CTDcast == str(c[2]))]

        fCTD = ''.join([CTDcast_info.iloc[0]['filepath_primary'], CTDcast_info.iloc[0]['CTD_rawdata_filepath']])
        print 'CTD filename: {}'.format(fCTD)

        # Open the raw CTD file
        profile = fCNV(fCTD)

        # CTD cast information
        CTDloc = [profile.attributes['LATITUDE'], profile.attributes['LONGITUDE']]  # CTD cast location
        diff_loc = round(geodesic(ploc, CTDloc).kilometers,4)
        print 'The CTD cast was done {} km from the mooring location'.format(diff_loc)
        CTDdate = profile.attributes['datetime'].strftime('%Y-%m-%dT%H:%M:%S')

        if c[1] == '':
            ptitle = 'Cruise ' + CTDcast_info.iloc[0]['CUID'] + ' Cast ' + str(c[2]) + ': ' + CTDdate + \
                     ' (distance {} km)'.format(diff_loc)
        else:
            ptitle = 'Cruise ' + CTDcast_info.iloc[0]['CUID'] + ' Leg ' + c[1] + ' Cast ' + str(c[2]) + ': ' + CTDdate + \
                     ' (distance {} km)'.format(diff_loc)

        # Try variations in variable names
        param_notes = []
        try:
            conductivity = profile['CNDC'].data
        except KeyError:
            try:
                conductivity = profile['c1mS/cm'].data / 10
            except KeyError:
                print 'No conductivity variable found in the cruise CTD file'
                param_notes.append('No conductivity variable found in the cruise CTD file')
                conductivity = []

        try:
            density = profile['density'].data
        except KeyError:
            try:
                density = profile['sigma-\xe900'].data + 1000
            except KeyError:
                print 'No density variable found in the cruise CTD file'
                param_notes.append('No density variable found in the cruise CTD file')
                density = []


        CTDcast_data = {
            'pres': {'values': profile['PRES'].data, 'units': 'db'},
            'temp': {'values': profile['TEMP'].data, 'units': 'deg C'},
            'cond': {'values': conductivity, 'units': 'S/m'},
            'sal': {'values': profile['PSAL'].data, 'units': 'PSU'},
            'den': {'values': density, 'units': 'kg/m^3'},
            'chla': {'values': profile['flECO-AFL'].data, 'units': 'ug/L'}  # mg/m^3 is the same as ug/L
        }

        # specify the date of the cruise CTD cast for the uFrame API request
        params = {
            'beginDT': profile.attributes['datetime'].strftime('%Y-%m-%dT00:00:00.000Z'),
            'endDT': (profile.attributes['datetime'] + datetime.timedelta(days=1)).strftime('%Y-%m-%dT00:00:00.000Z'),
            #'beginDT': (profile.attributes['datetime'] + datetime.timedelta(days=1)).strftime('%Y-%m-%dT00:00:00.000Z'), # take the day after the cruise CTD
            #'endDT': (profile.attributes['datetime'] + datetime.timedelta(days=2)).strftime('%Y-%m-%dT00:00:00.000Z'),
            'limit': 10000
        }

        # Build the url for the data request from uFrame
        session = requests.session()
        method, stream, request_url = data_request_url(session, rd)

        summary[i] = OrderedDict()
        summary[i]['refdes'] = refdes
        summary[i]['method'] = method
        summary[i]['stream'] = stream
        summary[i]['deployment'] = deployment
        summary[i]['platform_lat_lon'] = ploc
        summary[i]['cruise'] = c[0]
        summary[i]['CUID'] = CTDcast_info.iloc[0]['CUID']
        summary[i]['cruiseleg'] = c[1]
        summary[i]['cast'] = str(c[2])
        summary[i]['cruiseCTDcast_date'] = profile.attributes['datetime'].strftime('%Y-%m-%dT%H:%M:%SZ')
        summary[i]['cruiseCTDcast_lat_lon'] = CTDloc
        summary[i]['cruiseCTDcast_platform_loc_diff_km'] = diff_loc
        summary[i]['cruiseCTDcast_filename'] = fCTD
        summary[i]['param_notes'] = param_notes
        summary[i]['uframe_data_date'] = params['beginDT']

        # Request data from uFrame
        print 'Requesting data from uFrame'
        r = session.get(request_url, params=params, auth=(api_key, api_token))

        if r.status_code != 200:
            print r.json()['message']
            summary[i]['uframe_message'] = r.json()['message']
        elif r.status_code == 200:
            summary[i]['uframe_message'] = 'Data request successful'
            data = r.json()

            uF = {}

            if 'CTD' in refdes:
                keys = ['time', 'pres', 'temp', 'cond', 'sal', 'den']
                for k in keys:
                    uF.setdefault(k, [])

                for i in range(len(data)):
                    uF['time'].append(ntp_seconds_to_datetime(data[i]['time']))
                    uF['pres'].append(data[i]['ctdpf_ckl_seawater_pressure'])
                    uF['temp'].append(data[i]['ctdpf_ckl_seawater_temperature'])
                    uF['cond'].append(data[i]['ctdpf_ckl_seawater_conductivity'])
                    uF['sal'].append(data[i]['practical_salinity'])
                    uF['den'].append(data[i]['density'])

                print 'Plotting CTD data'
                cast_args = (CTDcast_data['pres']['values'], CTDcast_data['cond']['values'], CTDcast_data['temp']['values'])
                uF_args = (uF['pres'], uF['cond'], uF['temp'])
                units = (CTDcast_data['pres']['units'], CTDcast_data['cond']['units'], CTDcast_data['temp']['units'])
                labels = ('Conductivity', 'Temperature')
                fname = '_'.join((refdes, deployment, method, c[0], c[1], c[2], 'cond_temp'))
                sfile = os.path.join(sDir,fname)
                profile_plot_panel(cast_args, uF_args, units, labels, ptitle, sfile, params['beginDT'][0:10])

                cast_args = (CTDcast_data['pres']['values'], CTDcast_data['sal']['values'], CTDcast_data['den']['values'])
                uF_args = (uF['pres'], uF['sal'], uF['den'])
                units = (CTDcast_data['pres']['units'], CTDcast_data['sal']['units'], CTDcast_data['den']['units'])
                labels = ('Salinity', 'Density')
                fname = '_'.join((refdes, deployment, method, c[0], c[1], c[2], 'sal_den'))
                sfile = os.path.join(sDir,fname)
                profile_plot_panel(cast_args, uF_args, units, labels, ptitle, sfile, params['beginDT'][0:10])

            if 'FLOR' in refdes:
                keys = ['time', 'pres', 'chla']
                for k in keys:
                    uF.setdefault(k, [])

                for i in range(len(data)):
                    uF['time'].append(ntp_seconds_to_datetime(data[i]['time']))
                    uF['pres'].append(data[i]['int_ctd_pressure'])
                    uF['chla'].append(data[i]['fluorometric_chlorophyll_a'])

                print 'Plotting FLOR data'
                cast_args = (CTDcast_data['pres']['values'], CTDcast_data['chla']['values'])
                uF_args = (uF['pres'], uF['chla'])
                units = (CTDcast_data['pres']['units'], CTDcast_data['chla']['units'])
                label = 'Fluorometric Chlorophyll-a'
                fname = '_'.join((refdes, deployment, method, c[0], c[1], c[2], 'chla'))
                sfile = os.path.join(sDir, fname)
                profile_plot_single(cast_args, uF_args, units, label, ptitle, sfile, params['beginDT'][0:10])

    sname = refdes + '_cruise_CTD_summary.csv'
    pd.DataFrame.from_dict(summary, orient='index').to_csv(os.path.join(sDir, sname), index=False)


if __name__ == '__main__':
    sDir = '/Users/lgarzio/Documents/OOI/CruiseData/profiler_comparisons/'
    api_key = 'username'
    api_token = 'token'
    refdes = 'CP02PMUO-WFP01-03-CTDPFK000'
    deployment = 'D00009'  #R00009
    main(sDir, api_key, api_token, refdes, deployment)
