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
import logging

logger = logging.getLogger('multiwrt')
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
            logger.info("Pinging")
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
app.config['SECRET_KEY'] = 'dkjfasdfasdfsdfj9iu8908234234j23lj23lj43'

Bootstrap(app)

app.debug = CONFIG["DEBUG"]

if app.debug:
    toolbar = DebugToolbarExtension(app)
    app.config['DEBUG_TB_PROFILER_ENABLED'] = True

assert len(CONFIG["ROUTERS"]) > 0, "You must configure at least one router"

routers = []
poll_errors = {}
for name, ip in CONFIG["ROUTERS"].iteritems():
    routers.append(Router(name, ip))
    poll_errors[ip] = False

station_info = {}

def threaded_info(ip, use_local_arp, interval, results):
    while True:
        logger.info("Updating info for %s" % ip)
        try:
            results[ip] = collect_station_info(ip, use_local_arp)
            poll_errors[ip] = False
        except Exception as e:
            poll_errors[ip] = True
            print "Error trying to collect %s" % ip
        time.sleep(interval)

assert CONFIG['UPDATE_INTERVAL'] > 0, "You must configure UPDATE_INTERVAL"

for router in routers:
    logger.info("Starting thread for %s" % router.ip)
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
    #while len(station_info.keys()) < len(routers):
        #print "Waiting for station information..."
        #time.sleep(1)

    for router in routers:
        if router.ip in station_info.keys():
            station_str = station_info[router.ip]
            router.stations = parse_station_string(station_str, MAC_ALIASES)
    return render_template("bruteforcetable.html", routers=routers, poll_errors=poll_errors)

if __name__ == '__main__':
    app.run(host='0.0.0.0', use_reloader=False)
