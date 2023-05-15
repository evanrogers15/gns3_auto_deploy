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


def export_project(server, port, project_id): 
    url = f"http://{server}:{port}/v2/projects/{project_id}/export"
    response = requests.get(url)
    print (response)
    if not response.ok:
        print(f"Error retrieving links: {response.status_code}")
        exit()
    try:
        projects = response.json()
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response content: {response.content}")
        exit()

def set_single_packet_filter(server, port, project_id, link_id, filter_type=None, filter_value=None):
    # Get available packet filter types
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}/available_filters"
    response = requests.get(url)
    available_filters = [f["type"] for f in response.json()]

    # Select the filter type
    if filter_type is None:
        print("Available packet filter types:")
        for i, filter_type in enumerate(available_filters):
            print(f"{i + 1}. {filter_type}")
        selected_filter_type = input("Enter the number of the packet filter type you want to set: ")
        while not selected_filter_type.isdigit() or int(selected_filter_type) < 1 or int(selected_filter_type) > len(available_filters):
            print("Invalid selection.")
            selected_filter_type = input("Enter the number of the packet filter type you want to set: ")
        selected_filter_type = available_filters[int(selected_filter_type) - 1]
    else:
        if filter_type not in available_filters:
            print(f"Filter type {filter_type} is not available for this link.")
            return None, None
        selected_filter_type = filter_type

    # Enter the filter value
    if filter_value is None:
        selected_filter_value = input(f"Enter the value for the '{selected_filter_type}' packet filter: ")
        while not selected_filter_value.isdigit():
            print("Invalid input. Please enter a numerical value.")
            selected_filter_value = input(f"Enter the value for the '{selected_filter_type}' packet filter: ")
    else:
        selected_filter_value = filter_value

    # Construct the payload for the PUT request
    payload = {
        "filters": {
            selected_filter_type: [int(selected_filter_value)]
        }
    }

    # Submit the PUT request
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    response = requests.put(url, json=payload)

    # Check the response status code and print a message if successful
    if response.status_code == 200 or response.status_code == 201:
        #print(f"\nFilter {selected_filter_type} has been successfully added.")
        return selected_filter_type, selected_filter_value
    elif response.status_code == 400:
        print("\nThe request could not be processed. Check your request parameters and try again.")
        return None, None
    elif response.status_code == 404:
        print("\nThe specified link or project was not found. Check the link and project IDs and try again.")
        return None, None
    else:
        print(f"\nAn unexpected error occurred: {response.status_code}")
        return None, None

def remove_single_packet_filter(server, port, project_id, link_id):    
    # Remove all filters
    payload = {"filters": {}}

    # Submit the PUT request
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    response = requests.put(url, json=payload)

    # Parse the output of the response for the filters
    output = response.json()
    
    # Check the response status code and print a message if successful
    if response.status_code == 200 or response.status_code == 201:
        #print("\nAll packet filters have been successfully removed.")
        return
    elif response.status_code == 400:
        print("\nThe request could not be processed. Check your request parameters and try again.")
        return
    elif response.status_code == 404:
        print("\nThe specified link or project was not found. Check the link and project IDs and try again.")
        return
    else:
        print(f"\nAn unexpected error occurred: {response.status_code}")
        return
            
def set_suspend(server, port, project_id, link_id):
    # Get the current state of the link
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    response = requests.get(url)
    link_data = response.json()
    # Check if the "suspend" key exists in the link_data dictionary
    if "suspend" in link_data:
        current_suspend = link_data["suspend"]
        if current_suspend:
            selected_suspend = False
        else:
            selected_suspend = True
    else:
        selected_suspend = False
    # Update the state of the link
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    data = {"suspend": selected_suspend}
    response = requests.put(url, json=data)
    if response.ok:
        if selected_suspend:
            print("Link suspended.")
        else:
            print("Link enabled.")
    else:
        print("Error updating link state.")    

def reset_single_suspend(server, port, project_id, link_id):
    # Get the current state of the link
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    response = requests.get(url)
    link_data = response.json()
    # Check if the "suspend" key exists in the link_data dictionary
    if "suspend" in link_data:
        current_suspend = link_data["suspend"]
        if current_suspend:
            selected_suspend = False
        else:
            selected_suspend = True
    else:
        selected_suspend = False
    # Set the suspend value to False
    selected_suspend = False
    # Update the state of the link
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    data = {"suspend": selected_suspend}
    response = requests.put(url, json=data)
    if response.ok:
        if selected_suspend:
            print("Link suspended.")
        else:
            print("Link enabled.")
    else:
        print("Error updating link state.")

def reset_all_packet_filters(server, port, project_id):
    # Get links in the project
    links_url = f"http://{server}:{port}/v2/projects/{project_id}/links"
    response = requests.get(links_url)
    links = response.json()
    for link in links:
        # Get available packet filter types
        available_filters_url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link['link_id']}/available_filters"
        response = requests.get(available_filters_url)
        available_filters = [f["type"] for f in response.json()]
        payload = { "filters": { filter_type: [0] for filter_type in available_filters } }
        # Submit the PUT request
        url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link['link_id']}"
        response = requests.put(url, json=payload)
    # Check the response status code and print a message if successful
    if response.status_code == 200 or response.status_code == 201:
        print("\nAll packet filters have been successfully removed.")
    elif response.status_code == 400:
        print("\nThe request could not be processed. Check your request parameters and try again.")
    elif response.status_code == 404:
        print("\nThe specified link or project was not found. Check the link and project IDs and try again.")
    else:
        print(f"\nAn unexpected error occurred: {response.status_code}")
        return

def reset_all_link_states(server, port, project_id):
    # Get links in the project
    links_url = f"http://{server}:{port}/v2/projects/{project_id}/links"
    response = requests.get(links_url)
    links = response.json()
    print(f"http://{server}:{port}/v2/projects/{project_id}/links")
    for link in links:
        payload = { "suspend": False }
        # Submit the PUT request
        url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link['link_id']}"
        response = requests.put(url, json=payload)
    if response.status_code not in (200, 201):
        print(f"\nError: failed to update 'suspend' value for all links (status code {response.status_code})")
    else:
        print(f"\nAll links have been resumed")
        
def reset_lab_client_states(server, port, project_id):
    reset_all_link_states(server, port, project_id)
    reset_all_packet_filters(server, port, project_id)
    nodes = get_nodes(server, port, project_id)
    client_nodes = find_nodes_by_name(nodes, 'Network-Test-Client')
    for client_node in client_nodes:
        client_node_id = client_node[0]
        change_node_state(server, port, project_id, client_node_id, 'off')
    return True
        
def restart_node(server, port, project_id, node_id):
    url = f"http://{server}:{port}/v2/projects/{project_id}/nodes/{node_id}/stop"
    response = requests.post(url)
    if response.status_code != 200:
        print("Error stopping node:", response.text)
        return False
    url = f"http://{server}:{port}/v2/projects/{project_id}/nodes/{node_id}/start"
    response = requests.post(url)
    if response.status_code != 200:
        print("Error starting node:", response.text)
        return False
    return True

def change_node_state(server, port, project_id, node_id, state):
    if state == "on":
        url = f"http://{server}:{port}/v2/projects/{project_id}/nodes/{node_id}/start"
    elif state == "off":
        url = f"http://{server}:{port}/v2/projects/{project_id}/nodes/{node_id}/stop"
    else:
        print("Invalid state. Please use 'on' or 'off'.")
        return False
    response = requests.post(url)
    if response.status_code != 200:
        print(f"Error changing node state to {state}:", response.text)
        return False
    return True
