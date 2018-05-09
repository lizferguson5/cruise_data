# OOI Cruise Data
This repo contains preliminary tools to work with OOI cruise data (primarily shipboard CTD files), update the OOI Datateam Database files with the most recent asset information, and compare cruise data to data downloaded from uFrame via the Machine to Machine (M2M) interface for OOI platforms.

- Author: Lori Garzio - Rutgers University

### Installation
    > git clone https://github.com/ooi-data-review/cruise_data.git
    > cd cruise_data
    > pip install .
    > pip install -r requirements.txt

### Tools
- [compare_cruise_CTD_profilers.py](https://github.com/ooi-data-review/cruise_data/blob/master/tools/compare_cruise_CTD_profilers.py): Compares profiler CTD or FLORT data in uFrame to the cruise shipboard CTD casts. Uses the platform-to-CTD-cast mapping files in the OOI Datateam Database (https://github.com/seagrinch/data-team-python/tree/master/cruise_data). Requires server connection to alfresco.ooi.rutgers.edu on local machine to directly access the shipboard CTD files.

- [convert_cnv_files.py](https://github.com/ooi-data-review/cruise_data/blob/master/tools/convert_cnv_files.py): Converts OOI cruise shipboard CTD .cnv files to .csv files. Requires server connection to alfresco.ooi.rutgers.edu on local machine if directly accessing the OOI shipboard CTD files (files can alternatively be downloaded and converted). There are two acceptable input formats: 1) path to an individual *.cnv file, or 2) .csv file containing CTD files to be converted (e.g. https://github.com/seagrinch/data-team-python/blob/master/cruise_data/cruise_CTDs.csv)

- [update_cruise_CTD_attributes.py](https://github.com/ooi-data-review/cruise_data/blob/master/tools/update_cruise_CTD_attributes.py): Updates the cruise CTD information sheet in the OOI Datateam Database (https://github.com/seagrinch/data-team-python/tree/master/cruise_data/cruise_CTDs.csv) with the time, lat, lon from the cruise .cnv files. Requires server connection to alfresco.ooi.rutgers.edu on local machine to directly access the shipboard CTD files.

- [update_cruise_platform_mapping.py](https://github.com/ooi-data-review/cruise_data/blob/master/tools/update_cruise_platform_mapping.py): Updates the platform-to-CTD-cast mapping file (https://github.com/seagrinch/data-team-python/tree/master/cruise_data/platform_CTDcast_mapping.csv) with the latest information from the asset management deployment sheets: https://github.com/ooi-integration/asset-management/tree/master/deployment. Currently only updates Pioneer and Global platforms.

### Notes
- In order to access OOI data through the uFrame API, you will need to create a user account on ooinet.oceanobservatories.org. Your API Username and Token can be found in your User Profile.
