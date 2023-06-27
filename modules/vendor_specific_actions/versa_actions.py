from modules.gns3.gns3_actions import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# region Functions: Viptela API
def versa_configure_analytics_cluster(director_ip, analytics_ip):
    url = f"https://{director_ip}:9182/api/config/nms/provider"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

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
                    "172.14.4.6"
                ]
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")

def versa_create_provider_org(director_ip):
    url = f"https://{director_ip}:9182/nextgen/organization"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {"name": "Versa-Root","uuid": "310f513a-01aa-4e91-9a53-4dae9b324839","subscriptionPlan": "Default-All-Services-Plan","id": 1,"authType": "psk","cpeDeploymentType": "SDWAN","vrfsGroups": [ { "id": 1, "vrfId": 1, "name": "Versa-Root-LAN-VR", "description": "", "enable_vpn": True }],"analyticsClusters": [ "Analytics"],"sharedControlPlane": False,"dynamicTenantConfig": { "inactivityInterval": 48},"blockInterRegionRouting": False}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")

def versa_create_overlay_prefix(director_ip):
    url = f"https://{director_ip}:9182/vnms/ipam/overlay/prefixes"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {"prefix":"10.10.0.0/16","status":{"value":1,"label":"Active"}, "is_pool":True}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")

def versa_create_overlay_route(director_ip):
    url = f"https://{director_ip}:9182/api/config/nms/routing-options/static"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {"route":{"description":"Overlay-Route","destination-prefix":"10.10.0.0/16","next-hop-address":"172.14.4.10","outgoing-interface":"eth1"}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")
    
def versa_create_controller_workflow(director_ip, controller_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/controllers/controller"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = { "versanms.sdwan-controller-workflow": { "controllerName": "Controller-01", "siteId": 1, "orgName": "Versa-Root", "resourceType": "Baremetal", "stagingController": True, "postStagingController": True, "baremetalController": { "serverIP": controller_ip, "controllerInterface": { "interfaceName": "vni-0/1", "unitInfoList": [ { "networkName": "Control-Network", "ipv4address": [ "172.14.4.10/24" ], "ipv4gateway": "", "ipv6gateway": "", "ipv4dhcp": False, "ipv6dhcp": False, "vlanId": 0, "wanStaging": True, "poolSize": 256 } ] }, "wanInterfaces": [ { "interfaceName": "vni-0/2", "unitInfoList": [ { "networkName": "ISP-1", "ipv4address": [ "172.14.5.2/30" ], "ipv4gateway": "172.14.5.1", "ipv4dhcp": False, "ipv6dhcp": False, "vlanId": 0, "wanStaging": True, "poolSize": 128, "transportDomainList": [ "Internet" ] } ] }, { "interfaceName": "vni-0/3", "unitInfoList": [ { "networkName": "ISP-2", "ipv4address": [ "172.14.5.6/30" ], "ipv4gateway": "172.14.5.5", "ipv4dhcp": False, "ipv6dhcp": False, "vlanId": 0, "wanStaging": True, "poolSize": 128, "transportDomainList": [ "Internet" ] } ] } ] }, "locationInfo": { "state": "CA", "country": "USA", "city": "San Jose", "longitude": -121.885252, "latitude": 37.33874 }, "analyticsCluster": "Analytics" }}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")
        
def versa_deploy_controller(director_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/controllers/controller/deploy/Controller-01"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")

def versa_create_device_template(director_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/templates/template"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {
        "versanms.sdwan-template-workflow": {
            "analyticsCluster": "Analytics", "bandwidth": "100", "licensePeriod": "1", "controllers": ["Controller-01"],
            "deviceFirmfactor": 6, "deviceType": "full-mesh", "diaConfig": {"loadBalance": False}, "isStaging": False,
            "SNMPServers": [{"networkName": "MGMT", "server": "0.0.0.0"}],
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
                                    }]}, {
                                "interfaceName": "vni-0/4", "unitInfo": [{
                                    "vlanId": "0",
                                    "subOrganization": "Versa-Root",
                                    "vrfName": "Versa-Root-LAN-VR",
                                    "networkName": "MGMT", "subUnit": "0",
                                    "ipv4Static": True, "ipv4Dhcp": False,
                                    "ip6Static": False, "ipv6Dhcp": False,
                                    "ipv4DhcpServer": False,
                                    "dhcpv4Profile": "DHCP",
                                    "dhcpV4Relay": False,
                                    "dhcpV4RelayAddress": ""
                }]
            }],
            "providerOrg": {"name": "Versa-Root", "nextGenFW": False, "statefulFW": False},
            "redundantPair": {"enable": False}, "routingInstances": [], "siteToSiteTunnels": [],
            "solutionTier": "Premier-Elite-SDWAN",
            "snmp": {
                "snmpV1": False, "snmpV2": True, "snmpV3": False, "community": "public"
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
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")
        
def versa_deploy_device_template(director_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/templates/template/deploy/Edge-Template?verifyDiff=True"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")

def versa_create_device_group(director_ip):
    url = f"https://{director_ip}:9182/nextgen/deviceGroup"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {"device-group":{"name":"Sites","dg:organization":"Versa-Root","dg:enable-2factor-auth":False,"dg:ca-config-on-branch-notification":False,"dg:enable-staging-url":False,"template-association":[{"organization":"Versa-Root","category":"DataStore","name":"Versa-Root-DataStore"},{"organization":"Versa-Root","category":"Main","name":"Edge-Template"}],"dg:poststaging-template":"Edge-Template"}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")

def versa_create_dhcp_profile(director_ip):
    url = f"https://{director_ip}:9182/api/config/devices/template/Versa-Root-DataStore/config/orgs/org-services/Versa-Root/dhcp/dhcp4-options-profiles"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {"dhcp4-options-profile":{"name":"DHCP","domain-name":"demo.local","dns-server":["192.168.122.1"]}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")

def versa_deploy_device_workflow(director_ip, site_name):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/devices/device/deploy/{site_name}"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")

def versa_create_site_device_workflow(director_ip, vr_1_route_ip, lan_ip, lan_dhcp_base, site_name, site_id, device_serial_number, device_country, device_city, isp_1_ip, isp_1_gateway, isp_2_ip, isp_2_gateway, tvi_0_2_ip, tvi_0_3_ip, latitude, longitude, mgmt_address):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/devices/device"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")
    lan_dhcp_start = lan_dhcp_base + ".50"
    lan_dhcp_end = lan_dhcp_base + ".100"
    mgmt_snmp_target_source = mgmt_address.rstrip("/24")
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
                                "name": "{$v_MGMT_IPv4__staticaddress}",
                                "value": mgmt_address, "isAutogeneratable": False
                            }, {
                                "name": "{$v_MGMT__snmpTargetSource}",
                                "value": mgmt_snmp_target_source, "isAutogeneratable": False
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
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")

# endregion

# region Old
def versa_create_site_device_workflow_1(director_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/devices/device"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {"versanms.sdwan-device-workflow": {"deviceName": "NewYork", "siteId": "101", "orgName": "Versa-Root",
                                               "serialNumber": "SN101", "deviceGroup": "Sites", "licensePeriod": 1,
                                               "deploymentType": "physical",
                                               "locationInfo": {"state": "New York", "country": "US",
                                                                "longitude": "-74.005973", "latitude": "40.712775",
                                                                "city": "New York"},
                                               "postStagingTemplateInfo": {"templateName": "Edge-Template",
                                                                           "templateData": {
                                                                               "device-template-variable": {
                                                                                   "template": "Edge-Template",
                                                                                   "variable-binding": {"attrs": [{
                                                                                                                      "name": "{$v_Site_Id__siteSiteID}",
                                                                                                                      "value": "101",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_Chassis_Id__sitesChassisId}",
                                                                                                                      "value": "SN101",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_Versa-Root-Control-VR_1_Local_address__vrRouterAddress}",
                                                                                                                      "value": "10.10.0.4",
                                                                                                                      "isAutogeneratable": True,
                                                                                                                      "isOverwritten": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_longitude__Idlongitude}",
                                                                                                                      "value": "-74.005973",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_LAN_IPv4__staticaddress}",
                                                                                                                      "value": "172.14.101.1/24",
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_Versa-Root_Site_Name__sitesSiteName}",
                                                                                                                      "value": "NewYork",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_location__IdLocation}",
                                                                                                                      "value": "New York, New York, US",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_ISP-1_IPv4__staticaddress}",
                                                                                                                      "value": "172.14.6.2/30",
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_ISP-2_IPv4__staticaddress}",
                                                                                                                      "value": "172.14.7.2/30",
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_tvi-0-2_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                                                                                      "value": "10.10.0.5/32",
                                                                                                                      "isAutogeneratable": True,
                                                                                                                      "isOverwritten": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_ISP-2-Transport-VR_IPv4__vrHopAddress}",
                                                                                                                      "value": "172.14.7.1",
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_ISP-1-Transport-VR_IPv4__vrHopAddress}",
                                                                                                                      "value": "172.14.6.1",
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_latitude__IdLatitude}",
                                                                                                                      "value": "40.712775",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_Versa-Root_Controller-01_Local_auth_email_identifier__IKELIdentifier}",
                                                                                                                      "value": "NewYork@Versa-Root.com",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_Versa-Root-Control-VR_1_Router_ID__vrRouteId}",
                                                                                                                      "value": "10.10.0.4",
                                                                                                                      "isAutogeneratable": True,
                                                                                                                      "isOverwritten": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_tvi-0-3_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                                                                                      "value": "10.10.0.4/32",
                                                                                                                      "isAutogeneratable": True,
                                                                                                                      "isOverwritten": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_identification__IdName}",
                                                                                                                      "value": "NewYork",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_Versa-Root_Controller-01_Local_auth_email_key__IKELKey}",
                                                                                                                      "value": "EFz2vxM/mRsoaS82d+nCg01/jDE5knE1cl10B6sNWJTBGgnFe+hUFIvi9Kz987fm8PK4MhxFw9j89sGXHm1xKK3ZTFVlouUwAWEuuaFeZBOKanA2joKkumDKUDO2cw19iJDzhQ+/OQIE+bzX/p8rULBDlONmszYBLKWpgsXvT5eqfFo5S1awko+Hk+1kATeBjiyqH9MG+XwDEsKLfdZMGcAVtUfnFQv02e+XZ5qQq9RwopgypCJbPbbULMnMDLeb121PjudYh0SkgLXuY74gt++NuxhmCKP/4c2T99wFTMftquTwjhfrylDeYW2pETx3Hs790EL+fpg/XFgiXS7DaQ==",
                                                                                                                      "isAutogeneratable": True}]}},
                                                                               "variableMetadata": [{
                                                                                                        "variable": "{$v_Site_Id__siteSiteID}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "INTEGER",
                                                                                                        "range": {
                                                                                                            "start": 100,
                                                                                                            "end": 16383}},
                                                                                                    {
                                                                                                        "variable": "{$v_Chassis_Id__sitesChassisId}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root-Control-VR_1_Local_address__vrRouterAddress}",
                                                                                                        "group": "Virtual Routers",
                                                                                                        "overlay": True,
                                                                                                        "type": "IPV4"},
                                                                                                    {
                                                                                                        "variable": "{$v_longitude__Idlongitude}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "FLOAT",
                                                                                                        "floatRange": {
                                                                                                            "start": -180,
                                                                                                            "end": 180}},
                                                                                                    {
                                                                                                        "variable": "{$v_LAN_IPv4__staticaddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root_Site_Name__sitesSiteName}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_location__IdLocation}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_ISP-1_IPv4__staticaddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_ISP-2_IPv4__staticaddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_tvi-0-2_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": True,
                                                                                                        "type": "IPV4_IPV6_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_ISP-2-Transport-VR_IPv4__vrHopAddress}",
                                                                                                        "group": "Virtual Routers",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4"},
                                                                                                    {
                                                                                                        "variable": "{$v_ISP-1-Transport-VR_IPv4__vrHopAddress}",
                                                                                                        "group": "Virtual Routers",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4"},
                                                                                                    {
                                                                                                        "variable": "{$v_latitude__IdLatitude}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "FLOAT",
                                                                                                        "floatRange": {
                                                                                                            "start": -90,
                                                                                                            "end": 90}},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root_Controller-01_Local_auth_email_identifier__IKELIdentifier}",
                                                                                                        "group": "IPSEC",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root-Control-VR_1_Router_ID__vrRouteId}",
                                                                                                        "group": "Virtual Routers",
                                                                                                        "overlay": True,
                                                                                                        "type": "IPV4"},
                                                                                                    {
                                                                                                        "variable": "{$v_tvi-0-3_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": True,
                                                                                                        "type": "IPV4_IPV6_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_identification__IdName}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root_Controller-01_Local_auth_email_key__IKELKey}",
                                                                                                        "group": "IPSEC",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"}]}},
                                               "serviceTemplateInfo": {"templateData": {"device-template-variable": [
                                                   {"device": "NewYork", "template": "Versa-Root-DataStore"}]}}}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")

def versa_deploy_device_workflow_1(director_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/devices/device/deploy/NewYork"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")

def versa_create_site_device_workflow_2(director_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/devices/device"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {"versanms.sdwan-device-workflow": {"deviceName": "Cairns", "siteId": "102", "orgName": "Versa-Root",
                                               "serialNumber": "SN102", "deviceGroup": "Sites", "licensePeriod": 1,
                                               "deploymentType": "physical",
                                               "locationInfo": {"country": "France",
                                                                "longitude": "145.770953", "latitude": "-16.920348",
                                                                "city": "Cairns"},
                                               "postStagingTemplateInfo": {"templateName": "Edge-Template",
                                                                           "templateData": {
                                                                               "device-template-variable": {
                                                                                   "template": "Edge-Template",
                                                                                   "variable-binding": {"attrs": [{
                                                                                                                      "name": "{$v_Site_Id__siteSiteID}",
                                                                                                                      "value": "102",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_Chassis_Id__sitesChassisId}",
                                                                                                                      "value": "SN102",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_Versa-Root-Control-VR_1_Local_address__vrRouterAddress}",
                                                                                                                      "value": "10.10.0.6",
                                                                                                                      "isAutogeneratable": True,
                                                                                                                      "isOverwritten": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_longitude__Idlongitude}",
                                                                                                                      "longitude": "145.770953",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_LAN_IPv4__staticaddress}",
                                                                                                                      "value": "172.14.102.1/24",
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_Versa-Root_Site_Name__sitesSiteName}",
                                                                                                                      "value": "Cairns",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_location__IdLocation}",
                                                                                                                      "value": "Cairns, France",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_ISP-1_IPv4__staticaddress}",
                                                                                                                      "value": "172.14.6.6/30",
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_ISP-2_IPv4__staticaddress}",
                                                                                                                      "value": "172.14.7.6/30",
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_tvi-0-2_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                                                                                      "value": "10.10.0.7/32",
                                                                                                                      "isAutogeneratable": True,
                                                                                                                      "isOverwritten": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_ISP-2-Transport-VR_IPv4__vrHopAddress}",
                                                                                                                      "value": "172.14.7.5",
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_ISP-1-Transport-VR_IPv4__vrHopAddress}",
                                                                                                                      "value": "172.14.6.5",
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_latitude__IdLatitude}",
                                                                                                                      "latitude": "-16.920348",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_Versa-Root_Controller-01_Local_auth_email_identifier__IKELIdentifier}",
                                                                                                                      "value": "Cairns@Versa-Root.com",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_Versa-Root-Control-VR_1_Router_ID__vrRouteId}",
                                                                                                                      "value": "10.10.0.6",
                                                                                                                      "isAutogeneratable": True,
                                                                                                                      "isOverwritten": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_tvi-0-3_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                                                                                      "value": "10.10.0.6/32",
                                                                                                                      "isAutogeneratable": True,
                                                                                                                      "isOverwritten": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_identification__IdName}",
                                                                                                                      "value": "Cairns",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  ]}},
                                                                               "variableMetadata": [{
                                                                                                        "variable": "{$v_Site_Id__siteSiteID}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "INTEGER",
                                                                                                        "range": {
                                                                                                            "start": 100,
                                                                                                            "end": 16383}},
                                                                                                    {
                                                                                                        "variable": "{$v_Chassis_Id__sitesChassisId}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root-Control-VR_1_Local_address__vrRouterAddress}",
                                                                                                        "group": "Virtual Routers",
                                                                                                        "overlay": True,
                                                                                                        "type": "IPV4"},
                                                                                                    {
                                                                                                        "variable": "{$v_longitude__Idlongitude}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "FLOAT",
                                                                                                        "floatRange": {
                                                                                                            "start": -180,
                                                                                                            "end": 180}},
                                                                                                    {
                                                                                                        "variable": "{$v_LAN_IPv4__staticaddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root_Site_Name__sitesSiteName}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_location__IdLocation}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_ISP-1_IPv4__staticaddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_ISP-2_IPv4__staticaddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_tvi-0-2_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": True,
                                                                                                        "type": "IPV4_IPV6_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_ISP-2-Transport-VR_IPv4__vrHopAddress}",
                                                                                                        "group": "Virtual Routers",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4"},
                                                                                                    {
                                                                                                        "variable": "{$v_ISP-1-Transport-VR_IPv4__vrHopAddress}",
                                                                                                        "group": "Virtual Routers",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4"},
                                                                                                    {
                                                                                                        "variable": "{$v_latitude__IdLatitude}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "FLOAT",
                                                                                                        "floatRange": {
                                                                                                            "start": -90,
                                                                                                            "end": 90}},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root_Controller-01_Local_auth_email_identifier__IKELIdentifier}",
                                                                                                        "group": "IPSEC",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root-Control-VR_1_Router_ID__vrRouteId}",
                                                                                                        "group": "Virtual Routers",
                                                                                                        "overlay": True,
                                                                                                        "type": "IPV4"},
                                                                                                    {
                                                                                                        "variable": "{$v_tvi-0-3_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": True,
                                                                                                        "type": "IPV4_IPV6_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_identification__IdName}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root_Controller-01_Local_auth_email_key__IKELKey}",
                                                                                                        "group": "IPSEC",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"}]}},
                                               "serviceTemplateInfo": {"templateData": {"device-template-variable": [
                                                   {"device": "Cairns", "template": "Versa-Root-DataStore"}]}}}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
        print(response)
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")
        print(response)

def versa_deploy_device_workflow_2(director_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/devices/device/deploy/Cairns"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")

def versa_create_site_device_workflow_old(director_ip, vr_1_local_ip, vr_1_route_id, lan_ip, site_name, site_id, device_serial_number, device_country, device_city, isp_1_ip, isp_1_gateway, isp_2_ip, isp_2_gateway, tvi_0_2_ip, tvi_0_3_ip, latitude, longitude):
    # print(director_ip, vr_1_local_ip, vr_1_route_id, lan_ip, site_name, site_id, device_serial_number, device_country, device_city, isp_1_ip, isp_1_gateway, isp_2_ip, isp_2_gateway, tvi_0_2_ip, tvi_0_3_ip, latitude, longitude)
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/devices/device"
    headers = {
        "Content-Type": "application/json"
    }
    auth = ("Administrator", "versa123")

    data = {"versanms.sdwan-device-workflow": {"deviceName": site_name, "siteId": site_id, "orgName": "Versa-Root",
                                               "serialNumber": device_serial_number, "deviceGroup": "Sites", "licensePeriod": 1,
                                               "deploymentType": "physical",
                                               "locationInfo": {"country": device_country,
                                                                "longitude": longitude, "latitude": latitude,
                                                                "city": device_city},
                                               "postStagingTemplateInfo": {"templateName": "Edge-Template",
                                                                           "templateData": {
                                                                               "device-template-variable": {
                                                                                   "template": "Edge-Template",
                                                                                   "variable-binding": {"attrs": [{
                                                                                                                      "name": "{$v_Site_Id__siteSiteID}",
                                                                                                                      "value": site_id,
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_Chassis_Id__sitesChassisId}",
                                                                                                                      "value": device_serial_number,
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_Versa-Root-Control-VR_1_Local_address__vrRouterAddress}",
                                                                                                                      "value": vr_1_local_ip,
                                                                                                                      "isAutogeneratable": True,
                                                                                                                      "isOverwritten": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_longitude__Idlongitude}",
                                                                                                                      "value": longitude,
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_LAN_IPv4__staticaddress}",
                                                                                                                      "value": lan_ip,
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_Versa-Root_Site_Name__sitesSiteName}",
                                                                                                                      "value": site_name,
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_location__IdLocation}",
                                                                                                                      "value": f"{device_city}, {device_country}",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_ISP-1_IPv4__staticaddress}",
                                                                                                                      "value": isp_1_ip,
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_ISP-2_IPv4__staticaddress}",
                                                                                                                      "value": isp_2_ip,
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_tvi-0-2_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                                                                                      "value": tvi_0_2_ip,
                                                                                                                      "isAutogeneratable": True,
                                                                                                                      "isOverwritten": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_ISP-2-Transport-VR_IPv4__vrHopAddress}",
                                                                                                                      "value": isp_2_gateway,
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_ISP-1-Transport-VR_IPv4__vrHopAddress}",
                                                                                                                      "value": isp_1_gateway,
                                                                                                                      "isAutogeneratable": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_latitude__IdLatitude}",
                                                                                                                      "value": latitude,
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_Versa-Root_Controller-01_Local_auth_email_identifier__IKELIdentifier}",
                                                                                                                      "value": f"{site_name}@Versa-Root.com",
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  {
                                                                                                                      "name": "{$v_Versa-Root-Control-VR_1_Router_ID__vrRouteId}",
                                                                                                                      "value": vr_1_route_id,
                                                                                                                      "isAutogeneratable": True,
                                                                                                                      "isOverwritten": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_tvi-0-3_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                                                                                      "value": tvi_0_3_ip,
                                                                                                                      "isAutogeneratable": True,
                                                                                                                      "isOverwritten": False},
                                                                                                                  {
                                                                                                                      "name": "{$v_identification__IdName}",
                                                                                                                      "value": site_name,
                                                                                                                      "isAutogeneratable": True},
                                                                                                                  ]}},
                                                                               "variableMetadata": [{
                                                                                                        "variable": "{$v_Site_Id__siteSiteID}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "INTEGER",
                                                                                                        "range": {
                                                                                                            "start": 100,
                                                                                                            "end": 16383}},
                                                                                                    {
                                                                                                        "variable": "{$v_Chassis_Id__sitesChassisId}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root-Control-VR_1_Local_address__vrRouterAddress}",
                                                                                                        "group": "Virtual Routers",
                                                                                                        "overlay": True,
                                                                                                        "type": "IPV4"},
                                                                                                    {
                                                                                                        "variable": "{$v_longitude__Idlongitude}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "FLOAT",
                                                                                                        "floatRange": {
                                                                                                            "start": -180,
                                                                                                            "end": 180}},
                                                                                                    {
                                                                                                        "variable": "{$v_LAN_IPv4__staticaddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root_Site_Name__sitesSiteName}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_location__IdLocation}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_ISP-1_IPv4__staticaddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_ISP-2_IPv4__staticaddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_tvi-0-2_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": True,
                                                                                                        "type": "IPV4_IPV6_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_ISP-2-Transport-VR_IPv4__vrHopAddress}",
                                                                                                        "group": "Virtual Routers",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4"},
                                                                                                    {
                                                                                                        "variable": "{$v_ISP-1-Transport-VR_IPv4__vrHopAddress}",
                                                                                                        "group": "Virtual Routers",
                                                                                                        "overlay": False,
                                                                                                        "type": "IPV4"},
                                                                                                    {
                                                                                                        "variable": "{$v_latitude__IdLatitude}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "FLOAT",
                                                                                                        "floatRange": {
                                                                                                            "start": -90,
                                                                                                            "end": 90}},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root_Controller-01_Local_auth_email_identifier__IKELIdentifier}",
                                                                                                        "group": "IPSEC",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root-Control-VR_1_Router_ID__vrRouteId}",
                                                                                                        "group": "Virtual Routers",
                                                                                                        "overlay": True,
                                                                                                        "type": "IPV4"},
                                                                                                    {
                                                                                                        "variable": "{$v_tvi-0-3_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                                                                        "group": "Interfaces",
                                                                                                        "overlay": True,
                                                                                                        "type": "IPV4_IPV6_MASK"},
                                                                                                    {
                                                                                                        "variable": "{$v_identification__IdName}",
                                                                                                        "group": "SDWAN",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"},
                                                                                                    {
                                                                                                        "variable": "{$v_Versa-Root_Controller-01_Local_auth_email_key__IKELKey}",
                                                                                                        "group": "IPSEC",
                                                                                                        "overlay": False,
                                                                                                        "type": "STRING"}]}},
                                               "serviceTemplateInfo": {"templateData": {"device-template-variable": [
                                                   {"device": {site_name}, "template": "Versa-Root-DataStore"}]}}}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        print("Configuration successful.")
    except requests.exceptions.RequestException as e:
        print(f"Configuration failed. Error: {str(e)}")
# endregion