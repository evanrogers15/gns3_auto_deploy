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
from modules.gns3_query import *

def viptela_mgmt_deploy():
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
    deployment_type = 'viptela_mgmt'
    deployment_status = 'running'
    deployment_step = '- Action - '
    cloud_node_deploy_data = {"x": -79, "y": -485, "name": "MGMT-Cloud-TAP", "node_type": "cloud",
                              "compute_id": "local", "symbol": ":/symbols/cloud.svg"}
    required_qemu_images = {"viptela-vmanage-li-20.10.1-genericx86-64.qcow2", "empty30G.qcow2", "viptela-smart-li-20.10.1-genericx86-64.qcow2", "viptela-edge-20.10.1-genericx86-64.qcow2"}
    required_image_response = 201
    # endregion
    # region Runtime
    start_time = time.time()
    # region GNS3 Lab Setup
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM mgmt_config")
    row = c.fetchone()
    conn.close()
    if row:
        server_name = row[1]
        server_ip = row[2]
        server_port = row[3]
        project_name = row[7]
        new_project_id = row[8]
        vedge_count = row[9]
        isp_tap_name = row[10]
        mgmt_tap_name = row[11]
        vmanage_api_ip = row[12]
    if mgmt_tap_name == 'none':
        use_tap = 0
    else:
        use_tap = 1
    gns3_server_data = [{"GNS3 Server": server_ip, "Server Name": server_name, "Server Port": server_port,
                    "vManage API IP": vmanage_api_ip, "Project Name": project_name, "Project ID": new_project_id,
                    "ISP Tap Name": isp_tap_name, "MGMT Tap Name": mgmt_tap_name,
                    "Site Count": vedge_count, "Use Tap": use_tap, "Deployment Type": deployment_type, "Deployment Status": deployment_status, "Deployment Step": deployment_step}]
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM deployments")
    c.execute("SELECT COUNT(*) FROM deployments")
    count = c.fetchone()[0]
    if count == 0:
        # Perform initial insertion to populate the table
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
    gns3_actions_remove_templates(gns3_server_data)
    gns3_set_project(gns3_server_data, new_project_id)
    # endregion
    # region Create GNS3 Templates
    deployment_step = 'Creating Templates'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Starting Template Creation")
    vmanage_template_id = gns3_create_template(gns3_server_data, viptela_vmanage_template_data)
    vbond_template_id = gns3_create_template(gns3_server_data, viptela_vbond_template_data)
    vsmart_template_id = gns3_create_template(gns3_server_data, viptela_vsmart_template_data)
    temp_hub_data = generate_temp_hub_data(mgmt_main_switchport_count, mgmt_main_hub_template_name)
    regular_ethernet_hub_template_id = gns3_create_template(gns3_server_data, temp_hub_data)
    # endregion
    # region Deploy GNS3 Nodes
    deployment_step = 'Deploy GNS3 Nodes'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Node Deployment")
    vmanage_node_id = gns3_create_node(gns3_server_data, new_project_id, vmanage_template_id, vmanage_deploy_data)
    vsmart_node_id = gns3_create_node(gns3_server_data, new_project_id, vsmart_template_id, vsmart_deploy_data)
    vbond_node_id = gns3_create_node(gns3_server_data, new_project_id, vbond_template_id, vbond_deploy_data)
    mgmt_main_switch_node_id = gns3_create_node(gns3_server_data, new_project_id, regular_ethernet_hub_template_id,
                                                main_mgmt_switch_deploy_data)
    isp_switch_node_id = gns3_create_node(gns3_server_data, new_project_id, regular_ethernet_hub_template_id,
                                                isp_switch_deploy_data)
    cloud_node_id = gns3_create_cloud_node(gns3_server_data, new_project_id, cloud_node_deploy_data)

    gns3_update_nodes(gns3_server_data, new_project_id, vmanage_node_id, vmanage_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, vsmart_node_id, vsmart_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, vbond_node_id, vbond_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, main_mgmt_switch_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, deploy_data_z)
    gns3_update_nodes(gns3_server_data, new_project_id, isp_switch_node_id, isp_switch_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, isp_switch_node_id, deploy_data_z)
    # endregion
    # region Connect GNS3 Lab Nodes
    deployment_step = 'Connect GNS3 Nodes'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting GNS3 Nodes Connect")
    matching_nodes = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'name', 'ports', 'MGMT-Cloud-TAP')
    mgmt_tap_interface = 0
    for port in matching_nodes[0]:
        if port["short_name"] == mgmt_tap_name:
            mgmt_tap_interface = port['port_number']
    for port in matching_nodes[0]:
        if port["short_name"] == isp_tap_name:
            isp_tap_interface = port['port_number']
    gns3_connect_nodes(gns3_server_data, new_project_id, isp_switch_node_id, 0, 1, vmanage_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, isp_switch_node_id, 0, 2, vsmart_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, isp_switch_node_id, 0, 3, vbond_node_id, 1, 0)
    if use_tap == 1:
        gns3_connect_nodes(gns3_server_data, new_project_id, cloud_node_id, 0, mgmt_tap_interface,
                           mgmt_main_switch_node_id, 0, 0)
        gns3_connect_nodes(gns3_server_data, new_project_id, cloud_node_id, 0, isp_tap_interface,
                           isp_switch_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 1, vmanage_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 2, vsmart_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 3, vbond_node_id, 0, 0)
    # endregion
    # region Create GNS3 Drawings
    #gns3_create_drawing(gns3_server_data, new_project_id, big_block_deploy_data)
    #for i in range(1, vedge_count + 1):
    #    gns3_create_drawing(gns3_server_data, new_project_id,
    #                        site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"])
    # drawing_index = 1
    #for drawing_data in viptela_drawing_data:
    #    gns3_create_drawing(gns3_server_data, new_project_id, viptela_drawing_data[f'drawing_{drawing_index:02}'])
    #    drawing_index += 1
    # endregion
    # region Start All GNS3 Nodes
    deployment_step = 'Starting Nodes'
    gns3_start_all_nodes(gns3_server_data, new_project_id)
    # endregion
    # region Viptela vManage Setup Part 1
    deployment_step = 'vManage Setup Part 1'
    wait_time = 5  # minutes
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Waiting {wait_time} mins for devices to come up, to resume at {util_resume_time(wait_time)}")
    time.sleep(wait_time * 60)
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Starting vManage device setup part 1")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'vManage'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {temp_node_name}")
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
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
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
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed vManage Device Setup Part 1")
    # endregion
    # region Viptela vSmart Setup
    deployment_step = 'vSmart Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting vSmart Device Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/viptela')
    file_name = os.path.join(configs_path, 'vsmart_template')
    for server_ip in server_ips:
        temp_node_name = f'vSmart'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', node_id)
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {node_name[0]}")
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
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"#")
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Sending configuration commands to {node_name[0]}")
                    for line in lines:
                        formatted_line = line.format(
                            hostname=temp_node_name,
                            latitude='40.758701',
                            longitude='-111.876183',
                            system_ip='172.16.240.3',
                            org_name=org_name,
                            vbond_address=vbond_address,
                            vpn_0_eth1_ip_address='10.0.0.3/24',
                            vpn_0_eth1_ip_gateway='10.0.0.1',
                            vpn_512_eth0_ip_address='172.16.240.3/24',
                            vpn_512_eth0_ip_gateway='172.16.240.1'
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
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed vSmart Device Setup")
    # endregion
    # region Viptela vBond Setup
    deployment_step = 'vBond Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting vBond Device Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/viptela')
    file_name = os.path.join(configs_path, 'vbond_template')
    for server_ip in server_ips:
        temp_node_name = f'vBond'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', node_id)
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {temp_node_name}")
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
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"#")
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Sending configuration commands to {temp_node_name}")
                    for line in lines:
                        formatted_line = line.format(
                            hostname=temp_node_name,
                            latitude='40.758701',
                            longitude='-111.876183',
                            system_ip='172.16.240.4',
                            org_name=org_name,
                            vbond_address=vbond_address,
                            vpn_0_eth1_ip_address='10.0.0.4/24',
                            vpn_0_eth1_ip_gateway='10.0.0.1',
                            vpn_512_eth0_ip_address='172.16.240.4/24',
                            vpn_512_eth0_ip_gateway='172.16.240.1'
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
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed vBond Device Setup")
    # endregion
    # region Viptela vManage Setup Part 2
    deployment_step = 'vManage Setup Part 2'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting vManage setup part 2")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/viptela')
    file_name = os.path.join(configs_path, 'vmanage_template')
    vdevices = [2, 3]
    for server_ip in server_ips:
        temp_node_name = f'vManage'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {temp_node_name}")
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
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"#")
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Sending configuration commands to {temp_node_name}")
                    for line in lines:
                        formatted_line = line.format(
                            hostname=temp_node_name,
                            latitude='40.758701',
                            longitude='-111.876183',
                            system_ip='172.16.240.2',
                            org_name=org_name,
                            vbond_address=vbond_address,
                            vpn_0_eth1_ip_address='10.0.0.2/24',
                            vpn_0_eth1_ip_gateway='10.0.0.1',
                            vpn_512_eth0_ip_address='172.16.240.2/24',
                            vpn_512_eth0_ip_gateway='172.16.240.1'
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
                    scp_command = f"request execute vpn 512 scp /home/admin/SDWAN.pem admin@172.16.240.{vdevice}:/home/admin"
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
                tn.read_until(b'exit')
                tn.close()
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Completed vManage Device Setup Part 2")
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
                    tn.write(viptela_password.encode("ascii") + b"\n")
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
                vmanage_csr = vmanage_generate_csr(gns3_server_data, vmanage_headers, vmanage_mgmt_address, 'vmanage')
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
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed vManage API Setup")
    # endregion

    end_time = time.time()
    total_time = (end_time - start_time) / 60
    deployment_step = 'Complete'
    deployment_status = 'Complete'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Total time for GNS3 Lab Deployment with {vedge_count} vEdge Devices: {total_time:.2f} minutes")
    # endregion

