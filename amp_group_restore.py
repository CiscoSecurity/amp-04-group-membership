'''

This script is intended to return computer objects in Cisco AMP
for Endpoints back to their previous group.

This is helpful for when connector updates are not deployed
through the AMP console and the wrong deployment package was
used causing the computer to change groups.

INSTRUCTIONS

Edit the 'api.cfg' file in the './config' folder with your Cisco
AMP for Endpoints API client ID and password.

Run the 'amp_group_document.py' to generate a listing of all your
computers group memberships.

A copy of the 'AMP Simp_computers.json' file that is generated
using the 'amp_group_document.py' script will need to
be copied from the './data' folder to the './known_good' folder.

Execute this script to gather the existing group that each
computer is in and if that group has changed, move it back
to the group listed in the './known_good' folder.

'''

### IMPORTS
import sys
import configparser
import requests
import pandas as pd
from tqdm import tqdm

### CONSTANTS


### FUNC - DATA LOAD/SAVE
def read_json_df(file_name):
    '''
    Read the dataframes in from a json file
    '''
    try:
        return pd.read_json(r'.\known_good\\' + file_name)
    except ValueError:
        sys.exit('ERROR: There was an issue reading "{}"'.format(file_name))


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


### MOVE COMPUTER
def comp_to_group(conn_guid, old_group):
    '''
    move a computer to a different group
    '''
    api = 'computers/'
    url = '{0}{1}{2}'.format(AMP_BASE_URL, api, conn_guid)

    payload = 'group_guid=' + old_group
    headers = {'Content-Type': "application/x-www-form-urlencoded",
               'Accept': "application/json"}

    response = AMP_SESSION.patch(url, data=payload, headers=headers)
    if response.status_code == 202:
        sys.stdout.write(conn_guid + ' moved to ' + old_group + '\n')
    else:
        sys.stdout.write(conn_guid + ' failed moving to ' +
                         old_group + ' due to ' +
                         str(response.status_code) + ' error\n')


def compare_dfs(old_data, new_data):
    '''
    Join the data frames from the new responses and the previous known
    settings and find where there is a computer that has been assigned
    a new group. For computers with a new group, send the connector guid
    and group guid to the move computer function.
    '''
    # Join the two dataframes
    df_joined = new_data.set_index('connector_guid').join(old_data.set_index('connector_guid'),
                                                          lsuffix='_new',
                                                          rsuffix='_old')

    # Remove rows for new connector guids
    # (i.e. there was not value in the known_good file)
    df_joined = df_joined.dropna(subset=['group_guid_old'])

    # Check if computer is in new group, then move to the old group
    same_group = 0
    changed_group = 0

    for index, row in df_joined.iterrows():
        if row['group_guid_new'] == row['group_guid_old']:
            same_group = same_group + 1
        else:  # need to check if old group is nan
            changed_group = changed_group + 1
            sys.stdout.write(index + ' was in ' + row['group_guid_old'] +
                             ' but now is in ' + row['group_guid_new'] + '\n')
            grp_guid = row['group_guid_old']
            comp_to_group(index, grp_guid)

    sys.stdout.write('\nChanged group count = ' + str(changed_group) + '\n')
    sys.stdout.write('Same group count = ' + str(same_group))


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

### Initiate a new session with Cisco AMP for Endpoints
AMP_SESSION = requests.session()
AMP_SESSION.auth = (AMP_CLIENT_ID, AMP_CLIENT_PASSWORD)

### Gather data from the APIs
sys.stdout.write('\nCollecting data from Cisco AMP for Endpoints...\n')
sys.stdout.write('Collecting computer information...\n')
DF_NEW_COMPUTERS = get_computers()

### Create simplified computer json
sys.stdout.write('Creating simplified computer json file...\n')
DF_COMPUTERS_SIMP_NEW = DF_NEW_COMPUTERS.drop(columns=['active',
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

sys.stdout.write('\nReading the known good file...\n')
DF_COMPUTERS_SIMP_OLD = read_json_df('AMP Simp_computers.json')

## Resolve wrong group
compare_dfs(DF_COMPUTERS_SIMP_OLD, DF_NEW_COMPUTERS)
