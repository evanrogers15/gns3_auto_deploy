import logging.handlers

from modules.gns3.gns3_actions import *
from modules.gns3.gns3_dynamic_data import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#viptela_username = modules.gns3_variables.viptela_username
# region Functions: Viptela API
class Authentication:
    def get_jsessionid(self, gns3_server_data):
        server_ips = set(d['vManage API IP'] for d in gns3_server_data)
        for server_ip in server_ips:
            api = "/j_security_check"
            base_url = f"https://{server_ip}"
            url = base_url + api
            payload = {'j_username': viptela_username, 'j_password': viptela_password}
            response = requests.post(url=url, data=payload, verify=False)
            try:
                cookies = response.headers["Set-Cookie"]
                jsessionid = cookies.split(";")
                return jsessionid[0]
            except:
                # logging.info("No valid JSESSION ID returned\n")
                exit()

    def get_token(self, jsessionid, gns3_server_data):
        server_ips = set(d['vManage API IP'] for d in gns3_server_data)
        for server_ip in server_ips:
            headers = {'Cookie': jsessionid}
            base_url = f"https://{server_ip}"
            api = "/dataservice/client/token"
            url = base_url + api
            response = requests.get(url=url, headers=headers, verify=False)
            if response.status_code == 200:
                return response.text
            else:
                return None


def vmanage_create_auth(gns3_server_data):
    vmanage_auth = Authentication()
    jsessionid = vmanage_auth.get_jsessionid(gns3_server_data)
    token = vmanage_auth.get_token(jsessionid, gns3_server_data)
    if token is not None:
        vmanage_headers = {'Content-Type': "application/json", 'Cookie': jsessionid, 'X-XSRF-TOKEN': token}
    else:
        vmanage_headers = {'Content-Type': "application/json", 'Cookie': jsessionid}
    return vmanage_headers


def vmanage_set_cert_type(gns3_server_data, vmanage_headers):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/settings/configuration/certificate"
        catype = "enterprise"
        response_data = {'certificateSigning': catype}
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Set certificate authority type for vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(response.content)
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_set_cert(gns3_server_data, vmanage_headers, cert):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/settings/configuration/certificate/enterpriserootca"
        response_data = {'enterpriseRootCA': cert}
        try:
            response = requests.put(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                    timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Uploaded new root certificate to vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(response.content)
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_install_cert(gns3_server_data, vmanage_headers, cert):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/certificate/install/signedCert"
        response_data = {'enterpriseRootCA': cert}
        try:
            response = requests.post(url, data=cert, headers=vmanage_headers, verify=False, timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Installed device certificate for vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(response.content)
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_forcesync_rootcert(gns3_server_data, vmanage_headers):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/certificate/forcesync/rootCert"
        response_data = {}
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Forced root certificate sync on vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(response.content)
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_sync_rootcertchain(gns3_server_data, vmanage_headers):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/system/device/sync/rootcertchain"
        response_data = {}
        try:
            response = requests.get(url, headers=vmanage_headers, verify=False, timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Synced root certificate chain for vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(response.content)
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_set_vbond(gns3_server_data, vmanage_headers):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/settings/configuration/device"
        response_data = {'domainIp': vbond_address, 'port': '12346'}
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Set vBond {vbond_address} for vManage {vmanage_address} in configuration settings")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_set_org(gns3_server_data, vmanage_headers):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/settings/configuration/organization"
        response_data = {'org': org_name}
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Set organization for vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_push_certs(gns3_server_data, vmanage_headers):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/certificate/vedge/list?action=push"
        response_data = {}
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=20)
            response.raise_for_status()
            logging.info(f"Deploy - Pushed vEdge certificates to control devices for vManage {vmanage_address}")
            return response
        except requests.exceptions.RequestException as e:
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_set_device(gns3_server_data, vmanage_headers, vdevice_ip, vdevice_personality):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/system/device"
        response_data = {"deviceIP": vdevice_ip, "username": viptela_username, "password": viptela_password,
                         "personality": vdevice_personality, "generateCSR": "true", }
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=35)
            if response.status_code == requests.codes.ok:
                logging.info(f"Deploy - {vdevice_personality} with address {vdevice_ip} set successfully on vManage {vmanage_address}")
            else:
                logging.info(f"Deploy - Failed to add {vdevice_personality} device. ")
                logging.info("Response: {}".format(response.text))
            return response
        except requests.exceptions.RequestException as e:
            logging.info(f"vManage not available: {str(e)}")
            continue


def vmanage_generate_csr(gns3_server_data, vmanage_headers, vdevice_ip, vdevice_personality):
    server_ips = set(d['vManage API IP'] for d in gns3_server_data)
    for server_ip in server_ips:
        url = f"https://{server_ip}/dataservice/certificate/generate/csr"
        response_data = {"deviceIP": vdevice_ip}
        try:
            response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                     timeout=20)
            response.raise_for_status()
            result = util_extract_csr(response)
            logging.info(f"Deploy - Generated CSR for {vdevice_personality} on vManage {vmanage_address}")
            return result[0]['deviceCSR']
        except requests.exceptions.RequestException as e:
            logging.info(f"vManage not available: {str(e)}")
            continue


# endregion