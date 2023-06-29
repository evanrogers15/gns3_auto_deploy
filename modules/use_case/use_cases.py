from modules.gns3.gns3_query import *
from modules.gns3.gns3_actions_old import set_single_packet_filter, remove_single_packet_filter, change_node_state
from modules.use_case.telnet import run_telnet_command
import logging.handlers

def use_case_1(server, port, project_id, state):
    matching_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', 'Client')
    site_001_matching_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', '001')
    for node_name in site_001_matching_nodes:
        if 'vEdge' in node_name or 'FlexVNF' in node_name:
            router_node_name = node_name
    else:
        logging.info("No site routers found..")

    remote_node_name_1 = 'Cloud_ISP_01'
    # router_node_name = 'vEdge_001_NewYork'
    filter_type = 'packet_loss'
    filter_value = '5'
    nodes = gns3_query_get_nodes(server, port, project_id)
    router_node_id, router_console, router_aux = gns3_query_find_node_by_name(nodes, router_node_name)
    links = gns3_query_get_links(server, port, project_id, router_node_id)
    remote_node_id_1, remote_node_console_1, remote_node_aux_1 = gns3_query_find_node_by_name(nodes, remote_node_name_1)
    link_id = gns3_query_get_node_links(nodes, links, server, port, project_id, router_node_id, remote_node_id_1, '1/0')
    client_count = len(matching_nodes)
    #client_command_2 = f'nohup python3 /home/scripts/iperf3_server.py {client_count} &'
    client_command_2 = f'nohup python3 /home/scripts/iperf3_server.py {client_count} | tail -n 60 > output.log 2>&1 &'
    if state == 'on':
        for index, client in enumerate(matching_nodes):
            server_ip = f"172.16.102.50"
            client_command_1 = f'nohup sh -c "while true; do rand=\$(shuf -i 5-80 -n 1)m; echo \$rand; iperf3 -c {server_ip} -p 520{index+1} -u -b \$rand -t 30; done" > /dev/null 2>&1 &'
            client_node_id, client_console, client_aux = gns3_query_find_node_by_name(nodes, client)
            change_node_state(server, port, project_id, client_node_id, 'on')
            if index == 1: #len(matching_nodes) - 1:
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
    client_count = len(client_nodes)
    client_command_2 = f'python3 /home/scripts/iperf3_server.py {client_count}'
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
            client_command_1 = f'nohup sh -c "while true; do rand=\$(shuf -i 5-20 -n 1)m; echo \$rand; iperf3 -c {server_ip} -p 520{index + 1} -u -b \$rand -t 30; done" > /dev/null 2>&1 &'
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
def use_case_3(server, port, project_id, state):
    matching_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', 'vEdge')
    client_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', 'Client')
    client_count = len(client_nodes)
    client_command_2 = f'python3 /home/scripts/iperf3_server.py {client_count}'
    nodes = gns3_query_get_nodes(server, port, project_id)
    if state == 'on':
        for site in matching_nodes:
            remote_node_name_1 = 'Cloud_ISP_001'
            router_node_name = site
            filter_type = 'latency'
            filter_value = '2'
            router_node_id, router_console, router_aux = gns3_query_find_node_by_name(nodes, router_node_name)
            remote_node_id_1, remote_node_console_1, remote_node_aux_1 = gns3_query_find_node_by_name(nodes, remote_node_name_1)
            links = gns3_query_get_links(server, port, project_id, router_node_id)
            link_id = gns3_query_get_node_links(nodes, links, server, port, project_id, router_node_id, remote_node_id_1, '1/0')
            set_single_packet_filter(server, port, project_id, link_id, filter_type, filter_value)
        for index, client in enumerate(client_nodes):
            server_ip = f"172.16.1{client_count:02}.51"
            client_command_1 = f'nohup sh -c "while true; do rand=\$(shuf -i 5-20 -n 1)m; echo \$rand; iperf3 -c {server_ip} -p 520{index + 1} -u -b \$rand -t 30; done" > /dev/null 2>&1 &'
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