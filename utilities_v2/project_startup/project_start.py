import subprocess

def run_command(cmd):
    """
    Runs the given command in a subprocess.
    """
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f"Error executing command: {cmd}")
        print(stderr.decode())
    else:
        print(stdout.decode())

def main():
    commands = [
        "python3 start_nodes_utility.py 192.168.122.1 80 bgp_core_versa_01 start bgp,isp,Versa,FlexVNF,sw-core,sw-dist,sw-acc,Client,Server,vk35,Tix",
        "python3 latency_utility.py 192.168.122.1 80 bgp_core_versa_01 add bgp",
        "python3 traffic_control_utility.py 192.168.122.1 80 bgp_core_versa_01 start Client",
        "python3 start_nodes_utility.py 192.168.122.1 80 bgp_core_versa_01 start ISP_Router",
        "python3 isp_route_utility.py 192.168.122.1 80 bgp_core_versa_01 ISP_Router",
    ]

    for cmd in commands:
        print(f'Running command {cmd}..')
        run_command(cmd)

if __name__ == "__main__":
    main()
