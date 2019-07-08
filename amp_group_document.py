'''
This script is intended to enumberate the various computer,
groups, and policies in the Cisco AMP for Endpoints environment
and writes the results to a data folder in JSON format.

It also creates a simplified version of the data for computers
that can be used as a source of truth for restoring all computers
back to their original group. This is helpful for when connector
updates are not deployed through the AMP console and the wrong
deployment package was used causing the computer to change groups.

INSTRUCTIONS

Edit the 'api.cfg' file in the './config' folder with your
Cisco AMP for Endpoints API client ID and password.

Execute this script to gather the existing group that each computer
is in and write that in JSON format to the './data' folder.

'''

### IMPORTS
import sys
import configparser
import requests
import pandas as pd
from tqdm import tqdm

### CONSTANTS


### FUNC - DATA LOAD/SAVE
def save_json():
    '''
    Write the dataframes out as json files
    '''
    DF_GROUPS.to_json(r'.\data\AMP groups.json', orient='records')
    DF_COMPUTERS.to_json(r'.\data\AMP computers.json', orient='records')
    DF_POLICIES.to_json(r'.\data\AMP policies.json', orient='records')


### FUNC - API RESPONSE CHECKS
def status_ok(response):
    '''
    Check returned status code
    '''
    if response.status_code // 100 != 2:
        return False
    return True


def exit_if_fail(response):
    '''
    If returned status code is not 200 exit
    '''
    if status_ok(response) is False:
        if response.status_code == 404:
            sys.exit('The server returned 404 Not Found')
        elif response.status_code == 401:
            message_401 = 'The server returned 401 Unauthorized'
            sys.exit(message_401)
        else:
            if response.text:
                print('Server response: {}'.format(response.text))
            sys.exit('Something went wrong!')


### FUNC - GET DATA
def get_data(url, api):
    '''
    Get data from the AMP API and store in a dataframe
    '''
    # Create dataframes for storing
    df_response_data = pd.DataFrame()

    # Query the AMP API for data
    response = AMP_SESSION.get(url)
    exit_if_fail(response)
    response_json = response.json()

    # Create a progress bar
    cnt_total = response_json['metadata']['results']['total']
    cnt_current = response_json['metadata']['results']['current_item_count']
    pbar = tqdm(desc="    " + api,
                ncols=70,
                total=cnt_total,
                bar_format='{desc}:|{bar}|{n_fmt}/{total_fmt}',
                initial=cnt_current)

    # Normalize the results into a dataframe
    df_result_data = pd.io.json.json_normalize(response_json['data'])

    # Check in more data needs to be retrieved
    while 'next' in response_json['metadata']['links']:
        next_url = response_json['metadata']['links']['next']

        # Query the AMP API for more data
        response = AMP_SESSION.get(next_url)
        exit_if_fail(response)
        response_json = response.json()

        # Added the additional data to the dataframe
        df_response_data = pd.io.json.json_normalize(response_json['data'])
        df_result_data = df_result_data.append(df_response_data,
                                               ignore_index=True)

        # Update the progress bar
        cnt_update = response_json['metadata']['results']['current_item_count']
        pbar.update(cnt_update)

    # Close the progress bar
    pbar.close()

    # Return the results
    return df_result_data


def get_computers():
    '''
    Configure the URL needed to gather computers
    '''
    api = 'computers'
    url = '{0}{1}'.format(AMP_BASE_URL, api)
    result = get_data(url, api)
    return result


def get_groups():
    '''
    Configure the URL needed to gather groups
    '''
    api = 'groups'
    url = '{0}{1}'.format(AMP_BASE_URL, api)
    result = get_data(url, api)
    return result


def get_policies():
    '''
    Configure the URL needed to gather policies
    '''
    api = 'policies'
    url = '{0}{1}'.format(AMP_BASE_URL, api)
    result = get_data(url, api)
    return result


### MAIN CODE

### LOAD CONFIG
# Specify the config file
CONFIG_FILE = r'.\config\api.cfg'

# Reading the config file
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_FILE)

# Parse settings from config file
AMP_CLIENT_ID = CONFIG.get('AMP', 'amp_client_id')
AMP_CLIENT_PASSWORD = CONFIG.get('AMP', 'amp_client_password')
AMP_BASE_URL = CONFIG.get('AMP', 'amp_base_url')

### CONNECT TO AMPE
# Initiate a new session with Cisco AMP for Endpoints
AMP_SESSION = requests.session()
AMP_SESSION.auth = (AMP_CLIENT_ID, AMP_CLIENT_PASSWORD)

### GET DATA
# Gather data from the APIs
sys.stdout.write('\nCollecting data from Cisco AMP for Endpoints...\n')

# Gather group information
sys.stdout.write('Collecting group information...\n')
DF_GROUPS = get_groups()

# Gather policy information
sys.stdout.write('Collecting policy information...\n')
DF_POLICIES = get_policies()

# Gather computer information
sys.stdout.write('Collecting computer information...\n')
DF_COMPUTERS = get_computers()

### SAVE DATA
# Save data to disk in json format
sys.stdout.write('Writing results to disk...\n')
save_json()

### Create simplified computer json
sys.stdout.write('Creating simplified computer json file...\n')
DF_COMPUTERS_SIMP = DF_COMPUTERS.drop(columns=['active',
                                               'connector_version',
                                               'external_ip',
                                               'faults',
                                               'install_date',
                                               'internal_ips',
                                               'last_seen',
                                               'links.computer',
                                               'links.group',
                                               'links.trajectory',
                                               'network_addresses',
                                               'operating_system',
                                               'policy.guid',
                                               'policy.name'])

sys.stdout.write('Writing simplified computer json file to disk...\n')
DF_COMPUTERS_SIMP.to_json(r'.\data\AMP Simp_computers.json', orient='records')
