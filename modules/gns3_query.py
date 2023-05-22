import requests

def get_computes_name(server, port):
    url = f"http://{server}:{port}/v2/computes"
    response = requests.get(url)
    if not response.ok:
        print(f"Error retrieving compute servers: {response.status_code}")
        exit()
    try:
        compute_info = response.json()
        server_name = compute_info[0]['name']
        return server_name
    except (ValueError, IndexError) as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response content: {response.content}")
        exit()

def get_projects(server, port):
    url = f"http://{server}:{port}/v2/projects"
    response = requests.get(url)
    if not response.ok:
        print(f"Error retrieving links: {response.status_code}")
        exit()
    try:
        projects = response.json()
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response content: {response.content}")
        exit()
    return projects

def get_nodes(server, port, project_id):
    url = f"http://{server}:{port}/v2/projects/{project_id}/nodes"
    response = requests.get(url)
    if not response.ok:
        print(f"Error retrieving links: {response.status_code}")
        exit()
    try:
        nodes = response.json()
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response content: {response.content}")
        exit()
    return nodes

def get_links(server, port, project_id, node_id):
    url = f"http://{server}:{port}/v2/projects/{project_id}/nodes/{node_id}/links"
    response = requests.get(url)
    if not response.ok:
        print(f"Error retrieving links: {response.status_code}")
        exit()
    try:
        links = response.json()
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response content: {response.content}")
        exit()
    return links

def find_node_by_name(nodes, node_name=None):
    if node_name:
        for node in nodes:
            if node['name'] == node_name:
                node_id = node['node_id']
                console = node['console']
                aux = node['properties'].get('aux')
                return node_id, console, aux
        print(f"Node '{node_name}' not found.")
    else:
        nuttcp_nodes = [node for node in nodes if 'NutTCP-Client' in node['name']]
        if not nuttcp_nodes:
            print("No nodes named with 'NutTCP' found.")
        else:
            print("Available nodes:")
            for i, node in enumerate(nuttcp_nodes):
                print(f"{i+1}. {node['name']}")
            selected_num = int(input("Enter the number of the node to select: "))
            selected_node = nuttcp_nodes[selected_num - 1]
            node_id = selected_node['node_id']
            console = selected_node['console']
            aux = selected_node['properties'].get('aux')
            return node_id, console, aux
    return None, None, None

def find_nodes_by_name(nodes, search_string=None):
    if search_string:
        matching_nodes = [node for node in nodes if search_string in node['name']]
        if not matching_nodes:
            print(f"No nodes with '{search_string}' in their name were found.")
        else:
            return [(node['node_id'], node['console'], node['properties'].get('aux')) for node in matching_nodes]
    else:
        print("Please provide a search string to filter nodes by name.")
        return []

def get_node_links_interactive(nodes, links, server, port, project_id, node_id, node_name):
    link_numbers = []
    seen_node_ids = set()
    for link in links:
        node_labels = []
        for node in link["nodes"]:
            node_labels.append(node["label"]["text"])
        link_id = link['link_id']
        link_url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
        response = requests.get(link_url)
        link_data = response.json()
        for endpoint in link_data['nodes']:
            endpoint_node_id = endpoint['node_id']
            if endpoint_node_id == node_id:
                endpoint_port_number = endpoint['port_number']
                remote_node_id = [n['node_id'] for n in link_data['nodes'] if n['node_id'] != node_id][0]
                for node in nodes:
                    if node['node_id'] == remote_node_id and node['node_id'] not in seen_node_ids and 'ISP' in node['name']:
                        index = nodes.index(node)
                        message = f"{len(link_numbers)+1}. Link connects {node_labels[0]} on {node_name} to {node_labels[1]} on {node['name']}"
                        print(message)
                        link_numbers.append(link_id)
                        seen_node_ids.add(node['node_id'])
                        break
    if not link_numbers:
        print(f"No links found for node {node_id} ({node_name})")

    # Add an option to exit back to the previous menu
    message = f"{len(link_numbers)+1}. Go back to previous menu"
    print(message)

    # Prompt the user for input
    selected_link_id = input("Enter the number of the link you want to select: ")
    while not selected_link_id.isdigit() or int(selected_link_id) < 1 or int(selected_link_id) > len(link_numbers) + 1:
        print("Invalid selection.")
        selected_link_id = input("Enter the number of the link you want to select: ")

    # Return the selected link ID or None if the user chooses to go back
    selected_link_id = int(selected_link_id)
    if selected_link_id == len(link_numbers) + 1:
        return None, True
    else:
        return link_numbers[selected_link_id - 1], False

def get_node_links(nodes, links, server, port, project_id, node_id, node_name, remote_node_id=None):
    link_numbers = []
    seen_node_ids = set()
    for link in links:
        node_labels = []
        for node in link["nodes"]:
            node_labels.append(node["label"]["text"])
        link_id = link['link_id']
        link_url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
        response = requests.get(link_url)
        link_data = response.json()
        for endpoint in link_data['nodes']:
            endpoint_node_id = endpoint['node_id']
            if endpoint_node_id == node_id:
                endpoint_port_number = endpoint['port_number']
                if remote_node_id:
                    if any(n['node_id'] == remote_node_id for n in link_data['nodes']):
                        link_numbers.append(link_id)
                        break
                else:
                    remote_node_id = [n['node_id'] for n in link_data['nodes'] if n['node_id'] != node_id][0]
                for node in nodes:
                    if node['node_id'] == remote_node_id and node['node_id'] not in seen_node_ids:
                        index = nodes.index(node)
                        link_numbers.append(link_id)
                        seen_node_ids.add(node['node_id'])
                        break
    if not link_numbers:
        return None
    print(link_numbers)
    return link_numbers[0]