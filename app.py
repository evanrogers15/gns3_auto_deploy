from flask import Flask, jsonify, abort, make_response, request, render_template
import subprocess
import psutil
import threading
import logging.handlers

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

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('file')
    for file in files:
        # Save the file to the "images" folder
        file.save('images/' + file.filename)
    return 'Files uploaded successfully'


@app.route('/api/tasks/start_viptela_deploy_old', methods=['PUT'])
def viptela_deploy_full_old():
    threading.Thread(target=viptela_deploy, args=()).start()
    return make_response(jsonify({'message': 'Deployment Started Successfully'}), 200)


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


@app.route('/api/tasks/stop_viptela_deploy', methods=['PUT'])
def stop_viptela_deploy():
    global running_thread

    # Check if a thread is running
    if running_thread is not None and running_thread.is_alive():
        # Forcefully stop the thread by calling the terminate() method
        running_thread.stop()
        running_thread.join()

        # Reset the running_thread variable
        running_thread = None

        return make_response(jsonify({'message': 'Deployment Stopped Successfully'}), 200)
    else:
        return make_response(jsonify({'message': 'No deployment is currently running'}), 400)

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
