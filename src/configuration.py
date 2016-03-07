# Routers you wish to poll
ROUTERS = {'Den': '192.168.1.2',
           'Office': '192.168.1.3'}

# you can override how mac addresses appear in the table
# by placing aliases in this dict
MAC_ALIASES = {'ff:ff:ff:ff:ff:ff': 'an_alias'}

# if routers are in bridge mode, they won't have ip
# info. We'll ping the broadcast addresses here
# and use the local arp table to look up macs:ips
NET_BROADCAST_ADDRESSES = ['192.168.1.255']

# If we're pinging to get ip/arp mappings, how often to do so
PING_INTERVAL=60

# if set to false, arp will be pulled from remote routers. Otherwise,
# it will be pulled from the local machine. If you plan to pull from
# the remote routers, you'll need to set up some sort of broadcast ping
# there
USE_LOCAL_ARP = False

# how often should the threads poll the router
UPDATE_INTERVAL=30

DEBUG=False


