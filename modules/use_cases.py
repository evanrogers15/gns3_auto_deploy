from modules.gns3_query import get_links, get_nodes, get_node_links, find_node_by_name
from modules.gns3_actions_old import set_single_packet_filter, remove_single_packet_filter, set_suspend, change_node_state, reset_single_suspend
from modules.telnet import run_telnet_command
from modules.gns3_actions import *
import time

def use_case_1(server, port, project_id, state):
    test_clients = ['Site_001_Client', 'Site_002_Client', 'Site_003_Client', 'Site_004_Client', 'Site_005_Client']
    remote_node_name_1 = 'Cloud_ISP_001'
    remote_node_name_2 = 'Cloud_ISP_001'
    router_node_name = 'vEdge_001_NewYork'
    filter_type = 'packet_loss'
    filter_value = '5'
    server_command = 'nohup iperf3 -s &'
    client_command_2 = 'python3 /home/scripts/iperf3_server.py'
    nodes = get_nodes(server, port, project_id)
    router_node_id, router_console, router_aux = find_node_by_name(nodes, router_node_name)
    links = get_links(server, port, project_id, router_node_id)
    remote_node_id_1, remote_node_console_1, remote_node_aux_1 = find_node_by_name(nodes, remote_node_name_1)
    link_ids = get_node_links(nodes, links, server, port, project_id, router_node_id, router_node_name, remote_node_id_1)
    client_count = len(test_clients)
    if state == 'on':
        for index, client in enumerate(test_clients):
            server_ip = f"172.16.1{client_count:02}.51"
            client_command_1 = f'nohup sh -c "while true; do rand=\$(shuf -i 20-60 -n 1)m; echo \$rand; iperf3 -c {server_ip} -p 520{index+1} -u -b \$rand -t 30; done" > /dev/null 2>&1 &'
            client_node_id, client_console, client_aux = find_node_by_name(nodes, client)
            change_node_state(server, port, project_id, client_node_id, 'on')
            time.sleep(2)
            if index == len(test_clients) - 1:
                run_telnet_command(server, port, project_id, client_node_id, client_console, state, client_command_2)
            else:
                run_telnet_command(server, port, project_id, client_node_id, client_console, state, client_command_1)
        for i in range(2, len(link_ids)):
            link_id = link_ids[i]
            set_single_packet_filter(server, port, project_id, link_id, filter_type, filter_value)
        time.sleep(3)
        print("Use Case 1 Applied")
        return {'message': 'Scenario started successfully.'}, 200
    else:
        for index, client in enumerate(test_clients):
            client_node_id, client_node_console, client_node_aux = find_node_by_name(nodes, client)
            change_node_state(server, port, project_id, client_node_id, 'off')
        for i in range(2, len(link_ids)):
            link_id = link_ids[i]
            remove_single_packet_filter(server, port, project_id, link_id)
        print("Use Case 1 Removed")
        return {'message': 'Scenario started successfully.'}, 200

def use_case_2(server, port, project_id, state):
    site_list = ['vEdge_001_NewYork', 'vEdge_002_LosAngeles', 'vEdge_003_Chicago', 'vEdge_004_Houston', 'vEdge_005_Phoenix', 'vEdge_006_Philadelphia', 'vEdge_007_SanAntonio', 'vEdge_008_SanDiego', 'vEdge_009_Dallas', 'vEdge_010_SanJose']
    # matching_nodes = gns3_find_nodes_by_field_new(project_id, 'name', 'name', 'vEdge', server, port)
    for site in site_list:
        remote_node_name_1 = 'Cloud_ISP_001'
        router_node_name = site
        filter_type = 'packet_loss'
        filter_value = '5'
        nodes = get_nodes(server, port, project_id)
        router_node_id, router_console, router_aux = find_node_by_name(nodes, router_node_name)
        remote_node_id_1, remote_node_console_1, remote_node_aux_1 = find_node_by_name(nodes, remote_node_name_1)
        links = get_links(server, port, project_id, router_node_id)
        link_ids = get_node_links(nodes, links, server, port, project_id, router_node_id, router_node_name, remote_node_id_1, '2/0')
        if state == 'on':
            for i in range(2, len(link_ids)):
                link_id = link_ids[i]
                set_single_packet_filter(server, port, project_id, link_id, filter_type, filter_value)
            print(f"Use Case 2 Applied to Site {site}")
        else:
            for i in range(2, len(link_ids)):
                link_id = link_ids[i]
                remove_single_packet_filter(server, port, project_id, link_id)
            print(f"Use Case 2 Removed from Site {site}")
    return {'message': 'Success.'}, 200

def use_case_2_old(server, port, project_id, state):
    test_client_node_name_2 = 'Site-4-Network-Test-Client-2'
    remote_node_name_1 = 'ISP-1'
    remote_node_name_2 = 'ISP-2'
    router_node_name = 'vEdge-Cloud-Site-4'
    filter_type = 'packet_loss'
    filter_value = '5'
    client_command_2 = 'nohup sh -c "python3 /home/scripts/scapy_udp_flood.py &" > /dev/null 2>&1 &'
    nodes = get_nodes(server, port, project_id)
    test_client_2_id, test_client_2_console, test_client_2_aux = find_node_by_name(nodes, test_client_node_name_2)
    router_node_id, router_console, router_aux = find_node_by_name(nodes, router_node_name)
    remote_node_id_1, remote_node_console_1, remote_node_aux_1 = find_node_by_name(nodes, remote_node_name_1)
    remote_node_id_2, remote_node_console_2, remote_node_aux_2 = find_node_by_name(nodes, remote_node_name_2)
    links = get_links(server, port, project_id, router_node_id)
    link_id_1 = get_node_links(nodes, links, server, port, project_id, router_node_id, router_node_name, remote_node_id_1)
    link_id_2 = get_node_links(nodes, links, server, port, project_id, router_node_id, router_node_name, remote_node_id_2)
    if state == 'on':
        change_node_state(server, port, project_id, test_client_2_id, 'on')
        time.sleep(3)
        set_single_packet_filter(server, port, project_id, link_id_1, filter_type, filter_value)
        set_single_packet_filter(server, port, project_id, link_id_2, filter_type, filter_value)
        time.sleep(3)
        run_telnet_command(server, port, project_id, test_client_2_id, test_client_2_console, state, client_command_2)
        print("Use Case 2 Applied")
        return {'message': 'Scenario started successfully.'}, 200
    else:
        change_node_state(server, port, project_id, test_client_2_id, 'off')
        remove_single_packet_filter(server, port, project_id, link_id_1)
        remove_single_packet_filter(server, port, project_id, link_id_2)
        print("Use Case 2 Removed")
        return {'message': 'Scenario started successfully.'}, 200 
        
def use_case_2_sim_user(server, port, project_id, state):
    test_client_node_name_1 = 'Site-4-Network-Test-Client-1'
    test_server_node_name = 'Site-1-Network-Test-Server'
    IP_ADDRESS = '172.16.14.30'
    server_command = 'nohup iperf3 -s &'
    client_command_1 = 'nohup sh -c "ip_address={}; while true; do rand=\$(shuf -i 50-100 -n 1)m; echo \$rand; iperf3 -c \$ip_address -p 5201 -u -b \$rand -t 30; done" > /dev/null 2>&1 &'.format(IP_ADDRESS)
    nodes = get_nodes(server, port, project_id)
    test_client_1_id, test_client_1_console, test_client_1_aux = find_node_by_name(nodes, test_client_node_name_1)
    test_server_id, test_server_console, test_server_aux = find_node_by_name(nodes, test_server_node_name)
    if state == 'on':
        change_node_state(server, port, project_id, test_client_1_id, 'on')
        time.sleep(3)
        run_telnet_command(server, port, project_id, test_client_1_id, test_client_1_console, state, client_command_1)
        print("Use Case 2 Sim Applied")
        return {'message': 'Scenario started successfully.'}, 200
    else:
        change_node_state(server, port, project_id, test_client_1_id, 'off')
        print("Use Case 2 Sim Removed")
        return {'message': 'Scenario started successfully.'}, 200
    
def use_case_3(server, port, project_id, state, set_link=None):
    node_name = 'Site-2-Network-Test-Client-1'
    remote_node_name_1 = 'ISP-1'
    remote_node_name_2 = 'ISP-2'
    router_node_name = 'vEdge-Cloud-Site-2'
    nodes = get_nodes(server, port, project_id)
    node_test_client_id, node_test_console, node_test_aux = find_node_by_name(nodes, node_name)
    router_node_id, router_console, router_aux = find_node_by_name(nodes, router_node_name)
    remote_node_id_1, remote_node_console_1, remote_node_aux_1 = find_node_by_name(nodes, remote_node_name_1)
    remote_node_id_2, remote_node_console_2, remote_node_aux_2 = find_node_by_name(nodes, remote_node_name_2)
    links = get_links(server, port, project_id, router_node_id)
    link_id_1 = get_node_links(nodes, links, server, port, project_id, router_node_id, router_node_name, remote_node_id_1)
    link_id_2 = get_node_links(nodes, links, server, port, project_id, router_node_id, router_node_name, remote_node_id_2)
    if set_link == 1:
        link_id = get_node_links(nodes, links, server, port, project_id, router_node_id, router_node_name, remote_node_id_1)
    else:
        link_id = get_node_links(nodes, links, server, port, project_id, router_node_id, router_node_name, remote_node_id_2)
    if state == 'on':
        set_suspend(server, port, project_id, link_id )
        print("Use 3 Case Applied")
    else:
        reset_single_suspend(server, port, project_id, link_id_1)
        reset_single_suspend(server, port, project_id, link_id_2)
        print("Use 3 Case Removed")

def use_case_4(server, port, project_id, state, set_link=None):
    node_name = 'Site-2-Network-Test-Client-1'
    remote_node_name_1 = 'ISP-1'
    remote_node_name_2 = 'ISP-2'
    router_node_name = 'vEdge-Cloud-Site-2'
    nodes = get_nodes(server, port, project_id)
    node_test_client_id, node_test_console, node_test_aux = find_node_by_name(nodes, node_name)
    router_node_id, router_console, router_aux = find_node_by_name(nodes, router_node_name)
    remote_node_id_1, remote_node_console_1, remote_node_aux_1 = find_node_by_name(nodes, remote_node_name_1)
    remote_node_id_2, remote_node_console_2, remote_node_aux_2 = find_node_by_name(nodes, remote_node_name_2)
    links = get_links(server, port, project_id, router_node_id)
    link_id_1 = get_node_links(nodes, links, server, port, project_id, router_node_id, router_node_name, remote_node_id_1)
    link_id_2 = get_node_links(nodes, links, server, port, project_id, router_node_id, router_node_name, remote_node_id_2)
    if set_link == 1:
        link_id = get_node_links(nodes, links, server, port, project_id, router_node_id, router_node_name, remote_node_id_1)
    else:
        link_id = get_node_links(nodes, links, server, port, project_id, router_node_id, router_node_name, remote_node_id_2)
    if state == 'on':
        set_suspend(server, port, project_id, link_id )
        print("Use 4 Case Applied")
    else:
        reset_single_suspend(server, port, project_id, link_id_1)
        reset_single_suspend(server, port, project_id, link_id_2)
        print("Use 4 Case Removed")

def use_case_4_sim_user(server, port, project_id, state):
    test_client_node_name_1 = 'Site-2-Network-Test-Client-1'
    IP_ADDRESS = '172.16.14.30'
    client_command_1 = 'nohup sh -c "ip_address={}; while true; do rand=\$(shuf -i 50-100 -n 1)m; echo \$rand; iperf3 -c \$ip_address -p 5202 -u -b \$rand -t 10; done" > /dev/null 2>&1 &'.format(IP_ADDRESS)
    nodes = get_nodes(server, port, project_id)
    test_client_1_id, test_client_1_console, test_client_1_aux = find_node_by_name(nodes, test_client_node_name_1)
    if state == 'on':
        change_node_state(server, port, project_id, test_client_1_id, 'on')
        time.sleep(5)
        run_telnet_command(server, port, project_id, test_client_1_id, test_client_1_console, state, client_command_1)
        print("Use Case 4 Sim Applied")
        return {'message': 'Scenario started successfully.'}, 200
    else:
        change_node_state(server, port, project_id, test_client_1_id, 'off')
        print("Use Case 4 Sim Removed")
        return {'message': 'Scenario started successfully.'}, 200