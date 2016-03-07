multiopenwrt is a utility used to provide visibility across multiple openwrt routers. 
In my situation, I have three different openwrt routers each sharing the same
SSID. It became cumbersome to track clients as they moved between routers,
so I wanted an easy way to quickly see associated stations across all routers.

In this initial implementation, I assume you've copied an ssh key to the 
authorized_keys for root on the openwrt routers. Then from one of my other machines,
 after adding the key/passphrase to the shell's ssh-agent (after insuring it's running),
cd into the src/ directory and run python ./server.py. This launches a flask server 
which should be accessible on http://<yourip>:5000.

I will likely add more information in the future. Hope you find it useful.

Configuration is done by editing src/configuration.py. You should also change app.config["SECRET_KEY"]
in server.py. I'll move this to the configuration file soon.

