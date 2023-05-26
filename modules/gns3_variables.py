import logging
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

processes = {}

db_path = 'gns3.db'

deployment_type = ''
deployment_status = ''
deployment_step = ''

# region Viptela Variables
viptela_username = 'admin'
viptela_old_password = "admin"
viptela_password = 'PW4netops'
org_name = 'sdwan-lab'
vbond_address = '172.16.4.10'
vmanage_address = '172.16.2.2'
vsmart_address = '172.16.4.6'
switchport_count = 95

versa_director_username = 'Administrator'
versa_old_password = "versa123"
versa_analytics_username = "admin"
versa_flexvnf_username = "admin"

mgmt_switchport_count = 45
mgmt_main_switchport_count = 30
# endregion

gns3_server_data_old = [
 {
     "GNS3 Server": "10.210.242.13",
     "Server Name": "er-test-01",
     "Server Port": "80",
     "vManage API IP": "172.16.2.2",
     "Project Name": "test111",
     "Tap Name": "tap1",
     "Use Tap": 0,
     "Site Count": 0
 }
]

# region Variables: GNS3 Template Data
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

client_filename = 'client_interfaces'
client_node_file_path = 'etc/network/interfaces'

vmanage_template_name = 'vManage'
vbond_template_name = 'vBond'
vsmart_template_name = 'vSmart'
vedge_template_name = 'vEdge'
open_vswitch_cloud_template_name = 'Open_vSwitch_Cloud'
network_test_tool_template_name = 'Network_Test_Tool'
cisco_l3_router_template_name = 'Cisco IOU L3 155-2T'
mgmt_hub_template_name = 'MGMT_Hub'
mgmt_main_hub_template_name = 'Main-MGMT-Switch'
arista_veos_template_name = 'arista_switch'
arista_ceos_template_name = 'arista_ceos'
fortinet_fortigate_template_name = 'Fortigate 7.0.5'
versa_director_template_name = 'Versa Director 21.2.3'
versa_analytics_template_name = 'Versa Analytics 21.2.3'
versa_flexvnf_template_name = 'Versa FlexVNF 21.2.3'
# region Viptela Template Data
viptela_vmanage_template_data = {"compute_id": "local", "cpus": 16, "adapters": 6,
                                 "symbol": ":/symbols/affinity/circle/blue/server_cluster.svg",
                                 "adapter_type": "vmxnet3", "qemu_path": "/usr/bin/qemu-system-x86_64",
                                 "hda_disk_image": "viptela-vmanage-li-20.10.1-genericx86-64.qcow2",
                                 "hdb_disk_image": "empty30G.qcow2", "name": vmanage_template_name, "ram": 32768,
                                 "template_type": "qemu", "hda_disk_interface": "virtio",
                                 "hdb_disk_interface": "virtio", "options": "-cpu host -smp 2,maxcpus=2"}
viptela_vsmart_template_data = {"compute_id": "local", "cpus": 2, "adapters": 3,
                                "symbol": ":/symbols/affinity/circle/blue/interconnect.svg",
                                "adapter_type": "vmxnet3", "qemu_path": "/usr/bin/qemu-system-x86_64",
                                "hda_disk_image": "viptela-smart-li-20.10.1-genericx86-64.qcow2",
                                "name": vsmart_template_name, "ram": 4096, "template_type": "qemu",
                                "hda_disk_interface": "virtio", "options": "-cpu host"}
viptela_vbond_template_data = {"compute_id": "local", "cpus": 2, "adapters": 3,
                               "symbol": ":/symbols/affinity/circle/blue/isdn.svg", "adapter_type": "vmxnet3",
                               "qemu_path": "/usr/bin/qemu-system-x86_64",
                               "hda_disk_image": "viptela-edge-20.10.1-genericx86-64.qcow2",
                               "name": vbond_template_name, "ram": 2048, "template_type": "qemu",
                               "hda_disk_interface": "virtio", "options": "-cpu host"}
viptela_vedge_template_data = {"compute_id": "local", "cpus": 1, "adapters": 6,
                               "symbol": ":/symbols/affinity/square/blue/communications.svg",
                               "adapter_type": "vmxnet3", "qemu_path": "/usr/bin/qemu-system-x86_64",
                               "hda_disk_image": "viptela-edge-20.10.1-genericx86-64.qcow2",
                               "name": vedge_template_name, "ram": 2048, "template_type": "qemu",
                               "hda_disk_interface": "virtio", "options": "-cpu host -smp 2,maxcpus=2"}
# endregion
# region Misc Template Data
appneta_mp_template_data = {"compute_id": "local", "cpus": 2, "port_name_format": "eth{0}", "adapters": 3,
                            "adapter_type": "virtio-net-pci", "qemu_path": "/usr/bin/qemu-system-x86_64",
                            "mac_address": "52:54:00:E0:00:00",
                            "hda_disk_image": "pathview-amd64-13.12.6.53966.qcow2", "name": "Appneta-vk35",
                            "ram": 4096, "template_type": "qemu"}
openvswitch_template_data = {"compute_id": "local", "adapters": 16, "category": "switch",
                             "image": "gns3/ovs-snmp:latest", "name": "Open vSwitch",
                             "symbol": ":/symbols/classic/multilayer_switch.svg", "template_type": "docker",
                             "usage": "By default all interfaces are connected to the br0"}
openvswitch_cloud_template_data = {"compute_id": "local", "adapters": switchport_count, "category": "switch",
                                   "image": "gns3/ovs-snmp:latest", "name": open_vswitch_cloud_template_name,
                                   "symbol": ":/symbols/cloud.svg", "template_type": "docker",
                                   "usage": "By default all interfaces are connected to the br0"}
network_test_tool_template_data = {"compute_id": "local", "adapters": 2, "category": "guest",
                                   "image": "evanrogers719/network_test_tool:latest",
                                   "name": network_test_tool_template_name, "symbol": ":/symbols/docker_guest.svg",
                                   "template_type": "docker"}
cisco_l3_router_template_data = {"compute_id": "local", "path": "L3-ADVENTERPRISEK9-M-15.5-2T.bin", "nvram": 256,
                                 "ram": 512, "symbol": ":/symbols/classic/router.svg", "template_type": "iou",
                                 "use_default_iou_values": True, "ethernet_adapters": 2, "serial_adapters": 0,
                                 "name": cisco_l3_router_template_name,
                                 "startup_config": "iou_l3_base_startup-config.txt"}
fortinet_fortigate_template_data = {"compute_id": "local", "cpus": 4, "adapters": 10, "adapter_type": "e1000",
                                    "qemu_path": "/usr/bin/qemu-system-x86_64",
                                    "hda_disk_image": "FGT_VM64_KVM-v7.0.5.F-FORTINET.out.kvm.qcow2",
                                    "hdb_disk_image": "empty30G.qcow2", "name": fortinet_fortigate_template_name,
                                    "ram": 2048, "template_type": "qemu", "hda_disk_interface": "virtio",
                                    "hdb_disk_interface": "virtio"}
arista_veos_template_data = {"compute_id": "local", "cpus": 2, "adapters": 20, "adapter_type": "e1000",
                             "qemu_path": "/usr/bin/qemu-system-x86_64", "hda_disk_image": "cdrom.iso",
                             "hdb_disk_image": "vEOS-lab-4.28.0F.qcow2",
                             "name": arista_veos_template_name,
                             "ram": 2048, "template_type": "qemu", "hda_disk_interface": "ide",
                             "hdb_disk_interface": "ide", "options": "-cpu host"}
arista_ceos_old_template_data = {"compute_id": "local", "adapters": 20, "category": "router",
                                 "image": "ceosimage:4.26.0.1F", "name": arista_ceos_template_name,
                                 "symbol": ":/symbols/classic/multilayer_switch.svg", "template_type": "docker",
                                 "usage": "By default all interfaces are connected to the br0",
                                 "start_command": "/sbin/init systemd.setenv=INTFTYPE=eth systemd.setenv=ETBA=1 systemd.setenv=SKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 systemd.setenv=CEOS=1 systemd.setenv=EOS_PLATFORM=ceoslab systemd.setenv=container=docker",
                                 "environment": "INTFTYPE=eth\nETBA=1 \nSKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 \nCEOS=1 \nEOS_PLATFORM=ceoslab \ncontainer=docker\nMAPETH0=1\nMGMTINF=eth0", }

arista_ceos_template_data = {"compute_id": "local", "adapters": 20, "category": "router",
                             "image": "ceosimage:4.28.6.1M", "name": arista_ceos_template_name,
                             "symbol": ":/symbols/classic/multilayer_switch.svg", "template_type": "docker",
                             "usage": "By default all interfaces are connected to the br0",
                             "start_command": "/sbin/init systemd.setenv=INTFTYPE=eth systemd.setenv=ETBA=1 systemd.setenv=SKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 systemd.setenv=CEOS=1 systemd.setenv=EOS_PLATFORM=ceoslab systemd.setenv=container=docker",
                             "environment": "INTFTYPE=eth\nETBA=1 \nSKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 \nCEOS=1 \nEOS_PLATFORM=ceoslab \ncontainer=docker\nMAPETH0=1\nMGMTINF=eth0", }
# endregion
versa_director_template_data = {"compute_id": "local", "cpus": 16, "adapters": 6,
                                 "symbol": ":/symbols/affinity/circle/blue/server_cluster.svg",
                                 "adapter_type": "virtio-net-pci", "qemu_path": "/usr/bin/qemu-system-x86_64",
                                 "hda_disk_image": "versa-director-c19c43c-21.2.3.qcow2",
                                 "name": versa_director_template_name, "ram": 16384,
                                 "template_type": "qemu", "hda_disk_interface": "virtio",
                                 "options": "-cpu host -smp 2,maxcpus=2"}
versa_analytics_template_data = {"compute_id": "local", "cpus": 6, "adapters": 6,
                                "symbol": ":/symbols/affinity/circle/blue/interconnect.svg",
                                "adapter_type": "virtio-net-pci", "qemu_path": "/usr/bin/qemu-system-x86_64",
                                "hda_disk_image": "versa-analytics-67ff6c7-21.2.3.qcow2",
                                "name": versa_analytics_template_name, "ram": 16384, "template_type": "qemu",
                                "hda_disk_interface": "virtio", "options": "-cpu host"}
versa_flexvnf_template_data = {"compute_id": "local", "cpus": 2, "adapters": 6,
                               "symbol": ":/symbols/affinity/circle/blue/isdn.svg", "adapter_type": "vmxnet3",
                               "qemu_path": "/usr/bin/qemu-system-x86_64",
                               "hda_disk_image": "versa-flexvnf-67ff6c7-21.2.3.qcow2",
                               "name": versa_flexvnf_template_name, "ram": 2048, "template_type": "qemu",
                               "hda_disk_interface": "virtio", "options": "-cpu host"}


vmanage_deploy_data = {"x": -107, "y": 570, "name": "vManage"}
vsmart_deploy_data = {"x": -182, "y": 495, "name": "vSmart"}
vbond_deploy_data = {"x": -32, "y": 495, "name": "vBond"}
isp_router_deploy_data = {"x": -108, "y": -247, "name": "ISP-Router"}
cloud_node_deploy_data = {"x": -154, "y": -247, "name": "MGMT-Cloud-TAP", "node_type": "cloud",
                          "compute_id": "local", "symbol": ":/symbols/cloud.svg"}
main_mgmt_switch_deploy_data = {"x": 278, "y": -141, "name": "Main_MGMT-switch"}
nat_node_deploy_data = {"x": -154, "y": -554, "name": "Internet", "node_type": "nat", "compute_id": "local",
                        "symbol": ":/symbols/cloud.svg"}

versa_director_deploy_data = {"x": -107, "y": 570, "name": "Versa_Director"}
versa_analytics_deploy_data = {"x": -182, "y": 495, "name": "Versa_Analytics"}
versa_controller_deploy_data = {"x": -32, "y": 495, "name": "Versa_Controller"}

big_block_deploy_data = {
    "svg": "<svg height=\"1500\" width=\"3681\"><rect fill=\"#ffffff\" fill-opacity=\"1.0\" height=\"1500\" stroke=\"#000000\" stroke-width=\"2\" width=\"3681\" /></svg>",
    "x": -1950, "y": -630, "z": -1}

arista_deploy_data = {
    "arista_01_deploy_data": {"x": -323, "y": -219, "name": "arista-spine1"},
    "arista_02_deploy_data": {"x": -23, "y": -219, "name": "arista-spine2"},
    "arista_03_deploy_data": {"x": -558, "y": 79, "name": "arista-leaf1"},
    "arista_04_deploy_data": {"x": -323, "y": 79, "name": "arista-leaf2"},
    "arista_05_deploy_data": {"x": -23, "y": 79, "name": "arista-leaf3"},
    "arista_06_deploy_data": {"x": 200, "y": 79, "name": "arista-leaf4"},
    "arista_07_deploy_data": {"x": 500, "y": 79, "name": "arista-leaf5"}
}
arista_2 = {
    "arista_07_deploy_data": {"x": -25, "y": -23, "name": "arista-leaf5"},
    "arista_08_deploy_data": {"x": -550, "y": 276, "name": "arista-leaf6"},
    "arista_09_deploy_data": {"x": -325, "y": 276, "name": "arista-leaf7"},
    "arista_10_deploy_data": {"x": -25, "y": 276, "name": "arista-leaf8"},
}
client_deploy_data = {
    "client_01_deploy_data": {"x": -555, "y": 373, "name": "Client-1"},
    "client_02_deploy_data": {"x": -330, "y": 373, "name": "Client-2"},
    "client_03_deploy_data": {"x": -30, "y": 373, "name": "Client-3"},
    "client_04_deploy_data": {"x": 200, "y": 373, "name": "Client-4"},
    "client_05_deploy_data": {"x": 494, "y": 373, "name": "Client-5"},
}
local_switch_deploy_data = {
    "switch_01_deploy_data": {"x": -445, "y": 237, "name": "switch-1"},
    "switch_02_deploy_data": {"x": 83, "y": 237, "name": "switch-2"},
    "switch_03_deploy_data": {"x": 491, "y": 237, "name": "switch-3"},
    "switch_04_deploy_data": {"x": 199, "y": 237, "name": "switch-4"},
    "switch_05_deploy_data": {"x": 499, "y": 237, "name": "switch-5"},
}
drawing_deploy_data = {
    "drawing_01": {
        "svg": "<svg width=\"374.71428571428567\" height=\"146.57142857142856\"><ellipse cx=\"187\" rx=\"188\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": -600, "y": 26, "z": 0},
    "drawing_02": {
        "svg": "<svg width=\"374.71428571428567\" height=\"146.57142857142856\"><ellipse cx=\"187\" rx=\"188\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": -77, "y": 24, "z": 0},
    "drawing_03": {
        "svg": "<svg width=\"495.7142857142858\" height=\"146.57142857142856\"><ellipse cx=\"247\" rx=\"248\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": -390, "y": -274, "z": 0},
    "drawing_04": {
        "svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65001</text></svg>",
        "x": -453, "y": 75, "z": 2},
    "drawing_05": {
        "svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65002</text></svg>",
        "x": 69, "y": 74, "z": 2},
    "drawing_06": {
        "svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65000</text></svg>",
        "x": -189, "y": -268, "z": 2},
    "drawing_07": {
        "svg": "<svg width=\"95\" height=\"23\"><text font-family=\"Arial Black\" font-size=\"10.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">MLAG Peer Link</text></svg>",
        "x": -457, "y": 99, "z": 2},
    "drawing_08": {
        "svg": "<svg width=\"95\" height=\"23\"><text font-family=\"Arial Black\" font-size=\"10.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">MLAG Peer Link</text></svg>",
        "x": 66, "y": 101, "z": 2},
    "drawing_09": {
        "svg": "<svg width=\"356\" height=\"36\"><text font-family=\"Arial\" font-size=\"24.0\" fill=\"#000000\" fill-opacity=\"1.0\">Arista EVPN / BGP / VXLAN Lab</text></svg>",
        "x": -238, "y": -407, "z": 2},
    "drawing_10": {
        "svg": "<svg width=\"194\" height=\"212\"><text font-family=\"TypeWriter\" font-size=\"10.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">Managment Network: 172.16.3.0/24\narista-spine1 - 172.16.3.2\narista-spine1 - 172.16.3.3\narista-leaf1 - 172.16.3.4\narista-leaf2 - 172.16.3.5\narista-leaf3 - 172.16.3.6\narista-leaf4 - 172.16.3.7\narista-leaf5 - 172.16.3.8\n\nClient Network: 172.16.101.0/24\nVLAN 40\nVXLAN1\nClient-1: 172.16.101.2\nClient-2: 172.16.101.3\nClient-3: 172.16.101.4\nClient-4: 172.16.101.5\nClient-5: 172.16.101.6</text></svg>",
        "x": -603, "y": -293, "z": 2},
    "drawing_11": {
        "svg": "<svg width=\"1326\" height=\"163\"><rect width=\"1326\" height=\"163\" fill=\"#00f900\" fill-opacity=\"0.19299610894941635\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": -640, "y": 318, "z": 0},
    "drawing_12": {
        "svg": "<svg width=\"74\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">VLAN 40</text></svg>",
        "x": -182, "y": 320, "z": 2},
    "drawing_13": {
        "svg": "<svg width=\"207.5\" height=\"146.57142857142856\"><ellipse cx=\"103\" rx=\"104\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": 422, "y": 21, "z": 0},
    "drawing_14": {
        "svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65003</text></svg>",
        "x": 481, "y": 29, "z": 2},
}

deploy_data_z = {"z": -1}

oa_city_data = {
"vEdge_001": {"city": "NewYork", "latitude": 40.712776, "longitude": -74.005974},
"vEdge_002": {"city": "Cairns", "latitude": -16.920334, "longitude": 145.770889},
"vEdge_003": {"city": "London", "latitude": 51.507351, "longitude": -0.127758},
"vEdge_004": {"city": "Stockholm", "latitude": 59.329323, "longitude": 18.068581},
"vEdge_005": {"city": "Pune", "latitude": 18.520430, "longitude": 73.856743},
"vEdge_006": {"city": "Hamburg", "latitude": 53.551086, "longitude": 9.993682},
"vEdge_007": {"city": "RiodeJaneiro", "latitude": -22.9068, "longitude": -43.1729},
"vEdge_008": {"city": "Rome", "latitude": 41.902782, "longitude": 12.496366},
"vEdge_009": {"city": "Copenhagen", "latitude": 55.676097, "longitude": 12.568337},
"vEdge_010": {"city": "SaoPaulo", "latitude": -23.5505, "longitude": -46.6333},
}

versa_city_data = {
"FlexVNF_001": {"city": "NewYork", "latitude": 40.712776, "longitude": -74.005974},
"FlexVNF_002": {"city": "Cairns", "latitude": -16.920334, "longitude": 145.770889},
"FlexVNF_003": {"city": "London", "latitude": 51.507351, "longitude": -0.127758},
"FlexVNF_004": {"city": "Stockholm", "latitude": 59.329323, "longitude": 18.068581},
"FlexVNF_005": {"city": "Pune", "latitude": 18.520430, "longitude": 73.856743},
"FlexVNF_006": {"city": "Hamburg", "latitude": 53.551086, "longitude": 9.993682},
"FlexVNF_007": {"city": "RiodeJaneiro", "latitude": -22.9068, "longitude": -43.1729},
"FlexVNF_008": {"city": "Rome", "latitude": 41.902782, "longitude": 12.496366},
"FlexVNF_009": {"city": "Copenhagen", "latitude": 55.676097, "longitude": 12.568337},
"FlexVNF_010": {"city": "SaoPaulo", "latitude": -23.5505, "longitude": -46.6333},
}

city_data = {
        "vEdge_001": {"city": "NewYork", "latitude": 40.712776, "longitude": -74.005974},
        "vEdge_002": {"city": "LosAngeles", "latitude": 34.052235, "longitude": -118.243683},
        "vEdge_003": {"city": "Chicago", "latitude": 41.878113, "longitude": -87.629799},
        "vEdge_004": {"city": "Houston", "latitude": 29.760427, "longitude": -95.369804},
        "vEdge_005": {"city": "Phoenix", "latitude": 33.448376, "longitude": -112.074036},
        "vEdge_006": {"city": "Philadelphia", "latitude": 39.952583, "longitude": -75.165222},
        "vEdge_007": {"city": "SanAntonio", "latitude": 29.424122, "longitude": -98.493628},
        "vEdge_008": {"city": "SanDiego", "latitude": 32.715736, "longitude": -117.161087},
        "vEdge_009": {"city": "Dallas", "latitude": 32.776665, "longitude": -96.796989},
        "vEdge_010": {"city": "SanJose", "latitude": 37.338207, "longitude": -121.886329},
        "vEdge_011": {"city": "Paris", "latitude": 48.856613, "longitude": 2.352222},
        "vEdge_012": {"city": "London", "latitude": 51.507351, "longitude": -0.127758},
        "vEdge_013": {"city": "Barcelona", "latitude": 41.385064, "longitude": 2.173404},
        "vEdge_014": {"city": "Rome", "latitude": 41.902782, "longitude": 12.496366},
        "vEdge_015": {"city": "Berlin", "latitude": 52.520008, "longitude": 13.404954},
        "vEdge_016": {"city": "Vienna", "latitude": 48.208176, "longitude": 16.373819},
        "vEdge_017": {"city": "Amsterdam", "latitude": 52.370216, "longitude": 4.895168},
        "vEdge_018": {"city": "Munich", "latitude": 48.135125, "longitude": 11.581981},
        "vEdge_019": {"city": "Madrid", "latitude": 40.416775, "longitude": -3.703790},
        "vEdge_020": {"city": "Zurich", "latitude": 47.376887, "longitude": 8.541694},
        "vEdge_021": {"city": "Edinburgh", "latitude": 55.953251, "longitude": -3.188267},
        "vEdge_022": {"city": "Athens", "latitude": 37.983810, "longitude": 23.727539},
        "vEdge_023": {"city": "Dublin", "latitude": 53.349805, "longitude": -6.260310},
        "vEdge_024": {"city": "Stockholm", "latitude": 59.329323, "longitude": 18.068581},
        "vEdge_025": {"city": "Brussels", "latitude": 50.850346, "longitude": 4.351721},
        "vEdge_026": {"city": "Copenhagen", "latitude": 55.676097, "longitude": 12.568337},
        "vEdge_027": {"city": "Oslo", "latitude": 59.913869, "longitude": 10.752245},
        "vEdge_028": {"city": "Helsinki", "latitude": 60.169856, "longitude": 24.938379},
        "vEdge_029": {"city": "Lisbon", "latitude": 38.722252, "longitude": -9.139337},
        "vEdge_030": {"city": "Venice", "latitude": 45.440847, "longitude": 12.315515},
        "vEdge_031": {"city": "Mumbai", "latitude": 19.076090, "longitude": 72.877426},
        "vEdge_032": {"city": "Delhi", "latitude": 28.704060, "longitude": 77.102493},
        "vEdge_033": {"city": "Bangalore", "latitude": 12.971599, "longitude": 77.594566},
        "vEdge_034": {"city": "Hyderabad", "latitude": 17.385044, "longitude": 78.486671},
        "vEdge_035": {"city": "Chennai", "latitude": 13.082680, "longitude": 80.270721},
        "vEdge_036": {"city": "Kolkata", "latitude": 22.572645, "longitude": 88.363892},
        "vEdge_037": {"city": "Ahmedabad", "latitude": 23.022505, "longitude": 72.571365},
        "vEdge_038": {"city": "Pune", "latitude": 18.520430, "longitude": 73.856743},
        "vEdge_039": {"city": "Jaipur", "latitude": 26.912434, "longitude": 75.787271},
        "vEdge_040": {"city": "Lucknow", "latitude": 26.846693, "longitude": 80.946166},
        "vEdge_041": {"city": "Kanpur", "latitude": 26.449923, "longitude": 80.331871},
        "vEdge_042": {"city": "Nagpur", "latitude": 21.145800, "longitude": 79.088155},
        "vEdge_043": {"city": "Visakhapatnam", "latitude": 17.686815, "longitude": 83.218483},
        "vEdge_044": {"city": "Bhopal", "latitude": 23.259933, "longitude": 77.412615},
        "vEdge_045": {"city": "Patna", "latitude": 25.594095, "longitude": 85.137566},
        "vEdge_046": {"city": "Sydney", "latitude": -33.865143, "longitude": 151.209900},
        "vEdge_047": {"city": "Melbourne", "latitude": -37.813628, "longitude": 144.963058},
        "vEdge_048": {"city": "Brisbane", "latitude": -27.469771, "longitude": 153.025124},
        "vEdge_049": {"city": "Perth", "latitude": -31.953512, "longitude": 115.857048},
        "vEdge_050": {"city": "Adelaide", "latitude": -34.928499, "longitude": 138.600746},
        "vEdge_051": {"city": "GoldCoast", "latitude": -28.016666, "longitude": 153.399994},
        "vEdge_052": {"city": "Newcastle", "latitude": -32.926689, "longitude": 151.778916},
        "vEdge_053": {"city": "Canberra", "latitude": -35.282001, "longitude": 149.128998},
        "vEdge_054": {"city": "Wollongong", "latitude": -34.424999, "longitude": 150.893555},
        "vEdge_055": {"city": "Geelong", "latitude": -38.149918, "longitude": 144.361718},
        "vEdge_056": {"city": "Hobart", "latitude": -42.882137, "longitude": 147.327194},
        "vEdge_057": {"city": "Townsville", "latitude": -19.258965, "longitude": 146.816956},
        "vEdge_058": {"city": "Cairns", "latitude": -16.920334, "longitude": 145.770889},
        "vEdge_059": {"city": "Toowoomba", "latitude": -27.560560, "longitude": 151.953796},
        "vEdge_060": {"city": "Darwin", "latitude": -12.462827, "longitude": 130.841782},
        "vEdge_061": {"city": "Berlin", "latitude": 52.520008, "longitude": 13.404954},
        "vEdge_062": {"city": "Hamburg", "latitude": 53.551086, "longitude": 9.993682},
        "vEdge_063": {"city": "Munich", "latitude": 48.135125, "longitude": 11.581981},
        "vEdge_064": {"city": "Cologne", "latitude": 50.937531, "longitude": 6.960279},
        "vEdge_065": {"city": "Frankfurt", "latitude": 50.110924, "longitude": 8.682127},
        "vEdge_066": {"city": "Stuttgart", "latitude": 48.775846, "longitude": 9.182932},
        "vEdge_067": {"city": "Dusseldorf", "latitude": 51.227741, "longitude": 6.773456},
        "vEdge_068": {"city": "Dortmund", "latitude": 51.513587, "longitude": 7.465298},
        "vEdge_069": {"city": "Essen", "latitude": 51.458426, "longitude": 7.014088},
        "vEdge_070": {"city": "Leipzig", "latitude": 51.339695, "longitude": 12.373075},
        "vEdge_071": {"city": "Bremen", "latitude": 53.079296, "longitude": 8.801694},
        "vEdge_072": {"city": "Dresden", "latitude": 51.050409, "longitude": 13.737262},
        "vEdge_073": {"city": "Hanover", "latitude": 52.375892, "longitude": 9.732010},
        "vEdge_074": {"city": "Nuremberg", "latitude": 49.452030, "longitude": 11.076750},
        "vEdge_075": {"city": "Duisburg", "latitude": 51.434407, "longitude": 6.762329},
        "vEdge_076": {"city": "Saskatoon", "latitude": 52.1332, "longitude": -106.6700},
        "vEdge_077": {"city": "Regina", "latitude": 50.4452, "longitude": -104.6189},
        "vEdge_078": {"city": "Sherbrooke", "latitude": 45.4000, "longitude": -71.9000},
        "vEdge_079": {"city": "St.John's", "latitude": 47.5615, "longitude": -52.7126},
        "vEdge_080": {"city": "Saguenay", "latitude": 48.4168, "longitude": -71.0682},
        "vEdge_081": {"city": "Trois-Rivieres", "latitude": 46.3508, "longitude": -72.5461},
        "vEdge_082": {"city": "Kelowna", "latitude": 49.8879, "longitude": -119.4960},
        "vEdge_083": {"city": "Abbotsford", "latitude": 49.0579, "longitude": -122.2526},
        "vEdge_084": {"city": "Kingston", "latitude": 44.2312, "longitude": -76.4860},
        "vEdge_085": {"city": "Guelph", "latitude": 43.5448, "longitude": -80.2482},
        "vEdge_086": {"city": "Moncton", "latitude": 46.0878, "longitude": -64.7782},
        "vEdge_087": {"city": "Thunder Bay", "latitude": 48.3809, "longitude": -89.2477},
        "vEdge_088": {"city": "Saint John", "latitude": 45.2733, "longitude": -66.0633},
        "vEdge_089": {"city": "Peterborough", "latitude": 44.3000, "longitude": -78.3167},
        "vEdge_090": {"city": "Lethbridge", "latitude": 49.6935, "longitude": -112.8418},
        "vEdge_091": {"city": "BuenosAires", "latitude": -34.6037, "longitude": -58.3816},
        "vEdge_092": {"city": "Rio de Janeiro", "latitude": -22.9068, "longitude": -43.1729},
        "vEdge_093": {"city": "Lima", "latitude": -12.0464, "longitude": -77.0428},
        "vEdge_094": {"city": "Bogota", "latitude": 4.7109, "longitude": -74.0721},
        "vEdge_095": {"city": "Santiago", "latitude": -33.4489, "longitude": -70.6693},
        "vEdge_096": {"city": "Brasilia", "latitude": -15.7942, "longitude": -47.8822},
        "vEdge_097": {"city": "Salvador", "latitude": -12.9722, "longitude": -38.5014},
        "vEdge_098": {"city": "Fortaleza", "latitude": -3.7319, "longitude": -38.5267},
        "vEdge_099": {"city": "Recife", "latitude": -8.0543, "longitude": -34.8813},
        "vEdge_100": {"city": "Montevideo", "latitude": -34.9011, "longitude": -56.1645},
        "vEdge_101": {"city": "SaoPaulo", "latitude": -23.5505, "longitude": -46.6333},
    }
