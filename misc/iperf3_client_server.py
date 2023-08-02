import argparse
import subprocess
import time
import random
import socket
import fcntl
import struct
import multiprocessing
import os

def get_ip_address(interface):
    # Get the IP address of the specified interface
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ip_address = socket.inet_ntoa(fcntl.ioctl(
            sock.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', interface[:15].encode())
        )[20:24])
        return ip_address
    except IOError:
        return None

def start_iperf_server_sessions(other_clients):
    for client in other_clients:
        port = int(client['ip'].split('.')[2]) + 5200
        server_log_file = f'iperf3_server_{client["ip"]}.log'
        server_cmd = ['iperf3', '-s', '--logfile', server_log_file, '-p', str(port)]
        subprocess.Popen(server_cmd, stderr=subprocess.STDOUT, universal_newlines=True)

def start_iperf_client_sessions(other_clients, local_ip):
    port = int(local_ip.split('.')[2]) + 5200
    # Start iperf3 client sessions
    processes = []
    for client in other_clients:
        if client['ip'] != local_ip:
            bandwidth = random.randint(2, 10)
            client_log_file = f'iperf3_client_{client["ip"]}.log'
            server_log_file = f'iperf3_server_{client["ip"]}.log'
            delete_file(client_log_file)
            delete_and_recreate_file(server_log_file)
            client_cmd = ['iperf3', '-c', client['ip'], '--logfile', client_log_file, '--connect-timeout', '5', '-p', str(port), '-b', f'{bandwidth}M', '-t', '60']
            process = subprocess.Popen(client_cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            processes.append((process, client['ip']))
    for process, client_ip in processes:
        process.communicate()

def delete_and_recreate_file(file_path):
    # Delete the file if it exists and create a new empty file
    if os.path.exists(file_path):
        os.remove(file_path)
    open(file_path, 'a').close()

def delete_file(file_path):
    # Delete the file if it exists and create a new empty file
    if os.path.exists(file_path):
        os.remove(file_path)

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Start multiple iperf3 sessions.')
parser.add_argument('num_clients', type=int, help='number of iperf3 clients')
args = parser.parse_args()

# Get the IP address of eth0
eth0_ip = get_ip_address('eth0')

if eth0_ip is None:
    print('Failed to retrieve IP address of eth0. Make sure the interface exists.')
    exit()

# Generate client configurations
clients = []
for i in range(1, args.num_clients+1):
    client_ip = f'172.16.1{i:02d}.51'
    clients.append({'ip': client_ip})

# Exclude the eth0 IP address from the list of target clients
other_clients = [client for client in clients if client['ip'] != eth0_ip]

start_iperf_server_sessions(other_clients)

# Delete and recreate the log files every 5 minutes
while True:
    # Start iperf3 sessions for each client
    for client in clients:
        start_iperf_client_sessions(other_clients, eth0_ip)
    time.sleep(60)  # Sleep for 1 minute before deleting and recreating the log files
