#/bin/bash

tee /lib/systemd/system/tap1.service << EOF
[Unit]
Description=TAP Interfaces
After=network.target
[Service]
Type=oneshot
User=root
ExecStart=/bin/sh /usr/bin/tap1.sh
[Install]
WantedBy=multi-user.target
EOF

tee /usr/bin/tap1.sh << EOF
#!/bin/bash
if [ ! -d "/sys/class/net/tap1" ];
then
/usr/bin/tunctl -t tap1
/sbin/ifconfig tap1 172.16.2.1 netmask 255.255.255.0 up
fi
EOF

chmod +x /usr/bin/tap1.sh

apt-get install -y uml-utilities

apt install -y net-tools

systemctl enable tap1.service

systemctl start tap1.service

MODULES=("requests" "json" "telnetlib" "time" "datetime" "socket" "urllib3" "ipaddress" "os" "sys" "re")

# Check if modules are installed
for MODULE_NAME in "${MODULES[@]}"
do
    if ! python -c "import $MODULE_NAME" > /dev/null 2>&1; then
        # Module is not installed, install it
        pip install $MODULE_NAME
    fi
done
