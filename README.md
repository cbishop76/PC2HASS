# PC2HASS
PC2HASS is a Python program that can control a Windows PC from Home Assistant.
* Switch between different display configuration of a Windows PC from Home Assistant.  Unlimited combinations of:
  * Different resolutions
  * Multi-monitor setups (#, left, right, extended, duplicate)
* Launch Windows applications and websites from Home Assistant 

## Getting Started
Follow this guide to get up and running, controling your PC from the lovelace frontend and backend scripts. 

### Prerequisites
* Home Assistant server
* Windows PC with Python 3.7 or later installed

You will need to know and have both configured with a fixed IP addresses.

* Python Requests library on your Windows PC

The Requests libraray, https://2.python-requests.org/en/v2.7.0/ can be installed with the following command line:
```
pip install requests
```


### Installation
Download the PC2HASS zip file and extract it to a known location on your drive.

Download Monitor Profile Switcher from https://sourceforge.net/projects/monitorswitcher/ and extract the file `MonitorSwitcher.exe` to the same folder that you have `PC2HASS.py` in.


### Setup
#### Access Token
* Open Home Assistant and navigate to your Profile page.
* Under Log-Lived Access Tokens, click CREATE TOKEN.
* Give it any name you like, and copy the token it gives you to the clipboard.
* Using your favorite editor (IDLE, Notepad++, Notepad) open `PC2HASS.py`
```
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
from subprocess import call, Popen
from os import listdir
import fnmatch

import json
import requests

CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008
AUTH = 'Bearer ENTER-HA-LONG-LIVED-TOKEN-HERE'
HASS_IP = 'ENTER-HA-IP-ADDRESS-HERE:8123'
APPS_ENTITY = 'input_select.pc_apps'
MODES_ENTITY = 'input_select.pc_modes'

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
```
* Replace the text `ENTER-HA-LONG-LIVED-TOKEN-HERE` with the token text you just copied
* Replace the text `ENTER-HA-IP-ADDRESS-HERE` with the IP address of your Home Assistant server
* Save and close the file `PC2HASS.py`

####  Generate Monitor Configurations
* In Windows setup your display(s) to a configuration that you would like to use
  * Resolutions, Duplicate, Extended, DIsabled, Positions, etc.
* Open a command prompt and navigate to the PC2HASS directory
* Enter the command `MonitorSwitcher.exe -save:\screens\CONFIG.xml`, replacing `CONFIG` with a name for your current configuration
* Repeat for each different display configuration you would like to have

#### Place Application Shortcuts (Optional)
Place shortcuts to any applications you would like to launch from HA in the `\apps` folder inside the PC2HASS folder
* Shortcuts can be `.lnk` or `.url` files only

#### Home Assistant Configuration
Within Home Assistant add the following to your `configuration.yaml` file:
* Entities for the display switcher and application launcher 
```
input_select:
  pc_modes:
    options:
      - none
    name: PC Video Modes
    initial: none
  pc_apps:
    options:
      - none
    name: PC Applications
    initial: none
```
* Rest commands to refresh the two enities and execute the requests
```
rest_command:
    set_pc_mode:
      url: 'http://ENTER-WINDOWS-PC-IP:17017/'
      method: POST
      content_type: 'application/json'
      payload: '{"cmd": "pcres_load", "data": "{{ newres }}"}'

    set_pc_app:
      url: 'http://ENTER-WINDOWS-PC-IP:17017/'
      method: POST
      content_type: 'application/json'
      payload: '{"cmd": "pcapp_load", "data": "{{ newapp }}"}'

    get_pc_modes:
      url: 'http://ENTER-WINDOWS-PC-IP:17017'
      method: POST
      content_type: 'application/json'
      payload: '{"cmd": "pcres_list"}'

    get_pc_apps:
      url: 'http://ENTER-WINDOWS-PC-IP:17017'
      method: POST
      content_type: 'application/json'
      payload: '{"cmd": "pcapps_list"}'
```
* Change `ENTER-WINDOWS-PC-IP` to the IP address of your Windows PC

#### Home Assistant Automations
Within Home Assistant add the following to your `automations.yaml` file:
* Refresh the display options/state and the apps options every 5 minutes
```
- id: 'loadpcmodes'
  alias: load_pcmodes
  description: ''
  trigger:
  - event: start
    platform: homeassistant
  - minutes: /5
    platform: time_pattern
  condition: []
  action:
  - service: rest_command.get_pc_modes
- id: 'loadpcapps'
  alias: load_pcapps
  description: ''
  trigger:
  - event: start
    platform: homeassistant
  - minutes: /5
    platform: time_pattern
  condition: []
  action:
  - service: rest_command.get_pc_apps
```
* Command the PC when the display or application is selected
```
- id: 'changepcres'
  alias: change_pcres
  description: ''
  trigger:
  - entity_id: input_select.pc_modes
    platform: state
  condition:
  - condition: template
    value_template: '{{ trigger.from_state.state != trigger.to_state.state }}'
  action:
  - service: rest_command.set_pc_mode
    data_template:
      newres: '{{ trigger.to_state.state }}'
- id: 'changepcapp'
  alias: change_pcapp
  description: ''
  trigger:
  - entity_id: input_select.pc_apps
    platform: state
  condition:
  - condition: template
    value_template: '{{ trigger.from_state.state != trigger.to_state.state }}'
  action:
  - service: rest_command.set_pc_app
    data_template:
      newapp: '{{ trigger.to_state.state }}'
```