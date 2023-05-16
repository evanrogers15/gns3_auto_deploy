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

from modules.gns3_actions import *
from modules.viptela_actions import *
from modules.gns3_variables import *
from modules.gns3_dynamic_data import *


def viptela_deploy():
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
    configure_mgmt_tap = 0
    # endregion
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # region Runtime
    start_time = time.time()
    update_query = '''
            UPDATE deployments
            SET deployment_type = ?,
                deployment_status = ?,
                deployment_step = ?
            WHERE id = ?;
        '''
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
        vedge_count = row[9]
        tap_name = row[10]
        vmanage_api_ip = row[11]
    if tap_name:
        use_tap = 1
    else:
        use_tap = 0

    gns3_server_data = [{"GNS3 Server": server_ip, "Server Name": server_name, "Server Port": server_port,
                    "vManage API IP": vmanage_api_ip, "Project Name": project_name, "Project ID": new_project_id,
                    "Tap Name": tap_name,
                    "Site Count": vedge_count, "Use Tap": use_tap, "Deployment Type": "viptela"}]
    isp_switch_count = (vedge_count // 40) + 1
    mgmt_switch_count = (vedge_count // 30) + 1
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM deployments")
    count = c.fetchone()[0]

    if count == 0:
        # Perform initial insertion to populate the table
        c.execute(
            "INSERT INTO deployments (server_name, server_ip, server_port, project_name) VALUES (?, ?, ?, ?)", (server_ip, server_port, server_name, project_name))
        conn.commit()

    #gns3_delete_project(gns3_server_data)
    gns3_actions_remove_templates(gns3_server_data)
    #new_project_id = gns3_create_project(gns3_server_data)
    gns3_set_project(gns3_server_data, new_project_id)
    # endregion
    # region Create GNS3 Templates
    c.execute(update_query, ('viptela', 'ok', 'Creating Templates', 1))
    conn.commit()
    
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
    c.execute(update_query, ('viptela', 'ok', 'Deploying Nodes', 1))
    conn.commit()
    
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
    c.execute(update_query, ('viptela', 'ok', 'Connecting Nodes', 1))
    conn.commit()
    
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
    if configure_mgmt_tap == 1:
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
    c.execute(update_query, ('viptela', 'ok', 'Creating Config Files', 1))
    conn.commit()
    
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
    c.execute(update_query, ('viptela', 'ok', 'Starting Nodes', 1))
    conn.commit()
    
    gns3_start_all_nodes(gns3_server_data, new_project_id)
    wait_time = 5  # minutes
    logging.info(f"Deploy - Waiting {wait_time} mins for devices to come up, to resume at {util_resume_time(wait_time)}")
    time.sleep(wait_time * 60)
    # endregion
    # region Viptela vManage Setup Part 1
    c.execute(update_query, ('viptela', 'ok', 'vManage Part 1', 1))
    conn.commit()
    
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
    c.execute(update_query, ('viptela', 'ok', 'vSmart Setup', 1))
    conn.commit()
    
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
    c.execute(update_query, ('viptela', 'ok', 'vBond Setup', 1))
    conn.commit()
    
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
    c.execute(update_query, ('viptela', 'ok', 'vManage Part 2', 1))
    conn.commit()
    
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
    c.execute(update_query, ('viptela', 'ok', 'vEdge Setup', 1))
    conn.commit()
    
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
    c.execute(update_query, ('viptela', 'ok', 'vManage API Setup', 1))
    conn.commit()
    
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
    c.execute(update_query, ('viptela', 'ok', 'vEdge Final Setup', 1))
    conn.commit()
    
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
    c.execute(update_query, ('viptela', 'ok', 'Site Client Deployment', 1))
    conn.commit()
    
    network_test_tool_template_id = gns3_get_template_id(gns3_server_data, 'Network_Test_Tool')
    client_filename = 'client_interfaces'
    client_node_file_path = 'etc/network/interfaces'
    generate_client_interfaces_file(client_filename)
    vedge_deploy_data, client_deploy_data, site_drawing_deploy_data = generate_vedge_deploy_data(vedge_count)
    client_every = 1

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
    c.execute(update_query, ('viptela', 'ok', 'Pushing vEdge Certs', 1))
    conn.commit()
    
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
    c.execute(update_query, ('viptela', 'ok', 'Validation', 1))
    conn.commit()
    
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
    c.execute(update_query, ('viptela', 'ok', 'Complete', 1))
    conn.commit()
    conn.close()
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    logging.info(f"Total time for GNS3 Lab Deployment with {vedge_count} vEdge Devices: {total_time:.2f} minutes")
    # endregion

