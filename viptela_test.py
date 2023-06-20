from modules.viptela_mgmt_deployment import *
from modules.viptela_vedge_deployment import *
from modules.gns3_actions import *
from modules.gns3_query import *
from modules.viptela_vedge_scale_deployment import *

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

gns3_sites_02_server_ip = '10.142.0.135'
gns3_sites_02_server_port = '80'
gns3_sites_02_project_name = 'viptela_sites'
gns3_sites_02_site_count = 40

viptela_vedge_scale_deploy(gns3_sites_01_server_ip, gns3_sites_01_server_port, gns3_sites_01_project_name, vmanage_address, gns3_isp_tap_name, gns3_mgmt_tap_name, 1, 1, 1, 1, 20)
viptela_vedge_scale_deploy(gns3_sites_02_server_ip, gns3_sites_02_server_port, gns3_sites_02_project_name, vmanage_address, gns3_isp_tap_name, gns3_mgmt_tap_name, 21, 21, 2, 2, 20)


#start_scale_deploy()
