import requests
import urllib.request
import sys
import os
gns3_server_data = [
 {
     "GNS3 Server": "10.128.15.234",
     "Server Name": "er-test-01",
     "Server Port": "80",
     "vManage API IP": "172.16.2.2",
     "Project Name": "test111",
     "Tap Name": "tap1",
     "Use Tap": 0,
     "Site Count": 0,
     "Deployment Type": 'viptela',
     "Deployment Step": 'test',
     "Deployment Status": 'test'
 }
]

def gns3_get_image(gns3_server_data, image_type, filename):
    # Create the images directory if it doesn't exist
    if not os.path.exists('images'):
        os.makedirs('images')

    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, vmanage_api_ip, deployment_type, deployment_status, deployment_step = \
            server_record['GNS3 Server'], server_record['Server Port'], server_record['Server Name'], server_record[
                'Project Name'], server_record['vManage API IP'], server_record['Deployment Type'], server_record[
                'Deployment Status'], server_record['Deployment Step']
        url = f"http://{server_ip}:{server_port}/v2/compute/{image_type}/images"
        response = requests.get(url)
        for image in response.json():
            if image['filename'] == filename:
                print(f"Downloading {filename}")
                url = f'http://{server_ip}:{server_port}/v2/compute/{image_type}/images/{filename}'
                file_path = os.path.join('images', filename)
                urllib.request.urlretrieve(url, file_path)
                return 201
    return 200

#required_qemu_images = {"viptela-vmanage-li-20.10.1-genericx86-64.qcow2", "empty30G.qcow2", "viptela-smart-li-20.10.1-genericx86-64.qcow2", "viptela-edge-20.10.1-genericx86-64.qcow2",}
#required_iou_images = {"L3-ADVENTERPRISEK9-M-15.5-2T.bin"}

#required_qemu_images = {"c8000v-universalk9_8G_serial.17.09.01a.qcow2"}
required_qemu_images = {"versa-director-c19c43c-21.2.3.qcow2", "versa-analytics-67ff6c7-21.2.3.qcow2", "versa-flexvnf-67ff6c7-21.2.3.qcow2", "pathview-amd64-14.0.0.54253.qcow2"}


#for image in required_iou_images:
#    gns3_get_image(gns3_server_data, 'iou', image)

for image in required_qemu_images:
    gns3_get_image(gns3_server_data, 'qemu', image)