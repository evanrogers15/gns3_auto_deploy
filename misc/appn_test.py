import telnetlib
import time

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
        print("Not Ready, try again 30 seconds...")
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
        print("Not Ready, try again 30 seconds...")
        time.sleep(30)
    tn.write(set_nis_command.encode('ascii') + b"\n")
    tn.read_until(b'status":')
    tn.write(set_password_command.encode('ascii') + b"\n")
    tn.read_until(b'status":')
    tn.close()

appneta_cli_curl_commands('100.92.8.44', '5024', 'Site-03-AppNeta-vk35', '525400E00000', '172.16.2.53', 'B9HVE-C4OF-T-H', 'app-01.pm.appneta.com')
