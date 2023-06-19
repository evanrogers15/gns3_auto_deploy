from modules.viptela_mgmt_deployment import *
from modules.viptela_vedge_deployment import *
from modules.gns3_actions import *
from modules.gns3_query import *

gns3_isp_tap_name = 'tap1'
gns3_mgmt_tap_name = 'tap2'
vmanage_address = '10.0.0.2'

gns3_mgmt_server_ip = '10.142.0.134'
gns3_mgmt_server_port = '80'
gns3_mgmt_project_name = 'viptela_mgmt'

gns3_sites_01_server_ip = '10.142.0.133'
gns3_sites_01_server_port = '80'
gns3_sites_01_project_name = 'viptela_sites'
gns3_sites_01_site_count = 40

def set_config(server_ip, server_port, new_project_name, vmanage_api_ip, site_count, isp_tap_name, mgmt_tap_name):
    projects = gns3_query_get_projects(server_ip, server_port)
    server_name = gns3_query_get_computes_name(server_ip, server_port)
    if new_project_name not in [project['name'] for project in projects]:
        project_id = gns3_create_project(server_ip, server_port, new_project_name)
    else:
        matching_projects = [project for project in projects if project['name'] == new_project_name]
        project_id = matching_projects[0]['project_id']
        gns3_delete_project_static(server_ip, server_port, new_project_name, project_id)
        project_id = gns3_create_project(server_ip, server_port, new_project_name)
    projects = gns3_query_get_projects(server_ip, server_port)
    project_names = [project['name'] for project in projects]
    project_ids = [project['project_id'] for project in projects]
    project_status = [project['status'] for project in projects]
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM config")
    c.execute(
        "INSERT INTO config (server_ip, server_port, server_name, project_list, project_names, project_status, project_name, project_id, vmanage_api_ip, site_count, isp_tap_name, mgmt_tap_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (server_ip, server_port, server_name, json.dumps(project_ids), json.dumps(project_names),
         json.dumps(project_status), new_project_name, project_id, vmanage_api_ip, site_count, isp_tap_name, mgmt_tap_name))
    conn.commit()
    conn.close()

def start_scale_deploy():
    # set_config(gns3_mgmt_server_ip, gns3_mgmt_server_port, gns3_mgmt_project_name, vmanage_address, gns3_sites_01_site_count, gns3_isp_tap_name, gns3_mgmt_tap_name)
    viptela_mgmt_deploy()
    # set_config(gns3_sites_01_server_ip, gns3_sites_01_server_port, gns3_sites_01_project_name, vmanage_address, gns3_sites_01_site_count, gns3_isp_tap_name, gns3_mgmt_tap_name)
    viptela_vedge_deploy()

start_scale_deploy()
