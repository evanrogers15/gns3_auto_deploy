import requests
import json
import telnetlib
import time
import socket

from modules.gns3.gns3_actions import *
def appneta_cli_commands(server_ip, console_port, node_name, appn_password):
    tn = telnetlib.Telnet(server_ip, console_port)
    user = "admin"
    tn.write(b"\r\n")
    while True:
        tn.write(b"\r\n")
        tn.read_until(b"login:", timeout=1)
        tn.write(user.encode("ascii") + b"\n")
        output = tn.read_until(b"Password:", timeout=3)
        if b"Password:" in output:
            tn.write(appn_password.encode("ascii") + b"\n")
            break
        log_and_update_db(server_ip, 'project_name', "deployment_type", 'Running',
                              deployment_step,
                              f"{node_name} not available yet, trying again in 30 seconds")
        time.sleep(30)
    tn.read_until(b"admin@vk25")
    tn.write(b'echo "vk35-r01" > /var/lib/pathview/ma-platform.force\n')
    tn.write(b'sudo reboot\n')
    tn.write(appn_password.encode("ascii") + b"\n")
    tn.read_until(b"$ ")
    tn.close()


def appneta_cli_curl_commands(server_ip, console_port, node_name, appn_password, mp_ip_address, appn_site_key, appn_url):
    tn = telnetlib.Telnet(server_ip, console_port)
    user = "admin"
    set_eth2_command = f'curl -k -u admin:525400E00000 -X POST -H "Content-Type: application/json" -d \'{{"name": "eth2", "family": "inet", "method": "static", "address": "{mp_ip_address}", "netmask": "255.255.255.0"}}\' \'https://127.0.0.1/api/v1/interface/\''
    set_hostname_command = f'curl -k -u admin:525400E00000 -X PUT -H "Content-Type: application/json" -H "Accept: application/json" -d \'{{"hostname": "{node_name}"}}\' "https://127.0.0.1/api/v1/hostname/"'
    set_nis_command = f'curl -k -u admin:525400E00000 -X POST -H "Content-Type: application/json" -d \'{{"address": "{appn_url}", "site_key": "{appn_site_key}", "ports": "80,8080", "relay_addresses": "{appn_url}:443", "ssl": "true", "protocol": "TCP"}}\' "https://127.0.0.1/api/v1/nis/?restart_services=true"'
    set_password_command = f'curl -k -u admin:525400E00000 -X PUT -H "Content-Type: application/json" -H "Accept: application/json" -d \'{{"password": "PW4netops!"}}\' "https://127.0.0.1/api/v1/appliance/password/"'
    tn.write(b"\r\n")
    while True:
        tn.write(b"\r\n")
        tn.read_until(b"login:", timeout=1)
        tn.write(user.encode("ascii") + b"\n")
        output = tn.read_until(b"Password:", timeout=3)
        if b"Password:" in output:
            tn.write(appn_password.encode("ascii") + b"\n")
            break
        log_and_update_db(server_ip, 'project_name', "deployment_type", 'Running',
                              deployment_step,
                              f"{node_name} not available yet, trying again in 30 seconds")
        time.sleep(30)
    tn.read_until(b"admin@vk25")
    tn.write(b'echo "vk35-r01" > /var/lib/pathview/ma-platform.force\n')
    tn.read_until(b"$ ")
    tn.write(set_eth2_command.encode('ascii') + b"\n")
    tn.read_until(b'status":')
    tn.write(set_hostname_command.encode('ascii') + b"\n")
    tn.read_until(b'status":')
    tn.write(set_eth2_command.encode('ascii') + b"\n")
    tn.read_until(b'status":')
    tn.write(b'sudo reboot\n')
    tn.write(appn_password.encode("ascii") + b"\n")
    tn.read_until(b"$ ")
    while True:
        tn.write(b"\r\n")
        tn.read_until(b"login:", timeout=1)
        tn.write(user.encode("ascii") + b"\n")
        output = tn.read_until(b"Password:", timeout=3)
        if b"Password:" in output:
            tn.write(appn_password.encode("ascii") + b"\n")
            break
        log_and_update_db(server_ip, 'project_name', "deployment_type", 'Running',
                              deployment_step,
                              f"{node_name} not available yet, trying again in 30 seconds")
        time.sleep(30)
    tn.write(set_nis_command.encode('ascii') + b"\n")
    tn.read_until(b'status":')
    tn.write(set_password_command.encode('ascii') + b"\n")
    tn.read_until(b'status":')
    tn.close()

def appneta_configure_mp(mp_ip_address, hostname, appn_site_key, appn_url, appn_mp_password):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    auth = ('admin', appn_mp_password)

    # Set the hostname
    url1 = f"https://{mp_ip_address}/api/v1/hostname/"
    data1 = {
        "hostname": hostname
    }
    response1 = requests.put(url1, headers=headers, auth=auth, json=data1, verify=False)
    print(f"{hostname} Hostname API call response: {response1.status_code}, {response1.json()}")

    # Set the NIS
    url2 = f"https://{mp_ip_address}/api/v1/nis/?restart_services=true"
    data2 = {
        # "address": "demo.pm.appneta.com",
        "address": "app-01.pm.appneta.com",
        "site_key": appn_site_key,
        "ports": "80,8080",
        "relay_addresses": f"{appn_url}:443",
        "ssl": "true",
        "protocol": "TCP",
    }
    response2 = requests.post(url2, headers=headers, auth=auth, json=data2, verify=False)
    print(f"{hostname} NIS API call response: {response2.status_code}, {response2.json()}")

    # Reboot the appliance
    url3 = f"https://{mp_ip_address}/api/v1/appliance/?action=reboot"
    data3 = {
        "body": "string"
    }
    response3 = requests.put(url3, headers=headers, auth=auth, json=data3, verify=False)
    print(f"{hostname} Host Reboot API call response: {response3.status_code}, {response3.json()}")
