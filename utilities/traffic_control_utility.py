import requests
import telnetlib

def list_projects(server, port):
    response = requests.get(f"http://{server}:{port}/v2/projects")
    response.raise_for_status()
    return response.json()

def list_nodes(server, port, project_id):
    response = requests.get(f"http://{server}:{port}/v2/projects/{project_id}/nodes")
    response.raise_for_status()
    return response.json()

def run_telnet_command(host, port, command):
    tn = telnetlib.Telnet(host, port)
    tn.write(b"\n")
    tn.read_until(b"#")
    tn.write(command.encode('ascii') + b"\n")
    output = tn.read_until(b"#", timeout=5).decode('ascii')
    tn.write(b"\n")
    tn.close()
    return output

def main():
    server = input("Enter the GNS3 server address: ")
    port = input("Enter the GNS3 server port: ")

    projects = list_projects(server, port)
    for idx, project in enumerate(projects):
        print(f"{idx}. {project['name']}")

    project_idx = int(input("Select a project by entering its index: "))
    selected_project = projects[project_idx]

    action = input("Do you want to start or stop traffic generation? (start/stop) ")
    if action == "start":
        command = f"python3 /home/scripts/traffic_generator.py sites 4 20,21,25,80,443,3389 &"
    elif action == "stop":
        command = f"pkill -f 'traffic_generator\.py|iperf3'"

    node_name_portion = input("Enter the portion of the node name to filter nodes: ")

    nodes = list_nodes(server, port, selected_project['project_id'])
    filtered_nodes = [node for node in nodes if node_name_portion in node['name']]

    for node in filtered_nodes:
        console_port = node['properties']['aux']
        output = run_telnet_command(server, console_port, command)
        print(f"Output for {node['name']}:\n{output}")

if __name__ == "__main__":
    main()

