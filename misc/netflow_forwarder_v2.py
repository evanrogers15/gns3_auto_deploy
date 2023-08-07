from scapy.all import *
import os
import subprocess
import re
import time

# Define constants
TARGET_IP = os.getenv("FLOW_TARGET")
FULL_MANAGEMENT_SUBNET = os.getenv("MANAGEMENT_SUBNET")

# Convert the FULL_MANAGEMENT_SUBNET to a string, if necessary
FULL_MANAGEMENT_SUBNET = str(FULL_MANAGEMENT_SUBNET)

# Extract the first three octets from the full management subnet IP
management_subnet_match = re.match(r"(\d+\.\d+\.\d+)\.\d+", FULL_MANAGEMENT_SUBNET)
print(management_subnet_match)
if management_subnet_match:
    MANAGEMENT_SUBNET = management_subnet_match.group(1)
else:
    raise ValueError("Invalid MANAGEMENT_SUBNET format. Please provide a valid IPv4 address.")

def set_eth1_ip():
    # Calculate the new IP address for eth1 (30 added to the last octet of MANAGEMENT_SUBNET)
    eth1_ip = f"{MANAGEMENT_SUBNET}.30"

    # Set the IP address of eth1 using ifconfig
    subprocess.run(["ifconfig", "eth1", eth1_ip, "netmask", "255.255.255.0", "up"])

def add_route_to_flow_target():
    gateway_ip = f"{MANAGEMENT_SUBNET}.1"

    # Add a route to the FLOW_TARGET using the gateway IP
    subprocess.run(["route", "add", "-host", TARGET_IP, "gw", gateway_ip])

def is_netflow_packet(packet):
    # Check if the packet is a UDP packet and contains the NetflowHeader
    return UDP in packet and NetflowHeader in packet

def create_modified_packet(packet):
    if is_netflow_packet(packet):
        # Extract the third octet from the original source IP address
        original_source_ip = packet[IP].src
        third_octet = original_source_ip.split(".")[2]

        # Construct the new source IP address with the first three octets from MANAGEMENT_SUBNET and the third octet from the original source IP
        new_source_ip = f"{MANAGEMENT_SUBNET}.{third_octet}"
        # print(new_source_ip)

        # Create a new NetFlow packet with the new source IP address
        new_packet = IP(src=new_source_ip, dst=TARGET_IP) / UDP(sport=packet[UDP].sport, dport=packet[UDP].dport) / \
                     packet[NetflowHeader]

        # Remove checksums so they get recalculated
        del new_packet[IP].chksum
        del new_packet[UDP].chksum

        # Forward the modified packet to the new target
        send(new_packet, iface="eth1", verbose=0)

# Set the IP address of eth1
set_eth1_ip()

# Add a route to the specified FLOW_TARGET
add_route_to_flow_target()

time.sleep(5)

# Use the custom filter function to capture Netflow-related traffic
sniff(prn=create_modified_packet, iface="eth0", lfilter=is_netflow_packet)
