# PC2HASS - Windows PC to Home Assistant Interface for Display Settings and Application Launching
#    Copyright (C) <2020>  <Curtis Bishop>
#    https://github.com/cbishop76/PC2HASS/blob/master/PC2HASS.py
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>

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
    
    def do_GET(self):
        print("\n")
        #Do nothing for webpage requests, but log the attempt
        self.send_response(418)
        self.end_headers()
        self.wfile.write(b'No coffee here - move along...')
      
    def do_POST(self):

        def pcres_LOAD(rcvd_data):
            print("Load PC Display Settings - "+rcvd_data)
            files = fnmatch.filter(listdir('screens\\'),'*.xml')
            found = False
            alreadySet = False
            while files and not(found):
              file = files.pop(-1)
              if file == rcvd_data:
                  found = True
                  call(['MonitorSwitcher.exe','-save:cstate.xml'], shell=False, creationflags=CREATE_NO_WINDOW)
                  with open("cstate.xml","r") as f:
                      cur_xml = f.read()
                  with open('screens\\'+file,"r") as f:
                      chk_xml = f.read()
                  if chk_xml == cur_xml:
                      alreadySet = True
            if found and not(alreadySet):
                call(['MonitorSwitcher.exe','-load:screens\\'+rcvd_data], shell=False, creationflags=CREATE_NO_WINDOW)
                return(200)
            else:
                print('File not found or already set, not switching.')
                return(404)

        def pcapp_LOAD(rcvd_data):
            print("Load PC Application - "+rcvd_data)
            url = fnmatch.filter(listdir('apps\\'),'*.url')
            lnk = fnmatch.filter(listdir('apps\\'),'*.lnk')
            files = url + lnk
            found = False
            while files and not(found):
              file = files.pop(-1)
              if file == rcvd_data:
                  found = True
                  Popen(['apps\\'+rcvd_data],shell=True,stdin=None,stdout=None,stderr=None,close_fds=True,creationflags=DETACHED_PROCESS)
                  return(200)
            if not found:
                print('File not found, not launching.')
                return(404)

        def pcres_LIST():
            print("Send available PC Display Settings to HASS") 
            match = "Unknown"
            call(['MonitorSwitcher.exe','-save:cstate.xml'], shell=False, creationflags=CREATE_NO_WINDOW)
            with open("cstate.xml","r") as f:
                cur_xml = f.read()
            files = fnmatch.filter(listdir('screens\\'),'*.xml')
            files2 = ['Unknown'] + files
            while files and (match == "Unknown"):
                file = files.pop(-1)
                with open('screens\\'+file,"r") as f:
                    chk_xml = f.read()
                if chk_xml == cur_xml:
                    match = file
            
            headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8', 'Authorization':AUTH}

            x = {"entity_id":MODES_ENTITY,"options":files2}
            print("Sending Data - "+str(x))
            url = 'http://' + HASS_IP + '/api/services/input_select/set_options'
            payload = x
            r = requests.post(url, json=payload, headers=headers)
            print ("Response - " + str(r))

            print("Send current PC Display Settings to HASS") 
            x = {"entity_id":MODES_ENTITY,"option":match}
            print("Sending Data - "+str(x))
            url = 'http://' + HASS_IP + '/api/services/input_select/select_option'
            payload = x
            r = requests.post(url, json=payload, headers=headers)
            print ("Response - " + str(r))

            return(200)

        def pcapp_LIST():
            print("Send available PC Applications to HASS") 
            url = fnmatch.filter(listdir('apps\\'),'*.url')
            lnk = fnmatch.filter(listdir('apps\\'),'*.lnk')
            files = ['Select Application'] + url + lnk

            headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8', 'Authorization':AUTH}

            x = {"entity_id":APPS_ENTITY,"options":files}
            print("Sending Data - "+str(x))
            url = 'http://' + HASS_IP + '/api/services/input_select/set_options'
            payload = x
            r = requests.post(url, json=payload, headers=headers)
            print ("Response - " + str(r))

            return(200)

        
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        print("\n")
        print("Received - " + body.decode("utf-8"))

        response = BytesIO()
        received_json_data = json.loads(body.decode("utf-8"))
        rcvd_cmd = (received_json_data['cmd'])

        if rcvd_cmd == "pcres_load": response_code = pcres_LOAD(received_json_data['data'])
        if rcvd_cmd == "pcapp_load": response_code = pcapp_LOAD(received_json_data['data'])
        if rcvd_cmd == "pcres_list": response_code = pcres_LIST()
        if rcvd_cmd == "pcapps_list": response_code = pcapp_LIST()

        self.send_response(response_code)
        self.end_headers()
        response.write(body)
        self.wfile.write(response.getvalue())

def main():
    httpd = HTTPServer(('', 17017), SimpleHTTPRequestHandler)
    print("PC 2 Home Assistant Interface Started")
    print("PC2HASS  Copyright (C) <2020>  Curtis Bishop")
    print("This program comes with ABSOLUTELY NO WARRANTY")
    print("This is free software, and you are welcome to redistribute it under certain conditions")
    print("https://github.com/cbishop76/PC2HASS/blob/master/PC2HASS.py")
    httpd.serve_forever()


if __name__ == '__main__':
	main()
