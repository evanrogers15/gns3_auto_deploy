import subprocess
import sys
import time

def start_iperf3_servers(num_servers, start_port):
    servers = []
    for i in range(num_servers):
        port = start_port + i
        server = subprocess.Popen(['iperf3', '-s', '-p', str(port)])
        servers.append(server)
    return servers

def check_servers(servers):
    for server in servers:
        if server.poll() is not None:
            print(f"Server {server.pid} not responding, restarting...")
            new_server = subprocess.Popen(['iperf3', '-s', '-p', str(server.args[-1])])
            servers[servers.index(server)] = new_server

if __name__ == '__main__':
    # Ping command to run for 5 seconds
    ping_cmd = f'ping 192.168.122.1 -c 1 -W 1 -q > /dev/null && sleep 5 || exit 1'
    # Run the ping command in a subprocess
    ping_proc = subprocess.Popen(ping_cmd, shell=True)
    if len(sys.argv) > 2:
        print("Usage: python3 script.py [<num_servers>]")
        sys.exit(1)
    if len(sys.argv) == 2:
        try:
            num_servers = int(sys.argv[1])
        except ValueError:
            print("Error: <num_servers> must be an integer")
            sys.exit(1)
    else:
        num_servers = 5
    start_port = 5201
    servers = start_iperf3_servers(num_servers, start_port)
    while True:
        time.sleep(5)
        check_servers(servers)
