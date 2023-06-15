import requests
import json
import telnetlib
import time
import datetime
import urllib3
import ipaddress
import os
import re
import logging
import logging.handlers
import sqlite3
import sys
from modules.gns3_actions import *
from modules.versa_actions import *
from modules.gns3_variables import *
from modules.gns3_dynamic_data import *
from modules.gns3_query import *


def versa_deploy():
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
    flexvnf_info = []
    mgmt_switch_nodes = []
    isp_switch_nodes = []
    flexvnf_lan_objects = []
    flexvnf_lan_object = []
    isp_1_overall = []
    isp_2_overall = []
    flexvnf_nodes = []
    vmanage_root_cert = ""
    configure_mgmt_tap = 0
    deployment_type = 'versa'
    deployment_status = 'running'
    deployment_step = '- Action - '
    cloud_node_deploy_data = {"x": 25, "y": -554, "name": "MGMT-Cloud-TAP", "node_type": "cloud",
                              "compute_id": "local", "symbol": ":/symbols/cloud.svg"}
    required_qemu_images = {"versa-director-c19c43c-21.2.3.qcow2", "versa-analytics-67ff6c7-21.2.3.qcow2", "versa-flexvnf-67ff6c7-21.2.3.qcow2"}
    required_image_response = 201
    # endregion
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # region Runtime
    start_time = time.time()
    # region GNS3 Lab Setup
    # time.sleep(10)
    c = conn.cursor()
    c.execute("SELECT * FROM config")
    row = c.fetchone()
    conn.close()
    if row:
        server_name = row[1]
        server_ip = row[2]
        server_port = row[3]
        project_name = row[7]
        new_project_id = row[8]
        flexvnf_count = row[9]
        tap_name = row[10]
        vmanage_api_ip = row[11]
    if tap_name == 'none':
        use_tap = 0
    else:
        use_tap = 1

    gns3_server_data = [{"GNS3 Server": server_ip, "Server Name": server_name, "Server Port": server_port,
                    "vManage API IP": vmanage_api_ip, "Project Name": project_name, "Project ID": new_project_id,
                    "Tap Name": tap_name,
                    "Site Count": flexvnf_count, "Use Tap": use_tap, "Deployment Type": deployment_type, "Deployment Status": deployment_status, "Deployment Step": deployment_step}]
    isp_switch_count = (flexvnf_count // 40) + 1
    mgmt_switch_count = (flexvnf_count // 30) + 1
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM deployments")
    c.execute("SELECT COUNT(*) FROM deployments")
    count = c.fetchone()[0]
    if count == 0:
        c.execute(
            "INSERT INTO deployments (server_name, server_ip, project_name) VALUES (?, ?, ?)", (server_ip, server_name, project_name))
        conn.commit()

    gns3_actions_upload_images(gns3_server_data)
    for image in required_qemu_images:
        response_code = gns3_query_get_image(server_ip, server_port, 'qemu', image)
        if response_code != 201:
            log_and_update_db(server_name, project_name, deployment_type, 'Failed', 'Image Validation',
                              f"{image} image not on GNS3 Server")
            return 404
    gns3_actions_versa_remove_templates(gns3_server_data)
    gns3_set_project(gns3_server_data, new_project_id)
    # endregion
    # region Create GNS3 Templates
    deployment_step = 'Creating Templates'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Starting Template Creation")
    versa_director_template_id = gns3_create_template(gns3_server_data, versa_director_template_data)
    versa_analytics_template_id = gns3_create_template(gns3_server_data, versa_analytics_template_data)
    versa_flexvnf_template_id = gns3_create_template(gns3_server_data, versa_flexvnf_template_data)
    openvswitch_isp_template_id = gns3_create_template(gns3_server_data, openvswitch_isp_template_data)
    # cisco_iou_template_id = gns3_create_template(gns3_server_data, cisco_l3_router_template_data)
    network_test_tool_template_id = gns3_create_template(gns3_server_data, network_test_tool_template_data)
    openvswitch_template_id = gns3_create_template(gns3_server_data, openvswitch_cloud_template_data)
    temp_hub_data = generate_temp_hub_data(mgmt_main_switchport_count, mgmt_main_hub_template_name)
    regular_ethernet_hub_template_id = gns3_create_template(gns3_server_data, temp_hub_data)
    temp_hub_data = generate_temp_hub_data(mgmt_switchport_count, mgmt_hub_template_name)
    hub_template_id = gns3_create_template(gns3_server_data, temp_hub_data)
    nat_node_template_id = gns3_query_get_template_id(server_ip, server_port, "NAT")
    cloud_node_template_id = gns3_query_get_template_id(server_ip, server_port, "Cloud")
    # endregion
    #  region Setup Dynamic Networking
    flexvnf_deploy_data, client_deploy_data, site_drawing_deploy_data = versa_generate_flexvnf_deploy_data(flexvnf_count)
    mgmt_switch_deploy_data = generate_mgmt_switch_deploy_data(mgmt_switch_count)
    # endregion
    # region Deploy GNS3 Nodes
    deployment_step = 'Deploy GNS3 Nodes'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Node Deployment")
    
    versa_director_node_id = gns3_create_node(gns3_server_data, new_project_id, versa_director_template_id, versa_director_deploy_data)
    versa_analytics_node_id = gns3_create_node(gns3_server_data, new_project_id, versa_analytics_template_id, versa_analytics_deploy_data)
    versa_controller_node_id = gns3_create_node(gns3_server_data, new_project_id, versa_flexvnf_template_id,
                                               versa_controller_deploy_data)
    isp_ovs_node_id = gns3_create_node(gns3_server_data, new_project_id, openvswitch_isp_template_id, openvswitch_isp_deploy_data)
    mgmt_main_switch_node_id = gns3_create_node(gns3_server_data, new_project_id, regular_ethernet_hub_template_id,
                                                main_mgmt_switch_deploy_data)
    versa_control_switch_node_id = gns3_create_node(gns3_server_data, new_project_id, regular_ethernet_hub_template_id,
                                                versa_control_switch_deploy_data)
    nat_node_id = gns3_create_cloud_node(gns3_server_data, new_project_id, nat_node_deploy_data)
    cloud_node_id = gns3_create_cloud_node(gns3_server_data, new_project_id, cloud_node_deploy_data)

    for i in range(1, mgmt_switch_count + 1):
        node_name = f"MGMT_switch_{i:03}"
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, node_name)
        if not matching_nodes:
            node_id, node_name = gns3_create_node_multi_return(gns3_server_data, new_project_id, hub_template_id,
                                                               mgmt_switch_deploy_data[
                                                                   f"mgmt_switch_{i:03}_deploy_data"])
            mgmt_switch_nodes.append({'node_name': node_name, 'node_id': node_id})
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Node {node_name} already exists in project {project_name}")
    for i in range(1, flexvnf_count + 1):
        node_name = f"FlexVNF_{i:03}"
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, node_name)
        if not matching_nodes:
            node_id, node_name = gns3_create_node_multi_return(gns3_server_data, new_project_id, versa_flexvnf_template_id,
                                                               flexvnf_deploy_data[f"flexvnf_{i:03}_deploy_data"])
            flexvnf_info.append({'node_name': node_name, 'node_id': node_id})
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Node {node_name} already exists in project {project_name}")
    gns3_update_nodes(gns3_server_data, new_project_id, versa_director_node_id, versa_director_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, versa_analytics_node_id, versa_analytics_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, versa_controller_node_id, versa_controller_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, openvswitch_isp_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, main_mgmt_switch_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, deploy_data_z)

    for i in range(1, mgmt_switch_count + 1):
        matching_node = mgmt_switch_nodes[i - 1]
        if matching_node:
            node_id = matching_node['node_id']
            gns3_update_nodes(gns3_server_data, new_project_id, node_id,
                              mgmt_switch_deploy_data[f"mgmt_switch_{i:03}_deploy_data"])
            gns3_update_nodes(gns3_server_data, new_project_id, node_id, deploy_data_z)
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"No nodes found in project {project_name} for MGMT_switch_{i}")

    for i in range(1, flexvnf_count + 1):
        matching_node = flexvnf_info[i - 1]
        if matching_node:
            node_id = matching_node['node_id']
            gns3_update_nodes(gns3_server_data, new_project_id, node_id, flexvnf_deploy_data[f"flexvnf_{i:03}_deploy_data"])
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"No nodes found in project {project_name} for FlexVNF {i}")
    # endregion
    # region Connect GNS3 Lab Nodes
    deployment_step = 'Connect GNS3 Nodes'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting GNS3 Nodes Connect")
    matching_nodes = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'name', 'ports', 'MGMT-Cloud-TAP')
    mgmt_tap_interface = 0
    for port in matching_nodes[0]:
        if port["short_name"] == tap_name:
            mgmt_tap_interface = port['port_number']
    gns3_connect_nodes(gns3_server_data, new_project_id, nat_node_id, 0, 0, isp_ovs_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, 1, 0, versa_controller_node_id, 3, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, 2, 0, versa_controller_node_id, 4, 0)
    if use_tap == 1:
        gns3_connect_nodes(gns3_server_data, new_project_id, cloud_node_id, 0, mgmt_tap_interface,
                           mgmt_main_switch_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 1, versa_director_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 2, versa_analytics_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 3, versa_controller_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, versa_control_switch_node_id, 0, 0, versa_director_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, versa_control_switch_node_id, 0, 1, versa_analytics_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, versa_control_switch_node_id, 0, 2, versa_controller_node_id, 2, 0)
    mgmt_switch_interface = 1
    switch_adapter_a = 5
    switch_adapter_b = (switchport_count // 2) + 4
    mgmt_switch_node_index = 0
    for i in range(mgmt_switch_count):
        first_flexvnf_index = i * 30
        last_flexvnf_index = min((i + 1) * 30, flexvnf_count)
        mgmt_switch_node_id = mgmt_switch_nodes[mgmt_switch_node_index]['node_id']
        mgmt_switch_index = i + 5
        gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_switch_node_id, 0, 0, mgmt_main_switch_node_id, 0,
                           mgmt_switch_index)
        for j in range(first_flexvnf_index, last_flexvnf_index):
            flexvnf_node_id = flexvnf_info[j]['node_id']
            gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_switch_node_id, 0, mgmt_switch_interface,
                               flexvnf_node_id, 0, 0)
            gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, switch_adapter_a, 0, flexvnf_node_id,
                               1, 0)
            gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, switch_adapter_b, 0, flexvnf_node_id,
                               2, 0)
            switch_adapter_a += 1
            switch_adapter_b += 1
            mgmt_switch_interface += 1
            if (j + 1) % 44 == 0:
                switch_adapter_a = 5
                switch_adapter_b = (switchport_count // 2) + 4
                mgmt_switch_interface = 1
        mgmt_switch_node_index += 1
    # endregion
    # region Create GNS3 Drawings
    gns3_create_drawing(gns3_server_data, new_project_id, big_block_deploy_data)
    for i in range(1, flexvnf_count + 1):
        gns3_create_drawing(gns3_server_data, new_project_id,
                            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"])
    # endregion
    # region Deploy GNS3 Node Config Files
    deployment_step = 'Node Configs'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Node Config Creation")
    matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "Cloud_ISP")
    starting_subnet = 6
    router_ip = 0
    switch_index = 0
    flexvnf_index = 1
    if matching_nodes:
        for matching_node in matching_nodes:
            node_id = matching_node[0]
            isp_router_base_subnet = '172.14.3.0/24'
            flexvnf_isp_1_base_subnet = f'172.14.{starting_subnet}.0/24'
            flexvnf_isp_2_base_subnet = f'172.14.{starting_subnet + 1}.0/24'
            temp_file_name = f'cloud_isp_switch_{switch_index}_interfaces'
            isp_router_objects = generate_network_objects(isp_router_base_subnet, 30)
            isp_switch_1_objects = generate_network_objects(flexvnf_isp_1_base_subnet, 30, flexvnf_index)
            isp_switch_2_objects = generate_network_objects(flexvnf_isp_2_base_subnet, 30, flexvnf_index)
            isp_1_overall.append(isp_switch_1_objects)
            isp_2_overall.append(isp_switch_2_objects)
            starting_subnet += 2
            switch_index += 1
            generate_versa_interfaces_file(isp_router_objects, router_ip, isp_switch_1_objects, isp_switch_2_objects,
                                     temp_file_name)
            router_ip += 1
            gns3_upload_file_to_node(gns3_server_data, new_project_id, node_id, "etc/network/interfaces",
                                     temp_file_name)
            flexvnf_index += 44
    matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "ISP-Router")
    if matching_nodes:
        for matching_node in matching_nodes:
            temp_file_name = "versa_ISP-Router"
            node_id = matching_node[0]
            gns3_upload_file_to_node(gns3_server_data, new_project_id, node_id, "startup-config.cfg", temp_file_name)
    # endregion
    # region Start All GNS3 Nodes
    deployment_step = 'Starting Nodes'
    gns3_start_all_nodes(gns3_server_data, new_project_id)
    # endregion
    # region Deploy Site Clients in Lab
    deployment_step = 'Deploy Site Clients'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Deploying clients into each site.")
    network_test_tool_template_id = gns3_query_get_template_id(server_ip, server_port, 'Network_Test_Tool')
    client_filename = 'client_interfaces'
    client_node_file_path = 'etc/network/interfaces'
    generate_client_interfaces_file(client_filename)
    flexvnf_deploy_data, client_deploy_data, site_drawing_deploy_data = versa_generate_flexvnf_deploy_data(flexvnf_count)
    client_every = 1
    v = 1
    flexvnf_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "FlexVNF")
    if flexvnf_nodes:
        for flexvnf_node in flexvnf_nodes:
            temp_file_name = "client_interfaces"
            node_id = flexvnf_node[0]
            if v % client_every == 0:
                network_test_node_id = gns3_create_node(gns3_server_data, new_project_id, network_test_tool_template_id,
                                                        client_deploy_data[f"network_test_client_{v:03}_deploy_data"])
                gns3_update_nodes(gns3_server_data, new_project_id, network_test_node_id,
                                  client_deploy_data[f"network_test_client_{v:03}_deploy_data"])
                gns3_upload_file_to_node(gns3_server_data, new_project_id, network_test_node_id, client_node_file_path,
                                         temp_file_name)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 3, 0, network_test_node_id, 0, 0)
            v += 1
    # endregion
    # region Versa Director Setup Part 1
    deployment_step = 'Starting Nodes'
    wait_time = 2  # minutes
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Waiting {wait_time} mins for devices to come up, to resume at {util_resume_time(wait_time)}")
    time.sleep(wait_time * 60)
    deployment_step = 'Versa Director device Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Starting Director device setup part 1")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'Director'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {temp_node_name}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    tn.read_until(b"login:", timeout=1)
                    tn.write(versa_director_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=5)
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                    if 'enter setup' in output:
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"Do you want to enter setup? (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"[sudo] password for Administrator: ")
                tn.write(versa_old_password.encode("ascii") + b"\n")
                tn.read_until(b"Do you want to setup hostname for system? (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"Enter hostname:")
                tn.write(b'director.local\n')
                tn.read_until(b"Do you want to setup network interface configuration? (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"Enter interface name [eg. eth0]:")
                tn.write(b'eth0\n')
                tn.read_until(b"Enter IP Address:")
                tn.write(b'172.14.2.2\n')
                tn.read_until(b"Enter Netmask Address:")
                tn.write(b'255.255.255.0\n')
                tn.read_until(b"Configure Gateway Address? (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"Enter Gateway Address:")
                tn.write(b'172.14.2.1\n')
                tn.read_until(b"Configure another interface? (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"Enter interface name [eg. eth0]:")
                tn.write(b'eth1\n')
                tn.read_until(b"Enter IP Address:")
                tn.write(b'172.14.4.2\n')
                tn.read_until(b"Enter Netmask Address:")
                tn.write(b'255.255.255.0\n')
                tn.read_until(b"Configure another interface? (y/n)?")
                tn.write(b'n\n')
                tn.read_until(b"Configure North-Bound interface (If not configured, default 0.0.0.0 will be accepted) (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"Enter interface name [eg. eth0]:")
                tn.write(b'eth0\n')
                tn.read_until(b"Enter interface name [eg. eth0]:")
                tn.write(b'eth1\n')
                tn.read_until(b"Configure another South-Bound interface? (y/n)?")
                tn.write(b'n\n')
                tn.read_until(b"Enable secure mode for Director HA ports? (y/n)?")
                tn.write(b'n\n')
                tn.read_until(b"Secure Director HA communication? (y/n)?")
                tn.write(b'n\n')
                tn.read_until(b"Prompt to set new password at first time UI login? (y/n)?")
                tn.write(b'n\n')
                tn.read_until(b"Edit list of hosts allowed to access Versa GUI? (y/n)?")
                tn.write(b'n\n')
                tn.read_until(b"Press ENTER to continue")
                tn.write(b"\r\n")
                tn.read_until(b"director login:")
                tn.write(versa_director_username.encode("ascii") + b"\n")
                tn.read_until(b"Password:")
                tn.write(versa_old_password.encode("ascii") + b"\n")
                tn.read_until(b"[Administrator@director: ~] $")
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed Director Device Setup Part 1")
    # endregion
    # region Versa Analytics Device Setup
    deployment_step = 'Versa Analytics Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Versa Analytics Device Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    versa_interfaces = """auto eth0
    iface eth0 inet static
    address 172.14.2.6
    netmask 255.255.255.0
    gateway 172.14.2.1
    up echo nameserver 192.168.122.1 > /etc/resolv.conf
    auto eth1
    iface eth1 inet static
    address 172.14.4.6
    netmask 255.255.255.0
    """
    for server_ip in server_ips:
        temp_node_name = f'Analytics'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', node_id)
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {node_name[0]}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    tn.read_until(b"login:", timeout=1)
                    tn.write(versa_analytics_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=5)
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                    if 'admin@versa-analytics:~$' in output:
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                      f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"admin@versa-analytics:~$")
                tn.write(b'sudo su\r\n')
                tn.read_until(b"[sudo] password for admin:")
                tn.write(versa_old_password.encode("ascii") + b"\n")
                tn.read_until(b"[root@versa-analytics: admin]#")
                command = f"echo \"{versa_interfaces}\" > /etc/network/interfaces\n"
                tn.write(command.encode('utf-8'))
                tn.read_until(b"[root@versa-analytics: admin]#")
                tn.write(b"ifdown eth0 && ifup eth0 && ifup eth1\n")
                tn.write(b"exit\n")
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed Versa AnalyticsDevice Setup")
    # endregion
    # region Versa Controller Setup
    deployment_step = 'Versa Controller Device Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Versa Controller Device Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    versa_interfaces = """auto eth0
        iface eth0 inet static
        address 172.14.2.10
        netmask 255.255.255.0
        gateway 172.14.2.1
        up echo nameserver 192.168.122.1 > /etc/resolv.conf
        """
    for server_ip in server_ips:
        temp_node_name = f'Controller'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name',
                                                           node_id)
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                  f"Logging in to console for node {node_name[0]}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    tn.read_until(b"login:", timeout=1)
                    tn.write(versa_analytics_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=5)
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                    if 'admin@versa-flexvnf: ~] $' in output:
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                      f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"admin@versa-flexvnf: ~] $")
                tn.write(b'sudo su\r\n')
                tn.read_until(b"[sudo] password for admin:")
                tn.write(versa_old_password.encode("ascii") + b"\n")
                tn.read_until(b"[root@versa-flexvnf: admin]#")
                command = f"echo \"{versa_interfaces}\" > /etc/network/interfaces\n"
                tn.write(command.encode('utf-8'))
                tn.read_until(b"[root@versa-flexvnf: admin]#")
                tn.write(b"ifdown eth0 && ifup eth0\n")
                tn.write(b"exit\n")
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed Versa Controller Device Setup")
    # endregion
    # region Viptela Director Setup Part 2
    deployment_step = 'Director Setup Part 2'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Director setup part 2")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/versa')
    clustersetup_file = os.path.join(configs_path, 'clustersetup.conf')
    vdevices = [6, 10]
    director_ip = '172.14.2.2'
    versa_configure_analytics_cluster(director_ip)
    for server_ip in server_ips:
        temp_node_name = f'Director'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {temp_node_name}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    if '[Administrator@director: ~] $' in output:
                        break
                    tn.read_until(b"login:", timeout=1)
                    tn.write(versa_analytics_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=5)
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                    if '[Administrator@director: ~] $' in output:
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                      f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"[Administrator@director: ~] $")
                tn.write(b'sudo su\r\n')
                tn.read_until(b"[sudo] password for Administrator:")
                tn.write(versa_old_password.encode("ascii") + b"\n")
                tn.read_until(b"root@director:/home/Administrator#")
                with open(clustersetup_file, 'r') as f:
                    file_contents = f.read()
                remote_file_path = "/opt/versa/vnms/scripts/van-cluster-config/van_cluster_install/clustersetup.conf"
                command = f"echo \"{file_contents}\" > {remote_file_path}\n"
                tn.write(command.encode('utf-8'))
                tn.read_until(b"root@director:/home/Administrator#")
                tn.write(b"cd /opt/versa/vnms/scripts/van-cluster-config/van_cluster_install\r\n")
                tn.read_until(b"root@director:")
                tn.write(b"./van_cluster_installer.py --force\n")
                tn.read_until(b"VAN CLUSTER INSTALL COMPLETED")
                tn.write(b"./van_cluster_installer.py --post-setup --gen-vd-cert\r\n")
                tn.read_until(b"VAN CLUSTER POST-SETUP PROCEDURES COMPLETED")
                time.sleep(30)
    versa_create_provider_org(director_ip)
    versa_create_overlay_prefix(director_ip)
    versa_create_overlay_route(director_ip)
    versa_create_controller_workflow(director_ip)
    time.sleep(30)
    versa_deploy_controller(director_ip)
    time.sleep(30)
    versa_create_device_template(director_ip)
    time.sleep(5)
    versa_deploy_device_template(director_ip)
    time.sleep(5)
    versa_create_device_group(director_ip)
    time.sleep(5)
    versa_create_site_device_workflow_1(director_ip)
    time.sleep(5)
    versa_create_site_device_workflow_2(director_ip)
    time.sleep(5)
    versa_deploy_device_workflow_1(director_ip)
    time.sleep(5)
    versa_deploy_device_workflow_2(director_ip)
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Completed vManage Device Setup Part 2")
    # endregion
    # region Viptela FlexVNF Final Setup
    deployment_step = 'FlexVNF Final Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Starting FlexVNF deivce onboarding")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    v = 1
    for server_ip in server_ips:
        flexvnf_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "FlexVNF")
        if matching_nodes:
            for flexvnf_node in flexvnf_nodes:
                node_id, console_port, aux = flexvnf_node
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                  f"Logging in to console for node {node_name}")
                node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id',
                                                           'name', node_id)
                if v == 1:
                    command = f"sudo /opt/versa/scripts/staging.py -w 0 -n SN101 -c 172.14.5.2 -s 172.14.6.2/30 -g 172.14.6.1 -l SDWAN-Branch@Versa-Root.com -r Controller-01-staging@Versa-Root.com"
                elif v == 2:
                    command = f"sudo /opt/versa/scripts/staging.py -w 0 -n SN102 -c 172.14.5.2 -s 172.14.6.6/30 -g 172.14.6.5 -l SDWAN-Branch@Versa-Root.com -r Controller-01-staging@Versa-Root.com"
                else:
                    sys.exit()
                tn = telnetlib.Telnet(server_ip, console_port)
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                  f"Starting FlexVNF Onboarding for {node_name[0]} - FlexVNF {v} of {flexvnf_count}")
                while True:
                    tn.write(b"\r\n")
                    if '[admin@versa-flexvnf: ~] $' in output:
                        break
                    tn.read_until(b"versa-flexvnf login:", timeout=1)
                    tn.write(versa_analytics_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=5)
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"[admin@versa-flexvnf: ~] $", timeout=5).decode('ascii')
                    if '[admin@versa-flexvnf: ~] $' in output:
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                      f"{node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"[admin@versa-flexvnf: ~] $")
                tn.write(b'sudo su\r\n')
                tn.read_until(b"[sudo] password for admin:")
                tn.write(versa_old_password.encode("ascii") + b"\n")
                tn.read_until(b"[root@versa-flexvnf: admin]#")
                tn.write(command.encode('ascii') + b"\r")
                tn.read_until(b"[root@versa-flexvnf: admin]#")
                tn.close()
                v += 1

    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Completed FlexVNF Certificate setup and deployment into Viptela Environment")
    # endregion
    sys.exit()
    # region Viptela FlexVNF Device Setup
    deployment_step = 'FlexVNF Device Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting FlexVNF Device Setup for {flexvnf_count} FlexVNFs")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/viptela')
    file_name = os.path.join(configs_path, 'flexvnf_cloud_site_template')
    flexvnf_lan_objects = generate_vedge_objects(flexvnf_count, '172.14.2')
    isp_index = 0
    for server_ip in server_ips:
        for i in range(1, flexvnf_count + 1):
            temp_node_name = f'FlexVNF_{i:003}'
            matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
            if matching_nodes:
                for matching_node in matching_nodes:
                    node_id, console_port, aux = matching_node
                    node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', node_id)
                    for flexvnf_lan_object in flexvnf_lan_objects:
                        if flexvnf_lan_object['flexvnf'] == temp_node_name:
                            lan_dhcp_pool = flexvnf_lan_object['lan_dhcp_pool']
                            lan_subnet_address = flexvnf_lan_object['lan_subnet_address']
                            lan_dhcp_exclude = flexvnf_lan_object['lan_dhcp_exclude']
                            lan_gateway_address = flexvnf_lan_object['lan_gateway_address']
                            client_1_address = flexvnf_lan_object['client_1_address']
                            mgmt_address = flexvnf_lan_object['mgmt_address']
                            mgmt_gateway = flexvnf_lan_object['mgmt_gateway']
                            system_ip = flexvnf_lan_object['system_ip']
                            site_id = flexvnf_lan_object['site_id']
                    for dictionary_0 in isp_1_overall[isp_index]:
                        if dictionary_0['flexvnf'] == temp_node_name:
                            vpn_0_ge0_0_ip_address = dictionary_0['flexvnf_address']
                            vpn_0_ge0_0_ip_gateway = dictionary_0['router_address']
                    for dictionary_1 in isp_2_overall[isp_index]:
                        if dictionary_1['flexvnf'] == temp_node_name:
                            vpn_0_ge0_1_ip_address = dictionary_1['flexvnf_address']
                            vpn_0_ge0_1_ip_gateway = dictionary_1['router_address']
                    flexvnf_hostname = f"{temp_node_name}_{city_data[temp_node_name]['city']}"
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting FlexVNF Device Setup for {node_name[0]} - FlexVNF {i} of {flexvnf_count}")
                    tn = telnetlib.Telnet(server_ip, console_port)
                    while True:
                        tn.write(b"\r\n")
                        output = tn.read_until(b"login:", timeout=1).decode('ascii')
                        if 'flexvnf#' in output:
                            tn.write(b"\r\n")
                            break
                        tn.write(viptela_username.encode("ascii") + b"\n")
                        tn.read_until(b"Password:")
                        tn.write(versa_old_password.encode("ascii") + b"\n")
                        output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                        if 'Login incorrect' in output:
                            tn.read_until(b"login:", timeout=1)
                            tn.write(viptela_username.encode("ascii") + b"\n")
                            tn.read_until(b"Password:", timeout=1)
                            tn.write(versa_old_password.encode("ascii") + b"\n")
                            tn.write(b"\r\n")
                            break
                        elif 'Welcome' in output:
                            tn.write(versa_old_password.encode("ascii") + b"\n")
                            tn.read_until(b"password:", timeout=2)
                            tn.write(versa_old_password.encode("ascii") + b"\n")
                            tn.write(b"\r\n")
                            break
                        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                        time.sleep(30)
                    tn.write(b"\r\n")
                    tn.read_until(b"#")
                    with open(file_name, 'r') as f:
                        lines = f.readlines()
                        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Sending configuration commands to {node_name[0]}")
                        for line in lines:
                            formatted_line = line.format(
                                flexvnf_hostname=flexvnf_hostname,
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
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed FlexVNF Device Setup for {temp_node_name}, Remaining - {flexvnf_count - i}")
                    if i % 44 == 0 and i != 0:
                        isp_index += 1
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed FlexVNF Device Setup for {flexvnf_count} FlexVNF devices")
    # endregion
    # region Validation
    client_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "Client")
    if client_nodes:
        for client_node in client_nodes:
            node_id, console_port, aux = client_node
            gns3_start_node(gns3_server_data, new_project_id, node_id)
    wait_time = 10  # minutes
    deployment_step = 'Validation'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Waiting {wait_time} minutes to validate deployment, to resume at {util_resume_time(wait_time)}")
    time.sleep(wait_time * 60)
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'Client_001'
        flexvnf_nodes = f'FlexVNF_'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        client_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, flexvnf_nodes)
        client_ip = 101
        successful_site = 0
        i = 1
        if matching_nodes:
            node_id, console_port, aux = matching_nodes[0]
            node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', node_id)
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting deployment validation on node {node_name[0]}")
            tn = telnetlib.Telnet(server_ip, console_port)
            tn.write(b"\r\n")
            tn.read_until(b"#")
            for client_node in client_nodes:
                ping_command = f"ping -c 2 -W 1 172.16.{client_ip}.1"
                tn.write(ping_command.encode('ascii') + b"\r")
                output = tn.read_until(b"loss", timeout=5).decode('ascii')
                if "100% packet" in output:
                    client_node_name = \
                    gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', client_nodes[i][0])[0]
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Packet Loss to Site {client_ip}")
                else:
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,f"Successfully connected to Site {client_ip}")
                    successful_site += 1
                client_ip += 1
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Successful connection to {successful_site} of {len(client_nodes)} Sites")
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed deployment validation for project {project_name}")
    # endregion

    end_time = time.time()
    total_time = (end_time - start_time) / 60
    deployment_step = 'Complete'
    deployment_status = 'Complete'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Total time for GNS3 Lab Deployment with {flexvnf_count} FlexVNF Devices: {total_time:.2f} minutes")
    # endregion

