[![Gitter chat](https://img.shields.io/badge/gitter-join%20chat-brightgreen.svg)](https://gitter.im/CiscoSecurity/AMP-for-Endpoints "Gitter chat")

### AMP for Endpoints Group Document and Restore:
This is helpful for when connector updates are not deployed through the AMP console and the wrong deployment package was used causing the computer to change groups.

There are two script files provided:
- amp_group_document.py
- amp_group_restore.py

**amp_group_document.py** enumerates the various computers, groups, and policies in the Cisco AMP for Endpoints environment and writes the results to a ```./data``` folder in JSON format.
It also creates a simplified version of the data for computers -- ```AMP Simp_computers.json``` -- that can be used as a source of truth for restoring all computers back to their original group. 

**amp_group_restore.py** returns computer objects in Cisco AMP for Endpoints back to their previous group as documented in ```AMP Simp_computers.json```.

1. Execute ```amp_group_document.py``` to generate a listing of all your computers group memberships.
2. A copy of the ```AMP Simp_computers.json``` file that is generated using the ```amp_group_document.py``` script will need to be copied from the ```./data``` folder to the ```./known_good``` folder.
3. Execute ```amp_group_restore.py``` to gather the existing group that each computer is in and if that group has changed, move it back to the group listed in the ```./known_good``` folder.


### Before using you must update the following:
The authentication parameters are set in the ```api.cfg``` file in the ```./config``` folder 
- amp_client_id 
- amp_client_password

Install required Python modules using:
```pip install -r requirements.txt```

### amp_group_document.py Usage:
```
python amp_group_document.py
```

### Example script output:
```
Collecting data from Cisco AMP for Endpoints...
Collecting group information...
    groups:|████████████████████████████████████████████████████|15/15
Collecting policy information...
    policies:|██████████████████████████████████████████████████|19/19
Collecting computer information...
    computers:|█████████████████████████████████████████████████|50/50
Writing results to disk...
Creating simplified computer json file...
Writing simplified computer json file to disk...
```

### amp_group_restore.py Usage:
```
python amp_group_restore.py
```

### Example script output:
```
Collecting data from Cisco AMP for Endpoints...
Collecting computer information...
    computers:|█████████████████████████████████████████████████|50/50
Creating simplified computer json file...

Reading the known good file...
43ea5bb6-a4ec-48fa-876c-59cc304fda17 was in 9dad56da-5094-40e6-bc5c-5778b716b1bf but now is in 0f2d4c14-4c6b-4acb-bb8a-924c8b909b96
43ea5bb6-a4ec-48fa-876c-59cc304fda17 moved to 9dad56da-5094-40e6-bc5c-5778b716b1bf
```
