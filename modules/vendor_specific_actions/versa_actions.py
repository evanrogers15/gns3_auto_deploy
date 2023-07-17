import logging.handlers
from modules.gns3.gns3_actions import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

auth = ("Administrator", "versa123")

headers = {"Content-Type": "application/json"}

# region Functions: Versa API
def versa_configure_analytics_cluster(director_ip, analytics_ip, analytics_southbound_ip):
    url = f"https://{director_ip}:9182/api/config/nms/provider"
    data = {
        "analytics-cluster": {
            "name": "Analytics",
            "connector-config": {
                "port": "8443",
                "ip-address": [
                    analytics_ip
                ]
            },
            "log-collector-config": {
                "port": "1234",
                "ip-address": [
                    analytics_southbound_ip
                ]
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Configured Analytics Cluster on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_provider_org(director_ip):
    url = f"https://{director_ip}:9182/nextgen/organization"
    data = {"name": "Versa-Root","uuid": "310f513a-01aa-4e91-9a53-4dae9b324839","subscriptionPlan": "Default-All-Services-Plan","id": 1,"authType": "psk","cpeDeploymentType": "SDWAN","vrfsGroups": [ { "id": 1, "vrfId": 1, "name": "Versa-Root-LAN-VR", "description": "", "enable_vpn": True }],"analyticsClusters": [ "Analytics"],"sharedControlPlane": False,"dynamicTenantConfig": { "inactivityInterval": 48},"blockInterRegionRouting": False}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Provider Organization on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_overlay_prefix(director_ip):
    url = f"https://{director_ip}:9182/vnms/ipam/overlay/prefixes"
    data = {"prefix":"10.10.0.0/16","status":{"value":1,"label":"Active"}, "is_pool":True}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Overlay Prefix on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_overlay_route(director_ip, controller_southbound_ip):
    url = f"https://{director_ip}:9182/api/config/nms/routing-options/static"
    data = {"route":{"description":"Overlay-Route","destination-prefix":"10.10.0.0/16","next-hop-address":controller_southbound_ip,"outgoing-interface":"eth1"}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Overlay Route on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")
    
def versa_create_controller_workflow(director_ip, controller_ip, controller_southbound_ip, isp_1_gateway, isp_1_ip, isp_2_gateway, isp_2_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/controllers/controller"
    controller_southbound_ip = f'{controller_southbound_ip}/24'
    isp_1_ip = f'{isp_1_ip}/30'
    isp_2_ip = f'{isp_2_ip}/30'

    data = { "versanms.sdwan-controller-workflow": { "controllerName": "Controller-01", "siteId": 1, "orgName": "Versa-Root", "resourceType": "Baremetal", "stagingController": True, "postStagingController": True, "baremetalController": { "serverIP": controller_ip, "controllerInterface": { "interfaceName": "vni-0/1", "unitInfoList": [ { "networkName": "Control-Network", "ipv4address": [ controller_southbound_ip ], "ipv4gateway": "", "ipv6gateway": "", "ipv4dhcp": False, "ipv6dhcp": False, "vlanId": 0, "wanStaging": True, "poolSize": 256 } ] }, "wanInterfaces": [ { "interfaceName": "vni-0/2", "unitInfoList": [ { "networkName": "ISP-1", "ipv4address": [ isp_1_ip ], "ipv4gateway": isp_1_gateway, "ipv4dhcp": False, "ipv6dhcp": False, "vlanId": 0, "wanStaging": True, "poolSize": 128, "transportDomainList": [ "Internet" ] } ] }, { "interfaceName": "vni-0/3", "unitInfoList": [ { "networkName": "ISP-2", "ipv4address": [ isp_2_ip ], "ipv4gateway": isp_2_gateway, "ipv4dhcp": False, "ipv6dhcp": False, "vlanId": 0, "wanStaging": True, "poolSize": 128, "transportDomainList": [ "Internet" ] } ] } ] }, "locationInfo": { "state": "CA", "country": "USA", "city": "San Jose", "longitude": -121.885252, "latitude": 37.33874 }, "analyticsCluster": "Analytics" }}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Controller Workflow on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")
        
def versa_deploy_controller(director_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/controllers/controller/deploy/Controller-01"
    data = {}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Deployed Controller on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_device_template(director_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/templates/template"
    data = {
        "versanms.sdwan-template-workflow": {
            "analyticsCluster": "Analytics", "bandwidth": "100", "licensePeriod": "1", "controllers": ["Controller-01"],
            "deviceFirmfactor": 6, "deviceType": "full-mesh", "diaConfig": {"loadBalance": False}, "isStaging": False,
            "lanInterfaces": [{
                                "interfaceName": "vni-0/2", "unitInfo": [{
                                    "vlanId": "0",
                                    "subOrganization": "Versa-Root",
                                    "vrfName": "Versa-Root-LAN-VR",
                                    "networkName": "LAN", "subUnit": "0",
                                    "ipv4Static": True, "ipv4Dhcp": False,
                                    "ip6Static": False, "ipv6Dhcp": False,
                                    "ipv4DhcpServer": True,
                                    "dhcpv4Profile": "DHCP",
                                    "dhcpV4Relay": False,
                                    "dhcpV4RelayAddress": ""
                                    }]},
            ],
            "providerOrg": {"name": "Versa-Root", "nextGenFW": False, "statefulFW": False},
            "redundantPair": {"enable": False}, "routingInstances": [], "siteToSiteTunnels": [],
            "solutionTier": "Premier-Elite-SDWAN",
            "snmp": {
                "snmpV1": False, "snmpV2": True, "snmpV3": False, "community": "public", "target-source": "{$v_SNMP_TARGET_SOURCE__snmpTargetSource}"
            },
            "splitTunnels": [{"vrfName": "Versa-Root-LAN-VR", "wanNetworkName": "ISP-1", "dia": True, "gateway": False},
                             {
                                 "vrfName": "Versa-Root-LAN-VR", "wanNetworkName": "ISP-2", "dia": True,
                                 "gateway": False
                             }], "subOrgs": [], "templateName": "Edge-Template", "templateType": "sdwan-post-staging",
            "wanInterfaces": [{
                                  "pppoe": False, "interfaceName": "vni-0/0", "unitInfo": [{
                                                                                               "vlanId": "0",
                                                                                               "networkName": "ISP-1",
                                                                                               "routing": {},
                                                                                               "subUnit": "0",
                                                                                               "ipv4Static": True,
                                                                                               "ipv4Dhcp": False,
                                                                                               "ip6Static": False,
                                                                                               "ipv6Dhcp": False,
                                                                                               "transportDomains": [
                                                                                                   "Internet"]
                                                                                           }]
                              }, {
                                  "pppoe": False, "interfaceName": "vni-0/1", "unitInfo": [{
                                                                                               "vlanId": "0",
                                                                                               "networkName": "ISP-2",
                                                                                               "routing": {},
                                                                                               "subUnit": "0",
                                                                                               "ipv4Static": True,
                                                                                               "ipv4Dhcp": False,
                                                                                               "ip6Static": False,
                                                                                               "ipv6Dhcp": False,
                                                                                               "transportDomains": [
                                                                                                   "Internet"]
                                                                                           }]
                              }], "l2Interfaces": [], "stp": "RSTP"
        }
    }
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Site Device Template on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")
        
def versa_update_device_template_snmp(director_ip, snmp_trap_dst):
    url = f"https://{director_ip}:9182/api/config/devices/template/Edge-Template/config/snmp/target-source"
    data = {"target-source": "{$v_SNMP_TARGET_SOURCE__snmpTargetSource}"}
    try:
        response = requests.put(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Updated Site Device Template on Director {director_ip}")
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")
    url = f"https://{director_ip}:9182/api/config/devices/template/Edge-Template/config/snmp"

    data = {"target":{"name":"snmp_trap_destination","ip":snmp_trap_dst,"udp-port":"162","v2c":{"sec-name":"public"},"tag":["std_v2_trap"]}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Updated Site Device Template on Director {director_ip}")
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_update_device_template_oobm_interface(director_ip):
    url = f"https://{director_ip}:9182/api/config/devices/template/Edge-Template/config/interfaces"
    data = {"management": {"name": "eth-0/0", "enabled": True, "unit": [{"name": "0", "family": {"inet": {"address": [{"name": "{$v_eth-0-0_Unit_0_StaticAddress_IPV4_Mask-0__staticaddress}", "prefix-length": "24", "gateway": "{$v_eth-0-0_0-OOBM-VR-IPv4__vrHopAddress}"}]}}, "enabled": True}]}
    }
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Updated Site Device Template on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_deploy_device_template(director_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/templates/template/deploy/Edge-Template?verifyDiff=True"
    data = {}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Deployed Site Device Template on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_device_group(director_ip):
    url = f"https://{director_ip}:9182/nextgen/deviceGroup"
    data = {"device-group":{"name":"Sites","dg:organization":"Versa-Root","dg:enable-2factor-auth":False,"dg:ca-config-on-branch-notification":False,"dg:enable-staging-url":False,"template-association":[{"organization":"Versa-Root","category":"DataStore","name":"Versa-Root-DataStore"},{"organization":"Versa-Root","category":"Main","name":"Edge-Template"}],"dg:poststaging-template":"Edge-Template"}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Device Group on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_dhcp_profile(director_ip):
    url = f"https://{director_ip}:9182/api/config/devices/template/Versa-Root-DataStore/config/orgs/org-services/Versa-Root/dhcp/dhcp4-options-profiles"
    data = {"dhcp4-options-profile":{"name":"DHCP","domain-name":"demo.local","dns-server":["8.8.8.8"]}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created DHCP Profile on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_deploy_device_workflow(director_ip, site_name):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/devices/device/deploy/{site_name}"
    data = {}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Deployed Site Device Workflow on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_site_device_workflow(director_ip, vr_1_route_ip, lan_ip, lan_dhcp_base, site_name, site_id, device_serial_number, device_country, device_city, isp_1_ip, isp_1_gateway, isp_2_ip, isp_2_gateway, tvi_0_2_ip, tvi_0_3_ip, latitude, longitude, mgmt_gateway, mgmt_address):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/devices/device"
    lan_dhcp_start = lan_dhcp_base + ".51"
    lan_dhcp_end = lan_dhcp_base + ".100"
    snmp_address = f"{mgmt_address}/24"
    data = {
        "versanms.sdwan-device-workflow": {
            "deviceName": site_name, "siteId": site_id, "orgName": "Versa-Root", "serialNumber": device_serial_number,
            "deviceGroup": "Sites", "licensePeriod": 1, "deploymentType": "physical", "locationInfo": {
                "country": device_country, "longitude": longitude, "latitude": latitude, "city": device_city
            }, "postStagingTemplateInfo": {
                "templateName": "Edge-Template", "templateData": {
                    "device-template-variable": {
                        "template": "Edge-Template", "variable-binding": {
                            "attrs": [{"name": "{$v_Site_Id__siteSiteID}", "value": site_id, "isAutogeneratable": True},
                            {
                              "name": "{$v_Chassis_Id__sitesChassisId}", "value": device_serial_number,
                              "isAutogeneratable": True
                            }, {
                              "name": "{$v_Versa-Root-Control-VR_1_Local_address__vrRouterAddress}",
                              "value": vr_1_route_ip, "isAutogeneratable": True, "isOverwritten": False
                            }, {
                              "name": "{$v_longitude__Idlongitude}", "value": longitude,
                              "isAutogeneratable": True
                            }, {
                              "name": "{$v_LAN_IPv4__staticaddress}", "value": lan_ip,
                              "isAutogeneratable": False
                            }, {
                              "name": "{$v_eth-0-0_Unit_0_StaticAddress_IPV4_Mask-0__staticaddress}",
                              "value": mgmt_address, "isAutogeneratable": False
                            }, {
                                "name": "{$v_eth-0-0_0-OOBM-VR-IPv4__vrHopAddress}",
                                "value": mgmt_gateway,
                                "isAutogeneratable": False
                            }, {
                              "name": "{$v_SNMP_TARGET_SOURCE__snmpTargetSource}",
                              "value": snmp_address, "isAutogeneratable": False
                            }, {
                              "name": "{$v_Versa-Root_Site_Name__sitesSiteName}", "value": site_name,
                              "isAutogeneratable": True
                            }, {
                              "name": "{$v_location__IdLocation}",
                              "value": f"{device_city}, {device_country}", "isAutogeneratable": True
                            }, {
                              "name": "{$v_ISP-1_IPv4__staticaddress}", "value": isp_1_ip,
                              "isAutogeneratable": False
                            }, {
                              "name": "{$v_ISP-2_IPv4__staticaddress}", "value": isp_2_ip,
                              "isAutogeneratable": False
                            }, {
                              "name": "{$v_tvi-0-2_-_Unit_0_Static_address__tunnelStaticAddress}",
                              "value": tvi_0_2_ip, "isAutogeneratable": True, "isOverwritten": False
                            }, {
                              "name": "{$v_ISP-2-Transport-VR_IPv4__vrHopAddress}", "value": isp_2_gateway,
                              "isAutogeneratable": False
                            }, {
                              "name": "{$v_ISP-1-Transport-VR_IPv4__vrHopAddress}", "value": isp_1_gateway,
                              "isAutogeneratable": False
                            }, {
                                "name": "{$v_Versa-Root_LAN-POOL-LAN_Pool_Range_Begin_IP__apRangeBegin}",
                                "value": lan_dhcp_start,
                                "isAutogeneratable": False
                            }, {
                                "name": "{$v_Versa-Root_LAN-POOL-LAN_Pool_Range_End_IP__apRangeEnd}",
                                "value": lan_dhcp_end,
                                "isAutogeneratable": False
                            }, {
                              "name": "{$v_latitude__IdLatitude}", "value": latitude,
                              "isAutogeneratable": True
                            }, {
                              "name": "{$v_Versa-Root_Controller-01_Local_auth_email_identifier__IKELIdentifier}",
                              "value": f"{site_name}@Versa-Root.com", "isAutogeneratable": True
                            }, {
                              "name": "{$v_Versa-Root-Control-VR_1_Router_ID__vrRouteId}",
                              "value": vr_1_route_ip, "isAutogeneratable": True, "isOverwritten": False
                            }, {
                              "name": "{$v_tvi-0-3_-_Unit_0_Static_address__tunnelStaticAddress}",
                              "value": tvi_0_3_ip, "isAutogeneratable": True, "isOverwritten": False
                            }, {
                              "name": "{$v_identification__IdName}", "value": site_name,
                              "isAutogeneratable": True
                            }, ]
                        }
                    }, "variableMetadata": [{
                                                "variable": "{$v_Site_Id__siteSiteID}", "group": "SDWAN",
                                                "overlay": False, "type": "INTEGER",
                                                "range": {"start": 100, "end": 16383}
                                            }, {
                                                "variable": "{$v_Chassis_Id__sitesChassisId}", "group": "SDWAN",
                                                "overlay": False, "type": "STRING"
                                            }, {
                                                "variable": "{$v_Versa-Root-Control-VR_1_Local_address__vrRouterAddress}",
                                                "group": "Virtual Routers", "overlay": True, "type": "IPV4"
                                            }, {
                                                "variable": "{$v_longitude__Idlongitude}", "group": "SDWAN",
                                                "overlay": False, "type": "FLOAT",
                                                "floatRange": {"start": -180, "end": 180}
                                            }, {
                                                "variable": "{$v_LAN_IPv4__staticaddress}", "group": "Interfaces",
                                                "overlay": False, "type": "IPV4_MASK"
                                            }, {
                                                "variable": "{$v_Versa-Root_Site_Name__sitesSiteName}",
                                                "group": "SDWAN", "overlay": False, "type": "STRING"
                                            }, {
                                                "variable": "{$v_location__IdLocation}", "group": "SDWAN",
                                                "overlay": False, "type": "STRING"
                                            }, {
                                                "variable": "{$v_ISP-1_IPv4__staticaddress}", "group": "Interfaces",
                                                "overlay": False, "type": "IPV4_MASK"
                                            }, {
                                                "variable": "{$v_ISP-2_IPv4__staticaddress}", "group": "Interfaces",
                                                "overlay": False, "type": "IPV4_MASK"
                                            }, {
                                                "variable": "{$v_tvi-0-2_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                "group": "Interfaces", "overlay": True, "type": "IPV4_IPV6_MASK"
                                            }, {
                                                "variable": "{$v_ISP-2-Transport-VR_IPv4__vrHopAddress}",
                                                "group": "Virtual Routers", "overlay": False, "type": "IPV4"
                                            }, {
                                                "variable": "{$v_ISP-1-Transport-VR_IPv4__vrHopAddress}",
                                                "group": "Virtual Routers", "overlay": False, "type": "IPV4"
                                            }, {
                                                "variable": "{$v_latitude__IdLatitude}", "group": "SDWAN",
                                                "overlay": False, "type": "FLOAT",
                                                "floatRange": {"start": -90, "end": 90}
                                            }, {
                                                "variable": "{$v_Versa-Root_Controller-01_Local_auth_email_identifier__IKELIdentifier}",
                                                "group": "IPSEC", "overlay": False, "type": "STRING"
                                            }, {
                                                "variable": "{$v_Versa-Root-Control-VR_1_Router_ID__vrRouteId}",
                                                "group": "Virtual Routers", "overlay": True, "type": "IPV4"
                                            }, {
                                                "variable": "{$v_tvi-0-3_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                "group": "Interfaces", "overlay": True, "type": "IPV4_IPV6_MASK"
                                            }, {
                                                "variable": "{$v_identification__IdName}", "group": "SDWAN",
                                                "overlay": False, "type": "STRING"
                                            }, {
                                                "variable": "{$v_Versa-Root_Controller-01_Local_auth_email_key__IKELKey}",
                                                "group": "IPSEC", "overlay": False, "type": "STRING"
                                            }]
                }
            }, "serviceTemplateInfo": {
                "templateData": {
                    "device-template-variable": [{"device": site_name, "template": "Versa-Root-DataStore"}]
                }
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Site Device Template on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_config_edge_mgmt_interface(director_ip, site_name, management_ip, management_gateway):
    url = f"https://{director_ip}:9182/api/config/devices/device/{site_name}/config/interfaces"
    data = {"management":{"name":"eth-0/0","enabled":True,"unit":[{"name":"0","family":{"inet":{"address":[{"name":management_ip,"prefix-length":"24","gateway":management_gateway}]}},"enabled":True}]}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Configured Management interface for site {site_name} on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

# endregion
