mgmt_subnet_ip = '172.16.2.0/24'

mgmt_subnet_ip = '.'.join(mgmt_subnet_ip.split('/')[0].split('.')[:3])
print (mgmt_subnet_ip)