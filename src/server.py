#!/usr/bin/env python

from flask import Flask
from flask import render_template
from flask_bootstrap import Bootstrap
from flask_debugtoolbar import DebugToolbarExtension
from openwrt_info.station_info import parse_station_string, collect_station_info, Router
import threading
import os
import time
import platform

# load config file
CONFIG = {}
execfile("configuration.py", CONFIG)

USE_LOCAL_ARP = CONFIG["USE_LOCAL_ARP"]

if USE_LOCAL_ARP:
    assert CONFIG["PING_INTERVAL"], (
           "You must configure PING_INTERVAL if using local arp")

    def pinger():
        args = {"Darwin": "-W 1 -c 1", "Linux": "-b -W 3 -c 1"}
        while True:
            print "Pinging"
            assert len(CONFIG["NET_BROADCAST_ADDRESSES"]) > 0, (
                    "NET_BROADCAST_ADDRESSES must be configured "
                    "if using local arp")
            for broadcast in CONFIG["NET_BROADCAST_ADDRESSES"]:
                os.system("env ping %s %s 1>/dev/null 2>&1" %
                          (args[platform.system()], broadcast))
            time.sleep(CONFIG["PING_INTERVAL"])

    p = threading.Thread(target=pinger)
    p.daemon = True
    p.start()

MAC_ALIASES = CONFIG["MAC_ALIASES"]

app = Flask("OpenWRT Stations")
app.config['SECRET_KEY'] = 'dkjfkljdsf098d09f8092j4lj23l4j23lj23lj43'

Bootstrap(app)

app.debug = CONFIG["DEBUG"]

if app.debug:
    toolbar = DebugToolbarExtension(app)
    app.config['DEBUG_TB_PROFILER_ENABLED'] = True

assert len(CONFIG["ROUTERS"]) > 0, "You must configure at least one router"

routers = []
for name, ip in CONFIG["ROUTERS"].iteritems():
    routers.append(Router(name, ip))

station_info = {}

def threaded_info(ip, use_local_arp, interval, results):
    while True:
        print "Updating info for %s" % ip
        results[ip] = collect_station_info(ip, use_local_arp)
        time.sleep(interval)

assert CONFIG['UPDATE_INTERVAL'] > 0, "You must configure UPDATE_INTERVAL"

for router in routers:
    print "Starting thread for %s" % router.ip
    t = threading.Thread(target=threaded_info, 
                        args=(router.ip, 
                              USE_LOCAL_ARP, 
                              CONFIG["UPDATE_INTERVAL"], 
                              station_info))
    t.daemon = True
    t.start() 

@app.route('/')
def index():
    # wait for threads to populate first
    while len(station_info.keys()) < len(routers):
        time.sleep(1)

    for router in routers:
        station_str = station_info[router.ip]
        router.stations = parse_station_string(station_str, MAC_ALIASES)
    return render_template("bruteforcetable.html", routers=routers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', use_reloader=False)
