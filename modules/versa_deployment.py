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
from modules.viptela_actions import *
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
    required_iou_images = {"L3-ADVENTERPRISEK9-M-15.5-2T.bin"}
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
    for image in required_iou_images:
        response_code = gns3_query_get_image(server_ip, server_port, 'iou', image)
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
    cisco_iou_template_id = gns3_create_template(gns3_server_data, cisco_l3_router_template_data)
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
    isp_deploy_data = generate_isp_deploy_data(isp_switch_count)
    mgmt_switch_deploy_data = generate_mgmt_switch_deploy_data(mgmt_switch_count)
    # endregion
    # region Deploy GNS3 Nodes
    deployment_step = 'Deploy GNS3 Nodes'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Node Deployment")
    
    versa_director_node_id = gns3_create_node(gns3_server_data, new_project_id, versa_director_template_id, versa_director_deploy_data)
    versa_analytics_node_id = gns3_create_node(gns3_server_data, new_project_id, versa_analytics_template_id, versa_analytics_deploy_data)
    versa_controller_node_id = gns3_create_node(gns3_server_data, new_project_id, versa_flexvnf_template_id,
                                               versa_controller_deploy_data)
    isp_router_node_id = gns3_create_node(gns3_server_data, new_project_id, cisco_iou_template_id,
                                          isp_router_deploy_data)
    mgmt_main_switch_node_id = gns3_create_node(gns3_server_data, new_project_id, regular_ethernet_hub_template_id,
                                                main_mgmt_switch_deploy_data)
    nat_node_id = gns3_create_cloud_node(gns3_server_data, new_project_id, nat_node_deploy_data)
    cloud_node_id = gns3_create_cloud_node(gns3_server_data, new_project_id, cloud_node_deploy_data)
    for i in range(1, isp_switch_count + 1):
        node_name = f"ISP_{i:03}"
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, node_name)
        if not matching_nodes:
            node_id, node_name = gns3_create_node_multi_return(gns3_server_data, new_project_id,
                                                               openvswitch_template_id,
                                                               isp_deploy_data[f"isp_{i:03}_deploy_data"])
            isp_switch_nodes.append({'node_name': node_name, 'node_id': node_id})
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Node {node_name} already exists in project {project_name}")
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
    gns3_update_nodes(gns3_server_data, new_project_id, isp_router_node_id, isp_router_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, main_mgmt_switch_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, deploy_data_z)

    for i in range(1, isp_switch_count + 1):
        matching_node = isp_switch_nodes[i - 1]
        if matching_node:
            node_id = matching_node['node_id']
            gns3_update_nodes(gns3_server_data, new_project_id, node_id, isp_deploy_data[f"isp_{i:03}_deploy_data"])
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"No nodes found in project {project_name} for isp_switch_{i}")

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
    cloud_isp_node_id = isp_switch_nodes[0]['node_id']
    gns3_connect_nodes(gns3_server_data, new_project_id, nat_node_id, 0, 0, isp_router_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, cloud_isp_node_id, 1, 0, versa_director_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, cloud_isp_node_id, 2, 0, versa_analytics_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, cloud_isp_node_id, 3, 0, versa_controller_node_id, 1, 0)
    if use_tap == 1:
        gns3_connect_nodes(gns3_server_data, new_project_id, cloud_node_id, 0, mgmt_tap_interface,
                           mgmt_main_switch_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 1, versa_director_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 2, versa_analytics_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 3, versa_controller_node_id, 0, 0)
    mgmt_switch_interface = 1
    switch_adapter_a = 5
    switch_adapter_b = (switchport_count // 2) + 4
    cloud_isp_node_index = 0
    mgmt_switch_node_index = 0
    for i in range(isp_switch_count):
        cloud_isp_node_id = isp_switch_nodes[i]['node_id']
        gns3_connect_nodes(gns3_server_data, new_project_id, cloud_isp_node_id, 0, 0, isp_router_node_id, 0, i + 1)
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
            cloud_isp_node_id = isp_switch_nodes[cloud_isp_node_index]['node_id']
            gns3_connect_nodes(gns3_server_data, new_project_id, cloud_isp_node_id, switch_adapter_a, 0, flexvnf_node_id,
                               1, 0)
            gns3_connect_nodes(gns3_server_data, new_project_id, cloud_isp_node_id, switch_adapter_b, 0, flexvnf_node_id,
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
            isp_router_base_subnet = '172.16.5.0/24'
            flexvnf_isp_1_base_subnet = f'172.16.{starting_subnet}.0/24'
            flexvnf_isp_2_base_subnet = f'172.16.{starting_subnet + 1}.0/24'
            temp_file_name = f'cloud_isp_switch_{switch_index}_interfaces'
            isp_router_objects = generate_network_objects(isp_router_base_subnet, 30)
            isp_switch_1_objects = generate_network_objects(flexvnf_isp_1_base_subnet, 30, flexvnf_index)
            isp_switch_2_objects = generate_network_objects(flexvnf_isp_2_base_subnet, 30, flexvnf_index)
            isp_1_overall.append(isp_switch_1_objects)
            isp_2_overall.append(isp_switch_2_objects)
            starting_subnet += 2
            switch_index += 1
            generate_interfaces_file(isp_router_objects, router_ip, isp_switch_1_objects, isp_switch_2_objects,
                                     temp_file_name)
            router_ip += 1
            gns3_upload_file_to_node(gns3_server_data, new_project_id, node_id, "etc/network/interfaces",
                                     temp_file_name)
            flexvnf_index += 44
    matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "ISP-Router")
    if matching_nodes:
        for matching_node in matching_nodes:
            temp_file_name = "ISP-Router"
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
    wait_time = 5  # minutes

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
                tn.read_until(b"Configure Gateway Address? (y/n)?")
                tn.write(b'n\n')
                #tn.read_until(b"Enter Gateway Address:")
                #tn.write(b'172.16.4.1\n')
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
                #tn.read_until(b"Press ENTER to continue")
                #tn.write(b"\r\n")
                #tn.read_until(b"director login:")
                #tn.write(versa_director_username.encode("ascii") + b"\n")
                #tn.read_until(b"Password:")
                #tn.write(versa_old_password.encode("ascii") + b"\n")
                #tn.read_until(b"[Administrator@director: ~] $")
                tn.close()
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed Director Device Setup Part 1")
    # endregion
    # region Versa Analytics Device Setup
    deployment_step = 'Versa Analytics Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Versa Analytics Device Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    remote_file_name = '/etc/network/interfaces'
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/versa')
    local_file_name = os.path.join(configs_path, 'versa_interface_template')
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
                with open(local_file_name, 'r') as local_file:
                    lines = local_file.readlines()
                formatted_lines = []
                for line in lines:
                    formatted_line = line.format(
                        eth0_ip_address='172.14.2.6',
                        eth0_netmask='255.255.255.0',
                        eth0_gateway='172.14.2.1',
                        eth1_ip_address='172.14.4.6',
                        eth1_netmask='255.255.255.0',
                    )
                    formatted_lines.append(formatted_line.strip())
                command = f"echo $'{chr(92)}n'.join([{', '.join(map(repr, formatted_lines))}]) > {remote_file_name}\n"
                tn.write(command.encode('ascii'))
                tn.read_until(b"[root@versa-analytics: admin]#")
                tn.write(b"exit\n")
                tn.close()
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed Versa AnalyticsDevice Setup")
    # endregion
    # region Viptela vBond Setup
    deployment_step = 'Versa Controller Device Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Versa Controller Device Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    remote_file_name = '/etc/network/interfaces'
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/versa')
    local_file_name = os.path.join(configs_path, 'versa_interface_template')
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
                with open(local_file_name, 'r') as local_file:
                    lines = local_file.readlines()
                formatted_lines = []
                for line in lines:
                    formatted_line = line.format(
                        eth0_ip_address='172.14.2.10',
                        eth0_netmask='255.255.255.0',
                        eth0_gateway='172.14.2.1',
                        eth1_ip_address='172.14.4.10',
                        eth1_netmask='255.255.255.0',
                    )
                    formatted_lines.append(formatted_line.strip())
                command = f"echo $'{chr(92)}n'.join([{', '.join(map(repr, formatted_lines))}]) > {remote_file_name}\n"
                tn.write(command.encode('ascii'))
                tn.read_until(b"[root@versa-flexvnf: admin]#")
                tn.write(b"exit\n")
                tn.close()
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed Versa Controller Device Setup")
    # endregion
    sys.exit()
    # region Viptela Director Setup Part 2
    deployment_step = 'Director Setup Part 2'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Director setup part 2")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/versa')
    file_name = os.path.join(configs_path, 'director_template')
    vdevices = [6, 10]
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
                with open(local_file_name, 'r') as local_file:
                    lines = local_file.readlines()
                formatted_lines = []
                for line in lines:
                    formatted_line = line.format(
                        eth0_ip_address='172.14.2.10',
                        eth0_netmask='255.255.255.0',
                        eth0_gateway='172.14.2.1',
                        eth1_ip_address='172.16.4.10',
                        eth1_netmask='255.255.255.252',
                        eth1_gateway='172.16.4.9',
                    )
                    formatted_lines.append(formatted_line)
                for line in formatted_lines:
                    tn.write(f"echo '{line}' >> {remote_file_name}\n".encode('ascii'))
                    tn.read_until(b"[Administrator@director: ~] $")
                tn.write(b"\r\n")
                # exit_var = tn.read_until(b"Analytics#").decode('ascii')
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
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                tn.write(b'exit\r\n')
                tn.close()
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Completed vManage Device Setup Part 2")
    # endregion
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
    # region Viptela vManage API Setup
    deployment_step = ' vManage API Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting vManage API Setup")
    auth = Authentication()
    while True:
        try:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Checking if vManage API is available..")
            response = auth.get_jsessionid(gns3_server_data)
            break
        except:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f'vManage API is yet not available, checking again in 1 minute at {util_resume_time(1)}')
            time.sleep(60)
    vmanage_headers = vmanage_create_auth(gns3_server_data)
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'vManage'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
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
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"#", timeout=1).decode('ascii')
                    if '#' in output:
                        tn.write(b"\r\n")
                        tn.read_until(b"#")
                        tn.write(b'vshell\r\n')
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
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
                vmanage_set_device(gns3_server_data, vmanage_headers, versa_analytics_address, "versa_analytics")
                vmanage_set_device(gns3_server_data, vmanage_headers, vbond_address, "vbond")
                vbond_csr = vmanage_generate_csr(gns3_server_data, vmanage_headers, vbond_address, 'vbond')
                versa_analytics_csr = vmanage_generate_csr(gns3_server_data, vmanage_headers, versa_analytics_address, 'versa_analytics')
                tn.write(b'exit\r\n')
                tn.read_until(b'#')
                tn.write(b'vshell\r\n')
                tn.read_until(b'$')
                tn.write(b'echo -n "' + versa_analytics_csr.encode('ascii') + b'\n" > vdevice.csr\r\n')
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
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed vManage API Setup")
    # endregion
    # region Viptela FlexVNF Final Setup
    deployment_step = 'FlexVNF Final Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting FlexVNF Certificate setup and deployment into Viptela Environment")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    ve = 101
    v = 1
    for server_ip in server_ips:
        temp_node_name = f'vManage'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        flexvnf_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "FlexVNF")
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {temp_node_name}")
                for flexvnf_node in flexvnf_nodes:
                    flexvnf_id, flexvnf_console, flexvnf_aux = flexvnf_node
                    node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', flexvnf_id)
                    scp_command = f"request execute vpn 512 scp /home/admin/SDWAN.pem admin@172.16.2.{ve}:/home/admin"
                    scp_2_command = f"request execute vpn 512 scp /home/admin/flexvnf.crt admin@172.16.2.{ve}:/home/admin"
                    ssh_command = f"request execute vpn 512 ssh admin@172.16.2.{ve}"
                    ssh_2_command = f"request execute vpn 512 ssh admin@172.16.2.10"
                    tn = telnetlib.Telnet(server_ip, console_port)
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting FlexVNF Certificate Setup for {node_name[0]} - FlexVNF {v} of {flexvnf_count}")
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
                        tn.write(versa_old_password.encode("ascii") + b"\n")
                        output = tn.read_until(b"#", timeout=1).decode('ascii')
                        if '#' in output:
                            tn.write(b"\r\n")
                            tn.read_until(b"#")
                            tn.write(b'vshell\r\n')
                            break
                        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                        time.sleep(30)
                    tn.write(b"\r\n")
                    tn.read_until(b'$')
                    tn.write(b'rm -rf flexvnf*\r\n')
                    tn.read_until(b'$')
                    tn.write(b'exit\r\n')
                    # SCP SDWAN.pem to FlexVNF
                    tn.read_until(b'#')
                    tn.write(scp_command.encode('ascii') + b"\n")
                    test_o = tn.read_until(b"?", timeout=2).decode('ascii')
                    if "fingerprint" in test_o:
                        tn.write(b'yes\r\n')
                    else:
                        tn.write(b"\n")
                    tn.read_until(b"Password:")
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    # SSH to FlexVNF
                    tn.write(ssh_command.encode('ascii') + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    tn.write(b'request root-cert-chain install /home/admin/SDWAN.pem\n')
                    tn.read_until(b'#')
                    tn.write(b'request csr upload home/admin/flexvnf.csr\n')
                    tn.read_until(b":")
                    tn.write(b'sdwan-lab\n')
                    tn.read_until(b":")
                    tn.write(b'sdwan-lab\n')
                    tn.read_until(b'#')
                    # SCP the FlexVNF.csr to the vManage
                    tn.write(b'request execute vpn 512 scp /home/admin/flexvnf.csr admin@172.16.2.2:/home/admin\r\n')
                    test_o = tn.read_until(b"?", timeout=2).decode('ascii')
                    if "fingerprint" in test_o:
                        tn.write(b'yes\r\n')
                    else:
                        tn.write(b"\n")
                    tn.read_until(b"Password:")
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    # Drop back to the vManage
                    tn.write(b'exit\r\n')
                    tn.read_until(b'vManage#')
                    tn.write(b'vshell\r\n')
                    tn.read_until(b'$')
                    tn.write(
                        b'openssl x509 -req -in flexvnf.csr -CA SDWAN.pem -CAkey SDWAN.key -CAcreateserial -out flexvnf.crt -days 2000 -sha256\n')
                    tn.read_until(b'$')
                    tn.write(b'exit\r\n')
                    tn.read_until(b'#')
                    # SCP the FlexVNF.crt to the FlexVNF
                    tn.write(scp_2_command.encode('ascii') + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    # SSH to the FlexVNF to install the new cert
                    tn.write(ssh_command.encode('ascii') + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    while True:
                        tn.write(b'request certificate install /home/admin/flexvnf.crt\r\n')
                        tn.read_until(b'#')
                        tn.write(b'show certificate serial\r\n')
                        cert_output = tn.read_until(b"#").decode("ascii")
                        chassis_regex = r"Chassis number: (.+?)\s+serial number:"
                        serial_regex = r"serial number: ([A-F0-9]+)"
                        chassis_number = re.search(chassis_regex, cert_output).group(1)
                        serial_number = re.search(serial_regex, cert_output).group(1)
                        if chassis_number and serial_number:
                            break
                        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{node_name[0]} tried to install certificate too quickly, trying again in 10 seconds ")
                        time.sleep(10)
                    tn.write(b'exit\r\n')
                    tn.read_until(b'#')
                    flexvnf_install_command = f"request flexvnf add chassis-num {chassis_number} serial-num {serial_number}"
                    tn.write(ssh_2_command.encode('ascii') + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    tn.write(flexvnf_install_command.encode('ascii') + b"\n")
                    tn.read_until(b'#')
                    tn.write(b'exit\r\n')
                    tn.read_until(b'#')
                    tn.write(flexvnf_install_command.encode('ascii') + b"\n")
                    tn.read_until(b'#')
                    ve += 1
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed FlexVNF Certificate Setup for {node_name[0]}, Remaining - {flexvnf_count - v}")
                    tn.close()
                    v += 1
    while True:
        try:
            auth = Authentication()
            response = auth.get_jsessionid(gns3_server_data)
            break
        except:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f'vManage API is yet not available')
            time.sleep(60)
    vmanage_headers = vmanage_create_auth(gns3_server_data)
    vmanage_push_certs(gns3_server_data, vmanage_headers)
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed FlexVNF Certificate setup and deployment into Viptela Environment")
    # endregion
    # region Push FlexVNF Certs to Control Devices
    deployment_step = 'Push FlexVNF Certs'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Waiting 5 mins to send final API call to vManage to push FlexVNF certificates to control devices, to resume at {util_resume_time(5)}")
    time.sleep(300)
    while True:
        try:
            auth = Authentication()
            response = auth.get_jsessionid(gns3_server_data)
            break
        except:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f'vManage API is yet not available')
            time.sleep(60)
    vmanage_headers = vmanage_create_auth(gns3_server_data)
    vmanage_push_certs(gns3_server_data, vmanage_headers)
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

