from flask import Flask, jsonify, abort, make_response, request, render_template
import subprocess
import psutil
import threading
import logging.handlers
from werkzeug.utils import secure_filename

from modules.arista_evpn_deploy import *
from modules.gns3_query import *
from modules.viptela_deployment import *
from modules.oa_viptela_deployment import *
from modules.gns3_actions_old import *
from modules.gns3_variables import *
from modules.use_cases import *
from modules.versa_deployment import versa_deploy

app = Flask(__name__)

running_thread = None

@app.route('/')
def index():
    return render_template('create_sdwan.html')

@app.route('/oa')
def oa_sdwan_deploy():
    return render_template('oa_create_sdwan.html')

@app.route('/versa')
def oa_versa_deploy():
    return render_template('create_versa_sdwan.html')

@app.route('/demo')
def demo_sdwan_deploy():
    return render_template('demo_create_sdwan.html')

@app.route('/arista')
def arista_deploy():
    return render_template('create_arista_evpn.html')

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
    c.execute("INSERT INTO config (server_ip, server_port, server_name, project_list, project_names, project_status, project_name, project_id, vmanage_api_ip, site_count, tap_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (server_ip, server_port, server_name, json.dumps(project_ids), json.dumps(project_names), json.dumps(project_status), new_project_name, project_id, vmanage_api_ip, site_count, tap_name))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/demo_config', methods=['POST'])
def update_confign():
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
    use_existing = req_data.get('use_existing')
    projects = gns3_query_get_projects(server_ip, server_port)
    server_name = gns3_query_get_computes_name(server_ip, server_port)
    if use_existing == 0:
        if new_project_name not in [project['name'] for project in projects]:
            project_id = gns3_create_project(server_ip, server_port, new_project_name)
        else:
            matching_projects = [project for project in projects if project['name'] == new_project_name]
            project_id = matching_projects[0]['project_id']
            gns3_delete_project_static(server_ip, server_port, new_project_name, project_id)
            project_id = gns3_create_project(server_ip, server_port, new_project_name)
    else:
        project_id = gns3_query_get_project_id(server_ip, server_port, new_project_name)
        gns3_delete_all_nodes(server_ip, server_port, project_id)
        gns3_delete_all_drawings(server_ip, server_port, project_id)
    projects = gns3_query_get_projects(server_ip, server_port)
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

    return jsonify({'success': True})

@app.route('/api/tasks/oa_start_viptela_deploy', methods=['PUT'])
def oa_viptela_deploy_full():
    global running_thread
    # Check if a thread is already running
    if running_thread is not None and running_thread.is_alive():
        return make_response(jsonify({'message': 'Deployment is already in progress'}), 400)

    # Start a new thread for deployment
    running_thread = threading.Thread(target=oa_viptela_deploy, args=())
    running_thread.start()

    return make_response(jsonify({'message': 'Deployment Started Successfully'}), 200)

@app.route('/api/tasks/start_versa_deploy', methods=['PUT'])
def versa_deploy_full():
    global running_thread
    # Check if a thread is already running
    if running_thread is not None and running_thread.is_alive():
        return make_response(jsonify({'message': 'Deployment is already in progress'}), 400)

    # Start a new thread for deployment
    running_thread = threading.Thread(target=versa_deploy, args=())
    running_thread.start()

    return jsonify({'success': True})

@app.route('/api/tasks/start_arista_deploy', methods=['PUT'])
def arista_deploy_full():
    global running_thread
    # Check if a thread is already running
    if running_thread is not None and running_thread.is_alive():
        return make_response(jsonify({'message': 'Deployment is already in progress'}), 400)

    # Start a new thread for deployment
    running_thread = threading.Thread(target=arista_deploy, args=())
    running_thread.start()

    return jsonify({'success': True})

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

# region UC
@app.route('/uc-local')
def index_uc_index():
    return render_template('uc_local.html')

@app.route('/uc-remote')
def index_multi():
    return render_template('uc_remote.html')

@app.route('/uc_scenarios')
def uc_scenariosPage():
    return render_template('uc_scenarios.html')

@app.route('/api/uc_config', methods=['POST'])
def update_uc_config():
    req_data = request.get_json()
    if not req_data:
        return jsonify({'error': 'Request data is empty or None.'}), 400
    server_ip = req_data.get('server_ip')
    if not server_ip:
        return jsonify({'error': 'Server IP is missing.'}), 400
    server_port = req_data.get('server_port')
    uc_projects = gns3_query_get_projects(server_ip, server_port)
    server_name = gns3_query_get_computes_name(server_ip, server_port)
    project_ids = [project['project_id'] for project in uc_projects]
    project_names = [project['name'] for project in uc_projects]
    project_status = [project['status'] for project in uc_projects]
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM uc_config WHERE server_ip=?", (server_ip,))
    row = c.fetchone()
    if row[0] == 0:
        c.execute(
            "INSERT INTO uc_config (server_ip, server_port, server_name, project_list, project_name, project_status) VALUES (?, ?, ?, ?, ?, ?)",
            (server_ip, server_port, server_name, json.dumps(project_ids), json.dumps(project_names),
             json.dumps(project_status)))
    else:
        c.execute(
            "UPDATE uc_config SET server_port = ?, server_name = ?, project_list = ?, project_name = ?, project_status = ? WHERE server_ip = ?",
            (server_port, server_name, json.dumps(project_ids), json.dumps(project_names), json.dumps(project_status),
             server_ip))
    # Insert data into the uc_projects table if project_id is present
    if 'project_id' in req_data:
        project_id = req_data['project_id']
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT project_list FROM uc_config WHERE server_ip = ? AND server_port = ?",
                  (server_ip, server_port))
        row = c.fetchone()
        if row:
            project_list = json.loads(row[0])
            if project_id in project_list:
                index = project_list.index(project_id)
                c.execute("SELECT project_name, project_status FROM uc_config WHERE server_ip = ? AND server_port = ?",
                          (server_ip, server_port))
                row = c.fetchone()
                if row:
                    project_name = json.loads(row[0])[index]
                    project_status = json.loads(row[1])[index]
                    # Check if the project_id already exists in the uc_projects table
                    c.execute("SELECT COUNT(*) FROM uc_projects WHERE project_id=?", (project_id,))
                    row = c.fetchone()
                    if row[0] == 0:
                        c.execute(
                            "INSERT INTO uc_projects (server_name, server_ip, server_port, project_id, project_name, project_status) VALUES (?, ?, ?, ?, ?, ?)",
                            (req_data.get('server_name'), server_ip, server_port, project_id, project_name,
                             project_status))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/uc_config', methods=['GET'])
def get_uc_config():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM uc_config")
    rows = c.fetchall()
    conn.close()
    uc_config_data = [dict(row) for row in rows]
    return jsonify(uc_config_data)

@app.route('/api/uc_projects', methods=['GET'])
def uc_get_project_list():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT server_ip, server_port FROM uc_config")
    row = c.fetchone()
    if row is None:
        conn.close()
        return jsonify({'error': 'Server IP and Port not set in uc_config table'}), 500
    server_ip = row[0]
    server_port = row[1]
    c.execute("SELECT project_list, project_name, project_status FROM uc_config WHERE server_ip=? AND server_port=?",
              (server_ip, server_port))
    row = c.fetchone()
    if row is None:
        conn.close()
        return jsonify({'error': 'Project list not found in uc_config file'}), 500
    project_list = json.loads(row[0])
    project_name = json.loads(row[1])
    project_status = json.loads(row[2])
    project_data = [{'id': project_list[i], 'name': project_name[i], 'status': project_status[i]} for i in
                    range(len(project_list))]
    conn.close()
    return jsonify({'projects': project_data})

@app.route('/api/uc_scenarios', methods=['GET', 'POST', 'PUT'])
def uc_scenarios():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    if request.method == 'GET':
        c.execute("SELECT id, scenario_name AS title, scenario_description AS description FROM uc_scenarios")
        rows = c.fetchall()
        uc_scenarios = [{'id': row[0], 'title': row[1], 'description': row[2]} for row in rows]
        conn.close()
        return jsonify({'scenarios': uc_scenarios})
    elif request.method == 'POST':
        # Get the payload
        scenario_name = request.json.get('scenario_name')
        scenario_description = request.json.get('scenario_description')
        scenario_id = request.json.get('scenario_id')
        # If scenario_id is not provided, insert a new scenario
        if scenario_id is None:
            c.execute("INSERT INTO uc_scenarios (scenario_name, scenario_description) VALUES (?, ?)",
                      (scenario_name, scenario_description))
            scenario_id = c.lastrowid
            conn.commit()
        # If scenario_id is provided, update an existing scenario
        else:
            # Check if the scenario exists
            c.execute("SELECT * FROM uc_scenarios WHERE id=?", (scenario_id,))
            row = c.fetchone()
            if not row:
                conn.close()
                return jsonify({'error': 'Scenario not found.'}), 404
            # Update the scenario values
            if scenario_name:
                c.execute("UPDATE uc_scenarios SET scenario_name=? WHERE id=?", (scenario_name, scenario_id))
            if scenario_description:
                c.execute("UPDATE uc_scenarios SET scenario_description=? WHERE id=?",
                          (scenario_description, scenario_id))
            conn.commit()
        # Return the scenario
        c.execute("SELECT id, scenario_name AS title, scenario_description AS description FROM uc_scenarios WHERE id=?",
                  (scenario_id,))
        row = c.fetchone()
        scenario = {'id': row[0], 'title': row[1], 'description': row[2]}
        conn.close()
        return jsonify({'scenario': scenario})
    elif request.method == 'PUT':
        # Get the payload
        scenario_id = request.view_args.get('scenario_id')
        scenario_name = request.json.get('scenario_name')
        scenario_description = request.json.get('scenario_description')

        # Check if the scenario exists
        c.execute("SELECT * FROM uc_scenarios WHERE id=?", (scenario_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'Scenario not found.'}), 404
        # Update the scenario values
        if scenario_name:
            c.execute("UPDATE uc_scenarios SET scenario_name=? WHERE id=?", (scenario_name, scenario_id))
        if scenario_description:
            c.execute("UPDATE uc_scenarios SET scenario_description=? WHERE id=?", (scenario_description, scenario_id))
        conn.commit()
        # Return the updated scenario
        c.execute("SELECT id, scenario_name AS title, scenario_description AS description FROM uc_scenarios WHERE id=?",
                  (scenario_id,))
        row = c.fetchone()
        scenario = {'id': row[0], 'title': row[1], 'description': row[2]}
        conn.close()
        return jsonify({'scenario': scenario})

@app.route('/api/uc_scenarios/<int:scenario_id>', methods=['GET'])
def uc_get_scenario(scenario_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM uc_scenarios WHERE id=?", (scenario_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        abort(404)
    scenario = {
        'id': row[0],
        'name': row[1],
        'description': row[2]
    }
    return jsonify({'scenario': scenario})

@app.route('/api/uc_scenario_status', methods=['GET'])
def get_uc_scenario_status():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "SELECT uc_scenario_status.id, uc_scenario_status.server_ip, uc_config.server_port, uc_config.server_name, uc_scenario_status.project_id, uc_projects.project_name, uc_scenario_status.scenario_id, uc_scenario_status.status, uc_scenario_status.process_id FROM uc_scenario_status JOIN uc_projects ON uc_scenario_status.project_id = uc_projects.project_id JOIN uc_config ON uc_scenario_status.server_ip = uc_config.server_ip;")
    rows = c.fetchall()
    conn.close()
    data = []
    for row in rows:
        data.append({
            'id': row[0],
            'server_ip': row[1],
            'server_name': row[3],
            'server_port': row[2],
            'project_id': row[4],
            'project_name': row[5],
            'scenario_id': row[6],
            'status': row[7],
            'process_id': row[8]
        })
    return jsonify({'scenario_status': data})

@app.route('/api/tasks/<int:scenario_id>', methods=['POST'])
def uc_create_task(scenario_id):
    req_data = request.get_json()
    server_ip = req_data.get('server_ip')
    port = req_data.get('port')
    project_id = req_data.get('project_id')
    use_case_function = None
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM uc_scenario_status WHERE server_ip=? AND project_id=? AND scenario_id=?",
              (server_ip, project_id, scenario_id,))
    row = c.fetchone()
    if row[0] == 0:
        c.execute("INSERT INTO uc_scenario_status (server_ip, project_id, scenario_id, status) VALUES (?, ?, ?, ?)",
                  (server_ip, project_id, scenario_id, 1))
    else:
        c.execute("UPDATE uc_scenario_status SET status=? WHERE server_ip=? AND project_id=? AND scenario_id=?",
                  (1, server_ip, project_id, scenario_id))
    conn.commit()
    conn.close()
    # Call the appropriate use case function based on the scenario_id
    if scenario_id == 1:
        use_case_function_name = "use_case_1"
        use_case_function = globals().get(use_case_function_name)
    elif scenario_id == 2:
        use_case_function_name = "use_case_2"
        use_case_function = globals().get(use_case_function_name)
    else:
        return jsonify({'error': 'Invalid scenario ID.'}), 400
    if use_case_function is not None:
        success = use_case_function(server_ip, port, project_id, 'on')
        if success:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("UPDATE uc_scenario_status SET status=? WHERE server_ip=? AND project_id=? AND scenario_id=?",
                      (2, server_ip, project_id, scenario_id))
            conn.commit()
            conn.close()
    scenario = {
        'running': True
    }
    return jsonify({'scenario': scenario}), 201

@app.route('/api/tasks/<int:scenario_id>', methods=['DELETE'])
def uc_delete_task(scenario_id):
    req_data = request.get_json()
    server_ip = req_data.get('server_ip')
    port = req_data.get('port')
    project_id = req_data.get('project_id')
    conn = sqlite3.connect(db_path)
    status = '3'
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM uc_scenario_status WHERE server_ip=? AND project_id=? AND scenario_id=?",
              (server_ip, project_id, scenario_id,))
    row = c.fetchone()
    if row[0] == 0:
        c.execute("INSERT INTO uc_scenario_status (server_ip, project_id, scenario_id, status) VALUES (?, ?, ?, ?)",
                  (server_ip, project_id, scenario_id, status))
    else:
        c.execute("UPDATE uc_scenario_status SET status=? WHERE server_ip=? AND project_id=? AND scenario_id=?",
                  (status, server_ip, project_id, scenario_id))
    conn.commit()
    conn.close()
    # Call the appropriate use case function based on the scenario_id
    if scenario_id == 1:
        use_case_function_name = f"use_case_{scenario_id}"
        use_case_function = globals().get(use_case_function_name)
        if use_case_function is not None:
            success = use_case_function(server_ip, port, project_id, 'off')
            if success:
                status = 0
    elif scenario_id == 2:
        use_case_function_name = f"use_case_{scenario_id}"
        use_case_function = globals().get(use_case_function_name)
        if use_case_function is not None:
            success = use_case_function(server_ip, port, project_id, 'off')
            if success:
                status = 0
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE uc_scenario_status SET status=? WHERE server_ip=? AND project_id=? AND scenario_id=?",
              (status, server_ip, project_id, scenario_id))
    conn.commit()
    conn.close()
    return jsonify({'scenario': "stopped"}), 201

@app.route('/api/create-function-file/<int:scenario_id>', methods=['POST'])
def uc_create_function_file_endpoint(scenario_id):
    try:
        # Get the payload
        module_name = request.json['module_name']
        sim_function_name = request.json['sim_function_name']
        function_name = request.json['function_name']
        filename = request.json['filename']
        server_ip = request.json['server_ip']
        server_port = request.json['server_port']
        project_id = request.json['project_id']
        state = request.json['state']
        duration = request.json['duration']
        sleep = request.json['sleep']
        # Write the source code and dependencies to a file
        filename = f'{filename}.py'
        if scenario_id == 2:
            with open(filename, 'w') as f:
                f.write(
                    f"import time\nimport schedule\nfrom datetime import datetime\nfrom {module_name} import {function_name}, {sim_function_name}\n\n")
                f.write(f"{sim_function_name}('{server_ip}', {server_port}, '{project_id}', 'on')\n\n")
                f.write(f"def run_task():\n")
                f.write(f"\t{function_name}('{server_ip}', {server_port}, '{project_id}', 'on')\n")
                f.write(f"\ttime.sleep(3600)\n")
                f.write(f"\t{function_name}('{server_ip}', {server_port}, '{project_id}', 'off')\n")
                f.write(f"\n\nschedule.every().day.at('8:00').do(run_task)\n\n")
                f.write(
                    f"while True:\n\tschedule.run_pending()\n\tnow = datetime.now().strftime('%Y-%m-%d %H:%M:%S')\n\tprint(f'Waiting for scheduled task for {function_name}...')\n\ttime.sleep(60)\n")
        else:
            return jsonify({'error': f'Invalid use case ID {scenario_id}.'})
        return jsonify({'filename': filename})
    except ModuleNotFoundError:
        return jsonify({'error': f'Module {module_name} not found.'})
    except AttributeError:
        return jsonify({'error': f'Function {function_name} not found in module {module_name}.'})

@app.route('/api/run_script', methods=['POST'])
def uc_run_script():
    # Get the script path, arguments, project ID, and scenario ID from the request
    data = request.get_json()
    script_path = data.get('script_path')
    args = data.get('args', [])
    project_id = data.get('project_id')
    scenario_id = data.get('scenario_id')
    # Start the script as a subprocess and store the Popen object
    try:
        proc = subprocess.Popen(['python', script_path] + args)
        pid = proc.pid
        processes[pid] = proc
        # Return the process information in the response
        return jsonify({'pid': pid, 'project_id': project_id, 'scenario_id': scenario_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop_script', methods=['POST'])
def uc_stop_script():
    # Get the project ID and scenario ID from the request body
    project_id = str(request.json.get('project_id'))
    scenario_id = str(request.json.get('scenario_id'))
    # Get the process ID from the scenario status table
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT process_id FROM uc_scenario_status WHERE project_id=? AND scenario_id=?",
              (project_id, scenario_id,))
    row = c.fetchone()
    if row is None:
        return jsonify({'error': 'Scenario not found.'}), 404
    process_id = row[0]
    conn.close()
    # Check if the process ID is valid
    if not process_id or not isinstance(process_id, int):
        return jsonify({'error': 'Invalid process ID.'}), 400
    # Try to get the process by its ID
    try:
        process = psutil.Process(process_id)
    except psutil.NoSuchProcess:
        return jsonify({'error': 'Process not found.'}), 404
    # Try to stop the process
    try:
        process.terminate()
        # Update the scenario status table with null process ID
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("UPDATE uc_scenario_status SET process_id = NULL WHERE project_id = ? AND scenario_id = ?",
                  (project_id, scenario_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Process stopped successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop_process', methods=['POST'])
def uc_stop_process():
    # Get the process ID from the request body
    process_id = request.json.get('process_id')

    # Check if the process ID is valid
    if not process_id or not isinstance(process_id, int):
        return jsonify({'error': 'Invalid process ID.'}), 400

    # Try to get the process by its ID
    try:
        process = psutil.Process(process_id)
    except psutil.NoSuchProcess:
        return jsonify({'error': 'Process not found.'}), 404

    # Try to stop the process
    try:
        process.terminate()
        return jsonify({'message': 'Process stopped successfully.'}), 200
    except psutil.AccessDenied:
        return jsonify({'error': 'Access denied. Could not stop process.'}), 403

@app.route('/api/process_info', methods=['POST'])
def uc_process_info():
    # Get the process ID from the request
    data = request.get_json()
    pid = data.get('pid')
    # Get the process object from the global dictionary
    proc = processes.get(pid)
    if proc:
        # Return information about the process
        return jsonify({
            'pid': pid,
            'status': 'running' if proc.poll() is None else 'stopped',
            'returncode': proc.returncode
        })
    else:
        return jsonify({'error': f'Process with PID {pid} not found.'})

@app.route('/api/reset-tables', methods=['POST'])
def reset_tables():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Delete all rows from the uc_config and uc_projects tables
    c.execute('DELETE FROM uc_config')
    c.execute('DELETE FROM uc_projects')
    c.execute('DELETE FROM uc_scenario_status')
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
# endregion

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080 )
