from flask import Flask, jsonify, abort, make_response, request, render_template
import subprocess
import psutil
import threading
import logging.handlers
from werkzeug.utils import secure_filename

from modules.arista_evpn_deploy import *
from modules.gns3_query import *
from modules.viptela_deployment import *
from modules.sqlite_setup import *
from modules.gns3_actions_old import *
from modules.gns3_variables import *
from modules.use_cases import *

app = Flask(__name__)

running_thread = None

# Custom Thread class with terminate() method
class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def terminated(self):
        return self._stop_event.is_set()

@app.route('/')
def index():
    return render_template('create_sdwan.html')

@app.route('/admin')
def adminPage():
    return render_template('admin.html')

@app.route('/api/config', methods=['POST'])
def update_config():
    req_data = request.get_json()
    if not req_data:
        return jsonify({'error': 'Request data is empty or None.'}), 400
    server_ip = req_data.get('server_ip')
    if not server_ip:
        return jsonify({'error': 'Server IP is missing.'}), 400
    server_port = req_data.get('server_port')
    new_project_name = req_data.get('project_name')
    vmanage_api_ip = req_data.get('vmanage_api_ip')
    site_count = req_data.get('site_count')
    tap_name = req_data.get('tap_name')
    projects = get_projects(server_ip, server_port)
    server_name = get_computes_name(server_ip, server_port)
    if new_project_name not in [project['name'] for project in projects]:
        project_id = gns3_create_project_static(server_ip, server_port, new_project_name)
    else:
        matching_projects = [project for project in projects if project['name'] == new_project_name]
        project_id = matching_projects[0]['project_id']
        gns3_delete_project_static(server_ip, server_port, new_project_name, project_id)
        project_id = gns3_create_project_static(server_ip, server_port, new_project_name)
    projects = get_projects(server_ip, server_port)
    project_names = [project['name'] for project in projects]
    project_ids = [project['project_id'] for project in projects]
    project_status = [project['status'] for project in projects]
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM config")
    c.execute("INSERT INTO config (server_ip, server_port, server_name, project_list, project_names, project_status, project_name, project_id, vmanage_api_ip, site_count, tap_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (server_ip, server_port, server_name, json.dumps(project_ids), json.dumps(project_names), json.dumps(project_status), new_project_name, project_id, vmanage_api_ip, site_count, tap_name))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/config', methods=['GET'])
def get_config():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM config")
    rows = c.fetchall()
    conn.close()
    config_data = [dict(row) for row in rows]
    return jsonify(config_data)

@app.route('/api/deployment_status', methods=['GET'])
def get_deployment():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM deployments")
    rows = c.fetchall()
    conn.close()
    deployment_data = [dict(row) for row in rows]
    return jsonify(deployment_data)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    # Get the absolute path of the directory where the Flask app is located
    app_root = os.path.dirname(os.path.abspath(__file__))
    # Create the images folder if it doesn't exist
    images_dir = os.path.join(app_root, 'images')
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    files = request.files.getlist('file')
    for file in files:
        filename = secure_filename(file.filename)
        # Get the extension of the file
        _, extension = os.path.splitext(filename)
        # Determine the appropriate directory based on the file extension
        if extension.lower() in ['.qcow2', '.img', '.iso']:
            subdir = 'qemu'
        elif extension.lower() in ['.iourc', '.image', '.bin']:
            subdir = 'iou'
        else:
            subdir = 'unknown'  # Create a separate directory for unknown file types if needed
        # Create the subdirectory if it doesn't exist
        sub_dir_path = os.path.join(images_dir, subdir)
        if not os.path.exists(sub_dir_path):
            os.makedirs(sub_dir_path)
        # Save the file to the appropriate directory
        file.save(os.path.join(sub_dir_path, filename))
    return 'Files uploaded successfully'

@app.route('/api/uploaded_files', methods=['GET'])
def get_uploaded_files():
    # Get the list of uploaded files in the images/qemu and images/iou directories
    qemu_dir = os.path.join('/app', 'images', 'qemu')
    iou_dir = os.path.join('/app', 'images', 'iou')
    ios_dir = os.path.join('/app', 'images', 'ios')
    # Create the directories if they don't exist
    os.makedirs(qemu_dir, exist_ok=True)
    os.makedirs(iou_dir, exist_ok=True)
    os.makedirs(ios_dir, exist_ok=True)
    qemu_files = [file for file in os.listdir(qemu_dir) if os.path.isfile(os.path.join(qemu_dir, file))]
    iou_files = [file for file in os.listdir(iou_dir) if os.path.isfile(os.path.join(iou_dir, file))]
    ios_files = [file for file in os.listdir(ios_dir) if os.path.isfile(os.path.join(ios_dir, file))]
    return jsonify({'qemu_files': qemu_files, 'iou_files': iou_files, 'ios_files': ios_files})


@app.route('/api/tasks/start_viptela_deploy', methods=['PUT'])
def viptela_deploy_full():
    global running_thread

    # Check if a thread is already running
    if running_thread is not None and running_thread.is_alive():
        return make_response(jsonify({'message': 'Deployment is already in progress'}), 400)

    # Start a new thread for deployment
    running_thread = threading.Thread(target=viptela_deploy, args=())
    running_thread.start()

    return make_response(jsonify({'message': 'Deployment Started Successfully'}), 200)

@app.route('/api/projects', methods=['GET'])
def get_project_list():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT server_ip, server_port FROM config")
    row = c.fetchone()
    if row is None:
        conn.close()
        return jsonify({'error': 'Server IP and Port not set in config table'}), 500
    server_ip = row[0]
    server_port = row[1]
    c.execute("SELECT project_list, project_name, project_status FROM config WHERE server_ip=? AND server_port=?", (server_ip, server_port))
    row = c.fetchone()
    if row is None:
        conn.close()
        return jsonify({'error': 'Project list not found in config file'}), 500
    project_list = json.loads(row[0])
    project_name = json.loads(row[1])
    project_status = json.loads(row[2])
    project_data = [{'id': project_list[i], 'name': project_name[i], 'status': project_status[i]} for i in range(len(project_list))]
    conn.close()
    return jsonify({'projects': project_data})


@app.route('/api/reset-tables', methods=['POST'])
def reset_tables():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Delete all rows from the config and projects tables
    c.execute('DELETE FROM config')
    c.execute('DELETE FROM projects')
    c.execute('DELETE FROM scenario_status')
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/reset-lab-clients', methods=['POST'])
def reset_lab_clients():
    server_ip = request.json['server_ip']
    server_port = request.json['server_port']
    project_id = request.json['project_id']
    reset_lab_client_states(server_ip, server_port, project_id)
    return jsonify({'success': True})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080 )
