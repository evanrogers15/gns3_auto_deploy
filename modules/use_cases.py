from modules.gns3_query import *
from modules.gns3_actions_old import set_single_packet_filter, remove_single_packet_filter, set_suspend, change_node_state, reset_single_suspend
from modules.telnet import run_telnet_command
from modules.gns3_actions import *
import time
import sys

def use_case_1(server, port, project_id, state):
    matching_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', 'Client')
    remote_node_name_1 = 'Cloud_ISP_001'
    router_node_name = 'vEdge_001_NewYork'
    filter_type = 'packet_loss'
    filter_value = '5'
    client_command_2 = 'python3 /home/scripts/iperf3_server.py'
    nodes = gns3_query_get_nodes(server, port, project_id)
    router_node_id, router_console, router_aux = gns3_query_find_node_by_name(nodes, router_node_name)
    links = gns3_query_get_links(server, port, project_id, router_node_id)
    remote_node_id_1, remote_node_console_1, remote_node_aux_1 = gns3_query_find_node_by_name(nodes, remote_node_name_1)
    link_id = gns3_query_get_node_links(nodes, links, server, port, project_id, router_node_id, remote_node_id_1, '1/0')
    client_count = len(matching_nodes)
    if state == 'on':
        for index, client in enumerate(matching_nodes):
            server_ip = f"172.16.1{client_count:02}.51"
            client_command_1 = f'nohup sh -c "while true; do rand=\$(shuf -i 5-20 -n 1)m; echo \$rand; iperf3 -c {server_ip} -p 520{index+1} -u -b \$rand -t 30; done" > /dev/null 2>&1 &'
            client_node_id, client_console, client_aux = gns3_query_find_node_by_name(nodes, client)
            change_node_state(server, port, project_id, client_node_id, 'on')
            if index == len(matching_nodes) - 1:
                run_telnet_command(server, port, project_id, client_node_id, client_console, state, client_command_2)
            else:
                run_telnet_command(server, port, project_id, client_node_id, client_console, state, client_command_1)
        set_single_packet_filter(server, port, project_id, link_id, filter_type, filter_value)
        print("Use Case 1 Applied")
        return {'message': 'Scenario started successfully.'}, 200
    else:
        for index, client in enumerate(matching_nodes):
            client_node_id, client_node_console, client_node_aux = gns3_query_find_node_by_name(nodes, client)
            change_node_state(server, port, project_id, client_node_id, 'off')
        remove_single_packet_filter(server, port, project_id, link_id)
        print("Use Case 1 Removed")
        return {'message': 'Scenario started successfully.'}, 200

def use_case_2(server, port, project_id, state):
    matching_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', 'vEdge')
    client_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', 'Client')
    client_command_2 = 'python3 /home/scripts/iperf3_server.py'
    client_count = len(client_nodes)
    nodes = gns3_query_get_nodes(server, port, project_id)
    if state == 'on':
        for site in matching_nodes:
            remote_node_name_1 = 'Cloud_ISP_001'
            router_node_name = site
            filter_type = 'packet_loss'
            filter_value = '5'
            router_node_id, router_console, router_aux = gns3_query_find_node_by_name(nodes, router_node_name)
            remote_node_id_1, remote_node_console_1, remote_node_aux_1 = gns3_query_find_node_by_name(nodes, remote_node_name_1)
            links = gns3_query_get_links(server, port, project_id, router_node_id)
            link_id = gns3_query_get_node_links(nodes, links, server, port, project_id, router_node_id, remote_node_id_1, '1/0')
            set_single_packet_filter(server, port, project_id, link_id, filter_type, filter_value)
        for index, client in enumerate(client_nodes):
            server_ip = f"172.16.1{client_count:02}.51"
            client_command_1 = f'nohup sh -c "while true; do rand=\$(shuf -i 20-60 -n 1)m; echo \$rand; iperf3 -c {server_ip} -p 520{index + 1} -u -b \$rand -t 30; done" > /dev/null 2>&1 &'
            client_node_id, client_console, client_aux = gns3_query_find_node_by_name(nodes, client)
            change_node_state(server, port, project_id, client_node_id, 'on')
            if index == len(client_nodes) - 1:
                run_telnet_command(server, port, project_id, client_node_id, client_console, state, client_command_2)
            else:
                run_telnet_command(server, port, project_id, client_node_id, client_console, state, client_command_1)
        return {'message': 'Scenario started successfully.'}, 200
    else:
        for site in matching_nodes:
            remote_node_name_1 = 'Cloud_ISP_001'
            router_node_name = site
            router_node_id, router_console, router_aux = gns3_query_find_node_by_name(nodes, router_node_name)
            remote_node_id_1, remote_node_console_1, remote_node_aux_1 = gns3_query_find_node_by_name(nodes, remote_node_name_1)
            links = gns3_query_get_links(server, port, project_id, router_node_id)
            link_id = gns3_query_get_node_links(nodes, links, server, port, project_id, router_node_id, remote_node_id_1, '1/0')
            remove_single_packet_filter(server, port, project_id, link_id)
            print(f"Use Case 2 Removed from Site {site}")
        for index, client in enumerate(client_nodes):
            client_node_id, client_node_console, client_node_aux = gns3_query_find_node_by_name(nodes, client)
            change_node_state(server, port, project_id, client_node_id, 'off')
        return {'message': 'Scenario started successfully.'}, 200
