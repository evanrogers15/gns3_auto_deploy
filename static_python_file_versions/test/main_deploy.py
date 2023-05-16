import requests
from flask import Flask, jsonify, abort, make_response, request, render_template, Response
import json
import telnetlib
import time
import datetime
import socket
import urllib3
import ipaddress
import os
import sys
import re
import app_config
import threading
import logging
import logging.handlers

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

processes = {}

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index_1.html')

@app.route('/create_sdwan')
def create_sdwan():
    logging.basicConfig(filename='app_viptela.log', level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    log_content = ""
    with open('app_viptela.log', 'r') as log_file:
        for line in log_file:
            if "Deploy" in line:
                log_content += line
    return render_template('create_sdwan.html', log_content=log_content)

@app.route('/create_arista_evpn')
def create_arista_evpn():
    logging.basicConfig(filename='app_evpn.log', level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    log_content = ""
    with open('app_evpn.log', 'r') as log_file:
        for line in log_file:
            if "Deploy" in line:
                log_content += line
    return render_template('create_arista_evpn.html', log_content=log_content)

@app.route('/api/get_log_content/evpn', methods=['GET'])
def get_log_content_evpn():
    log_content = ""
    with open('app_evpn.log', 'r') as log_file:
        for line in log_file:
            if "Deploy" in line:
                log_content += line
    return log_content

@app.route('/api/get_log_content/viptela', methods=['GET'])
def get_log_content_viptela():
    log_content = ""
    with open('app_viptela.log', 'r') as log_file:
        for line in log_file:
            if "Deploy" in line:
                log_content += line
    return log_content

@app.route('/api/create_project', methods=['POST'])
def create_project():
    with open('app.log', 'w'):
        pass
    server_ip = request.json['server_ip']
    server_port = request.json['server_port']
    project_name = request.json['project_name']
    vmanage_api_ip = request.json['vmanage_api_ip']
    site_count = request.json['site_count']
    site_count = int(site_count)
    tap_name = request.json['tap_name']
    use_tap = request.json['use_tap']
    server_data = [{
        "GNS3 Server": server_ip,
        "Project Name": project_name,
        "vManage API IP": vmanage_api_ip,
        "Site Count": site_count,
        "Tap Name": tap_name,
        "Use Tap": use_tap,
        "Server Name": "er-test-01",
        "Server Port": server_port,
    }]
    logging.info(server_data)
    threading.Thread(target=viptela_deploy, args=(server_data,)).start()
    # deploy_sdwan(new_project_id, server_data)
    # return jsonify([server_data])
    return make_response(jsonify({'Deployment Started Successfully'}), 200)


@app.route('/api/deploy_sdwan', methods=['POST'])
def deploy_sdwan():
    server_ip = request.json['server_ip']
    server_port = request.json['server_port']
    project_name = request.json['project_name']
    template_data = {"name": project_name}
    node_url = f"http://{server_ip}:{server_port}/v2/projects"
    node_response = make_request("POST", node_url, data=template_data)
    project_id = node_response["project_id"]
    return f"Created project with ID {project_id}"


# region Variables from app_config
#project_name = app_config.project_name
#vedge_count = app_config.vedge_count
#tap_name = app_config.tap_name
mgmt_network_address = app_config.mgmt_network_address

city_data = app_config.city_data
deploy_new_gns3_project = app_config.deploy_new_gns3_project
use_existing_gns3_project = app_config.use_existing_gns3_project
cleanup_gns3 = app_config.cleanup_gns3
test_lab = app_config.test_lab
delete_node_name = app_config.delete_node_name
config_client_every = app_config.client_every

# endregion

# region Viptela Variables
viptela_username = 'admin'
viptela_old_password = "admin"
viptela_password = 'PW4netops'
org_name = 'sdwan-lab'
vbond_address = '172.16.4.10'
vmanage_address = '172.16.2.2'
vsmart_address = '172.16.4.6'
switchport_count = 95

mgmt_switchport_count = 45
mgmt_main_switchport_count = 10
# endregion

# region Variables: GNS3 Template Data
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

vmanage_template_name = 'vManage'
vbond_template_name = 'vBond'
vsmart_template_name = 'vSmart'
vedge_template_name = 'vEdge'
open_vswitch_cloud_template_name = 'Open_vSwitch_Cloud'
network_test_tool_template_name = 'Network_Test_Tool'
cisco_l3_router_template_name = 'Cisco IOU L3 155-2T'
mgmt_hub_template_name = 'MGMT_Hub'
mgmt_main_hub_template_name = 'Main-MGMT-Switch'
arista_veos_template_name = 'arista_switch'
arista_ceos_template_name = 'arista_ceos'
fortinet_fortigate_template_name = 'Fortigate 7.0.5'
viptela_vmanage_template_data = {"compute_id": "local", "cpus": 16, "adapters": 6,
                                 "symbol": ":/symbols/affinity/circle/blue/server_cluster.svg",
                                 "adapter_type": "vmxnet3", "qemu_path": "/usr/bin/qemu-system-x86_64",
                                 "hda_disk_image": "viptela-vmanage-li-20.10.1-genericx86-64.qcow2",
                                 "hdb_disk_image": "empty30G.qcow2", "name": vmanage_template_name, "ram": 32768,
                                 "template_type": "qemu", "hda_disk_interface": "virtio",
                                 "hdb_disk_interface": "virtio", "options": "-cpu host -smp 2,maxcpus=2"}
viptela_vsmart_template_data = {"compute_id": "local", "cpus": 2, "adapters": 3,
                                "symbol": ":/symbols/affinity/circle/blue/interconnect.svg",
                                "adapter_type": "vmxnet3", "qemu_path": "/usr/bin/qemu-system-x86_64",
                                "hda_disk_image": "viptela-smart-li-20.10.1-genericx86-64.qcow2",
                                "name": vsmart_template_name, "ram": 4096, "template_type": "qemu",
                                "hda_disk_interface": "virtio", "options": "-cpu host"}
viptela_vbond_template_data = {"compute_id": "local", "cpus": 2, "adapters": 3,
                               "symbol": ":/symbols/affinity/circle/blue/isdn.svg", "adapter_type": "vmxnet3",
                               "qemu_path": "/usr/bin/qemu-system-x86_64",
                               "hda_disk_image": "viptela-edge-20.10.1-genericx86-64.qcow2",
                               "name": vbond_template_name, "ram": 2048, "template_type": "qemu",
                               "hda_disk_interface": "virtio", "options": "-cpu host"}
viptela_vedge_template_data = {"compute_id": "local", "cpus": 1, "adapters": 6,
                               "symbol": ":/symbols/affinity/square/blue/communications.svg",
                               "adapter_type": "vmxnet3", "qemu_path": "/usr/bin/qemu-system-x86_64",
                               "hda_disk_image": "viptela-edge-20.10.1-genericx86-64.qcow2",
                               "name": vedge_template_name, "ram": 2048, "template_type": "qemu",
                               "hda_disk_interface": "virtio", "options": "-cpu host -smp 2,maxcpus=2"}
appneta_mp_template_data = {"compute_id": "local", "cpus": 2, "port_name_format": "eth{0}", "adapters": 3,
                            "adapter_type": "virtio-net-pci", "qemu_path": "/usr/bin/qemu-system-x86_64",
                            "mac_address": "52:54:00:E0:00:00",
                            "hda_disk_image": "pathview-amd64-13.12.6.53966.qcow2", "name": "Appneta-vk35",
                            "ram": 4096, "template_type": "qemu"}
openvswitch_template_data = {"compute_id": "local", "adapters": 16, "category": "switch",
                             "image": "gns3/openvswitch:latest", "name": "Open vSwitch",
                             "symbol": ":/symbols/classic/multilayer_switch.svg", "template_type": "docker",
                             "usage": "By default all interfaces are connected to the br0"}
openvswitch_cloud_template_data = {"compute_id": "local", "adapters": switchport_count, "category": "switch",
                                   "image": "gns3/openvswitch:latest", "name": open_vswitch_cloud_template_name,
                                   "symbol": ":/symbols/cloud.svg", "template_type": "docker",
                                   "usage": "By default all interfaces are connected to the br0"}
network_test_tool_template_data = {"compute_id": "local", "adapters": 2, "category": "guest",
                                   "image": "evanrogers719/network_test_tool:latest",
                                   "name": network_test_tool_template_name, "symbol": ":/symbols/docker_guest.svg",
                                   "template_type": "docker"}
cisco_l3_router_template_data = {"compute_id": "local", "path": "L3-ADVENTERPRISEK9-M-15.5-2T.bin", "nvram": 256,
                                 "ram": 512, "symbol": ":/symbols/classic/router.svg", "template_type": "iou",
                                 "use_default_iou_values": True, "ethernet_adapters": 2, "serial_adapters": 0,
                                 "name": cisco_l3_router_template_name,
                                 "startup_config": "iou_l3_base_startup-config.txt"}
fortinet_fortigate_template_data = {"compute_id": "local", "cpus": 4, "adapters": 10, "adapter_type": "e1000",
                                    "qemu_path": "/usr/bin/qemu-system-x86_64",
                                    "hda_disk_image": "FGT_VM64_KVM-v7.0.5.F-FORTINET.out.kvm.qcow2",
                                    "hdb_disk_image": "empty30G.qcow2", "name": fortinet_fortigate_template_name,
                                    "ram": 2048, "template_type": "qemu", "hda_disk_interface": "virtio",
                                    "hdb_disk_interface": "virtio"}
arista_veos_template_data = {"compute_id": "local", "cpus": 2, "adapters": 20, "adapter_type": "e1000",
                             "qemu_path": "/usr/bin/qemu-system-x86_64", "hda_disk_image": "cdrom.iso",
                             "hdb_disk_image": "vEOS-lab-4.28.0F.qcow2",
                             "name": arista_veos_template_name,
                             "ram": 2048, "template_type": "qemu", "hda_disk_interface": "ide",
                             "hdb_disk_interface": "ide", "options": "-cpu host"}
arista_ceos_old_template_data = {"compute_id": "local", "adapters": 20, "category": "router",
                                 "image": "ceosimage:4.26.0.1F", "name": arista_ceos_template_name,
                                 "symbol": ":/symbols/classic/multilayer_switch.svg", "template_type": "docker",
                                 "usage": "By default all interfaces are connected to the br0",
                                 "start_command": "/sbin/init systemd.setenv=INTFTYPE=eth systemd.setenv=ETBA=1 systemd.setenv=SKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 systemd.setenv=CEOS=1 systemd.setenv=EOS_PLATFORM=ceoslab systemd.setenv=container=docker",
                                 "environment": "INTFTYPE=eth\nETBA=1 \nSKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 \nCEOS=1 \nEOS_PLATFORM=ceoslab \ncontainer=docker\nMAPETH0=1\nMGMTINF=eth0", }

arista_ceos_template_data = {"compute_id": "local", "adapters": 20, "category": "router",
                             "image": "ceosimage:4.28.6.1M", "name": arista_ceos_template_name,
                             "symbol": ":/symbols/classic/multilayer_switch.svg", "template_type": "docker",
                             "usage": "By default all interfaces are connected to the br0",
                             "start_command": "/sbin/init systemd.setenv=INTFTYPE=eth systemd.setenv=ETBA=1 systemd.setenv=SKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 systemd.setenv=CEOS=1 systemd.setenv=EOS_PLATFORM=ceoslab systemd.setenv=container=docker",
                             "environment": "INTFTYPE=eth\nETBA=1 \nSKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 \nCEOS=1 \nEOS_PLATFORM=ceoslab \ncontainer=docker\nMAPETH0=1\nMGMTINF=eth0", }

vmanage_deploy_data = {"x": -107, "y": 570, "name": "vManage"}
vsmart_deploy_data = {"x": -182, "y": 495, "name": "vSmart"}
vbond_deploy_data = {"x": -32, "y": 495, "name": "vBond"}
isp_router_deploy_data = {"x": -108, "y": -247, "name": "ISP-Router"}
cloud_node_deploy_data = {"x": -154, "y": -247, "name": "MGMT-Cloud-TAP", "node_type": "cloud",
                          "compute_id": "local", "symbol": ":/symbols/cloud.svg"}
main_mgmt_switch_deploy_data = {"x": 278, "y": -141, "name": "Main_MGMT-switch"}
nat_node_deploy_data = {"x": -154, "y": -554, "name": "Internet", "node_type": "nat", "compute_id": "local",
                        "symbol": ":/symbols/cloud.svg"}

big_block_deploy_data = {
    "svg": "<svg height=\"1500\" width=\"3681\"><rect fill=\"#ffffff\" fill-opacity=\"1.0\" height=\"1500\" stroke=\"#000000\" stroke-width=\"2\" width=\"3681\" /></svg>",
    "x": -1950, "y": -630, "z": -1}

arista_deploy_data = {
    "arista_01_deploy_data": {"x": -323, "y": -219, "name": "arista-spine1"},
    "arista_02_deploy_data": {"x": -23, "y": -219, "name": "arista-spine2"},
    "arista_03_deploy_data": {"x": -558, "y": 79, "name": "arista-leaf1"},
    "arista_04_deploy_data": {"x": -323, "y": 79, "name": "arista-leaf2"},
    "arista_05_deploy_data": {"x": -23, "y": 79, "name": "arista-leaf3"},
    "arista_06_deploy_data": {"x": 200, "y": 79, "name": "arista-leaf4"},
    "arista_07_deploy_data": {"x": 500, "y": 79, "name": "arista-leaf5"}
}
arista_2 = {
    "arista_07_deploy_data": {"x": -25, "y": -23, "name": "arista-leaf5"},
    "arista_08_deploy_data": {"x": -550, "y": 276, "name": "arista-leaf6"},
    "arista_09_deploy_data": {"x": -325, "y": 276, "name": "arista-leaf7"},
    "arista_10_deploy_data": {"x": -25, "y": 276, "name": "arista-leaf8"},
}
client_deploy_data = {
    "client_01_deploy_data": {"x": -555, "y": 373, "name": "Client-1"},
    "client_02_deploy_data": {"x": -330, "y": 373, "name": "Client-2"},
    "client_03_deploy_data": {"x": -30, "y": 373, "name": "Client-3"},
    "client_04_deploy_data": {"x": 200, "y": 373, "name": "Client-4"},
    "client_05_deploy_data": {"x": 494, "y": 373, "name": "Client-5"},
}
local_switch_deploy_data = {
    "switch_01_deploy_data": {"x": -445, "y": 237, "name": "switch-1"},
    "switch_02_deploy_data": {"x": 83, "y": 237, "name": "switch-2"},
    "switch_03_deploy_data": {"x": 491, "y": 237, "name": "switch-3"},
    "switch_04_deploy_data": {"x": 199, "y": 237, "name": "switch-4"},
    "switch_05_deploy_data": {"x": 499, "y": 237, "name": "switch-5"},
}
drawing_deploy_data = {
    "drawing_01": {
        "svg": "<svg width=\"374.71428571428567\" height=\"146.57142857142856\"><ellipse cx=\"187\" rx=\"188\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": -600, "y": 26, "z": 0},
    "drawing_02": {
        "svg": "<svg width=\"374.71428571428567\" height=\"146.57142857142856\"><ellipse cx=\"187\" rx=\"188\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": -77, "y": 24, "z": 0},
    "drawing_03": {
        "svg": "<svg width=\"495.7142857142858\" height=\"146.57142857142856\"><ellipse cx=\"247\" rx=\"248\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": -390, "y": -274, "z": 0},
    "drawing_04": {
        "svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65001</text></svg>",
        "x": -453, "y": 75, "z": 2},
    "drawing_05": {
        "svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65002</text></svg>",
        "x": 69, "y": 74, "z": 2},
    "drawing_06": {
        "svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65000</text></svg>",
        "x": -189, "y": -268, "z": 2},
    "drawing_07": {
        "svg": "<svg width=\"95\" height=\"23\"><text font-family=\"Arial Black\" font-size=\"10.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">MLAG Peer Link</text></svg>",
        "x": -457, "y": 99, "z": 2},
    "drawing_08": {
        "svg": "<svg width=\"95\" height=\"23\"><text font-family=\"Arial Black\" font-size=\"10.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">MLAG Peer Link</text></svg>",
        "x": 66, "y": 101, "z": 2},
    "drawing_09": {
        "svg": "<svg width=\"356\" height=\"36\"><text font-family=\"Arial\" font-size=\"24.0\" fill=\"#000000\" fill-opacity=\"1.0\">Arista EVPN / BGP / VXLAN Lab</text></svg>",
        "x": -238, "y": -407, "z": 2},
    "drawing_10": {
        "svg": "<svg width=\"194\" height=\"212\"><text font-family=\"TypeWriter\" font-size=\"10.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">Managment Network: 172.16.3.0/24\narista-spine1 - 172.16.3.2\narista-spine1 - 172.16.3.3\narista-leaf1 - 172.16.3.4\narista-leaf2 - 172.16.3.5\narista-leaf3 - 172.16.3.6\narista-leaf4 - 172.16.3.7\narista-leaf5 - 172.16.3.8\n\nClient Network: 172.16.101.0/24\nVLAN 40\nVXLAN1\nClient-1: 172.16.101.2\nClient-2: 172.16.101.3\nClient-3: 172.16.101.4\nClient-4: 172.16.101.5\nClient-5: 172.16.101.6</text></svg>",
        "x": -603, "y": -293, "z": 2},
    "drawing_11": {
        "svg": "<svg width=\"1326\" height=\"163\"><rect width=\"1326\" height=\"163\" fill=\"#00f900\" fill-opacity=\"0.19299610894941635\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": -640, "y": 318, "z": 0},
    "drawing_12": {
        "svg": "<svg width=\"74\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">VLAN 40</text></svg>",
        "x": -182, "y": 320, "z": 2},
    "drawing_13": {
        "svg": "<svg width=\"207.5\" height=\"146.57142857142856\"><ellipse cx=\"103\" rx=\"104\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": 422, "y": 21, "z": 0},
    "drawing_14": {
        "svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65003</text></svg>",
        "x": 481, "y": 29, "z": 2},
}
client_filename = 'client_interfaces'
client_node_file_path = 'etc/network/interfaces'

deploy_data_z = {"z": -1}


# endregion

# region Functions: Utilities
def make_request(method, url, data=None):
    if method == "GET":
        response = requests.get(url)
    elif method == "POST":
        response = requests.post(url, json=data)  # Add json=data here
    elif method == "PUT":
        response = requests.put(url, json=data)
    elif method == "DELETE":
        response = requests.delete(url)
    else:
        raise ValueError("Invalid method")
    response.raise_for_status()
    if response.content:
        return response.json()
    else:
        return {}


def util_extract_csr(response):
    json_data = response.json()
    if 'data' in json_data:
        return json_data['data']
    else:
        raise Exception(f"Failed to extract CSR. Response: {json_data}")


def util_print_response(response_data):
    if response_data.content:
        json_data = response_data.json()
        logging.info(json.dumps(json_data, indent=4))
    else:
        logging.info("Response content is empty.")


def util_get_file_size(file_path):
    size = os.path.getsize(file_path)
    size_name = ["B", "KB", "MB", "GB"]
    i = 0
    while size > 1024:
        size = size / 1024
        i += 1
    return f"{size:.2f} {size_name[i]}"


def util_resume_time(delay_time):
    resume_time = (datetime.datetime.now() + datetime.timedelta(minutes=delay_time)).strftime("%H:%M:%S")
    return resume_time


def util_current_time():
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return current_time


# endregion

# region Functions: GNS3 API Functions
def gns3_create_project(gns3_server_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        template_data = {"name": project_name}
        node_url = f"http://{server_ip}:{server_port}/v2/projects"
        node_response = make_request("POST", node_url, data=template_data)
        project_id = node_response["project_id"]
        return project_id


def gns3_create_drawing(gns3_server_data, project_id, node_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/drawings"
        node_response = make_request("POST", node_url, data=node_data)


def gns3_create_node(gns3_server_data, project_id, template_id, node_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/templates/{template_id}"
        node_response = make_request("POST", node_url, data=node_data)
        node_name = node_response["name"]
        logging.info(f"Deploy - Created Node {node_name}")
        node_id = node_response["node_id"]
        return node_id


def gns3_create_node_multi_return(gns3_server_data, project_id, template_id, node_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/templates/{template_id}"
        node_response = make_request("POST", node_url, data=node_data)
        node_name = node_response["name"]
        logging.info(f"Deploy - Created Node {node_name}")
        node_id = node_response["node_id"]
        return node_id, node_name


def gns3_create_cloud_node(gns3_server_data, project_id, node_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes"
        node_response = make_request("POST", node_url, data=node_data)
        node_name = node_response["name"]
        logging.info(f"Deploy - Created Node {node_name}")
        node_id = node_response["node_id"]
        return node_id


def gns3_create_template(gns3_server_data, template_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/templates"
        node_response = make_request("POST", node_url, data=template_data)
        template_id = node_response["template_id"]
        template_name = node_response["name"]
        logging.info(f"Deploy - Created template {template_name}")
        return template_id


def gns3_connect_nodes(gns3_server_data, project_id, node_a, adapter_a, port_a, node_b, adapter_b, port_b):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/links"
        node_data = {"nodes": [{"adapter_number": adapter_a, "node_id": node_a, "port_number": port_a},
                               {"adapter_number": adapter_b, "node_id": node_b, "port_number": port_b}]}
        node_a_name = gns3_find_nodes_by_field(gns3_server_data, project_id, 'node_id', 'name', node_a)
        node_b_name = gns3_find_nodes_by_field(gns3_server_data, project_id, 'node_id', 'name', node_b)
        logging.info(f"Deploy - Connected (adapter/port) {adapter_a}/{port_a} of {node_a_name[0]} to (adapter/port) {adapter_b}/{port_b} of {node_b_name[0]}")
        node_response = make_request("POST", node_url, data=node_data)
        return node_response["link_id"]


def gns3_delete_nodes(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        matching_nodes = gns3_find_nodes_by_name(gns3_server_data, delete_node_name)
        if matching_nodes:
            for node_id, console_port, aux in matching_nodes:
                delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
                response = make_request("DELETE", delete_url)
                node_name = response["name"]
                logging.info(f"Deleted node {node_name} on GNS3 Server {server_ip}")
        else:
            logging.info(f"Deploy - No nodes with '{delete_node_name}' in their name were found in project {project_name} on GNS3 Server {server_ip}")


def gns3_delete_all_nodes(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        nodes = gns3_get_nodes(gns3_server_data, project_id)
        for node in nodes:
            node_id = node['node_id']
            delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
            response = make_request("DELETE", delete_url)
            node_name = node["name"]
            logging.info(f"Deploy - Deleted node {node_name} on GNS3 Server {server_ip}")


def gns3_delete_all_drawings(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        drawings = gns3_get_drawings(gns3_server_data, project_id)
        for drawing in drawings:
            drawing_id = drawing['drawing_id']
            delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/drawings/{drawing_id}"
            response = make_request("DELETE", delete_url)
            logging.info(f"Deploy - Deleted drawing {drawing_id} on GNS3 Server {server_ip}")


def gns3_delete_template(gns3_server_data, template_name):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        template_id = gns3_get_template_id(gns3_server_data, template_name)
        if template_id:
            delete_url = f"http://{server_ip}:{server_port}/v2/templates/{template_id}"
            make_request("DELETE", delete_url)
            logging.info(f"Deploy - Deleted template ID {template_name} on GNS3 Server {server_ip}")
        else:
            logging.info(f"No templates with '{template_name}' in their name were found on GNS3 Server {server_ip}")


def gns3_delete_project(gns3_server_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        project_id = gns3_get_project_id(gns3_server_data)
        if project_id:
            delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}"
            make_request("DELETE", delete_url)
            logging.info(f"Deploy - Deleted project ID {project_name} on GNS3 Server {server_ip}")
        else:
            logging.info(f"No projects with '{project_name}' in their name were found on GNS3 Server {server_ip}")


def gns3_find_nodes_by_name(gns3_server_data, project_id, search_string=None):
    node_data = gns3_get_nodes(gns3_server_data, project_id)
    if search_string:
        matching_nodes = [node for node in node_data if search_string in node['name']]
        if not matching_nodes:
            return []
        else:
            return [(node['node_id'], node['console'], node['properties'].get('aux')) for node in matching_nodes]
    else:
        return []


def gns3_get_location_data(gns3_server_data, project_id, item_type):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/{item_type}"
        response = requests.get(url)
        data = json.loads(response.text)
        nodes = []
        if item_type == 'nodes':
            for node in data:
                name = node['name']
                x = node['x']
                y = node['y']
                z = node['z']
                nodes.append({'name': name, 'x': x, 'y': y, 'z': z})
        elif item_type == 'drawings':
            for node in data:
                svg = node['svg']
                x = node['x']
                y = node['y']
                z = node['z']
                nodes.append({'svg': svg, 'x': x, 'y': y, 'z': z})
        location_data = nodes
        drawing_data = {}
        for i, item_data in enumerate(location_data):
            drawing_key = f"drawing_{i + 1:02}"
            drawing_data[drawing_key] = item_data

        logging.info("\n".join([f'"{k}": {json.dumps(v, separators=(",", ":"))},' for k, v in drawing_data.items()]))
        return nodes


def gns3_find_nodes_by_field(gns3_server_data, project_id, search_field, return_field, search_string):
    nodes = gns3_get_nodes(gns3_server_data, project_id)
    if search_string:
        matching_nodes = [node for node in nodes if search_string in node[search_field]]
        if not matching_nodes:
            return []
        else:
            return [(node[return_field]) for node in matching_nodes]
    else:
        return []


def gns3_get_project_id(gns3_server_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/projects"
        response = requests.get(url)
        projects = json.loads(response.text)
        for project in projects:
            if project['name'] == project_name:
                return project['project_id']
        return None


def gns3_get_template_id(gns3_server_data, template_name):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/templates"
        response = requests.get(url)
        templates = json.loads(response.text)
        for template in templates:
            if template['name'] == template_name:
                return template['template_id']
        return None


def gns3_get_drawings(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/drawings"
        response = requests.get(url)
        if not response.ok:
            logging.info(f"Error retrieving links: {response.status_code}")
            exit()
        try:
            nodes = response.json()
        except ValueError as e:
            logging.info(f"Error parsing JSON: {e}")
            logging.info(f"Response content: {response.content}")
            exit()
        return nodes


def gns3_get_image(gns3_server_data, image_type, filename):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/compute/{image_type}/images/{filename}"
        response = requests.get(url)

        return response.status_code


def gns3_get_nodes(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes"
        response = requests.get(url)
        if not response.ok:
            logging.info(f"Error retrieving links: {response.status_code}")
            exit()
        try:
            nodes = response.json()
        except ValueError as e:
            logging.info(f"Error parsing JSON: {e}")
            logging.info(f"Response content: {response.content}")
            exit()
        return nodes


def gns3_get_node_files(gns3_server_data, project_id, node_id, file_path):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/files/{file_path}"
        response = requests.get(url)
        if not response.ok:
            logging.info(f"Error retrieving links: {response.status_code}")
            exit()
        try:
            nodes = response.json()
        except ValueError as e:
            logging.info(f"Error parsing JSON: {e}")
            logging.info(f"Response content: {response.content}")
            exit()
        return nodes


def gns3_reload_node(gns3_server_data, project_id, node_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/reload"
        response = make_request("POST", node_url, data={})
        logging.info(f"Reloaded node {node_id}")


def gns3_upload_symbol(gns3_server_data, symbol_file, symbol_name):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f'http://{server_ip}:{server_port}/v2/symbols/{symbol_name}/raw'
        headers = {"accept": "*/*"}
        response = requests.post(url, headers=headers, data=symbol_file)
        if response.status_code == 204:
            logging.info(f'Deploy - Uploaded symbol {symbol_name}')
            return
        else:
            logging.info(f'Deploy - Failed to upload {symbol_name}. Status code: {response.status_code}')


def gns3_upload_file_to_node(gns3_server_data, project_id, node_id, file_path_var, filename_temp):
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/')
    file_path = os.path.join(configs_path, filename_temp)
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        # Set the file path and name to be written to the node
        node_name = gns3_find_nodes_by_field(gns3_server_data, project_id, 'node_id', 'name', node_id)

        # Set the API endpoint URL for the node file write
        url = f'http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/files/{file_path_var}'

        # Open the local file and read its content
        with open(file_path, 'r') as f:
            file_content = f.read()

        # Set the API request headers and payload
        headers = {"accept": "application/json"}
        request_data = file_content.encode('utf-8')

        # Send the API request to write the file to the node
        response = requests.post(url, headers=headers, data=request_data)

        # Check if the API request was successful
        if response.status_code == 201:
            logging.info(f'Deploy - File - {filename_temp} successfully written to the node {node_name[0]}')
            return
        else:
            logging.info(f'Deploy - Failed to write file to the node {node_name[0]}. Status code: {response.status_code}')


def gns3_upload_image(gns3_server_data, image_type, filename):
    image_file_path = f'images/{image_type}'
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), image_file_path)
    file_path = os.path.join(configs_path, filename)
    file_size = util_get_file_size(file_path)
    logging.info(f"File Size: {file_size}")
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f'http://{server_ip}:{server_port}/v2/compute/{image_type}/images/{filename}'
        response = gns3_get_image(gns3_server_data, image_type, filename)
        if response != 200:
            headers = {"accept": "*/*"}
            logging.info(f'Deploy - Image - {filename} being uploaded to server. Please wait..')
            response = requests.post(url, headers=headers, data=open(file_path, "rb"))
            if response.status_code == 204:
                logging.info(f'Deploy - Image - {filename} successfully written to server')
                return
            else:
                logging.info(f'Deploy - Failed to write file to the server. Status code: {response.status_code}')


def gns3_update_nodes(gns3_server_data, project_id, node_id, request_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        request_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
        node_name = gns3_find_nodes_by_field(gns3_server_data, project_id, 'node_id', 'name', node_id)
        request_response = make_request("PUT", request_url, data=request_data)
        logging.info(f"Deploy - Updated deploy data for node {node_name[0]}")


def gns3_start_node(gns3_server_data, project_id, node_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        template_data = {}
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/start"
        node_response = make_request("POST", node_url, data=template_data)


def gns3_stop_node(gns3_server_data, project_id, node_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        template_data = {}
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/stop"
        node_response = make_request("POST", node_url, data=template_data)


def gns3_start_all_nodes(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        template_data = {}
        logging.info(f"Deploy - Starting all nodes in project {project_name}")
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/start"
        node_response = make_request("POST", node_url, data=template_data)
        logging.info(f"Deploy - Started all nodes in project {project_name}")


def gns3_set_project(gns3_server_data, project_id):
    logging.info(gns3_server_data)
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, vedge_count = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP'], server_record['Site Count']
        if vedge_count is None:
            project_zoom = 80
            project_scene_height = 1000
            project_scene_width = 2000
        elif vedge_count <= 30:
            project_zoom = 57
            project_scene_height = 1000
            project_scene_width = 2000
        else:
            project_zoom = 30
            project_scene_height = 1500
            project_scene_width = 4200
        template_data = {"auto_close": False, "scene_height": project_scene_height,
                         "scene_width": project_scene_width,
                         "zoom": project_zoom}
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}"
        node_response = make_request("PUT", node_url, data=template_data)
        project_id = node_response["project_id"]
        logging.info(f"Deploy - Update project settings for {project_name}")
        return project_id


def gns3_actions_upload_images(gns3_server_data):
    for root, dirs, files in os.walk("images/"):
        for file_name in files:
            image_type = os.path.basename(root)
            logging.info(f"image_type:{image_type}, filename: {file_name}")
            gns3_upload_image(gns3_server_data, image_type, file_name)


def gns3_actions_remove_templates(gns3_server_data):
    gns3_delete_template(gns3_server_data, vmanage_template_name)
    gns3_delete_template(gns3_server_data, vbond_template_name)
    gns3_delete_template(gns3_server_data, vsmart_template_name)
    gns3_delete_template(gns3_server_data, vedge_template_name)
    gns3_delete_template(gns3_server_data, cisco_l3_router_template_name)
    gns3_delete_template(gns3_server_data, network_test_tool_template_name)
    gns3_delete_template(gns3_server_data, open_vswitch_cloud_template_name)
    gns3_delete_template(gns3_server_data, mgmt_hub_template_name)
    gns3_delete_template(gns3_server_data, mgmt_main_hub_template_name)
    gns3_delete_template(gns3_server_data, arista_ceos_template_name)
    delete_more_than_1_var = 0
    if delete_more_than_1_var == 1:
        while True:
            template_id = gns3_get_template_id(gns3_server_data, arista_ceos_template_name)
            if not template_id:
                break
            gns3_delete_template(gns3_server_data, arista_ceos_template_name)


# endregion

# region Generate Dynamic Data for Deployment
def generate_temp_hub_data(num_ports, template_name):
    ports_mapping = [{"name": f"Ethernet{i}", "port_number": i} for i in range(num_ports)]

    temp_hub_data = {
        "category": "switch",
        "compute_id": "local",
        "default_name_format": "Hub{0}",
        "name": template_name,
        "ports_mapping": ports_mapping,
        "symbol": ":/symbols/hub.svg",
        "template_type": "ethernet_hub"
    }

    return temp_hub_data


def generate_network_objects(base_subnet, subnet_mask, vedge_index=1):
    network = ipaddress.IPv4Network(base_subnet)
    subnets_64 = list(network.subnets(new_prefix=subnet_mask))
    networks = []
    switch_limit = 1
    for subnet in subnets_64:
        if subnet.prefixlen == subnet_mask:
            if switch_limit == 45:
                break
            router_address = str(subnet.network_address + 1)
            vedge_address = str(subnet.network_address + 2)
            subnet_address = str(
                ipaddress.IPv4Interface(str(subnet.network_address) + '/' + str(subnet_mask)).netmask)
            subnet_address_long = str(vedge_address) + '/' + str(subnet_mask)
            network_dict = {
                'subnet': str(subnet.network_address),
                'subnet_mask': str(subnet.prefixlen),
                'subnet_address': subnet_address,
                'router_address': router_address,
                'vedge_address': subnet_address_long,
                'isp_switch_address': vedge_address,
                'vedge': f'vEdge_{vedge_index:003}'
            }
            networks.append(network_dict)
            vedge_index += 1
            switch_limit += 1
    return networks


def generate_client_interfaces_file(filename_temp, ip=None):
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/')
    filename = os.path.join(configs_path, filename_temp)

    with open(filename, 'w') as f:
        f.write('auto eth0\n')
        f.write('iface eth0 inet dhcp\n')
        f.write('\tup echo nameserver 192.168.122.1 > /etc/resolv.conf\n')
        f.write('\thwaddress ether 4C:D7:17:00:00:00\n\n')
        if ip:
            f.write('auto eth1\n')
            f.write('iface eth1 inet static\n')
            f.write(f'\taddress {ip}\n')
            f.write('\tnetmask 255.255.255.0\n\n')

    logging.info(f"Deploy - Created file {filename_temp}")


def generate_interfaces_file(interface_data_1, router_index, interface_data_2, interface_data_3, filename_temp):
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/')
    filename = os.path.join(configs_path, filename_temp)
    with open(filename, 'w') as f:
        eth_1 = 0
        eth_2 = 0
        f.write(f'#{filename}\n')
        f.write('auto eth0\n')
        f.write('iface eth0 inet static\n')
        f.write(f'\taddress {interface_data_1[router_index]["isp_switch_address"]}\n')
        f.write(f'\tnetmask {interface_data_1[router_index]["subnet_address"]}\n')
        f.write(f'\tgateway {interface_data_1[router_index]["router_address"]}\n')
        f.write('\tup echo nameserver 192.168.122.1 > /etc/resolv.conf\n\n')
        f.write('auto eth1\n')
        f.write('iface eth1 inet static\n')
        if filename_temp == "cloud_isp_switch_0_interfaces":
            f.write(f'\taddress 172.16.4.1\n')
            f.write(f'\tnetmask 255.255.255.252\n')
            f.write('auto eth2\n')
            f.write('iface eth2 inet static\n')
            f.write(f'\taddress 172.16.4.5\n')
            f.write(f'\tnetmask 255.255.255.252\n')
            f.write('auto eth3\n')
            f.write('iface eth3 inet static\n')
            f.write(f'\taddress 172.16.4.9\n')
            f.write(f'\tnetmask 255.255.255.252\n')
        for i in range(5, 49):
            f.write(f'#{interface_data_2[eth_1]["vedge"]} interface ge0/0\n')
            f.write(f'auto eth{i}\n')
            f.write(f'iface eth{i} inet static\n')
            f.write(f'\taddress {interface_data_2[eth_1]["router_address"]}\n')
            f.write(f'\tnetmask {interface_data_2[eth_1]["subnet_address"]}\n')
            f.write('\n')
            eth_1 += 1
        for i in range(51, 95):
            f.write(f'#{interface_data_3[eth_2]["vedge"]} interface ge0/1\n')
            f.write(f'auto eth{i}\n')
            f.write(f'iface eth{i} inet static\n')
            f.write(f'\taddress {interface_data_3[eth_2]["router_address"]}\n')
            f.write(f'\tnetmask {interface_data_3[eth_2]["subnet_address"]}\n')
            f.write('\n')
            eth_2 += 1
    logging.info(f"Deploy - Created file {filename_temp}")


def generate_arista_interfaces_file(filename_temp, ip_var):
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/')
    filename = os.path.join(configs_path, filename_temp)

    with open(filename, 'w') as f:
        f.write('auto eth0\n')
        f.write('iface eth0 inet static\n')
        f.write(f'\taddress {ip_var}\n')
        f.write('\tnetmask 255.255.255.0\n\n')
        f.write(f'\tgateway {mgmt_network_address}1\n')

    logging.info(f"Deploy - Created file {filename_temp}")


def generate_isp_deploy_data(num_nodes):
    deploy_data = {}
    x = -154
    y = 51

    for i in range(1, num_nodes + 1):
        name = f"Cloud_ISP_{i:03}"
        y += 75
        deploy_data[f"isp_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}

    return deploy_data


def generate_vedge_objects(vedge_count):
    subnet_mask = 24
    k = 101
    networks = []
    for i in range(1, vedge_count + 1):
        base_subnet = f'172.16.{k}.0/24'
        network = ipaddress.IPv4Network(base_subnet)
        subnets_64 = list(network.subnets(new_prefix=subnet_mask))
        for subnet in subnets_64:
            if subnet.prefixlen == subnet_mask:
                router_address = str(subnet.network_address + 1)
                vedge_address = str(subnet.network_address + 2)
                subnet_address_full = str(
                    ipaddress.IPv4Interface(str(subnet.network_address) + '/' + str(subnet_mask)).netmask)
                subnet_address_var = str(subnet.network_address) + '/' + str(subnet_mask)
                dhcp_exclude_var = str(subnet.network_address + 1) + '-' + str(subnet.network_address + 50)
                client_1_address_var = str(subnet.network_address + 51)
                network_dict = {
                    'lan_subnet_address': subnet_address_var,
                    'lan_gateway_address': router_address,
                    'lan_dhcp_pool': f'{router_address}/24',
                    'lan_dhcp_exclude': dhcp_exclude_var,
                    'client_1_address': client_1_address_var,
                    'vedge': f'vEdge_{i:003}',
                    'system_ip': f'172.16.2.{i + 100}',
                    'mgmt_address': f'172.16.2.{i + 100}/24',
                    'mgmt_gateway': '172.16.2.1',
                    'site_id': k,
                    'org_name': 'sdwan-lab'
                }
            networks.append(network_dict)
            k += 1
    # logging.info(networks)
    return networks


def generate_vedge_deploy_data(vedge_count):
    deploy_data = {}
    client_deploy_data = {}
    site_drawing_deploy_data = {}
    e = 1
    o = 1
    y_modifier = 0
    x_o = -557
    x_e = 267
    y = -554
    y_s = -554
    row_count = 20

    client_x = 0
    client_y = 0
    client_y_modifier = 115

    drawing_x = 0
    drawing_y = 0
    drawing_x_modifier = 200

    if vedge_count <= 10:
        row_count = 4
        y = -107
        y_s = -107
        for i in range(1, vedge_count + 1):
            temp_name = f"vEdge_{i:03}"
            name = f"vEdge_{i:03}_{city_data[temp_name]['city']}"
            client_name = f"Client_{i:03}_{city_data[temp_name]['city']}"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    client_x = x
                    drawing_x = x - 57
                    drawing_y = y - 55
                    e += 1
                else:
                    x = x_o + -200 * o
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                    o += 1
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    y = y_s + 300 * y_modifier
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"vedge_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}
    elif vedge_count <= 20:
        row_count = 10
        y = -107
        y_s = -107
        for i in range(1, vedge_count + 1):
            temp_name = f"vEdge_{i:03}"
            name = f"vEdge_{i:03}_{city_data[temp_name]['city']}"
            client_name = f"Client_{i:03}_{city_data[temp_name]['city']}"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    e += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o + -200 * (o)
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    y = y_s + 300 * y_modifier
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"vedge_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}
    else:
        for i in range(1, vedge_count + 1):
            temp_name = f"vEdge_{i:03}"
            name = f"vEdge_{i:03}_{city_data[temp_name]['city']}"
            client_name = f"Client_{i:03}_{city_data[temp_name]['city']}"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    e += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o + -200 * o
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"vedge_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}
    return deploy_data, client_deploy_data, site_drawing_deploy_data


def generate_mgmt_switch_deploy_data(num_nodes):
    deploy_data = {}
    e = 1
    o = 1
    x_o = -261
    x_e = 39
    y = -316
    z = -1
    row_count = 10

    for i in range(1, num_nodes + 1):
        name = f"MGMT_switch_{i:03}"
        if i == 1:
            x = x_o
        elif i == 2:
            x = x_e
        elif i <= row_count:
            if i % 2 == 0:
                x = x_e + 100 * e
                e += 1
            else:
                x = x_o + -100 * o
                o += 1
        deploy_data[f"mgmt_switch_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}

    return deploy_data


# endregion

# region Functions: Viptela API
class Authentication:
    def get_jsessionid(self, gns3_server_data):
        server_ips = set(d['vManage API IP'] for d in gns3_server_data)
        for server_ip in server_ips:
            api = "/j_security_check"
            base_url = f"https://{server_ip}"
            url = base_url + api
            payload = {'j_username': viptela_username, 'j_password': viptela_password}
            response = requests.post(url=url, data=payload, verify=False)
            try:
                cookies = response.headers["Set-Cookie"]
                jsessionid = cookies.split(";")
                return jsessionid[0]
            except:
                # logging.info("No valid JSESSION ID returned\n")
                exit()

    def get_token(self, jsessionid, gns3_server_data):
        server_ips = set(d['vManage API IP'] for d in gns3_server_data)
        for server_ip in server_ips:
            headers = {'Cookie': jsessionid}
            base_url = f"https://{server_ip}"
            api = "/dataservice/client/token"
            url = base_url + api
            response = requests.get(url=url, headers=headers, verify=False)
            if response.status_code == 200:
                return response.text
            else:
                return None


def vmanage_create_auth(gns3_server_data):
    vmanage_auth = Authentication()
    jsessionid = vmanage_auth.get_jsessionid(gns3_server_data)
    token = vmanage_auth.get_token(jsessionid, gns3_server_data)
    if token is not None:
        vmanage_headers = {'Content-Type': "application/json", 'Cookie': jsessionid, 'X-XSRF-TOKEN': token}
    else:
        vmanage_headers = {'Content-Type': "application/json", 'Cookie': jsessionid}
    return vmanage_headers


def vmanage_set_cert_type(gns3_server_data, vmanage_headers):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/settings/configuration/certificate"
        catype = "enterprise"
        response_data = {'certificateSigning': catype}
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Set certificate authority type for vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(response.content)
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_set_cert(gns3_server_data, vmanage_headers, cert):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/settings/configuration/certificate/enterpriserootca"
        response_data = {'enterpriseRootCA': cert}
        try:
            response = requests.put(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                    timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Uploaded new root certificate to vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(response.content)
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_install_cert(gns3_server_data, vmanage_headers, cert):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/certificate/install/signedCert"
        response_data = {'enterpriseRootCA': cert}
        try:
            response = requests.post(url, data=cert, headers=vmanage_headers, verify=False, timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Installed device certificate for vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(response.content)
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_forcesync_rootcert(gns3_server_data, vmanage_headers):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/certificate/forcesync/rootCert"
        response_data = {}
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Forced root certificate sync on vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(response.content)
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_sync_rootcertchain(gns3_server_data, vmanage_headers):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/system/device/sync/rootcertchain"
        response_data = {}
        try:
            response = requests.get(url, headers=vmanage_headers, verify=False, timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Synced root certificate chain for vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(response.content)
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_set_vbond(gns3_server_data, vmanage_headers):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/settings/configuration/device"
        response_data = {'domainIp': vbond_address, 'port': '12346'}
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Set vBond {vbond_address} for vManage {vmanage_address} in configuration settings")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_set_org(gns3_server_data, vmanage_headers):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/settings/configuration/organization"
        response_data = {'org': org_name}
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Set organization for vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_push_certs(gns3_server_data, vmanage_headers):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/certificate/vedge/list?action=push"
        response_data = {}
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Pushed vEdge certificates to control devices for vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_set_device(gns3_server_data, vmanage_headers, vdevice_ip, vdevice_personality):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/system/device"
        response_data = {"deviceIP": vdevice_ip, "username": viptela_username, "password": viptela_password,
                         "personality": vdevice_personality, "generateCSR": "true", }
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=35)
            if response.status_code == requests.codes.ok:
                logging.info(f"Deploy - {vdevice_personality} with address {vdevice_ip} set successfully on vManage {vmanage_address}")
            else:
                logging.info(f"Deploy - Failed to add {vdevice_personality} device. ")
                logging.info("Response: {}".format(response.text))
            return response
        except requests.exceptions.RequestException as e:
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_generate_csr(gns3_server_data, vmanage_headers, vdevice_ip, vdevice_personality):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/certificate/generate/csr"
        response_data = {"deviceIP": vdevice_ip}
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=20)
            response.raise_for_status()
            result = util_extract_csr(response)
            logging.info(f"Deploy - Generated CSR for {vdevice_personality} on vManage {vmanage_address}")
            return result[0]['deviceCSR']
        except requests.exceptions.RequestException as e:
            logging.info(f"vManage not available: {str(e)}")
            continue


# endregion

def evpn_deploy(gns3_server_data):
    # region Runtime
    start_time = time.time()
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, vedge_count, tap_name, use_tap = server_record[
            'GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP'], server_record['Site Count'], \
        server_record['Tap Name'], server_record['Use Tap']
    gns3_delete_project(gns3_server_data)
    gns3_actions_remove_templates(gns3_server_data)
    new_project_id = gns3_create_project(gns3_server_data)
    gns3_set_project(gns3_server_data, new_project_id)
    # region Deploy Nodes
    arista_count = 7
    arista_template_id = gns3_create_template(gns3_server_data, arista_ceos_template_data)
    temp_hub_data = generate_temp_hub_data(mgmt_main_switchport_count, mgmt_main_hub_template_name)
    regular_ethernet_hub_template_id = gns3_create_template(gns3_server_data, temp_hub_data)
    network_test_tool_template_id = gns3_create_template(gns3_server_data, network_test_tool_template_data)
    cloud_node_id = gns3_create_cloud_node(gns3_server_data, new_project_id, cloud_node_deploy_data)
    mgmt_main_switch_node_id = gns3_create_node(gns3_server_data, new_project_id, regular_ethernet_hub_template_id,
                                                main_mgmt_switch_deploy_data)
    for i in range(1, arista_count + 1):
        node_id, node_name = gns3_create_node_multi_return(gns3_server_data, new_project_id, arista_template_id,
                                                           arista_deploy_data[f"arista_{i:02}_deploy_data"])
        arista_deploy_data[f"arista_{i:02}_deploy_data"]["node_id"] = node_id
        gns3_update_nodes(gns3_server_data, new_project_id, node_id, arista_deploy_data[f"arista_{i:02}_deploy_data"])
    gns3_start_all_nodes(gns3_server_data, new_project_id)
    # endregion
    # region Connect Nodes
    if app_config.configure_mgmt_tap == 1:
        matching_nodes = gns3_find_nodes_by_field(gns3_server_data, new_project_id, 'name', 'ports', 'MGMT-Cloud-TAP')
        mgmt_tap_interface = 0
        for port in matching_nodes[0]:
            if port["short_name"] == tap_name:
                mgmt_tap_interface = port['port_number']
        gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 0, cloud_node_id, 0,
                           mgmt_tap_interface)
    for i in range(1, arista_count + 1):
        gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, i + 5,
                           arista_deploy_data[f"arista_{i:02}_deploy_data"]["node_id"], 19, 0)
    for i in range(1, arista_count + 1):
        name = arista_deploy_data[f"arista_{i:02}_deploy_data"]["name"]
        node_id = arista_deploy_data[f"arista_{i:02}_deploy_data"]["node_id"]
        if name == "arista-spine1":
            for k in range(1, 6):
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, k, 0,
                                   arista_deploy_data[f"arista_{k + 2:02}_deploy_data"]["node_id"], 11, 0)
        if name == "arista-spine2":
            for k in range(1, 6):
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, k, 0,
                                   arista_deploy_data[f"arista_{k + 2:02}_deploy_data"]["node_id"], 12, 0)
        if name == "arista-leaf1":
            gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 10, 0,
                               arista_deploy_data[f"arista_04_deploy_data"]["node_id"],
                               10, 0)
        if name == "arista-leaf3":
            gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 10, 0,
                               arista_deploy_data[f"arista_06_deploy_data"]["node_id"],
                               10, 0)
    # endregion
    # region Configure
    logging.info(f"Deploy - Waiting 1 minute for nodes to start")
    time.sleep(60)
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        arista_nodes = f'arista-'
        client_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, arista_nodes)
        abs_path = os.path.abspath(__file__)
        configs_path = os.path.join(os.path.dirname(abs_path), 'configs/arista')
        if client_nodes:
            for client_node in client_nodes:
                client_node_id, client_console_port, client_aux = client_node
                temp_node_name = gns3_find_nodes_by_field(gns3_server_data, new_project_id, 'node_id', 'name',
                                                          client_node_id)
                temp_file = temp_node_name[0]
                file_name = os.path.join(configs_path, temp_file)
                tn = telnetlib.Telnet(server_ip, client_aux)
                logging.info(f"Deploy - Starting Configuration Deploy to {temp_node_name[0]}")
                tn.write(b"\r\n")
                tn.read_until(b"#")
                tn.write(b"Cli\n")
                tn.read_until(b">")
                tn.write(b"enable\n")
                tn.read_until(b"#")
                tn.write(b"conf t\n")
                tn.read_until(b"#")
                tn.write(b"service routing protocols model multi-agent\n")
                tn.read_until(b"#")
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                    logging.info(f"Deploy - Sending configuration commands to {temp_node_name[0]}")
                    for line in lines:
                        formatted_line = line.format(
                        )
                        tn.write(formatted_line.encode('ascii') + b"\n")
                        tn.read_until(b"#")
                tn.write(b"wr mem\n")
                tn.read_until(b"Copy completed successfully.")
                time.sleep(2)
                gns3_stop_node(gns3_server_data, new_project_id, client_node_id)
                gns3_start_node(gns3_server_data, new_project_id, client_node_id)

    # endregion
    # region Deploy Site Clients in Lab
    regular_ethernet_hub_template_id = gns3_get_template_id(gns3_server_data, 'Main-MGMT-Switch')
    network_test_tool_template_id = gns3_get_template_id(gns3_server_data, 'Network_Test_Tool')
    v = 1
    leaf_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, "leaf")
    for i in range(1, 4):
        local_switch_deploy_data[f"switch_{i:02}_deploy_data"]["node_id"] = gns3_create_node(gns3_server_data,
                                                                                             new_project_id,
                                                                                             regular_ethernet_hub_template_id,
                                                                                             local_switch_deploy_data[
                                                                                                 f"switch_{i:02}_deploy_data"])
    if leaf_nodes:
        for leaf_node in leaf_nodes:
            node_id = leaf_node[0]
            client_node_id = gns3_create_node(gns3_server_data, new_project_id, network_test_tool_template_id,
                                              client_deploy_data[f"client_{v:02}_deploy_data"])
            gns3_update_nodes(gns3_server_data, new_project_id, client_node_id,
                              client_deploy_data[f"client_{v:02}_deploy_data"])
            temp_ip = f"172.16.101.{v + 1}"
            generate_client_interfaces_file(client_filename, temp_ip)
            gns3_upload_file_to_node(gns3_server_data, new_project_id, client_node_id, client_node_file_path,
                                     client_filename)

            if v == 1:
                local_switch_node_id = local_switch_deploy_data["switch_01_deploy_data"]["node_id"]
                gns3_connect_nodes(gns3_server_data, new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1,
                                   0)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 1, 0, local_switch_node_id, 0, 0)
            elif v == 2:
                gns3_connect_nodes(gns3_server_data, new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1,
                                   0)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 1, 0, local_switch_node_id, 0, 1)
            elif v == 3:
                local_switch_node_id = local_switch_deploy_data["switch_02_deploy_data"]["node_id"]
                gns3_connect_nodes(gns3_server_data, new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1,
                                   0)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 1, 0, local_switch_node_id, 0, 3)
            elif v == 4:
                gns3_connect_nodes(gns3_server_data, new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1,
                                   0)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 1, 0, local_switch_node_id, 0, 4)
            elif v == 5:
                local_switch_node_id = local_switch_deploy_data["switch_03_deploy_data"]["node_id"]
                gns3_connect_nodes(gns3_server_data, new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1,
                                   0)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 1, 0, local_switch_node_id, 0, 4)
            gns3_start_node(gns3_server_data, new_project_id, client_node_id)
            v += 1
    # endregion
    # region Create GNS3 Drawings
    drawing_index = 1
    for drawing_data in drawing_deploy_data:
        gns3_create_drawing(gns3_server_data, new_project_id, drawing_deploy_data[f'drawing_{drawing_index:02}'])
        drawing_index += 1
    # endregion
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    logging.info(f"Total time for GNS3 Lab Deployment for project {project_name} deployment: {total_time:.2f} minutes")
    # endregion


def viptela_deploy(gns3_server_data):
    # region Variables
    vmanage_headers = {}
    lan_subnet_address = ''
    lan_gateway_address = ''
    lan_dhcp_exclude = ''
    lan_dhcp_pool = ''
    system_ip = ''
    site_id = 0
    mgmt_address = ''
    mgmt_gateway = ''
    vedge_info = []
    mgmt_switch_nodes = []
    isp_switch_nodes = []
    vedge_lan_objects = []
    vedge_lan_object = []
    isp_1_overall = []
    isp_2_overall = []
    vedge_nodes = []
    vmanage_root_cert = ""
    # endregion

    # region Runtime
    start_time = time.time()

    # region GNS3 Lab Setup
    # time.sleep(10)
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, vedge_count, tap_name, use_tap = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP'], server_record['Site Count'], server_record['Tap Name'], server_record['Use Tap']
    isp_switch_count = (vedge_count // 40) + 1
    mgmt_switch_count = (vedge_count // 30) + 1
    gns3_delete_project(gns3_server_data)
    gns3_actions_remove_templates(gns3_server_data)
    new_project_id = gns3_create_project(gns3_server_data)
    gns3_set_project(gns3_server_data, new_project_id)
    # endregion
    # region Create GNS3 Templates
    vmanage_template_id = gns3_create_template(gns3_server_data, viptela_vmanage_template_data)
    vbond_template_id = gns3_create_template(gns3_server_data, viptela_vbond_template_data)
    vsmart_template_id = gns3_create_template(gns3_server_data, viptela_vsmart_template_data)
    vedge_template_id = gns3_create_template(gns3_server_data, viptela_vedge_template_data)
    cisco_iou_template_id = gns3_create_template(gns3_server_data, cisco_l3_router_template_data)
    network_test_tool_template_id = gns3_create_template(gns3_server_data, network_test_tool_template_data)
    openvswitch_template_id = gns3_create_template(gns3_server_data, openvswitch_cloud_template_data)
    temp_hub_data = generate_temp_hub_data(mgmt_main_switchport_count, mgmt_main_hub_template_name)
    regular_ethernet_hub_template_id = gns3_create_template(gns3_server_data, temp_hub_data)
    temp_hub_data = generate_temp_hub_data(mgmt_switchport_count, mgmt_hub_template_name)
    hub_template_id = gns3_create_template(gns3_server_data, temp_hub_data)
    nat_node_template_id = gns3_get_template_id(gns3_server_data, "NAT")
    cloud_node_template_id = gns3_get_template_id(gns3_server_data, "Cloud")
    # endregion
    #  region Setup Dynamic Networking
    vedge_deploy_data, client_deploy_data, site_drawing_deploy_data = generate_vedge_deploy_data(vedge_count)
    isp_deploy_data = generate_isp_deploy_data(isp_switch_count)
    mgmt_switch_deploy_data = generate_mgmt_switch_deploy_data(mgmt_switch_count)
    # endregion
    # region Deploy GNS3 Nodes
    vmanage_node_id = gns3_create_node(gns3_server_data, new_project_id, vmanage_template_id, vmanage_deploy_data)
    vsmart_node_id = gns3_create_node(gns3_server_data, new_project_id, vsmart_template_id, vsmart_deploy_data)
    vbond_node_id = gns3_create_node(gns3_server_data, new_project_id, vbond_template_id, vbond_deploy_data)
    isp_router_node_id = gns3_create_node(gns3_server_data, new_project_id, cisco_iou_template_id,
                                          isp_router_deploy_data)
    mgmt_main_switch_node_id = gns3_create_node(gns3_server_data, new_project_id, regular_ethernet_hub_template_id,
                                                main_mgmt_switch_deploy_data)
    nat_node_id = gns3_create_cloud_node(gns3_server_data, new_project_id, nat_node_deploy_data)
    cloud_node_id = gns3_create_cloud_node(gns3_server_data, new_project_id, cloud_node_deploy_data)
    for i in range(1, isp_switch_count + 1):
        node_name = f"ISP_{i:03}"
        matching_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, node_name)
        if not matching_nodes:
            node_id, node_name = gns3_create_node_multi_return(gns3_server_data, new_project_id,
                                                               openvswitch_template_id,
                                                               isp_deploy_data[f"isp_{i:03}_deploy_data"])
            isp_switch_nodes.append({'node_name': node_name, 'node_id': node_id})
        else:
            logging.info(f"Node {node_name} already exists in project {project_name}")
    for i in range(1, mgmt_switch_count + 1):
        node_name = f"MGMT_switch_{i:03}"
        matching_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, node_name)
        if not matching_nodes:
            node_id, node_name = gns3_create_node_multi_return(gns3_server_data, new_project_id, hub_template_id,
                                                               mgmt_switch_deploy_data[
                                                                   f"mgmt_switch_{i:03}_deploy_data"])
            mgmt_switch_nodes.append({'node_name': node_name, 'node_id': node_id})
        else:
            logging.info(f"Node {node_name} already exists in project {project_name}")
    for i in range(1, vedge_count + 1):
        node_name = f"vEdge_{i:03}"
        matching_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, node_name)
        if not matching_nodes:
            node_id, node_name = gns3_create_node_multi_return(gns3_server_data, new_project_id, vedge_template_id,
                                                               vedge_deploy_data[f"vedge_{i:03}_deploy_data"])
            vedge_info.append({'node_name': node_name, 'node_id': node_id})
        else:
            logging.info(f"Node {node_name} already exists in project {project_name}")
    gns3_update_nodes(gns3_server_data, new_project_id, vmanage_node_id, vmanage_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, vsmart_node_id, vsmart_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, vbond_node_id, vbond_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, isp_router_node_id, isp_router_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, main_mgmt_switch_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, deploy_data_z)

    for i in range(1, isp_switch_count + 1):
        matching_node = isp_switch_nodes[i - 1]
        if matching_node:
            node_id = matching_node['node_id']
            gns3_update_nodes(gns3_server_data, new_project_id, node_id, isp_deploy_data[f"isp_{i:03}_deploy_data"])
        else:
            logging.info(f"No nodes found in project {project_name} for isp_switch_{i}")

    for i in range(1, mgmt_switch_count + 1):
        matching_node = mgmt_switch_nodes[i - 1]
        if matching_node:
            node_id = matching_node['node_id']
            gns3_update_nodes(gns3_server_data, new_project_id, node_id,
                              mgmt_switch_deploy_data[f"mgmt_switch_{i:03}_deploy_data"])
            gns3_update_nodes(gns3_server_data, new_project_id, node_id, deploy_data_z)
        else:
            logging.info(f"No nodes found in project {project_name} for MGMT_switch_{i}")

    for i in range(1, vedge_count + 1):
        matching_node = vedge_info[i - 1]
        if matching_node:
            node_id = matching_node['node_id']
            gns3_update_nodes(gns3_server_data, new_project_id, node_id, vedge_deploy_data[f"vedge_{i:03}_deploy_data"])
        else:
            logging.info(f"No nodes found in project {project_name} for vEdge {i}")
    # endregion
    # region Connect GNS3 Lab Nodes
    matching_nodes = gns3_find_nodes_by_field(gns3_server_data, new_project_id, 'name', 'ports', 'MGMT-Cloud-TAP')
    mgmt_tap_interface = 0
    for port in matching_nodes[0]:
        if port["short_name"] == tap_name:
            mgmt_tap_interface = port['port_number']
    cloud_isp_node_id = isp_switch_nodes[0]['node_id']
    gns3_connect_nodes(gns3_server_data, new_project_id, nat_node_id, 0, 0, isp_router_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, cloud_isp_node_id, 1, 0, vmanage_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, cloud_isp_node_id, 2, 0, vsmart_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, cloud_isp_node_id, 3, 0, vbond_node_id, 1, 0)
    if app_config.configure_mgmt_tap == 1:
        gns3_connect_nodes(gns3_server_data, new_project_id, cloud_node_id, 0, mgmt_tap_interface,
                           mgmt_main_switch_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 1, vmanage_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 2, vsmart_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 3, vbond_node_id, 0, 0)
    mgmt_switch_interface = 1
    switch_adapter_a = 5
    switch_adapter_b = (switchport_count // 2) + 4
    cloud_isp_node_index = 0
    mgmt_switch_node_index = 0
    for i in range(isp_switch_count):
        cloud_isp_node_id = isp_switch_nodes[i]['node_id']
        gns3_connect_nodes(gns3_server_data, new_project_id, cloud_isp_node_id, 0, 0, isp_router_node_id, 0, i + 1)
    for i in range(mgmt_switch_count):
        first_vedge_index = i * 30
        last_vedge_index = min((i + 1) * 30, vedge_count)
        mgmt_switch_node_id = mgmt_switch_nodes[mgmt_switch_node_index]['node_id']
        mgmt_switch_index = i + 5
        gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_switch_node_id, 0, 0, mgmt_main_switch_node_id, 0,
                           mgmt_switch_index)
        for j in range(first_vedge_index, last_vedge_index):
            vedge_node_id = vedge_info[j]['node_id']
            gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_switch_node_id, 0, mgmt_switch_interface,
                               vedge_node_id, 0, 0)
            cloud_isp_node_id = isp_switch_nodes[cloud_isp_node_index]['node_id']
            gns3_connect_nodes(gns3_server_data, new_project_id, cloud_isp_node_id, switch_adapter_a, 0, vedge_node_id,
                               1, 0)
            gns3_connect_nodes(gns3_server_data, new_project_id, cloud_isp_node_id, switch_adapter_b, 0, vedge_node_id,
                               2, 0)
            switch_adapter_a += 1
            switch_adapter_b += 1
            mgmt_switch_interface += 1
            if (j + 1) % 44 == 0:
                cloud_isp_node_index += 1
                switch_adapter_a = 5
                switch_adapter_b = (switchport_count // 2) + 4
                mgmt_switch_interface = 1
        mgmt_switch_node_index += 1
    # endregion
    # region Create GNS3 Drawings
    gns3_create_drawing(gns3_server_data, new_project_id, big_block_deploy_data)
    for i in range(1, vedge_count + 1):
        gns3_create_drawing(gns3_server_data, new_project_id,
                            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"])
    # endregion
    # region Deploy GNS3 Node Config Files
    matching_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, "Cloud_ISP")
    starting_subnet = 6
    router_ip = 0
    switch_index = 0
    vedge_index = 1
    if matching_nodes:
        for matching_node in matching_nodes:
            node_id = matching_node[0]
            isp_router_base_subnet = '172.16.5.0/24'
            vedge_isp_1_base_subnet = f'172.16.{starting_subnet}.0/24'
            vedge_isp_2_base_subnet = f'172.16.{starting_subnet + 1}.0/24'
            temp_file_name = f'cloud_isp_switch_{switch_index}_interfaces'
            isp_router_objects = generate_network_objects(isp_router_base_subnet, 30)
            isp_switch_1_objects = generate_network_objects(vedge_isp_1_base_subnet, 30, vedge_index)
            isp_switch_2_objects = generate_network_objects(vedge_isp_2_base_subnet, 30, vedge_index)
            isp_1_overall.append(isp_switch_1_objects)
            isp_2_overall.append(isp_switch_2_objects)
            starting_subnet += 2
            switch_index += 1
            generate_interfaces_file(isp_router_objects, router_ip, isp_switch_1_objects, isp_switch_2_objects,
                                     temp_file_name)
            router_ip += 1
            gns3_upload_file_to_node(gns3_server_data, new_project_id, node_id, "etc/network/interfaces",
                                     temp_file_name)
            vedge_index += 44
    matching_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, "ISP-Router")
    if matching_nodes:
        for matching_node in matching_nodes:
            temp_file_name = "ISP-Router"
            node_id = matching_node[0]
            gns3_upload_file_to_node(gns3_server_data, new_project_id, node_id, "startup-config.cfg", temp_file_name)
    # endregion
    # region Start All GNS3 Nodes
    gns3_start_all_nodes(gns3_server_data, new_project_id)
    wait_time = 5  # minutes
    logging.info(f"Deploy - Waiting {wait_time} mins for devices to come up, to resume at {util_resume_time(wait_time)}")
    time.sleep(wait_time * 60)
    # endregion
    # region Viptela vManage Setup Part 1
    logging.info(f"Deploy - Starting vManage device setup part 1")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'vManage'
        matching_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                logging.info(f"Deploy - Logging in to console for node {temp_node_name}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    tn.read_until(b"login:", timeout=1)
                    tn.write(viptela_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=5)
                    tn.write(viptela_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                    if 'Welcome' in output:
                        break
                    logging.info(f"Deploy - {temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(viptela_password.encode("ascii") + b"\n")
                tn.read_until(b"password:")
                tn.write(viptela_password.encode("ascii") + b"\n")
                tn.read_until(b":")
                tn.write(b'1\n')
                tn.read_until(b"[y/n]")
                tn.write(b'y\n')
                tn.read_until(b":")
                tn.write(b'1\n')
                tn.read_until(b"):")
                tn.write(b'y\n')
                tn.read_until(b"umount")
                tn.close()
    logging.info(f"Deploy - Completed vManage Device Setup Part 1")
    # endregion
    # region Viptela vSmart Setup
    logging.info(f"Deploy - Starting vSmart Device Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/viptela')
    file_name = os.path.join(configs_path, 'vsmart_template')
    for server_ip in server_ips:
        temp_node_name = f'vSmart'
        matching_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                node_name = gns3_find_nodes_by_field(gns3_server_data, new_project_id, 'node_id', 'name', node_id)
                logging.info(f"Deploy - Logging in to console for node {node_name[0]}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    output = tn.read_until(b"login:", timeout=2).decode('ascii')
                    if 'vsmart#' in output:
                        tn.write(b"\r\n")
                        break
                    tn.write(viptela_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=2)
                    tn.write(viptela_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=10).decode('ascii')
                    if 'Login incorrect' in output:
                        tn.read_until(b"login:", timeout=1)
                        tn.write(viptela_username.encode("ascii") + b"\n")
                        tn.read_until(b"Password:", timeout=1)
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        tn.write(b"\r\n")
                        break
                    elif 'Welcome' in output:
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        tn.read_until(b"password:", timeout=2)
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        tn.write(b"\r\n")
                        break
                    logging.info(f"Deploy - {temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"#")
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                    logging.info(f"Deploy - Sending configuration commands to {node_name[0]}")
                    for line in lines:
                        formatted_line = line.format(
                            hostname=temp_node_name,
                            latitude='40.758701',
                            longitude='-111.876183',
                            system_ip='172.16.2.6',
                            org_name=org_name,
                            vbond_address=vbond_address,
                            vpn_0_eth1_ip_address='172.16.4.6/30',
                            vpn_0_eth1_ip_gateway='172.16.4.5',
                            vpn_512_eth0_ip_address='172.16.2.6/24',
                            vpn_512_eth0_ip_gateway='172.16.2.1'
                        )
                        tn.write(formatted_line.encode('ascii') + b"\n")
                        tn.read_until(b"#")
                tn.write(b"\r\n")
                output = tn.read_until(b"Commit complete.").decode('ascii')
                # tn.write(b"\r\n")
                # exit_var = tn.read_until(b"vSmart#").decode('ascii')
                # if temp_node_name not in exit_var:
                #        sys.exit()
                tn.write(b"exit\r")
                tn.read_until(b"exit")
                tn.close()
    logging.info(f"Deploy - Completed vSmart Device Setup")
    # endregion
    # region Viptela vBond Setup
    logging.info(f"Deploy - Starting vBond Device Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/viptela')
    file_name = os.path.join(configs_path, 'vbond_template')
    for server_ip in server_ips:
        temp_node_name = f'vBond'
        matching_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                node_name = gns3_find_nodes_by_field(gns3_server_data, new_project_id, 'node_id', 'name', node_id)
                logging.info(f"Deploy - Logging in to console for node {temp_node_name}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    output = tn.read_until(b"login:", timeout=1).decode('ascii')
                    if 'vbond#' in output:
                        tn.write(b"\r\n")
                        break
                    tn.write(viptela_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                    if 'Login incorrect' in output:
                        tn.read_until(b"login:", timeout=1)
                        tn.write(viptela_username.encode("ascii") + b"\n")
                        tn.read_until(b"Password:", timeout=1)
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        tn.write(b"\r\n")
                        break
                    elif 'Welcome' in output:
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        tn.read_until(b"password:", timeout=2)
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        tn.write(b"\r\n")
                        break
                    logging.info(f"Deploy - {temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"#")
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                    logging.info(f"Deploy - Sending configuration commands to {temp_node_name}")
                    for line in lines:
                        formatted_line = line.format(
                            hostname=temp_node_name,
                            latitude='40.758701',
                            longitude='-111.876183',
                            system_ip='172.16.2.10',
                            org_name=org_name,
                            vbond_address=vbond_address,
                            vpn_0_eth1_ip_address='172.16.4.10/30',
                            vpn_0_eth1_ip_gateway='172.16.4.9',
                            vpn_512_eth0_ip_address='172.16.2.10/24',
                            vpn_512_eth0_ip_gateway='172.16.2.1'
                        )
                        tn.write(formatted_line.encode('ascii') + b"\n")
                        tn.read_until(b"#")
                tn.write(b"\r\n")
                output = tn.read_until(b"Commit complete.").decode('ascii')
                # tn.write(b"\r\n")
                # exit_var = tn.read_until(b"vSmart#").decode('ascii')
                # if temp_node_name not in exit_var:
                #        sys.exit()
                tn.write(b"exit\r")
                tn.read_until(b"exit")
    logging.info(f"Deploy - Completed vBond Device Setup")
    # endregion
    # region Viptela vManage Setup Part 2
    logging.info(f"Deploy - Starting vManage setup part 2")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/viptela')
    file_name = os.path.join(configs_path, 'vmanage_template')
    vdevices = [6, 10]
    for server_ip in server_ips:
        temp_node_name = f'vManage'
        matching_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                logging.info(f"Deploy - Logging in to console for node {temp_node_name}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    output = tn.read_until(b"login:", timeout=2).decode('ascii')
                    if 'vManage#' in output:
                        break
                    elif 'vManage:~$' in output:
                        tn.write(b"exit\r\n")
                        tn.read_until(b"#")
                        break
                    tn.write(viptela_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=1)
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"#", timeout=1).decode('ascii')
                    if 'vmanage#' in output:
                        break
                    logging.info(f"Deploy - {temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"#")
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                    logging.info(f"Deploy - Sending configuration commands to {temp_node_name}")
                    for line in lines:
                        formatted_line = line.format(
                            hostname=temp_node_name,
                            latitude='40.758701',
                            longitude='-111.876183',
                            system_ip='172.16.2.2',
                            org_name=org_name,
                            vbond_address=vbond_address,
                            vpn_0_eth1_ip_address='172.16.4.2/30',
                            vpn_0_eth1_ip_gateway='172.16.4.1',
                            vpn_512_eth0_ip_address='172.16.2.2/24',
                            vpn_512_eth0_ip_gateway='172.16.2.1'
                        )
                        tn.write(formatted_line.encode('ascii') + b"\n")
                        tn.read_until(b"#")
                tn.write(b"\r\n")
                # exit_var = tn.read_until(b"vSmart#").decode('ascii')
                # if temp_node_name not in exit_var:
                #        sys.exit()
                tn.write(b'vshell\r\n')
                tn.read_until(b'vManage:~$')
                tn.write(b'openssl genrsa -out SDWAN.key 2048\r\n')
                tn.read_until(b'vManage:~$')
                tn.write(
                    b'openssl req -x509 -new -nodes -key SDWAN.key -sha256 -days 2000 -subj "/C=US/ST=MS/O=sdwan-lab/CN=sdwan-lab" -out SDWAN.pem\r')
                tn.read_until(b'vManage:~$')
                tn.write(b'exit\r\n')
                tn.read_until(b'#')
                for vdevice in vdevices:
                    scp_command = f"request execute vpn 512 scp /home/admin/SDWAN.pem admin@172.16.2.{vdevice}:/home/admin"
                    tn.write(scp_command.encode('ascii') + b"\r")
                    test_o = tn.read_until(b"?", timeout=2).decode('ascii')
                    if "fingerprint" in test_o:
                        tn.write(b'yes\r\n')
                    else:
                        tn.write(b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                tn.write(b'exit\r\n')
                tn.close()
    logging.info(f"Deploy - Completed vManage Device Setup Part 2")
    # endregion
    # region Viptela vEdge Device Setup
    logging.info(f"Deploy - Starting vEdge Device Setup for {vedge_count} vEdges")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/viptela')
    file_name = os.path.join(configs_path, 'vedge_cloud_site_template')
    vedge_lan_objects = generate_vedge_objects(vedge_count)
    isp_index = 0
    for server_ip in server_ips:
        for i in range(1, vedge_count + 1):
            temp_node_name = f'vEdge_{i:003}'
            matching_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, temp_node_name)
            if matching_nodes:
                for matching_node in matching_nodes:
                    node_id, console_port, aux = matching_node
                    node_name = gns3_find_nodes_by_field(gns3_server_data, new_project_id, 'node_id', 'name', node_id)
                    for vedge_lan_object in vedge_lan_objects:
                        if vedge_lan_object['vedge'] == temp_node_name:
                            lan_dhcp_pool = vedge_lan_object['lan_dhcp_pool']
                            lan_subnet_address = vedge_lan_object['lan_subnet_address']
                            lan_dhcp_exclude = vedge_lan_object['lan_dhcp_exclude']
                            lan_gateway_address = vedge_lan_object['lan_gateway_address']
                            client_1_address = vedge_lan_object['client_1_address']
                            mgmt_address = vedge_lan_object['mgmt_address']
                            mgmt_gateway = vedge_lan_object['mgmt_gateway']
                            system_ip = vedge_lan_object['system_ip']
                            site_id = vedge_lan_object['site_id']
                    for dictionary_0 in isp_1_overall[isp_index]:
                        if dictionary_0['vedge'] == temp_node_name:
                            vpn_0_ge0_0_ip_address = dictionary_0['vedge_address']
                            vpn_0_ge0_0_ip_gateway = dictionary_0['router_address']
                    for dictionary_1 in isp_2_overall[isp_index]:
                        if dictionary_1['vedge'] == temp_node_name:
                            vpn_0_ge0_1_ip_address = dictionary_1['vedge_address']
                            vpn_0_ge0_1_ip_gateway = dictionary_1['router_address']
                    vedge_hostname = f"{temp_node_name}_{city_data[temp_node_name]['city']}"
                    logging.info("-----------------------------------------------------------------------------------")
                    logging.info(f"Deploy - Starting vEdge Device Setup for {node_name[0]} - vEdge {i} of {vedge_count}")
                    tn = telnetlib.Telnet(server_ip, console_port)
                    while True:
                        tn.write(b"\r\n")
                        output = tn.read_until(b"login:", timeout=1).decode('ascii')
                        if 'vedge#' in output:
                            tn.write(b"\r\n")
                            break
                        tn.write(viptela_username.encode("ascii") + b"\n")
                        tn.read_until(b"Password:")
                        tn.write(viptela_old_password.encode("ascii") + b"\n")
                        output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                        if 'Login incorrect' in output:
                            tn.read_until(b"login:", timeout=1)
                            tn.write(viptela_username.encode("ascii") + b"\n")
                            tn.read_until(b"Password:", timeout=1)
                            tn.write(viptela_password.encode("ascii") + b"\n")
                            tn.write(b"\r\n")
                            break
                        elif 'Welcome' in output:
                            tn.write(viptela_password.encode("ascii") + b"\n")
                            tn.read_until(b"password:", timeout=2)
                            tn.write(viptela_password.encode("ascii") + b"\n")
                            tn.write(b"\r\n")
                            break
                        logging.info(
                            f"Deploy - {temp_node_name} not available yet, trying again in 30 seconds")
                        time.sleep(30)
                    tn.write(b"\r\n")
                    tn.read_until(b"#")
                    with open(file_name, 'r') as f:
                        lines = f.readlines()
                        logging.info(f"Deploy - Sending configuration commands to {node_name[0]}")
                        for line in lines:
                            formatted_line = line.format(
                                vedge_hostname=vedge_hostname,
                                latitude=city_data[temp_node_name]['latitude'],
                                longitude=city_data[temp_node_name]['longitude'],
                                system_ip=system_ip,
                                site_id=site_id,
                                org_name=org_name,
                                vbond_address=vbond_address,
                                vpn_0_ge0_0_ip_address=vpn_0_ge0_0_ip_address,
                                vpn_0_ge0_0_ip_gateway=vpn_0_ge0_0_ip_gateway,
                                vpn_0_ge0_1_ip_address=vpn_0_ge0_1_ip_address,
                                vpn_0_ge0_1_ip_gateway=vpn_0_ge0_1_ip_gateway,
                                vpn_1_ge0_2_ip_address=lan_dhcp_pool,
                                dhcp_pool=lan_subnet_address,
                                dhcp_exclude=lan_dhcp_exclude,
                                dhcp_gateway=lan_gateway_address,
                                client_1_address=client_1_address,
                                vpn_512_eth0_ip_address=mgmt_address,
                                vpn_512_eth0_ip_gateway=mgmt_gateway
                            )
                            tn.write(formatted_line.encode('ascii') + b"\n")
                            tn.read_until(b"#")
                    tn.write(b"\r\n")
                    output = tn.read_until(b"Commit complete.").decode('ascii')
                    tn.write(b"exit\r")
                    tn.read_until(b"exit")
                    tn.close()
                    logging.info(f"Deploy - Completed vEdge Device Setup for {temp_node_name}, Remaining - {vedge_count - i}")
                    if i % 44 == 0 and i != 0:
                        isp_index += 1
    logging.info(f"Deploy - Completed vEdge Device Setup for {vedge_count} vEdge devices")
    # endregion
    # region Viptela vManage API Setup
    auth = Authentication()
    while True:
        try:
            logging.info(f"Deploy - Checking if vManage API is available..")
            response = auth.get_jsessionid(gns3_server_data)
            break
        except:
            logging.info(f'Deploy - vManage API is yet not available, checking again in 1 minute at {util_resume_time(1)}')
            time.sleep(60)
    vmanage_headers = vmanage_create_auth(gns3_server_data)
    logging.info(f"Deploy - Starting vManage API Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'vManage'
        matching_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    output = tn.read_until(b"login:", timeout=2).decode('ascii')
                    if '#' in output:
                        tn.write(b"\r\n")
                        tn.read_until(b"#")
                        tn.write(b'vshell\r\n')
                        break
                    elif ':~$' in output:
                        tn.write(b"\r\n")
                        break
                    tn.write(viptela_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=1)
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"#", timeout=1).decode('ascii')
                    if '#' in output:
                        tn.write(b"\r\n")
                        tn.read_until(b"#")
                        tn.write(b'vshell\r\n')
                        break
                    logging.info(f"Deploy - {temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b'$')
                tn.write(b"cat SDWAN.pem\r")
                tn.read_until(b"cat SDWAN.pem")
                vmanage_root_cert = tn.read_until(b"-----END CERTIFICATE-----")
                vmanage_root_cert = vmanage_root_cert.decode('ascii').split('\r\n', 1)[1]
                vmanage_root_cert = vmanage_root_cert.replace('\r\n', '\n')
                vmanage_set_org(gns3_server_data, vmanage_headers)
                vmanage_set_cert_type(gns3_server_data, vmanage_headers)
                vmanage_set_cert(gns3_server_data, vmanage_headers, vmanage_root_cert)
                vmanage_sync_rootcertchain(gns3_server_data, vmanage_headers)
                vmanage_set_vbond(gns3_server_data, vmanage_headers)
                vmanage_csr = vmanage_generate_csr(gns3_server_data, vmanage_headers, vmanage_address, 'vmanage')
                tn.write(b'exit\r\n')
                tn.read_until(b'#')
                tn.write(b'vshell\r\n')
                tn.read_until(b'$')
                tn.write(b'echo -n "' + vmanage_csr.encode('ascii') + b'\n" > vdevice.csr\r\n')
                tn.read_until(b'$')
                tn.write(b"sed '/^$/d' vdevice.csr\n")
                tn.read_until(b'$')
                tn.write(
                    b'openssl x509 -req -in vdevice.csr -CA SDWAN.pem -CAkey SDWAN.key -CAcreateserial -out vdevice.crt -days 2000 -sha256\r\n')
                tn.read_until(b'$')
                tn.write(b"cat vdevice.crt\r")
                tn.read_until(b"cat vdevice.crt\r")
                vdevice_cert = tn.read_until(b"-----END CERTIFICATE-----")
                vdevice_cert = vdevice_cert.decode('ascii').split('\r\n', 1)[1]
                vdevice_cert = vdevice_cert.replace('\r\n', '\n')
                vmanage_install_cert(gns3_server_data, vmanage_headers, vdevice_cert)
                vmanage_set_device(gns3_server_data, vmanage_headers, vsmart_address, "vsmart")
                vmanage_set_device(gns3_server_data, vmanage_headers, vbond_address, "vbond")
                vbond_csr = vmanage_generate_csr(gns3_server_data, vmanage_headers, vbond_address, 'vbond')
                vsmart_csr = vmanage_generate_csr(gns3_server_data, vmanage_headers, vsmart_address, 'vsmart')
                tn.write(b'exit\r\n')
                tn.read_until(b'#')
                tn.write(b'vshell\r\n')
                tn.read_until(b'$')
                tn.write(b'echo -n "' + vsmart_csr.encode('ascii') + b'\n" > vdevice.csr\r\n')
                tn.read_until(b'$')
                tn.write(b"sed '/^$/d' vdevice.csr\n")
                tn.read_until(b'$')
                tn.write(
                    b'openssl x509 -req -in vdevice.csr -CA SDWAN.pem -CAkey SDWAN.key -CAcreateserial -out vdevice.crt -days 2000 -sha256\r\n')
                tn.read_until(b'$')
                tn.write(b"cat vdevice.crt\r")
                tn.read_until(b"cat vdevice.crt\r")
                vdevice_cert = tn.read_until(b"-----END CERTIFICATE-----")
                vdevice_cert = vdevice_cert.decode('ascii').split('\r\n', 1)[1]
                vdevice_cert = vdevice_cert.replace('\r\n', '\n')
                vmanage_install_cert(gns3_server_data, vmanage_headers, vdevice_cert)
                tn.write(b'exit\r\n')
                tn.read_until(b'#')
                tn.write(b'vshell\r\n')
                tn.read_until(b'$')
                tn.write(b'echo -n "' + vbond_csr.encode('ascii') + b'\n" > vdevice.csr\r\n')
                tn.read_until(b'$')
                tn.write(b"sed '/^$/d' vdevice.csr\n")
                tn.read_until(b'$')
                tn.write(
                    b'openssl x509 -req -in vdevice.csr -CA SDWAN.pem -CAkey SDWAN.key -CAcreateserial -out vdevice.crt -days 2000 -sha256\r\n')
                tn.read_until(b'$')
                tn.write(b"cat vdevice.crt\r")
                tn.read_until(b"cat vdevice.crt\r")
                vdevice_cert = tn.read_until(b"-----END CERTIFICATE-----")
                vdevice_cert = vdevice_cert.decode('ascii').split('\r\n', 1)[1]
                vdevice_cert = vdevice_cert.replace('\r\n', '\n')
                vmanage_install_cert(gns3_server_data, vmanage_headers, vdevice_cert)
                tn.write(b'exit\r\n')
                tn.read_until(b'#')
                tn.close()
    logging.info(f"Deploy - Completed vManage API Setup")
    # endregion
    # region Viptela vEdge Final Setup
    logging.info(f"Deploy - Starting vEdge Certificate setup and deployment into Viptela Environment")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    ve = 101
    v = 1
    for server_ip in server_ips:
        temp_node_name = f'vManage'
        matching_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, temp_node_name)
        vedge_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, "vEdge")
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                logging.info(f"Deploy - Logging in to console for node {temp_node_name}")
                for vedge_node in vedge_nodes:
                    vedge_id, vedge_console, vedge_aux = vedge_node
                    node_name = gns3_find_nodes_by_field(gns3_server_data, new_project_id, 'node_id', 'name', vedge_id)
                    scp_command = f"request execute vpn 512 scp /home/admin/SDWAN.pem admin@172.16.2.{ve}:/home/admin"
                    scp_2_command = f"request execute vpn 512 scp /home/admin/vedge.crt admin@172.16.2.{ve}:/home/admin"
                    ssh_command = f"request execute vpn 512 ssh admin@172.16.2.{ve}"
                    ssh_2_command = f"request execute vpn 512 ssh admin@172.16.2.10"
                    tn = telnetlib.Telnet(server_ip, console_port)
                    logging.info(f"Deploy - Starting vEdge Certificate Setup for {node_name[0]} - vEdge {v} of {vedge_count}")
                    while True:
                        tn.write(b"\r\n")
                        output = tn.read_until(b"login:", timeout=2).decode('ascii')
                        if '#' in output:
                            tn.write(b"\r\n")
                            tn.read_until(b"#")
                            tn.write(b'vshell\r\n')
                            break
                        elif ':~$' in output:
                            tn.write(b"\r\n")
                            break
                        tn.write(viptela_username.encode("ascii") + b"\n")
                        tn.read_until(b"Password:", timeout=1)
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        output = tn.read_until(b"#", timeout=1).decode('ascii')
                        if '#' in output:
                            tn.write(b"\r\n")
                            tn.read_until(b"#")
                            tn.write(b'vshell\r\n')
                            break
                        logging.info(
                            f"Deploy - {temp_node_name} not available yet, trying again in 30 seconds")
                        time.sleep(30)
                    tn.write(b"\r\n")
                    tn.read_until(b'$')
                    tn.write(b'rm -rf vedge*\r\n')
                    tn.read_until(b'$')
                    tn.write(b'exit\r\n')
                    # SCP SDWAN.pem to vEdge
                    tn.read_until(b'#')
                    tn.write(scp_command.encode('ascii') + b"\n")
                    test_o = tn.read_until(b"?", timeout=2).decode('ascii')
                    if "fingerprint" in test_o:
                        tn.write(b'yes\r\n')
                    else:
                        tn.write(b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    # SSH to vEdge
                    tn.write(ssh_command.encode('ascii') + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    tn.write(b'request root-cert-chain install /home/admin/SDWAN.pem\n')
                    tn.read_until(b'#')
                    tn.write(b'request csr upload home/admin/vedge.csr\n')
                    tn.read_until(b":")
                    tn.write(b'sdwan-lab\n')
                    tn.read_until(b":")
                    tn.write(b'sdwan-lab\n')
                    tn.read_until(b'#')
                    # SCP the vEdge.csr to the vManage
                    tn.write(b'request execute vpn 512 scp /home/admin/vedge.csr admin@172.16.2.2:/home/admin\r\n')
                    test_o = tn.read_until(b"?", timeout=2).decode('ascii')
                    if "fingerprint" in test_o:
                        tn.write(b'yes\r\n')
                    else:
                        tn.write(b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    # Drop back to the vManage
                    tn.write(b'exit\r\n')
                    tn.read_until(b'vManage#')
                    tn.write(b'vshell\r\n')
                    tn.read_until(b'$')
                    tn.write(
                        b'openssl x509 -req -in vedge.csr -CA SDWAN.pem -CAkey SDWAN.key -CAcreateserial -out vedge.crt -days 2000 -sha256\n')
                    tn.read_until(b'$')
                    tn.write(b'exit\r\n')
                    tn.read_until(b'#')
                    # SCP the vEdge.crt to the vEdge
                    tn.write(scp_2_command.encode('ascii') + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    # SSH to the vEdge to install the new cert
                    tn.write(ssh_command.encode('ascii') + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    while True:
                        tn.write(b'request certificate install /home/admin/vedge.crt\r\n')
                        tn.read_until(b'#')
                        tn.write(b'show certificate serial\r\n')
                        cert_output = tn.read_until(b"#").decode("ascii")
                        chassis_regex = r"Chassis number: (.+?)\s+serial number:"
                        serial_regex = r"serial number: ([A-F0-9]+)"
                        chassis_number = re.search(chassis_regex, cert_output).group(1)
                        serial_number = re.search(serial_regex, cert_output).group(1)
                        if chassis_number and serial_number:
                            break
                        logging.info(
                            f"Deploy - {node_name[0]} tried to install certificate too quickly, trying again in 10 seconds ")
                        time.sleep(10)
                    tn.write(b'exit\r\n')
                    tn.read_until(b'#')
                    vedge_install_command = f"request vedge add chassis-num {chassis_number} serial-num {serial_number}"
                    tn.write(ssh_2_command.encode('ascii') + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    tn.write(vedge_install_command.encode('ascii') + b"\n")
                    tn.read_until(b'#')
                    tn.write(b'exit\r\n')
                    tn.read_until(b'#')
                    tn.write(vedge_install_command.encode('ascii') + b"\n")
                    tn.read_until(b'#')
                    ve += 1
                    logging.info(f"Deploy - Completed vEdge Certificate Setup for {node_name[0]}, Remaining - {vedge_count - v}")
                    tn.close()
                    v += 1
    while True:
        try:
            auth = Authentication()
            response = auth.get_jsessionid(gns3_server_data)
            break
        except:
            logging.info(f'Deploy - vManage API is yet not available')
            time.sleep(60)
    vmanage_headers = vmanage_create_auth(gns3_server_data)
    vmanage_push_certs(gns3_server_data, vmanage_headers)
    logging.info(f"Deploy - Completed vEdge Certificate setup and deployment into Viptela Environment")
    # endregion
    # region Deploy Site Clients in Lab
    network_test_tool_template_id = gns3_get_template_id(gns3_server_data, 'Network_Test_Tool')
    client_filename = 'client_interfaces'
    client_node_file_path = 'etc/network/interfaces'
    generate_client_interfaces_file(client_filename)
    vedge_deploy_data, client_deploy_data, site_drawing_deploy_data = generate_vedge_deploy_data(vedge_count)
    if vedge_count == 1:
        client_every = 1
    elif vedge_count <= 5:
        client_every = 2
    elif vedge_count <= 10:
        client_every = 2
    elif vedge_count <= 20:
        client_every = 2
    else:
        client_every = 5
    if config_client_every: client_every = config_client_every
    v = 1
    vedge_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, "vEdge")
    if vedge_nodes:
        for vedge_node in vedge_nodes:
            temp_file_name = "client_interfaces"
            node_id = vedge_node[0]
            if v % client_every == 0:
                network_test_node_id = gns3_create_node(gns3_server_data, new_project_id, network_test_tool_template_id,
                                                        client_deploy_data[f"network_test_client_{v:03}_deploy_data"])
                gns3_update_nodes(gns3_server_data, new_project_id, network_test_node_id,
                                  client_deploy_data[f"network_test_client_{v:03}_deploy_data"])
                gns3_upload_file_to_node(gns3_server_data, new_project_id, network_test_node_id, client_node_file_path,
                                         temp_file_name)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 3, 0, network_test_node_id, 0, 0)
                gns3_start_node(gns3_server_data, new_project_id, network_test_node_id)
            v += 1
    # endregion
    # region Push vEdge Certs to Control Devices
    logging.info(f"Deploy - Waiting 5 mins to send final API call to vManage to push vEdge certificates to control devices, to resume at {util_resume_time(5)}")
    time.sleep(300)
    while True:
        try:
            auth = Authentication()
            response = auth.get_jsessionid(gns3_server_data)
            break
        except:
            logging.info(f'Deploy - vManage API is yet not available')
            time.sleep(60)
    vmanage_headers = vmanage_create_auth(gns3_server_data)
    vmanage_push_certs(gns3_server_data, vmanage_headers)
    # endregion
    # region Validation
    wait_time = 10  # minutes
    logging.info(f"Deploy - Waiting {wait_time} minutes to validate deployment, to resume at {util_resume_time(wait_time)}")
    time.sleep(wait_time * 60)
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'Client_001'
        vedge_nodes = f'vEdge_'
        matching_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, temp_node_name)
        client_nodes = gns3_find_nodes_by_name(gns3_server_data, new_project_id, vedge_nodes)
        client_ip = 101
        successful_site = 0
        i = 1
        if matching_nodes:
            node_id, console_port, aux = matching_nodes[0]
            node_name = gns3_find_nodes_by_field(gns3_server_data, new_project_id, 'node_id', 'name', node_id)
            logging.info(f"-----------------------------------------------------------------------------------")
            logging.info(f"Deploy - Starting deployment validation on node {node_name[0]}")
            tn = telnetlib.Telnet(server_ip, console_port)
            tn.write(b"\r\n")
            tn.read_until(b"#")
            for client_node in client_nodes:
                ping_command = f"ping -c 2 -W 1 172.16.{client_ip}.1"
                tn.write(ping_command.encode('ascii') + b"\r")
                output = tn.read_until(b"loss", timeout=5).decode('ascii')
                if "100% packet" in output:
                    client_node_name = \
                    gns3_find_nodes_by_field(gns3_server_data, new_project_id, 'node_id', 'name', client_nodes[i][0])[0]
                    logging.info(f"Deploy - Packet Loss to Site {client_ip}")
                else:
                    logging.info(f"Deploy - Successfully connected to Site {client_ip}")
                    successful_site += 1
                client_ip += 1
    logging.info(f"Deploy - Successful connection to {successful_site} of {len(client_nodes)} Sites")
    logging.info(f"Deploy - Completed deployment validation for project {project_name}")
    # endregion

    end_time = time.time()
    total_time = (end_time - start_time) / 60
    logging.info(f"Total time for GNS3 Lab Deployment with {vedge_count} vEdge Devices: {total_time:.2f} minutes")
    # endregion


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
