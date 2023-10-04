import sys
from modules.vendor_specific_actions.versa_actions import *
from modules.gns3.gns3_dynamic_data import *
from modules.gns3.gns3_query import *
from modules.gns3.gns3_variables import *
from modules.vendor_specific_actions.appneta_actions import *

import telnetlib
import time
from datetime import datetime

def query_find_nodes_by_field(server_ip, server_port, project_id, search_field, return_field, search_string):
    nodes = gns3_query_get_nodes(server_ip, server_port, project_id)
    if search_string:
        matching_nodes = [node for node in nodes if search_string in node[search_field]]
        if not matching_nodes:
            return []
        else:
            if return_field == "node_id":
                return matching_nodes[0][return_field]
            else:
                return [node[return_field] for node in matching_nodes]
    else:
        return []

def get_node_coordinates(gns3_server_ip, port, project_id, node_id):
    # Build the URL for the GNS3 API endpoint
    url = f"http://{gns3_server_ip}:{port}/v2/projects/{project_id}/nodes/{node_id}"

    # Make the request to the GNS3 server
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Error querying GNS3 server: {response.text}")

    # Parse the JSON response
    data = response.json()

    # Extract and return the coordinates
    x = data.get('x', None)
    y = data.get('y', None)
    return x, y

def update_node_coordinates(gns3_server_ip, port, project_id, node_id, x, y):
    # Build the URL for the GNS3 API endpoint
    url = f"http://{gns3_server_ip}:{port}/v2/projects/{project_id}/nodes/{node_id}"

    # Prepare the data to update
    payload = {
        "x": x,
        "y": y
    }

    # Make the request to the GNS3 server to update the node coordinates
    response = requests.put(url, json=payload)

    # Check if the request was successful
    if response.status_code not in (200, 204):  # 200 for OK, 204 for No Content (both indicate success)
        raise Exception(f"Error updating coordinates on GNS3 server: {response.text}")

    return response.json()

def delete_node(gns3_server_data, project_id, node_id):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
        response = make_request("DELETE", delete_url)
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Deleted node on GNS3 Server {server_ip}")

def versa_appneta_deploy():
    # region Variables
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
    deployment_type = 'versa'
    deployment_status = 'running'
    deployment_step = '- Action - '
    cloud_node_deploy_data = {"x": 25, "y": -554, "name": "MGMT-Cloud-TAP", "node_type": "cloud",
                              "compute_id": "local", "symbol": ":/symbols/cloud.svg"}
    required_qemu_images = {"versa-director-c19c43c-21.2.3.qcow2", "versa-analytics-67ff6c7-21.2.3.qcow2", "versa-flexvnf-67ff6c7-21.2.3.qcow2"}

    local_city_data = {}
    for key, value in template_city_data.items():
        new_key = key.replace("replace", "FlexVNF")
        local_city_data[new_key] = value

    start_time = time.time()
    current_date = datetime.now().strftime("%m/%d/%Y")
    server_name = "temp"
    server_ip = "100.103.164.104"
    server_ip = "192.168.122.1"
    server_port = "80"
    project_name = "versa-gss-team-lab-flow-ate"
    new_project_id = "d0119f33-1a6b-4861-8617-55173bcb8c34"
    site_count = 5
    tap_name = "tap2"

    mgmt_subnet_ip = "172.16.30"
    mgmt_subnet_gateway_ip = mgmt_subnet_ip + ".1"
    director_mgmt_ip = mgmt_subnet_ip + ".2"
    analytics_mgmt_ip = mgmt_subnet_ip + ".6"
    controller_mgmt_ip = mgmt_subnet_ip + ".10"

    southbound_subnet = '172.16.1'
    director_southbound_gateway_ip = southbound_subnet + ".1"
    director_southbound_ip = southbound_subnet + ".2"
    analytics_southbound_gateway_ip = southbound_subnet + ".5"
    analytics_southbound_ip = southbound_subnet + ".6"
    controller_southbound_gateway_ip = southbound_subnet + ".1"
    controller_southbound_ip = southbound_subnet + ".10"

    controller_isp_subnet = '172.16.5'
    controller_isp_1_ip_gateway = controller_isp_subnet + ".1"
    controller_isp_1_ip = controller_isp_subnet + ".2"
    controller_isp_2_ip_gateway = controller_isp_subnet + ".5"
    controller_isp_2_ip = controller_isp_subnet + ".6"

    snmp_trap_dst = "172.16.102.52"

    gns3_server_data = [{
        "GNS3 Server": server_ip, "Server Name": server_name, "Server Port": server_port, "Project Name": project_name,
        "Project ID": new_project_id, "Tap Name": tap_name, "Site Count": site_count,
        "Deployment Type": deployment_type, "Deployment Status": deployment_status, "Deployment Step": deployment_step
    }]
    info_drawing_data = {
        "drawing_01": {
            "svg": "<svg width=\"297\" height=\"307\"><rect width=\"297\" height=\"307\" fill=\"#6080b3\" fill-opacity=\"0.6399938963912413\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
            "x": -215, "y": 286, "z": 0
        }, "drawing_02": {
            "svg": "<svg width=\"224\" height=\"25\"><text font-family=\"Arial\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">Versa Management Components</text></svg>",
            "x": -173, "y": 566, "z": 2
        }, "drawing_03": {
            "svg": "<svg width=\"471\" height=\"50\"><text font-family=\"Arial\" font-size=\"36.0\" fill=\"#000000\" fill-opacity=\"1.0\">Versa SDWAN Environment</text></svg>",
            "x": -1172, "y": -591, "z": 2
        }, "drawing_04": {
            "svg": f"<svg width=\"318\" height=\"50\"><text font-family=\"Arial\" font-size=\"18.0\" fill=\"#000000\" fill-opacity=\"1.0\">Management IP Range: {mgmt_subnet_ip}.0/24\nVersa Director MGMT IP: {director_mgmt_ip}\nCreated On: {current_date}</text></svg>",
            "x": -1165, "y": -541, "z": 2
        },
    }

    isp_switch_count = (site_count // 40) + 1
    mgmt_switch_count = (site_count // 30) + 1

    # endregion
    # region Runtime
    #  region Setup Dynamic Networking
    flexvnf_deploy_data, client_deploy_data, site_drawing_deploy_data = versa_generate_flexvnf_deploy_data(site_count, local_city_data)
    starting_subnet = 6
    flexvnf_index = 1
    flexvnf_isp_1_base_subnet = f'172.16.{starting_subnet}.0/24'
    flexvnf_isp_2_base_subnet = f'172.16.{starting_subnet + 1}.0/24'
    isp_switch_1_objects = generate_versa_network_objects(flexvnf_isp_1_base_subnet, 30, flexvnf_index)
    isp_switch_2_objects = generate_versa_network_objects(flexvnf_isp_2_base_subnet, 30, flexvnf_index)
    isp_1_overall.append(isp_switch_1_objects)
    isp_2_overall.append(isp_switch_2_objects)
    # endregion
    # region Create GNS3 Templates
    deployment_step = 'Creating Templates'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Starting Template Creation")
    gns3_delete_template(gns3_server_data, versa_director_template_name)
    gns3_delete_template(gns3_server_data, versa_analytics_template_name)
    versa_director_template_id = gns3_create_template(gns3_server_data, versa_director_template_data)
    versa_analytics_template_id = gns3_create_template(gns3_server_data, versa_analytics_template_data)
    # endregion
    # region Deploy GNS3 Nodes
    deployment_step = 'Deploy GNS3 Nodes'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Starting Node Deployment")
    versa_director_node_id = query_find_nodes_by_field(server_ip, server_port, new_project_id, 'name', 'node_id', 'Versa_Director')
    versa_analytics_node_id = query_find_nodes_by_field(server_ip, server_port, new_project_id, 'name', 'node_id', 'Versa_Analytics')

    versa_director_x, versa_director_y = get_node_coordinates(server_ip, server_port, new_project_id, versa_director_node_id)
    versa_analytics_x, versa_analytics_y = get_node_coordinates(server_ip, server_port, new_project_id, versa_analytics_node_id)
    delete_node(gns3_server_data, new_project_id, versa_director_node_id)
    delete_node(gns3_server_data, new_project_id, versa_analytics_node_id)
    versa_director_node_id = gns3_create_node(gns3_server_data, new_project_id, versa_director_template_id, versa_director_deploy_data)
    versa_analytics_node_id = gns3_create_node(gns3_server_data, new_project_id, versa_analytics_template_id, versa_analytics_deploy_data)

    gns3_update_nodes(gns3_server_data, new_project_id, versa_director_node_id, versa_director_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, versa_analytics_node_id, versa_analytics_deploy_data)
    update_node_coordinates(server_ip, server_port, new_project_id, versa_director_node_id, versa_director_x, versa_director_y)
    update_node_coordinates(server_ip, server_port, new_project_id, versa_analytics_node_id, versa_analytics_x, versa_analytics_y)

    # endregion
    # region Connect GNS3 Lab Nodes
    deployment_step = 'Connect GNS3 Nodes'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting GNS3 Nodes Connect")
    mgmt_main_switch_node_id = query_find_nodes_by_field(server_ip, server_port, new_project_id, 'name', 'node_id', 'Main_MGMT-switch')
    versa_director_node_id = query_find_nodes_by_field(server_ip, server_port, new_project_id, 'name', 'node_id', 'Versa_Director')
    versa_analytics_node_id = query_find_nodes_by_field(server_ip, server_port, new_project_id, 'name', 'node_id', 'Versa_Analytics')
    versa_control_switch_node_id = query_find_nodes_by_field(server_ip, server_port, new_project_id, 'name', 'node_id', 'Control_Network')

    # gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, 1, 0, versa_controller_node_id, 3, 0)
    # gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, 2, 0, versa_controller_node_id, 4, 0)
    # gns3_connect_nodes(gns3_server_data, new_project_id, versa_control_switch_node_id, 0, 2, versa_controller_node_id, 2, 0)
    # gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 3, versa_controller_node_id, 0, 0)

    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 1, versa_director_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 2, versa_analytics_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, versa_control_switch_node_id, 0, 0, versa_director_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, versa_control_switch_node_id, 0, 1, versa_analytics_node_id, 1, 0)

    # endregion
    # region Start All GNS3 Nodes
    deployment_step = 'Starting Nodes'
    gns3_start_node(gns3_server_data, new_project_id, versa_director_node_id)
    gns3_start_node(gns3_server_data, new_project_id, versa_analytics_node_id)
    # endregion
    # region Versa Director Setup Part 1
    deployment_step = 'Starting Nodes'
    wait_time = 2  # minutes
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Waiting {wait_time} mins for devices to come up, to resume at {util_resume_time(wait_time)}")
    # time.sleep(wait_time * 60)
    deployment_step = 'Versa Director device Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Starting Director device setup part 1")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'Director'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        print(matching_nodes)
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
                tn.write(director_mgmt_ip.encode('ascii') + b"\n")
                tn.read_until(b"Enter Netmask Address:")
                tn.write(b'255.255.255.0\n')
                tn.read_until(b"Configure Gateway Address? (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"Enter Gateway Address:")
                tn.write(mgmt_subnet_gateway_ip.encode('ascii') + b"\n")
                tn.read_until(b"Configure another interface? (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"Enter interface name [eg. eth0]:")
                tn.write(b'eth1\n')
                tn.read_until(b"Enter IP Address:")
                tn.write(director_southbound_ip.encode('ascii') + b"\n")
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
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Starting Versa Analytics Device Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    versa_interfaces = f"""auto eth0
            iface eth0 inet static
            address {analytics_mgmt_ip}
            netmask 255.255.255.0
            gateway {mgmt_subnet_gateway_ip}
            up echo nameserver 192.168.122.1 > /etc/resolv.conf
            auto eth1
            iface eth1 inet static
            address {analytics_southbound_ip}
            netmask 255.255.255.0
            """
    for server_ip in server_ips:
        temp_node_name = f'Analytics'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        analytics_temp_route_command = f'route add -net 10.10.0.0/16 gw {controller_southbound_ip} dev eth1'
        analytics_persistent_route_command = f"sudo sed -i '/^exit 0/i route add -net 10.10.0.0/16 gw {controller_southbound_ip} dev eth1' /etc/rc.local\n"
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
                tn.read_until(b"[root@versa-analytics: admin]#")
                tn.write(analytics_temp_route_command.encode('ascii') + b"\n")
                tn.read_until(b"[root@versa-analytics: admin]#")
                tn.write(analytics_persistent_route_command.encode('ascii') + b"\n")
                tn.read_until(b"[root@versa-analytics: admin]#")
                tn.write(b"exit\n")
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Completed Versa AnalyticsDevice Setup")
    # endregion
    # region Versa Director Setup Part 2
    deployment_step = 'Director Setup Part 2'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Director setup part 2")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), '/app/modules/configs/versa')
    clustersetup_file = os.path.join(configs_path, 'clustersetup.conf')
    versa_configure_analytics_cluster(director_mgmt_ip, analytics_mgmt_ip, analytics_southbound_ip)
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
                    output = tn.read_until(b"login:", timeout=2).decode('ascii')
                    if '[Administrator@director: ~] $' in output:
                        break
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
                file_contents = file_contents.replace("versa_director_ip", director_mgmt_ip)
                file_contents = file_contents.replace("versa_analytics_ip", analytics_mgmt_ip)
                file_contents = file_contents.replace("analytics_southbound_ip", analytics_southbound_ip)
                remote_file_path = "/opt/versa/vnms/scripts/van-cluster-config/van_cluster_install/clustersetup.conf"
                command = f"echo \"{file_contents}\" > {remote_file_path}\n"
                tn.write(command.encode('utf-8'))
                tn.read_until(b"root@director:/home/Administrator#")
                tn.write(b"cd /opt/versa/vnms/scripts/van-cluster-config/van_cluster_install\r\n")
                tn.read_until(b"root@director:")
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                  f"Starting VAN Cluster Install")
                tn.write(b"./van_cluster_installer.py --force\n")
                tn.read_until(b"VAN CLUSTER INSTALL COMPLETED")
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                  f"Starting Post Install VAN Cluster Setup")
                tn.write(b"./van_cluster_installer.py --post-setup --gen-vd-cert\r\n")
                tn.read_until(b"VAN CLUSTER POST-SETUP PROCEDURES COMPLETED")
                time.sleep(30)
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Completed vManage Device Setup Part 2")
    # endregion
    # region Versa Director Setup Part 3
    deployment_step = 'Director Setup Part 2'
    versa_configure_analytics_cluster(director_mgmt_ip, analytics_mgmt_ip, analytics_southbound_ip)
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Starting Director API Tasks")
    versa_create_provider_org(director_mgmt_ip)
    org_id = versa_get_org_uuid(director_mgmt_ip)
    versa_create_overlay_prefix(director_mgmt_ip)
    versa_create_overlay_route(director_mgmt_ip, controller_southbound_ip)
    versa_create_controller_workflow(director_mgmt_ip, controller_mgmt_ip, controller_southbound_ip, controller_isp_1_ip_gateway, controller_isp_1_ip, controller_isp_2_ip_gateway, controller_isp_2_ip)
    time.sleep(30)
    versa_create_dhcp_profile(director_mgmt_ip)
    versa_deploy_controller(director_mgmt_ip)
    time.sleep(30)
    versa_create_wan_network(director_mgmt_ip, org_id, "ISP-1")
    time.sleep(5)
    versa_create_wan_network(director_mgmt_ip, org_id, "ISP-2")
    time.sleep(5)
    versa_create_app_steering_template(director_mgmt_ip)
    time.sleep(5)
    versa_deploy_app_steering_template(director_mgmt_ip)
    time.sleep(5)
    versa_create_device_template(director_mgmt_ip)
    time.sleep(5)
    versa_deploy_device_template(director_mgmt_ip)
    time.sleep(5)
    versa_update_device_template_snmp(director_mgmt_ip, snmp_trap_dst)
    time.sleep(5)
    versa_update_device_template_oobm_interface(director_mgmt_ip)
    time.sleep(2)
    versa_update_device_template_netflow_1(director_mgmt_ip)
    time.sleep(2)
    versa_update_device_template_netflow_2(director_mgmt_ip)
    time.sleep(2)
    versa_update_device_template_netflow_3(director_mgmt_ip)
    time.sleep(2)
    versa_update_device_template_netflow_4(director_mgmt_ip)
    time.sleep(2)
    versa_update_device_template_netflow_5(director_mgmt_ip)
    time.sleep(5)
    versa_create_device_group(director_mgmt_ip)
    time.sleep(5)
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Completed vManage Device Setup Part 2")
# endregion
    # region Versa FlexVNF Device Reset
    deployment_step = 'FlexVNF Device Reset'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Starting FlexVNF Device Reset for {site_count} FlexVNFs")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        for i in range(1, site_count + 1):
            temp_node_name = f'FlexVNF-{i:003}'
            matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
            if matching_nodes:
                for matching_node in matching_nodes:
                    node_id, console_port, aux = matching_node
                    node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id',
                                                               'name', node_id)

                    reset_command = f"request erase running-config"
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                      f"Starting FlexVNF Device Reset for {node_name[0]} - FlexVNF {i} of {site_count}")
                    tn = telnetlib.Telnet(server_ip, console_port)
                    tn.write(b"\r\n")
                    while True:
                        tn.write(b"\r\n")
                        tn.read_until(b"login:", timeout=2)
                        tn.write(versa_analytics_username.encode("ascii") + b"\n")
                        tn.read_until(b"Password:", timeout=5)
                        tn.write(versa_old_password.encode("ascii") + b"\n")
                        output = tn.read_until(b"[admin@", timeout=5).decode('ascii')
                        if '[admin@' in output:
                            break
                        log_and_update_db(server_name, project_name, deployment_type, deployment_status,
                                          deployment_step, f"{node_name} not available yet, trying again in 30 seconds")
                        time.sleep(30)
                    tn.write(b"\r\n")
                    tn.read_until(b"[admin@")
                    tn.write(b"cli\n")
                    tn.read_until(b"-cli>")
                    tn.write(reset_command.encode('ascii') + b"\r")
                    tn.read_until(b"Are you sure? [no,yes]")
                    tn.write(b"yes\n")
                    tn.read_until(b"[admin@")
                    tn.close()
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                      f"Completed FlexVNF Device Reset for {temp_node_name}, Remaining - {site_count - i}")
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Completed FlexVNF Device Reset for {site_count} FlexVNF devices")
    # endregion
    # region Versa FlexVNF Device Setup
    deployment_step = 'FlexVNF Device Onboarding'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting FlexVNF Device Onbaording for {site_count} FlexVNFs")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    flexvnf_lan_objects = generate_flexvnf_objects(site_count, mgmt_subnet_ip)
    isp_index = 0
    flexvnf_vr_index = 4
    for server_ip in server_ips:
        for i in range(1, site_count + 1):
            temp_node_name = f'FlexVNF-{i:003}'
            matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
            if matching_nodes:
                for matching_node in matching_nodes:
                    node_id, console_port, aux = matching_node
                    node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', node_id)
                    for flexvnf_lan_object in flexvnf_lan_objects:
                        if flexvnf_lan_object['flexvnf'] == temp_node_name:
                            lan_dhcp_pool = flexvnf_lan_object['lan_dhcp_pool']
                            lan_subnet_base = flexvnf_lan_object['lan_subnet_base']
                            lan_dhcp_exclude = flexvnf_lan_object['lan_dhcp_exclude']
                            lan_gateway_address = flexvnf_lan_object['lan_gateway_address']
                            client_1_address = flexvnf_lan_object['client_1_address']
                            mgmt_address = flexvnf_lan_object['mgmt_address']
                            mgmt_gateway = flexvnf_lan_object['mgmt_gateway']
                            system_ip = flexvnf_lan_object['system_ip']
                            site_id = f"{flexvnf_lan_object['site_id']}"
                            device_serial_number = f"SN{site_id}"
                    for dictionary_0 in isp_1_overall[isp_index]:
                        if dictionary_0['flexvnf'] == temp_node_name:
                            vpn_0_ge0_0_ip_address = dictionary_0['flexvnf_address']
                            vpn_0_ge0_0_ip_gateway = dictionary_0['router_address']
                    for dictionary_1 in isp_2_overall[isp_index]:
                        if dictionary_1['flexvnf'] == temp_node_name:
                            vpn_0_ge0_1_ip_address = dictionary_1['flexvnf_address']
                            vpn_0_ge0_1_ip_gateway = dictionary_1['router_address']
                    flexvnf_hostname = f"{temp_node_name}-{local_city_data[temp_node_name]['city']}"
                    flexvnf_city = local_city_data[temp_node_name]['city']
                    site_country = local_city_data[temp_node_name]['country']
                    vr_1_route_ip = f'10.10.0.{flexvnf_vr_index}'
                    tvi_0_2_ip = f'10.10.0.{flexvnf_vr_index + 1}/32'
                    tvi_0_3_ip = f'10.10.0.{flexvnf_vr_index}/32'
                    latitude = local_city_data[temp_node_name]['latitude']
                    longitude = local_city_data[temp_node_name]['longitude']
                    onboard_command = f"sudo /opt/versa/scripts/staging.py -w 0 -n {device_serial_number} -c {controller_isp_1_ip} -s {vpn_0_ge0_0_ip_address} -g {vpn_0_ge0_0_ip_gateway} -l SDWAN-Branch@Versa-Root.com -r Controller-01-staging@Versa-Root.com"
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting FlexVNF Device Onboarding for {node_name[0]} - FlexVNF {i} of {site_count}")
                    versa_create_site_device_workflow(director_mgmt_ip, vr_1_route_ip, lan_gateway_address, lan_subnet_base, flexvnf_hostname, site_id, device_serial_number, site_country, flexvnf_city, vpn_0_ge0_0_ip_address, vpn_0_ge0_0_ip_gateway, vpn_0_ge0_1_ip_address, vpn_0_ge0_1_ip_gateway, tvi_0_2_ip, tvi_0_3_ip, latitude, longitude, mgmt_gateway, mgmt_address)
                    time.sleep(10)
                    versa_deploy_device_workflow(director_mgmt_ip, flexvnf_hostname)
                    time.sleep(10)
                    # versa_config_edge_mgmt_interface(director_mgmt_ip, flexvnf_hostname, mgmt_address, mgmt_subnet_gateway_ip)
                    time.sleep(10)
                    tn = telnetlib.Telnet(server_ip, console_port)
                    tn.write(b"\r\n")
                    while True:
                        tn.write(b"\r\n")
                        tn.read_until(b"login:", timeout=2)
                        tn.write(versa_analytics_username.encode("ascii") + b"\n")
                        tn.read_until(b"Password:", timeout=5)
                        tn.write(versa_old_password.encode("ascii") + b"\n")
                        output = tn.read_until(b"[admin@", timeout=5).decode('ascii')
                        if '[admin@' in output:
                            break
                        log_and_update_db(server_name, project_name, deployment_type, deployment_status,
                                          deployment_step,
                                          f"{node_name} not available yet, trying again in 30 seconds")
                        time.sleep(30)
                    tn.write(b"\r\n")
                    tn.read_until(b"[admin@")
                    while True:
                        tn.write(b"\r\n")
                        tn.write(b'sudo su\r\n')
                        tn.read_until(b"[sudo] password for admin:", timeout=2)
                        tn.write(versa_old_password.encode("ascii") + b"\n")
                        output = tn.read_until(b"[root@", timeout=5).decode('ascii')
                        if '[root@' in output:
                            break
                    tn.write(onboard_command.encode('ascii') + b"\r")
                    tn.read_until(b"[root@")
                    tn.close()
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed FlexVNF Device Onboarding for {temp_node_name}, Remaining - {site_count - i}")
                    if i % 44 == 0 and i != 0:
                        isp_index += 1
                    flexvnf_vr_index += 2
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed FlexVNF Device Onboarding for {site_count} FlexVNF devices")
    # endregion

    end_time = time.time()
    total_time = (end_time - start_time) / 60
    deployment_step = 'Complete'
    deployment_status = 'Complete'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Total time for GNS3 Lab Deployment with {site_count} FlexVNF Devices: {total_time:.2f} minutes")
    # endregion

versa_appneta_deploy()


