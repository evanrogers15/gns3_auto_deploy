import requests
import time


def get_project_id(base_url, project_name):
    # Fetch the list of projects
    response = requests.get(f"{base_url}/projects")
    response.raise_for_status()

    projects = response.json()
    for project in projects:
        if project["name"] == project_name:
            return project["project_id"]

    raise Exception(f"No project found with name {project_name}")


def get_matching_nodes(base_url, project_id, match_string):
    response = requests.get(f"{base_url}/projects/{project_id}/nodes")
    response.raise_for_status()

    nodes = response.json()
    return [node for node in nodes if match_string in node["name"]]


def start_or_stop_node(base_url, project_id, node_id, action):
    response = requests.post(f"{base_url}/projects/{project_id}/nodes/{node_id}/{action}")
    response.raise_for_status()

    # Wait until node has started or stopped successfully
    while True:
        time.sleep(1)
        node_status = requests.get(f"{base_url}/projects/{project_id}/nodes/{node_id}").json()
        if action == "start" and node_status["status"] == "started":
            break
        elif action == "stop" and node_status["status"] == "stopped":
            break


if __name__ == "__main__":
    # Get server details and criteria from user
    server_ip = input("Enter server IP: ")
    server_port = input("Enter server port: ")
    base_url = f"http://{server_ip}:{server_port}/v2"

    project_name = input("Enter project name: ")
    match_strings = input("Enter comma-separated strings to match nodes: ").split(',')

    # Get project ID
    project_id = get_project_id(base_url, project_name)

    # Ask user for action
    action = input("Do you want to start or stop the matching devices? (start/stop): ").strip().lower()
    if action not in ["start", "stop"]:
        print("Invalid choice.")
        exit()

    for match_string in match_strings:
        match_string = match_string.strip()  # Remove any spaces

        # Get nodes matching the current string
        matching_nodes = get_matching_nodes(base_url, project_id, match_string)
        if not matching_nodes:
            print(f"No nodes found matching string '{match_string}'.")
            continue

        # Start or stop nodes
        for node in matching_nodes:
            print(f"{action.capitalize()}ing {node['name']}...")
            start_or_stop_node(base_url, project_id, node["node_id"], action)
            print(f"{node['name']} {action}ed successfully.")
