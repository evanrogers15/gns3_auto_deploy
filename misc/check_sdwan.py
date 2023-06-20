import requests
import json
import sys
import time
import urllib3
import argparse
from datetime import datetime, timedelta

from twilio.rest import Client

# Twilio configuration
account_sid = 'AC029f41d2998f49c28ca2b1e6e479c294'
auth_token = '21ff0d127d9a8c3ddc2d2fe5faba4f63'
twilio_number = '+18665169489'
my_number = '6629107991'

client = Client(account_sid, auth_token)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

servers = {
    "servers": [
        {
            "server_ip": "10.142.0.81",
            "gns3_server": "10.142.0.81",
            "server_port": "80",
            "server_name": "oa-gns3-01",
            "project_id": "900d5fc8-1c47-45dc-92f4-8a7d7471c2fb",
            "vmanage_id": "38dd1050-a608-4888-b493-8d93159bfcb0"
        },
    ]
}

servers_test = {
    "servers": [
        {
            "server_ip": "100.92.8.44",
            "gns3_server": "100.92.8.44",
            "server_port": "80",
            "server_name": "er-test-lab-02",
            "project_id": "80a0ad29-9280-4891-b544-8e0ddb44dee4",
            "vmanage_id": "82a2feeb-b777-48d2-be6c-8fe4b6c5c71e"
        }
    ]
}


def check_and_reboot(restart=False):
    for server in servers['servers']:
        url = f"https://{server['gns3_server']}:443/j_security_check"
        payload = {'j_username': 'view_only', 'j_password': 'CAdemo@123'}
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        try:
            response = requests.post(url, data=payload, headers=headers, verify=False, timeout=10)
            response.raise_for_status()
            jsessionid_cookie = response.cookies.get('JSESSIONID')
        except requests.exceptions.RequestException as e:
            print(f"Server {server['server_name']} not available: {str(e)}")
            message = client.messages.create(to=my_number, from_=twilio_number,
                                             body=f"Server {server['server_name']} not available.")
            print("Message sent:", message.sid)
            if restart:
                print(f"Restarting vManage node on server {server['server_name']}")
                restart_vmanage_node(server['gns3_server'], server['server_port'], server['project_id'],
                                     server['vmanage_id'])
                message = client.messages.create(to=my_number, from_=twilio_number,
                                                 body=f"Server {server['server_name']} was restarted.")
                print("Message sent:", message.sid)
            continue
        if jsessionid_cookie:
            url = f"https://{server['gns3_server']}:443/dataservice/device"
            headers = {'Cookie': f'JSESSIONID={jsessionid_cookie}'}
            response = requests.get(url, headers=headers, verify=False)
            if 'Access Forbidden' in response.text:
                print(f"Login failed for server {server['server_name']}")
                message = client.messages.create(to=my_number, from_=twilio_number,
                                                 body=f"Login failed for server {server['server_name']}")
                print("Message sent:", message.sid)
                if restart:
                    print(f"Restarting vManage node on server {server['server_name']}")
                    restart_vmanage_node(server['gns3_server'], server['server_port'], server['project_id'],
                                         server['vmanage_id'])
                    message = client.messages.create(to=my_number, from_=twilio_number,
                                                     body=f"Server {server['server_name']} was restarted.")
                    print("Message sent:", message.sid)
            else:
                print(f"Login successful for server {server['server_name']}")
        else:
            print(f"JSESSIONID cookie not found in response for server {server['server_name']}")


def restart_vmanage_node(server_ip, server_port, project_id, node_id):
    # GNS3 API configuration
    api_url = f"http://{server_ip}:{server_port}/v2"
    # Stop Node
    node_url = f"{api_url}/projects/{project_id}/nodes/{node_id}/stop"
    stop_node_response = requests.post(node_url)
    if stop_node_response.status_code == 200:
        print(f"Node {node_id} stopped successfully.")
    else:
        print(f"Failed to stop node {node_id}. Status code: {stop_node_response.status_code}")
        return
    time.sleep(5)
    # Start Node
    node_url = f"{api_url}/projects/{project_id}/nodes/{node_id}/start"
    start_node_response = requests.post(node_url)
    if start_node_response.status_code == 200:
        print(f"Node {node_id} restarted successfully.")
    else:
        print(f"Failed to restart node {node_id}. Status code: {start_node_response.status_code}")
        return


def get_next_run_time():
    now = datetime.now()
    next_run = now + timedelta(minutes=30)
    return next_run.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--restart', action='store_true', help='Restart vManage nodes')
    args = parser.parse_args()

    while True:
        check_and_reboot(restart=args.restart)  # Pass restart argument to the function
        print("Waiting for next run at", get_next_run_time())
        for i in range(30):
            time.sleep(60)  # Wait for 1 minute
            print(f"Next run in {30 - i} minutes and {60 - time.localtime().tm_sec} seconds")

