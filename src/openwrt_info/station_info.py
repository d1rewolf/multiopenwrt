#!/usr/bin/env python
import os
import glob
import re
import paramiko
import sys
import socket
import subprocess


class Router:
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip
        self.stations = None


class Station:
    def __init__(self, list):
        o = list
        self.name = list[0]
        list = list[1:]
        parsed_vals = {}
        try:
            for line in list:          
                if line != '' and line != 'None':
                    fieldname, content = re.split(r'\t{0,}', line)
                    fieldname = fieldname.rstrip().replace(" ", "_").replace(":", "")
                    parsed_vals[fieldname.lower()] = content.lstrip().rstrip()
        except Exception as e:
            print e
            sys.exit(9)
        
        self.inactive_time = None
        self.interfaces = ""
        self.rx_bytes = 0
        self.rx_packets = 0
        self.tx_bytes = 0
        self.tx_retries = 0
        self.tx_failed = 0
        self.signal = None
        self.ip_address = None
        self.signal_avg = None
        self.tx_bitrate = None
        self.rx_bitrate = None
        self.authorized = None
        self.authenticated = None
        self.preamble = None
        self.wmm_wme = None
        self.mfp = None
        self.tdls_peer = None
        self.connected_time = None
        self.domain_name = ''

        # these keys should be the same as the field names based on testing
        different_names = ["wmm/wme"]
        for k, v in parsed_vals.iteritems():
            if k not in different_names:
                setattr(self, k, v)

        self.wmm_wme = parsed_vals["wmm/wme"]
        self.mac_address = self.name.split(" ")[1]


def collect_station_info(host, local_arp, username='root', password=''):
    dev_info_str = '''
        for x in /sys/class/net/*; do [ -L "$x/phy80211" ] && echo "${x##*/}"; done
    '''
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=username, password=password)
    wifi_interfaces = client.exec_command(dev_info_str)[1].read().split()
    # get arp table from router...if router is in bridge mode,
    # using a cron-scheduled broadcast ping is a reliable (yet
    # potentially costly in a large environment) way of getting
    # mac address->ip mappings
    arp_command = "cat /proc/net/arp | grep -v Flags| awk '{print $4, $1}'"
    if local_arp:
        return_str = subprocess.check_output(arp_command, shell=True)
    else:
        return_str = client.exec_command(arp_command)[1].read()
    # add delimeter for arp/station data
    return_str += "*&*&*&*&"
    for ifc in wifi_interfaces:
        return_str += "[[[[%s]]]]" % ifc
        output = client.exec_command("iw dev %s station dump" % ifc)[1].read()
        return_str += output

    client.close()
    return return_str


def parse_station_string(station_string, mac_aliases):
    arp_data, remote_data = station_string.split("*&*&*&*&")
    arp_dict = {}
    for line in arp_data.split("\n"):
        if line != '':
            mac, ip = line.split()
            arp_dict[mac] = ip

    stations = {}
    ifc_regex = r'\[\[\[\[([^\]]+)\]\]\]\]'
    wifi_interfaces = re.findall(ifc_regex, remote_data)
    string = re.sub(ifc_regex, '', remote_data)
    for ifc in wifi_interfaces:
        lines = [x.lstrip() for x in string.split("\n")]
        indices = [lines.index(x) for x in lines if re.search(r'Station .*(on.*)', x)]
        indices.append(None)
        for slice_idx in xrange(0, len(indices)):
            if indices[slice_idx] is not None:
                x, y = indices[slice_idx], indices[slice_idx+1]
                station = Station(lines[x:y])
                # if station record already exists, don't re-add...just add
                # this interface to that station's list of ifcs
                if station.mac_address not in stations.keys():
                    if station.mac_address in arp_dict.keys():
                        station.ip_address = arp_dict[station.mac_address]
                    if station.mac_address in mac_aliases.keys():
                        station.domain_name = mac_aliases[station.mac_address]
                    elif station.ip_address:
                        dns_info = None
                        try:
                            dns_info = socket.gethostbyaddr(station.ip_address)
                        except:
                            pass
                        if dns_info:
                            station.domain_name = dns_info[0]
                    else:
                        station.domain_name = "NOT AVAILABLE"
                    stations[station.mac_address] = station
                else:
                    stations[station.mac_address].interfaces += ":%s" % ifc
    return stations


