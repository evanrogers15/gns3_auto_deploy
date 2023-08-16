import sys
# from modules.vendor_specific_actions.versa_actions import *
from modules.gns3.gns3_dynamic_data import *
from modules.gns3.gns3_query import *
from modules.gns3.gns3_actions import *

# from modules.gns3.gns3_variables import *
# from modules.vendor_specific_actions.appneta_actions import *

server_ip = "192.168.122.1"
server_name = "mgmt"
server_port = "80"
project_name = "test"
project_id = "a6b1cd03-abf3-4830-a900-f711cf7495a3"
tap_name = ""
site_count = ""

frr_router_template_name = "frr_router_temp"

bgp_isp_count = 11

base_subnet = "1.0.0.1/24"

gns3_server_data = [{
    "GNS3 Server": server_ip, "Server Name": server_name, "Server Port": server_port, "Project Name": project_name,
    "Project ID": project_id, "Tap Name": tap_name, "Site Count": site_count, "Deployment Type": deployment_type,
    "Deployment Status": deployment_status, "Deployment Step": deployment_step
}]
switchport_count = 10

frr_router_template_data = {
    "compute_id": "local", "adapters": switchport_count, "category": "switch", "image": "frrouting/frr:latest",
    "name": frr_router_template_name, "symbol": ":/symbols/affinity/circle/blue/router2.svg", "template_type": "docker",
    "usage": "", "start_command": "", "extra_volumes": ["/etc/frr/"]
}

bgp_isp_deploy_data = {
    'bgp-router-01_deploy_data': {'x': -107, 'y': -254, 'name': 'bgp-router-01'},
    'bgp-router-02_deploy_data': {'x': -257, 'y': -104, 'name': 'bgp-router-02'},
    'bgp-router-03_deploy_data': {'x': -107, 'y': -104, 'name': 'bgp-router-03'},
    'bgp-router-04_deploy_data': {'x': 42, 'y': -104, 'name': 'bgp-router-04'},
    'bgp-router-05_deploy_data': {'x': -182, 'y': -29, 'name': 'bgp-router-05'},
    'bgp-router-06_deploy_data': {'x': -32, 'y': -29, 'name': 'bgp-router-06'},
    'bgp-router-07_deploy_data': {'x': -257, 'y': 45, 'name': 'bgp-router-07'},
    'bgp-router-08_deploy_data': {'x': -107, 'y': 45, 'name': 'bgp-router-08'},
    'bgp-router-09_deploy_data': {'x': 42, 'y': 45, 'name': 'bgp-router-09'},
    'bgp-router-10_deploy_data': {'x': -182, 'y': 120, 'name': 'bgp-router-10'},
    'bgp-router-11_deploy_data': {'x': -32, 'y': 120, 'name': 'bgp-router-11'}
}

links_template = [
    {
        'source_node_name': 'bgp-router-01', 'source_node_id': '973a04e9-22bf-4fe3-95e0-d0fad95b656f',
        'source_node_adapter': 1, 'source_node_port': 0, 'target_node_name': 'bgp-router-02',
        'target_node_id': 'bc3e5c09-b2a8-443a-96e4-c2da2f4c6773', 'target_node_adapter': 0, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-01', 'source_node_id': '973a04e9-22bf-4fe3-95e0-d0fad95b656f',
        'source_node_adapter': 2, 'source_node_port': 0, 'target_node_name': 'bgp-router-03',
        'target_node_id': '91fb8ad1-3d35-480e-bcdc-97920faf2c0e', 'target_node_adapter': 0, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-01', 'source_node_id': '973a04e9-22bf-4fe3-95e0-d0fad95b656f',
        'source_node_adapter': 3, 'source_node_port': 0, 'target_node_name': 'bgp-router-04',
        'target_node_id': '5bf77213-c783-45b0-ba6b-9806d00b83f4', 'target_node_adapter': 0, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-02', 'source_node_id': 'bc3e5c09-b2a8-443a-96e4-c2da2f4c6773',
        'source_node_adapter': 1, 'source_node_port': 0, 'target_node_name': 'bgp-router-05',
        'target_node_id': '9f562ea6-158c-47d3-924a-6a66cc6d65b1', 'target_node_adapter': 0, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-03', 'source_node_id': '91fb8ad1-3d35-480e-bcdc-97920faf2c0e',
        'source_node_adapter': 1, 'source_node_port': 0, 'target_node_name': 'bgp-router-05',
        'target_node_id': '9f562ea6-158c-47d3-924a-6a66cc6d65b1', 'target_node_adapter': 1, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-03', 'source_node_id': '91fb8ad1-3d35-480e-bcdc-97920faf2c0e',
        'source_node_adapter': 2, 'source_node_port': 0, 'target_node_name': 'bgp-router-06',
        'target_node_id': '9cc4867b-95d8-4619-a854-188aeddd0c1c', 'target_node_adapter': 0, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-04', 'source_node_id': '5bf77213-c783-45b0-ba6b-9806d00b83f4',
        'source_node_adapter': 1, 'source_node_port': 0, 'target_node_name': 'bgp-router-06',
        'target_node_id': '9cc4867b-95d8-4619-a854-188aeddd0c1c', 'target_node_adapter': 1, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-07', 'source_node_id': '72a65717-a771-4450-ba81-8130e30e60f6',
        'source_node_adapter': 0, 'source_node_port': 0, 'target_node_name': 'bgp-router-05',
        'target_node_id': '9f562ea6-158c-47d3-924a-6a66cc6d65b1', 'target_node_adapter': 2, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-08', 'source_node_id': 'ac03bee5-877d-4d2d-b2c5-120c22083e2a',
        'source_node_adapter': 0, 'source_node_port': 0, 'target_node_name': 'bgp-router-05',
        'target_node_id': '9f562ea6-158c-47d3-924a-6a66cc6d65b1', 'target_node_adapter': 3, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-08', 'source_node_id': 'ac03bee5-877d-4d2d-b2c5-120c22083e2a',
        'source_node_adapter': 1, 'source_node_port': 0, 'target_node_name': 'bgp-router-06',
        'target_node_id': '9cc4867b-95d8-4619-a854-188aeddd0c1c', 'target_node_adapter': 2, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-09', 'source_node_id': 'fa52b809-12e8-47f8-ab33-6374143ef0a5',
        'source_node_adapter': 0, 'source_node_port': 0, 'target_node_name': 'bgp-router-06',
        'target_node_id': '9cc4867b-95d8-4619-a854-188aeddd0c1c', 'target_node_adapter': 3, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-10', 'source_node_id': 'e6850857-f608-4f86-a8c1-5d035ddf623d',
        'source_node_adapter': 0, 'source_node_port': 0, 'target_node_name': 'bgp-router-07',
        'target_node_id': '72a65717-a771-4450-ba81-8130e30e60f6', 'target_node_adapter': 1, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-10', 'source_node_id': 'e6850857-f608-4f86-a8c1-5d035ddf623d',
        'source_node_adapter': 1, 'source_node_port': 0, 'target_node_name': 'bgp-router-08',
        'target_node_id': 'ac03bee5-877d-4d2d-b2c5-120c22083e2a', 'target_node_adapter': 2, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-11', 'source_node_id': 'e121596f-d07f-41b9-aa7e-20d6c7f84707',
        'source_node_adapter': 0, 'source_node_port': 0, 'target_node_name': 'bgp-router-08',
        'target_node_id': 'ac03bee5-877d-4d2d-b2c5-120c22083e2a', 'target_node_adapter': 3, 'target_node_port': 0
    }, {
        'source_node_name': 'bgp-router-11', 'source_node_id': 'e121596f-d07f-41b9-aa7e-20d6c7f84707',
        'source_node_adapter': 1, 'source_node_port': 0, 'target_node_name': 'bgp-router-09',
        'target_node_id': 'fa52b809-12e8-47f8-ab33-6374143ef0a5', 'target_node_adapter': 1, 'target_node_port': 0
    }, ]

def gns3_query_get_nodes(server_ip, server_port, project_id, return_type):
    url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes"
    response = requests.get(url)
    data = json.loads(response.text)
    nodes = {}

    if return_type == 'node_id':
        for node in data:
            node_id = node['node_id']
            name = node['name']
            nodes[node_id] = {"name": name, "node_id": node_id}
    elif return_type == 'name':
        for node in data:
            node_id = node['node_id']
            name = node['name']
            nodes[name] = {"name": name, "node_id": node_id}
    return nodes

def gns3_query_get_links(server_ip, server_port, project_id, node_name_filter):
    url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/links"
    response = requests.get(url)
    data = json.loads(response.text)
    links = []

    nodes = gns3_query_get_nodes(server_ip, server_port, project_id, 'node_id')

    for link in data:
        source_node_id = link['nodes'][0]['node_id']
        target_node_id = link['nodes'][1]['node_id']

        if source_node_id in nodes and target_node_id in nodes:
            source_node = nodes[source_node_id]
            source_node_adapter = link['nodes'][0]['adapter_number']
            source_node_port = link['nodes'][0]['port_number']
            target_node = nodes[target_node_id]
            target_node_adapter = link['nodes'][1]['adapter_number']
            target_node_port = link['nodes'][1]['port_number']

            if node_name_filter in source_node['name'] or node_name_filter in target_node['name']:
                links.append({'source_node_name': source_node['name'], 'source_node_id': source_node_id, 'source_node_adapter': source_node_adapter, 'source_node_port': source_node_port, 'target_node_name': target_node['name'], 'target_node_id': target_node_id, 'target_node_adapter': target_node_adapter, 'target_node_port': target_node_port,})

    return links

def gns3_create_links(server_ip, server_port, project_id, links_data):
    url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/links"
    existing_links = gns3_query_get_links(server_ip, server_port, project_id, "")

    for link_data in links_data:
        source_node_id = link_data['source_node_id']
        target_node_id = link_data['target_node_id']
        source_adapter = link_data['source_node_adapter']
        source_port = link_data['source_node_port']
        target_adapter = link_data['target_node_adapter']
        target_port = link_data['target_node_port']

        # Check if the link already exists in GNS3
        if {'source': source_node_id, 'target': target_node_id} in existing_links:
            print(f"Link from '{source_node_id}' to '{target_node_id}' already exists.")
            continue

        # Create the link
        link_data = {
            "nodes": [
                {"adapter_number": source_adapter, "node_id": source_node_id, "port_number": source_port},
                {"adapter_number": target_adapter, "node_id": target_node_id, "port_number": target_port}
            ]
        }

        response = requests.post(url, json=link_data)
        if response.status_code == 201:
            print(f"Link from '{source_node_id}' to '{target_node_id}' created successfully.")
        else:
            print(f"Failed to create link from '{source_node_id}' to '{target_node_id}'. Status code: {response.status_code}")

def update_links_with_new_node_ids(server_ip, server_port, project_id, links_data):
    new_nodes = gns3_query_get_nodes(server_ip, server_port, project_id, 'name')
    updated_links = []

    for link_data in links_data:
        source_node_name = link_data['source_node_name']
        target_node_name = link_data['target_node_name']
        if source_node_name in new_nodes and target_node_name in new_nodes:
            updated_source_node_id = new_nodes[source_node_name]['node_id']
            updated_target_node_id = new_nodes[target_node_name]['node_id']

            updated_link_data = {
                **link_data,
                'source_node_id': updated_source_node_id,
                'target_node_id': updated_target_node_id
            }

            updated_links.append(updated_link_data)
        else:
            print(f"Warning: Node name not found for {source_node_name} and {target_node_name}: {link_data}")

    return updated_links


def bgp_deploy():
    frr_router_template_id = gns3_create_template(gns3_server_data, frr_router_template_data)

    for i in range(1, bgp_isp_count + 1):
        node_name = f"bgp-router-{i:02}"
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, project_id, node_name)
        if not matching_nodes:
            node_id, node_name = gns3_create_node_multi_return(gns3_server_data, project_id, frr_router_template_id,
                                                               bgp_isp_deploy_data [f"bgp-router-{i:02}_deploy_data"])

    updated_links_data = update_links_with_new_node_ids(server_ip, server_port, project_id, links_template)
    gns3_create_links(server_ip, server_port, project_id, updated_links_data)
    gns3_start_all_nodes(gns3_server_data, project_id)
    time.sleep(15)
    gns3_stop_all_nodes(gns3_server_data, project_id)
    matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, project_id, "bgp-router")
    i = 1
    if matching_nodes:
        for matching_node in matching_nodes:
            node_id = matching_node[0]
            temp_file_name = f'bgp/bgp-router-{i:02}'
            daemons_file_name = "bgp/daemons"
            gns3_upload_file_to_node(gns3_server_data, project_id, node_id, "etc/frr/daemons", daemons_file_name)
            gns3_upload_file_to_node(gns3_server_data, project_id, node_id, "etc/frr/frr.conf", temp_file_name)
            i += 1

bgp_deploy()
