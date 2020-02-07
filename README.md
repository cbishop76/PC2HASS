# PC2HASS

PC2HASS is a Python program that can control a Windows PC from Home Assistant.
* Switch between different display configuration of a Windows PC from Home Assistant.  Unlimited combinations of:
  * Different resolutions
  * Multi-monitor setups (#, left, right, extended, duplicate)
* Launch Windows applications and websites from Home Assistant   


*-Thank-you to Martin (martink84) at Sourceforge for the MonitorSwitcher component-*  

*Before using this software, please refer to the security cautions at the end of this guide.*  

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
Download the PC2HASS zip file and extract it to a known location on your Windows drive.

Download Monitor Profile Switcher from https://sourceforge.net/projects/monitorswitcher/ and extract the file `MonitorSwitcher.exe` to the same folder that you have `PC2HASS.py` in.


## Setup
### Access Token
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

###  Generate Monitor Configurations
* In Windows setup your display(s) to a configuration that you would like to use
  * Resolutions, Duplicate, Extended, Disabled, Positions, etc.
* Open a command prompt and navigate to the PC2HASS directory
* Enter the command `MonitorSwitcher.exe -save:\screens\CONFIG.xml`, replacing `CONFIG` with a name for your current configuration
* Repeat for each different display configuration you would like to have

### Place Application Shortcuts (Optional)
Place shortcuts to any applications you would like to launch from HA in the `\apps` folder inside the PC2HASS folder
* Shortcuts can be `.lnk` or `.url` files only

### Home Assistant Configuration
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

### Home Assistant Automations
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
### Startup
* Double-click PC2HASS.py on the Windows PC to launch it
* Restart Home Assistant for the changes to take effect

## Simple Usage

### Lovelace Drop Down Box
Within Home Assistant you may add the entities to your lovelace file to create drop-down selection boxes:
```
- entity: input_select.pc_modes
- entity: input_select.pc_apps
```
![alt text](https://github.com/cbishop76/PC2HASS/raw/master/lovelace_pc2hass.png "lovelace example for pc2hass")  
*The Display Modes will update the current display state every 5 minutes.  If the current Windows display state matches one of the saved xml files, it will display that.  If no match is found it will display "Unknown".*  
*The Applications will always revert back to "Select Application" after 5 minutes however a choice may be selected at any time.*  
*Due to a bug in Home Assistant, the icon cannot for the input_select cannot be changed.*  


## Script Usage

Add an additional rest command in `configuration.yaml'
E.g. This one would activate the "TV Only - 4k.xml" profile.
Change the xml filename to suit any profile you have saved.
```
rest_command:
    pc_4k:
      url: 'http://ENTER-WINDOWS-PC-IP:17017/'
      method: POST
      content_type: 'application/json'
      payload: '{"cmd": "pcres_load", "data": "TV Only - 4k.xml"}'
```
Then add use the rest_command in your script or automation.

## Mini-Media Player Example
The buttons on the Mini-Media Player card shown above https://github.com/kalkih/mini-media-player were created with script(s) and additional `rest_command` (s)  

As an **example**, this is the lovelace code for the entire card above:
```
  - type: entities
    show_header_toggle: false
    entities:    
      - entity: media_player.ht_tv
        type: 'custom:mini-media-player'
        name: Home Theatre TV
        icon: 'mdi:television'
        group: true
        sound_mode: full
        hide:
          power_state: false
          sound_mode: false
          volume: true
		  
      - entity: media_player.avr_theatre
        type: 'custom:mini-media-player'
        name: Home Theatre
        icon: 'mdi:speaker'
        group: true
        hide:
          power_state: false
        shortcuts:
          columns: 6
          buttons:
            - image: /local/keyboard-multi_monitor.svg
              id: script.1579297159939
              type: script
            - image: /local/keyboard-4K_TV.svg
              id: script.1580231972116
              type: script
            - icon: 'mdi:disc'
              id: script.1579298837575
              type: script
            - icon: 'mdi:cast'
              id: script.1579306601961
              type: script
            - icon: 'mdi:playstation'
              type: script
              id: script.1579666236032
            - icon: 'mdi:close-box-multiple-outline'
              id: script.1579287391667
              type: script
			  
      - entity: input_select.pc_modes
      - entity: input_select.pc_apps
```
*(Note, the first two buttons use a custom icon)*  

and the script in `scripts.yaml` for just the 4k button:
```
'1580231972116':
  alias: ht_pc4k
  sequence:
  - entity_id: media_player.avr_theatre
    service: media_player.turn_on
  - data:
      source: PC
    entity_id: media_player.avr_theatre
    service: media_player.select_source
  - entity_id: media_player.ht_tv
    service: media_player.turn_on
  - data:
      source: HDMI-1
    entity_id: media_player.ht_tv
    service: media_player.select_source
  - data:
      sound_mode: Computer*
    entity_id: media_player.ht_tv
    service: media_player.select_sound_mode
  - service: rest_command.pc_4k
```
*(Turns on the receiver and the tv. Sets the receiver input. Sets the TV video mode. Sets the PC to 4k TV Only.)*  

## Security
The Python HttpServer https://docs.python.org/2/library/simplehttpserver.html used in this software is very basic, and not intended for production.  It only implments basic security checks.

Also of note, the application launcher runs windows commands sent to it over port 17017.  Normally this would be unacceptably dangerous, however to prevent unauthorized commands, it will only execute a command if the name received matches the name of a file present in the \apps directory of the installation.  Any attempt to escape this directory, or pass any arguments will fail this check.

**Please do not use this on a PC that is exposed directly (without a firewall) to the internet.**

**In addition it is recomended you set your PC to block all incoming requests to port 17017 except those coming from the IP address of your Home Assistant server.**

## License
 PC2HASS - Windows PC to Home Assistant Interface for Display Settings and Application Launching  
    Copyright (C) 2020  <Curtis Bishop>
    https://github.com/cbishop76/PC2HASS/blob/master/PC2HASS.py

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>
