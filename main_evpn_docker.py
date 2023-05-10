import requests
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


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# region Variables from app_config
project_name = app_config.project_name
vedge_count = app_config.vedge_count
tap_name = app_config.tap_name
mgmt_network_address = app_config.mgmt_network_address

gns3_server_data = app_config.gns3_server_data
city_data = app_config.city_data
deploy_new_gns3_project = app_config.deploy_new_gns3_project
use_existing_gns3_project = app_config.use_existing_gns3_project
cleanup_gns3 = app_config.cleanup_gns3
test_lab = app_config.test_lab
delete_node_name = app_config.delete_node_name
# endregion

def main():
    # region Intialize Variables
    # region Viptela Variables
    vmanage_headers = {}
    viptela_username = 'admin'
    viptela_old_password = "admin"
    viptela_password = 'PW4netops'
    org_name = 'sdwan-lab'
    vbond_address = '172.16.4.10'
    vmanage_address = '172.16.2.2'
    vsmart_address = '172.16.4.6'
    lan_subnet_address = ''
    lan_gateway_address = ''
    lan_dhcp_exclude = ''
    lan_dhcp_pool = ''

    system_ip = ''
    site_id = 0
    mgmt_address = ''
    mgmt_gateway = ''
    # endregion
    # region GNS3 Template Variables
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    switchport_count = 95

    mgmt_main_switchport_count = 30

    masking_block_drawing_height = 0
    masking_block_drawing_width = 0
    masking_block_drawing_x = 0
    masking_block_drawing_y = 0

    # region Variables: GNS3 Template Data
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
    cloud_node_deploy_data = {"x": 234, "y": -316, "name": "MGMT-Cloud-TAP", "node_type": "cloud",
                              "compute_id": "local", "symbol": ":/symbols/cloud.svg"}
    main_mgmt_switch_deploy_data = {"x": 278, "y": -141, "name": "Main_MGMT-switch"}
    nat_node_deploy_data = {"x": -154, "y": -554, "name": "Internet", "node_type": "nat", "compute_id": "local",
                            "symbol": ":/symbols/cloud.svg"}

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
    drawing_deploy_data1 = {
        "drawing_01": {"svg": "<svg width=\"374.71428571428567\" height=\"146.57142857142856\"><ellipse cx=\"187\" "
                              "rx=\"188\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" "
                              "stroke-width=\"2\" stroke=\"#000000\" /></svg>", "x": -600, "y": 26, "z": 0},
        "drawing_02": {"svg": "<svg width=\"374.71428571428567\" height=\"146.57142857142856\"><ellipse cx=\"187\" "
                              "rx=\"188\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" "
                              "stroke-width=\"2\" stroke=\"#000000\" /></svg>", "x": -77, "y": 26, "z": 0},
        "drawing_03": {"svg": "<svg width=\"495.7142857142858\" height=\"146.57142857142856\"><ellipse cx=\"247\" "
                              "rx=\"248\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" "
                              "stroke-width=\"2\" stroke=\"#000000\" /></svg>", "x": -390, "y": -274, "z": 0},
        "drawing_04": {"svg": "<svg width=\"207.5\" height=\"146.57142857142856\"><ellipse cx=\"103\" rx=\"104\" "
                              "cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" "
                              "stroke-width=\"2\" stroke=\"#000000\" /></svg>", "x": 422, "y": 21, "z": 0},
        "drawing_05": {"svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" "
                              "font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65001</text></svg>",
                       "x": -453, "y": 75, "z": 2},
        "drawing_06": {"svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" "
                              "font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65002</text></svg>",
                       "x": 69, "y": 74, "z": 2},
        "drawing_07": {"svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" "
                              "font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65000</text></svg>",
                       "x": -189, "y": -268, "z": 2},
        "drawing_08": {"svg": "<svg width=\"95\" height=\"23\"><text font-family=\"Arial Black\" font-size=\"10.0\" "
                              "font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">MLAG Peer "
                              "Link</text></svg>", "x": -457, "y": 99, "z": 2},
        "drawing_09": {"svg": "<svg width=\"95\" height=\"23\"><text font-family=\"Arial Black\" font-size=\"10.0\" "
                              "font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">MLAG Peer "
                              "Link</text></svg>", "x": 66, "y": 101, "z": 2},
        "drawing_10": {"svg": "<svg width=\"356\" height=\"36\"><text font-family=\"Arial\" font-size=\"24.0\" "
                              "fill=\"#000000\" fill-opacity=\"1.0\">Arista EVPN / BGP / VXLAN Lab</text></svg>",
                       "x": -238, "y": -407, "z": 2},
        "drawing_11": {"svg": "<svg width=\"194\" height=\"188\"><text font-family=\"TypeWriter\" font-size=\"10.0\" "
                              "font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">Managment Network: "
                              "172.16.3.0/24\narista-spine1 - 172.16.3.2\narista-spine1 - 172.16.3.3\narista-leaf1 - "
                              "172.16.3.4\narista-leaf2 - 172.16.3.5\narista-leaf3 - 172.16.3.6\narista-leaf4 - "
                              "172.16.3.7\n\nClient Network: 172.16.101.0/24\nVLAN 40\nVXLAN1\nClient-1: "
                              "172.16.101.2\nClient-2: 172.16.101.3\nClient-3: 172.16.101.4\nClient-4: "
                              "172.16.101.5</text></svg>", "x": -603, "y": -33, "z": 2},
        "drawing_12": {"svg": "<svg width=\"902\" height=\"163\"><rect width=\"902\" height=\"163\" fill=\"#00f900\" "
                              "fill-opacity=\"0.19299610894941635\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
                       "x": -640, "y": 318, "z": 0},
        "drawing_13": {"svg": "<svg width=\"74\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" "
                              "font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">VLAN 40</text></svg>",
                       "x": -182, "y": 320, "z": 2}
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
    # endregion
    # endregion

    # region Functions: GNS3 API Functions
    def gns3_create_project():
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            template_data = {"name": project_name}
            node_url = f"http://{server_ip}:{server_port}/v2/projects"
            node_response = make_request("POST", node_url, data=template_data)
            project_id = node_response["project_id"]
            return project_id

    def gns3_create_drawing(project_id, node_data):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/drawings"
            node_response = make_request("POST", node_url, data=node_data)

    def gns3_create_node(project_id, template_id, node_data):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/templates/{template_id}"
            node_response = make_request("POST", node_url, data=node_data)
            node_name = node_response["name"]
            print(f"[{util_current_time()}] - Created Node {node_name}")
            node_id = node_response["node_id"]
            return node_id

    def gns3_create_node_multi_return(project_id, template_id, node_data):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/templates/{template_id}"
            node_response = make_request("POST", node_url, data=node_data)
            node_name = node_response["name"]
            print(f"[{util_current_time()}] - Created Node {node_name}")
            node_id = node_response["node_id"]
            return node_id, node_name

    def gns3_create_cloud_node(project_id, node_data):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes"
            node_response = make_request("POST", node_url, data=node_data)
            node_name = node_response["name"]
            print(f"[{util_current_time()}] - Created Node {node_name}")
            node_id = node_response["node_id"]
            return node_id

    def gns3_create_template(template_data):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            node_url = f"http://{server_ip}:{server_port}/v2/templates"
            node_response = make_request("POST", node_url, data=template_data)
            template_id = node_response["template_id"]
            template_name = node_response["name"]
            print(f"[{util_current_time()}] - Created template {template_name}")
            return template_id

    def gns3_connect_nodes(project_id, node_a, adapter_a, port_a, node_b, adapter_b, port_b):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/links"
            node_data = {"nodes": [{"adapter_number": adapter_a, "node_id": node_a, "port_number": port_a},
                                   {"adapter_number": adapter_b, "node_id": node_b, "port_number": port_b}]}
            node_a_name = gns3_find_nodes_by_field('node_id', 'name', node_a)
            node_b_name = gns3_find_nodes_by_field('node_id', 'name', node_b)
            print(
                f"[{util_current_time()}] - Connected (adapter/port) {adapter_a}/{port_a} of {node_a_name[0]} to (adapter/port) {adapter_b}/{port_b} of {node_b_name[0]}",
                flush=True)
            node_response = make_request("POST", node_url, data=node_data)
            return node_response["link_id"]

    def gns3_delete_nodes():
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            project_id = gns3_get_project_id(project_name)
            nodes = gns3_get_nodes(project_id)
            matching_nodes = gns3_find_nodes_by_name(delete_node_name)
            if matching_nodes:
                for node_id, console_port, aux in matching_nodes:
                    delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
                    response = make_request("DELETE", delete_url)
                    node_name = response["name"]
                    print(f"Deleted node {node_name} on GNS3 Server {server_ip}")
            else:
                print(
                    f"[{util_current_time()}] - No nodes with '{delete_node_name}' in their name were found in project {project_name} on GNS3 Server {server_ip}")

    def gns3_delete_all_nodes(project_id):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            nodes = gns3_get_nodes(project_id)
            for node in nodes:
                node_id = node['node_id']
                delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
                response = make_request("DELETE", delete_url)
                node_name = node["name"]
                print(f"[{util_current_time()}] - Deleted node {node_name} on GNS3 Server {server_ip}")

    def gns3_delete_all_drawings(project_id):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            drawings = gns3_get_drawings(project_id)
            for drawing in drawings:
                drawing_id = drawing['drawing_id']
                delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/drawings/{drawing_id}"
                response = make_request("DELETE", delete_url)
                print(f"[{util_current_time()}] - Deleted drawing {drawing_id} on GNS3 Server {server_ip}")

    def gns3_delete_template(template_name):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            template_id = gns3_get_template_id(template_name)
            if template_id:
                delete_url = f"http://{server_ip}:{server_port}/v2/templates/{template_id}"
                make_request("DELETE", delete_url)
                print(f"[{util_current_time()}] - Deleted template ID {template_name} on GNS3 Server {server_ip}")
            else:
                print(f"No templates with '{template_name}' in their name were found on GNS3 Server {server_ip}")

    def gns3_delete_project(project_name):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            project_id = gns3_get_project_id(project_name)
            if project_id:
                delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}"
                make_request("DELETE", delete_url)
                print(f"[{util_current_time()}] - Deleted project ID {project_name} on GNS3 Server {server_ip}")
            else:
                print(f"No projects with '{project_name}' in their name were found on GNS3 Server {server_ip}")

    def gns3_find_nodes_by_name(search_string=None):
        node_data = gns3_get_nodes(new_project_id)
        if search_string:
            matching_nodes = [node for node in node_data if search_string in node['name']]
            if not matching_nodes:
                return []
            else:
                return [(node['node_id'], node['console'], node['properties'].get('aux')) for node in matching_nodes]
        else:
            return []

    def gns3_get_location_data():
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            url = f"http://{server_ip}:{server_port}/v2/projects/{new_project_id}/drawings"
            response = requests.get(url)
            data = json.loads(response.text)
            nodes = []
            for node in data:
                svg = node['svg']
                x = node['x']
                y = node['y']
                z = node['z']
                nodes.append({'svg': svg, 'x': x, 'y': y, 'z': z})
            return nodes

    def gns3_find_nodes_by_field(search_field, return_field, search_string):
        nodes = gns3_get_nodes(new_project_id)
        if search_string:
            matching_nodes = [node for node in nodes if search_string in node[search_field]]
            if not matching_nodes:
                return []
            else:
                return [(node[return_field]) for node in matching_nodes]
        else:
            return []

    def gns3_get_project_id(project_name):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            url = f"http://{server_ip}:{server_port}/v2/projects"
            response = requests.get(url)
            projects = json.loads(response.text)
            for project in projects:
                if project['name'] == project_name:
                    return project['project_id']
            return None

    def gns3_get_template_id(template_name):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            url = f"http://{server_ip}:{server_port}/v2/templates"
            response = requests.get(url)
            templates = json.loads(response.text)
            for template in templates:
                if template['name'] == template_name:
                    return template['template_id']
            return None

    def gns3_get_drawings(project_id):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/drawings"
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

    def gns3_get_image(image_type, filename):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            url = f"http://{server_ip}:{server_port}/v2/compute/{image_type}/images/{filename}"
            response = requests.get(url)

            return response.status_code

    def gns3_get_nodes(project_id):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes"
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

    def gns3_get_node_files(project_id, node_id, file_path):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/files/{file_path}"
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

    def gns3_reload_node(node_id):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            node_url = f"http://{server_ip}:{server_port}/v2/projects/{new_project_id}/nodes/{node_id}/reload"
            response = make_request("POST", node_url, data={})
            print(f"Reloaded node {node_id}")

    def gns3_upload_symbol(symbol_file, symbol_name):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            url = f'http://{server_ip}:{server_port}/v2/symbols/{symbol_name}/raw'
            headers = {"accept": "*/*"}
            response = requests.post(url, headers=headers, data=symbol_file)
            if response.status_code == 204:
                print(f'[{util_current_time()}] - Uploaded symbol {symbol_name}')
                return
            else:
                print(f'[{util_current_time()}] - Failed to upload {symbol_name}. Status code: {response.status_code}')

    def gns3_upload_file_to_node(project_id, node_id, file_path_var, filename_temp):
        abs_path = os.path.abspath(__file__)
        configs_path = os.path.join(os.path.dirname(abs_path), 'configs/')
        file_path = os.path.join(configs_path, filename_temp)
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            # Set the file path and name to be written to the node
            node_name = gns3_find_nodes_by_field('node_id', 'name', node_id)

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
                print(
                    f'[{util_current_time()}] - File - {filename_temp} successfully written to the node {node_name[0]}')
                return
            else:
                print(
                    f'[{util_current_time()}] - Failed to write file to the node {node_name[0]}. Status code: {response.status_code}')

    def gns3_upload_image(image_type, filename):
        image_file_path = f'images/{image_type}'
        abs_path = os.path.abspath(__file__)
        configs_path = os.path.join(os.path.dirname(abs_path), image_file_path)
        file_path = os.path.join(configs_path, filename)
        file_size = util_get_file_size(file_path)
        print(f"File Size: {file_size}")
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            url = f'http://{server_ip}:{server_port}/v2/compute/{image_type}/images/{filename}'
            response = gns3_get_image(image_type, filename)
            if response != 200:
                headers = {"accept": "*/*"}
                print(f'[{util_current_time()}] - Image - {filename} being uploaded to server. Please wait..')
                response = requests.post(url, headers=headers, data=open(file_path, "rb"))
                if response.status_code == 204:
                    print(f'[{util_current_time()}] - Image - {filename} successfully written to server')
                    return
                else:
                    print(
                        f'[{util_current_time()}] - Failed to write file to the server. Status code: {response.status_code}')

    def gns3_update_nodes(project_id, node_id, request_data):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            request_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
            node_name = gns3_find_nodes_by_field('node_id', 'name', node_id)
            request_response = make_request("PUT", request_url, data=request_data)
            print(f"[{util_current_time()}] - Updated deploy data for node {node_name[0]}")

    def gns3_start_node(node_id):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            template_data = {}
            node_url = f"http://{server_ip}:{server_port}/v2/projects/{new_project_id}/nodes/{node_id}/start"
            node_response = make_request("POST", node_url, data=template_data)

    def gns3_stop_node(node_id):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            template_data = {}
            node_url = f"http://{server_ip}:{server_port}/v2/projects/{new_project_id}/nodes/{node_id}/stop"
            node_response = make_request("POST", node_url, data=template_data)

    def gns3_start_all_nodes(project_id):
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            template_data = {}
            print(f"[{util_current_time()}] - Starting all nodes in project {project_name}")
            node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/start"
            node_response = make_request("POST", node_url, data=template_data)
            print(f"[{util_current_time()}] - Started all nodes in project {project_name}")

    def gns3_set_project(project_id):
        project_zoom = 80
        project_scene_height = 1000
        project_scene_width = 2000
        for server_record in gns3_server_data:
            server_ip, server_port = server_record['GNS3 Server'], server_record['Server Port']
            template_data = {"auto_close": False, "scene_height": project_scene_height,
                             "scene_width": project_scene_width,
                             "zoom": project_zoom}
            node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}"
            node_response = make_request("PUT", node_url, data=template_data)
            project_id = node_response["project_id"]
            print(f"[{util_current_time()}] - Update project settings for {project_name}")
            return project_id

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

    def generate_client_interfaces_file(filename_temp, ip):
        abs_path = os.path.abspath(__file__)
        configs_path = os.path.join(os.path.dirname(abs_path), 'configs/')
        filename = os.path.join(configs_path, filename_temp)

        with open(filename, 'w') as f:
            f.write('auto eth0\n')
            f.write('iface eth0 inet dhcp\n')
            f.write('\tup echo nameserver 192.168.122.1 > /etc/resolv.conf\n')
            f.write('\thwaddress ether 4C:D7:17:00:00:00\n\n')
            f.write('auto eth1\n')
            f.write('iface eth1 inet static\n')
            f.write(f'\taddress {ip}\n')
            f.write('\tnetmask 255.255.255.0\n\n')

        print(f"[{util_current_time()}] - Created file {filename_temp}")

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

        print(f"[{util_current_time()}] - Created file {filename_temp}")

    def generate_isp_deploy_data(num_nodes):
        deploy_data = {}
        x = -154
        y = 51

        for i in range(1, num_nodes + 1):
            name = f"Cloud_ISP_{i:03}"
            y += 75
            deploy_data[f"isp_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}

        return deploy_data

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
                    x = x_e + 100 * (e)
                    e += 1
                else:
                    x = x_o + -100 * (o)
                    o += 1
            deploy_data[f"mgmt_switch_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}

        return deploy_data

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
            print(json.dumps(json_data, indent=4))
        else:
            print("Response content is empty.")

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

    # region Functions: GNS3 Actions
    def gns3_actions_upload_images():
        for root, dirs, files in os.walk("images/"):
            for file_name in files:
                image_type = os.path.basename(root)
                print(f"image_type:{image_type}, filename: {file_name}")
                gns3_upload_image(image_type, file_name)

    def gns3_actions_remove_templates():
        gns3_delete_template(vmanage_template_name)
        gns3_delete_template(vbond_template_name)
        gns3_delete_template(vsmart_template_name)
        gns3_delete_template(vedge_template_name)
        gns3_delete_template(cisco_l3_router_template_name)
        gns3_delete_template(network_test_tool_template_name)
        gns3_delete_template(open_vswitch_cloud_template_name)
        gns3_delete_template(mgmt_hub_template_name)
        gns3_delete_template(mgmt_main_hub_template_name)
        gns3_delete_template(arista_ceos_template_name)
        delete_more_than_1_var = 0
        if delete_more_than_1_var == 1:
            while True:
                template_id = gns3_get_template_id(arista_ceos_template_name)
                if not template_id:
                    break
                gns3_delete_template(arista_ceos_template_name)

    # endregion

    # region Runtime
    start_time = time.time()

    # region GNS3 Lab Setup
    if test_lab == 1:
        #gns3_actions_upload_images()

        new_project_id = gns3_get_project_id(project_name)
        gns3_delete_all_drawings(new_project_id)
        #location_data = gns3_get_location_data()
        #drawing_data = {}
        #for i, item_data in enumerate(location_data):
        #    drawing_key = f"drawing_{i + 1:02}"  # e.g., drawing_01, drawing_02, etc.
        #    drawing_data[drawing_key] = item_data

        #print("\n".join([json.dumps({k:v}, separators=(",", ":")) for k,v in drawing_data.items()]))
        #output = "\n".join([f'"{k}": {json.dumps(v, separators=(",", ":"))},' for k,v in drawing_data.items()])

        drawing_index = 1
        for drawing_data in drawing_deploy_data:
            gns3_create_drawing(new_project_id, drawing_deploy_data[f'drawing_{drawing_index:02}'])
            drawing_index += 1
        sys.exit()
    if cleanup_gns3 == 1:
        gns3_delete_project(project_name)
        gns3_actions_remove_templates()
        print(
            f"[{util_current_time()}] - Removed GNS3 project ({project_name} and templates from server. Exiting now.)")
        sys.exit()
    elif deploy_new_gns3_project == 1:
        gns3_delete_project(project_name)
        new_project_id = gns3_create_project()
        gns3_actions_remove_templates()
    elif use_existing_gns3_project == 1:
        new_project_id = gns3_get_project_id(project_name)
        gns3_delete_all_nodes(new_project_id)
        gns3_delete_all_drawings(new_project_id)
    gns3_set_project(new_project_id)
    # endregion
    # region Deploy Nodes
    #gns3_actions_upload_images()
    arista_count = 7
    arista_template_id = gns3_create_template(arista_ceos_template_data)
    temp_hub_data = generate_temp_hub_data(mgmt_main_switchport_count, mgmt_main_hub_template_name)
    regular_ethernet_hub_template_id = gns3_create_template(temp_hub_data)
    network_test_tool_template_id = gns3_create_template(network_test_tool_template_data)
    cloud_node_id = gns3_create_cloud_node(new_project_id, cloud_node_deploy_data)
    mgmt_main_switch_node_id = gns3_create_node(new_project_id, regular_ethernet_hub_template_id,
                                                main_mgmt_switch_deploy_data)
    for i in range(1, arista_count + 1):
        node_id, node_name = gns3_create_node_multi_return(new_project_id, arista_template_id, arista_deploy_data[f"arista_{i:02}_deploy_data"])
        arista_deploy_data[f"arista_{i:02}_deploy_data"]["node_id"] = node_id
        gns3_update_nodes(new_project_id, node_id, arista_deploy_data[f"arista_{i:02}_deploy_data"])
        #temp_ip = f"{mgmt_network_address}{i + 1}"
        #generate_arista_interfaces_file(client_filename, temp_ip)
        #gns3_upload_file_to_node(new_project_id, node_id, client_node_file_path, client_filename)
    gns3_start_all_nodes(new_project_id)
    # endregion
    # region Connect Nodes
    if app_config.configure_mgmt_tap == 1:
        matching_nodes = gns3_find_nodes_by_field('name', 'ports', 'MGMT-Cloud-TAP')
        mgmt_tap_interface = 0
        for port in matching_nodes[0]:
            if port["short_name"] == tap_name:
                mgmt_tap_interface = port['port_number']
        print(mgmt_tap_interface)
        gns3_connect_nodes(new_project_id, mgmt_main_switch_node_id, 0, 0, cloud_node_id, 0, mgmt_tap_interface)
    for i in range(1, arista_count + 1):
        gns3_connect_nodes(new_project_id, mgmt_main_switch_node_id, 0, i + 5,
                           arista_deploy_data[f"arista_{i:02}_deploy_data"]["node_id"], 19, 0)
    for i in range(1, arista_count + 1):
        name = arista_deploy_data[f"arista_{i:02}_deploy_data"]["name"]
        node_id = arista_deploy_data[f"arista_{i:02}_deploy_data"]["node_id"]
        if name == "arista-spine1":
            for k in range(1, 6):
                gns3_connect_nodes(new_project_id, node_id, k, 0,
                                   arista_deploy_data[f"arista_{k + 2:02}_deploy_data"]["node_id"], 11, 0)
        if name == "arista-spine2":
            for k in range(1, 6):
                gns3_connect_nodes(new_project_id, node_id, k, 0,
                                   arista_deploy_data[f"arista_{k + 2:02}_deploy_data"]["node_id"], 12, 0)
        if name == "arista-leaf1":
            gns3_connect_nodes(new_project_id, node_id, 10, 0, arista_deploy_data[f"arista_04_deploy_data"]["node_id"],
                               10, 0)
        if name == "arista-leaf3":
            gns3_connect_nodes(new_project_id, node_id, 10, 0, arista_deploy_data[f"arista_06_deploy_data"]["node_id"],
                               10, 0)
    # endregion
    # region Configure
    print(f"[{util_current_time()}] - Waiting 1 minute for nodes to start")
    time.sleep(60)
    new_project_id = gns3_get_project_id(project_name)
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        arista_nodes = f'arista-'
        client_nodes = gns3_find_nodes_by_name(arista_nodes)
        abs_path = os.path.abspath(__file__)
        configs_path = os.path.join(os.path.dirname(abs_path), 'configs/arista')
        if client_nodes:
            for client_node in client_nodes:
                client_node_id, client_console_port, client_aux = client_node
                temp_node_name = gns3_find_nodes_by_field('node_id', 'name', client_node_id)
                temp_file = temp_node_name[0]
                file_name = os.path.join(configs_path, temp_file)
                tn = telnetlib.Telnet(server_ip, client_aux)
                print(f"[{util_current_time()}] - Starting Configuration Deploy to {temp_node_name[0]}")
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
                    print(
                        f"[{util_current_time()}] - Sending configuration commands to {temp_node_name[0]}")
                    for line in lines:
                        formatted_line = line.format(
                        )
                        tn.write(formatted_line.encode('ascii') + b"\n")
                        tn.read_until(b"#")
                tn.write(b"wr mem\n")
                tn.read_until(b"Copy completed successfully.")
                time.sleep(2)
                gns3_stop_node(client_node_id)
                gns3_start_node(client_node_id)

    # endregion
    # region Deploy Site Clients in Lab
    new_project_id = gns3_get_project_id(project_name)
    regular_ethernet_hub_template_id = gns3_get_template_id('Main-MGMT-Switch')
    network_test_tool_template_id = gns3_get_template_id('Network_Test_Tool')
    v = 1
    leaf_nodes = gns3_find_nodes_by_name("leaf")
    for i in range(1, 4):
        local_switch_deploy_data[f"switch_{i:02}_deploy_data"]["node_id"] = gns3_create_node(new_project_id,
                                                                                             regular_ethernet_hub_template_id,
                                                                                             local_switch_deploy_data[
                                                                                                 f"switch_{i:02}_deploy_data"])
    if leaf_nodes:
        for leaf_node in leaf_nodes:
            node_id = leaf_node[0]
            client_node_id = gns3_create_node(new_project_id, network_test_tool_template_id,
                                              client_deploy_data[f"client_{v:02}_deploy_data"])
            gns3_update_nodes(new_project_id, client_node_id, client_deploy_data[f"client_{v:02}_deploy_data"])
            temp_ip = f"172.16.101.{v + 1}"
            generate_client_interfaces_file(client_filename, temp_ip)
            gns3_upload_file_to_node(new_project_id, client_node_id, client_node_file_path, client_filename)

            if v == 1:
                local_switch_node_id = local_switch_deploy_data["switch_01_deploy_data"]["node_id"]
                gns3_connect_nodes(new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1, 0)
                gns3_connect_nodes(new_project_id, node_id, 1, 0, local_switch_node_id, 0, 0)
            elif v == 2:
                gns3_connect_nodes(new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1, 0)
                gns3_connect_nodes(new_project_id, node_id, 1, 0, local_switch_node_id, 0, 1)
            elif v == 3:
                local_switch_node_id = local_switch_deploy_data["switch_02_deploy_data"]["node_id"]
                gns3_connect_nodes(new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1, 0)
                gns3_connect_nodes(new_project_id, node_id, 1, 0, local_switch_node_id, 0, 3)
            elif v == 4:
                gns3_connect_nodes(new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1, 0)
                gns3_connect_nodes(new_project_id, node_id, 1, 0, local_switch_node_id, 0, 4)
            elif v == 5:
                local_switch_node_id = local_switch_deploy_data["switch_03_deploy_data"]["node_id"]
                gns3_connect_nodes(new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1, 0)
                gns3_connect_nodes(new_project_id, node_id, 1, 0, local_switch_node_id, 0, 4)
            gns3_start_node(client_node_id)
            v += 1
    # endregion
    # region Create GNS3 Drawings
    drawing_index = 1
    for drawing_data in drawing_deploy_data:
        gns3_create_drawing(new_project_id, drawing_deploy_data[f'drawing_{drawing_index:02}'])
        drawing_index += 1
    # endregion
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    print(f"Total time for GNS3 Lab Deployment for project {project_name} deployment: {total_time:.2f} minutes")
    # endregion


if __name__ == '__main__':
    main()
