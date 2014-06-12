import requests
import json 
import yaml
import time
import cwiid
import sys
import daemon
import lockfile

api_key = None
server = None
config = None
bindings = None
wm = None
profile = None

configfile = 'octowii.yaml';

buttons = { 
    'BTN_RIGHT',
    'BTN_LEFT',
    'BTN_UP',
    'BTN_DOWN',
    'BTN_1',
    'BTN_2',
    'BTN_PLUS',
    'BTN_MINUS',
    'BTN_A',
    'BTN_B',
    'BTN_HOME',
}

blinkpattern = 0;

def gcode_send(addr, apikey, code):
    payload = { 'command' : code } 
    headers = { 
        'X-Api-Key' : apikey, 
        'content-type': 'application/json' 
        }
    r = requests.post(addr, 
                  data = json.dumps(payload), 
                  headers = headers)

def conf_read(path, profile=None):
    global config, bindings, server, apikey, blinkpattern
    stream = file(path, 'r')
    y = yaml.load(stream)
    if not 'default_profile' in y:
        print("default_profile not set, exiting")

    if (profile == None):
        profile = y['default_profile']

    config = y

    bindings     = y[profile]['bindings']
    server       = y[profile]['server']
    apikey       = y[profile]['apikey']
    blinkpattern = y[profile]['blinkpattern']
    print("Switching to profile " + profile)

def check_key(key):
    global config, configfile, bindings, server, apikey
    if bool(wm.state['buttons'] & getattr(cwiid, key)):
        if 'gcode' in (bindings[key]):
            for g in bindings[key]['gcode']:
                gcode_send(server + '/api/printer/command', apikey, g)
        if 'profile' in (bindings[key]):
            conf_read(configfile, bindings[key]['profile'])

def handle_wii_message(mesg_list, time):
    global buttons;
    for b in buttons:
        check_key(b)

def do_blink_pattern(p):
    global wm;
    wm.led = 0;
    time.sleep(1)
    wm.led = int(p);
    time.sleep(1)

def main():
    global wm, blinkpattern;
    while True:
        try:
            wm = cwiid.Wiimote()
            wm.rumble = 1;
            time.sleep(0.5);
            wm.rumble = 0;
            
            wm.rpt_mode = cwiid.RPT_BTN | cwiid.RPT_STATUS;
            wm.enable(cwiid.FLAG_MESG_IFC);
            wm.led = 4;
            wm.mesg_callback = handle_wii_message;
            while True:
                print(blinkpattern);
                do_blink_pattern(blinkpattern)
        except (RuntimeError, AttributeError):
            pass


conf_read(configfile)
if (config['daemon']):
    context = daemon.DaemonContext(
    working_directory='/tmp',
    umask=0o002,
    pidfile=lockfile.FileLock(config['pidfile']),
    )
    with context:
        main()  
else:
    main()



 

