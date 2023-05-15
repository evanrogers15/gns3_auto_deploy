from flask import Flask, jsonify, abort, make_response, request, render_template
import subprocess
import psutil
import threading
import logging.handlers
import requests
import json
import telnetlib
import time
import datetime
import urllib3
import ipaddress
import os
import re
import logging

from modules.arista_evpn_deploy import *
from modules.gns3_actions import *
from modules.gns3_query import *
from modules.viptela_actions import *
from modules.viptela_deployment import *
from modules.sqlite_setup import *
from modules.gns3_actions_old import *
from modules.gns3_variables import *
from modules_old.use_cases import *

app = Flask(__name__)
DB_PATH = 'gns3.db'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index_multi')
def index_multi():
    return render_template('index_multi.html')

@app.route('/admin')
def adminPage():
    return render_template('admin.html')

@app.route('/scenarios')
def scenariosPage():
    return render_template('scenarios.html')

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
    project_ids = [project['project_id'] for project in projects]
    if new_project_name not in [project['name'] for project in projects]:
        gns3_create_project_static(server_ip, server_port, new_project_name)
        projects = get_projects(server_ip, server_port)
    project_names = [project['name'] for project in projects]
    project_status = [project['status'] for project in projects]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM config WHERE server_ip=?", (server_ip,))
    row = c.fetchone()
    if row[0] == 0:
        c.execute("INSERT INTO config (server_ip, server_port, server_name, project_list, project_name, project_status, vmanage_api_ip, site_count, tap_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (server_ip, server_port, server_name, json.dumps(project_ids), json.dumps(project_names), json.dumps(project_status), vmanage_api_ip, site_count, tap_name))
    else:
        c.execute("UPDATE config SET server_port = ?, server_name = ?, project_list = ?, project_name = ?, project_status = ? WHERE server_ip = ? WHERE vmanage_api_ip = ? WHERE site_count = ? WHERE tap_name = ?", (server_port, server_name, json.dumps(project_ids), json.dumps(project_names), json.dumps(project_status), server_ip, vmanage_api_ip, site_count, tap_name))
    # Insert data into the projects table if project_id is present
    if 'project_id' in req_data:
        project_id = req_data['project_id']
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT project_list FROM config WHERE server_ip = ? AND server_port = ?", (server_ip, server_port))
        row = c.fetchone()
        if row:
            project_list = json.loads(row[0])
            if project_id in project_list:
                index = project_list.index(project_id)
                c.execute("SELECT project_name, project_status FROM config WHERE server_ip = ? AND server_port = ?", (server_ip, server_port))
                row = c.fetchone()
                if row:
                    project_name = json.loads(row[0])[index]
                    project_status = json.loads(row[1])[index]
                    # Check if the project_id already exists in the projects table
                    c.execute("SELECT COUNT(*) FROM projects WHERE project_id=?", (project_id,))
                    row = c.fetchone()
                    if row[0] == 0:
                        c.execute("INSERT INTO projects (server_name, server_ip, server_port, project_id, project_name, project_status) VALUES (?, ?, ?, ?, ?, ?)", (req_data.get('server_name'), server_ip, server_port, project_id, project_name, project_status))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/config', methods=['GET'])
def get_config():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM config")
    rows = c.fetchall()
    conn.close()
    config_data = [dict(row) for row in rows]
    return jsonify(config_data)


@app.route('/api/create_project', methods=['POST'])
def create_project():
    with open('app.log', 'w'):
        pass
    server_ip = request.json['server_ip']
    server_port = request.json['server_port']
    project_name = request.json['project_name']
    vmanage_api_ip = request.json['vmanage_api_ip']
    site_count = request.json['site_count']
    site_count = int(site_count)
    tap_name = request.json['tap_name']
    use_tap = request.json['use_tap']
    server_data = [{
        "GNS3 Server": server_ip,
        "Project Name": project_name,
        "vManage API IP": vmanage_api_ip,
        "Site Count": site_count,
        "Tap Name": tap_name,
        "Use Tap": use_tap,
        "Server Name": "er-test-01",
        "Server Port": server_port,
    }]
    logging.info(server_data)
    threading.Thread(target=viptela_deploy, args=(server_data,)).start()
    # deploy_sdwan(new_project_id, server_data)
    # return jsonify([server_data])
    return make_response(jsonify({'Deployment Started Successfully'}), 200)

@app.route('/api/projects', methods=['GET'])
def get_project_list():
    conn = sqlite3.connect(DB_PATH)
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

@app.route('/api/scenarios', methods=['GET', 'POST', 'PUT'])
def scenarios():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'GET':
        c.execute("SELECT id, scenario_name AS title, scenario_description AS description FROM scenarios")
        rows = c.fetchall()
        scenarios = [{'id': row[0], 'title': row[1], 'description': row[2]} for row in rows]
        conn.close()
        return jsonify({'scenarios': scenarios})
    elif request.method == 'POST':
        # Get the payload
        scenario_name = request.json.get('scenario_name')
        scenario_description = request.json.get('scenario_description')
        scenario_id = request.json.get('scenario_id')
        # If scenario_id is not provided, insert a new scenario
        if scenario_id is None:
            c.execute("INSERT INTO scenarios (scenario_name, scenario_description) VALUES (?, ?)", (scenario_name, scenario_description))
            scenario_id = c.lastrowid
            conn.commit()
        # If scenario_id is provided, update an existing scenario
        else:
            # Check if the scenario exists
            c.execute("SELECT * FROM scenarios WHERE id=?", (scenario_id,))
            row = c.fetchone()
            if not row:
                conn.close()
                return jsonify({'error': 'Scenario not found.'}), 404
            # Update the scenario values
            if scenario_name:
                c.execute("UPDATE scenarios SET scenario_name=? WHERE id=?", (scenario_name, scenario_id))
            if scenario_description:
                c.execute("UPDATE scenarios SET scenario_description=? WHERE id=?", (scenario_description, scenario_id))
            conn.commit()
        # Return the scenario
        c.execute("SELECT id, scenario_name AS title, scenario_description AS description FROM scenarios WHERE id=?", (scenario_id,))
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
        c.execute("SELECT * FROM scenarios WHERE id=?", (scenario_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'Scenario not found.'}), 404
        # Update the scenario values
        if scenario_name:
            c.execute("UPDATE scenarios SET scenario_name=? WHERE id=?", (scenario_name, scenario_id))
        if scenario_description:
            c.execute("UPDATE scenarios SET scenario_description=? WHERE id=?", (scenario_description, scenario_id))
        conn.commit()
        # Return the updated scenario
        c.execute("SELECT id, scenario_name AS title, scenario_description AS description FROM scenarios WHERE id=?", (scenario_id,))
        row = c.fetchone()
        scenario = {'id': row[0], 'title': row[1], 'description': row[2]}
        conn.close()
        return jsonify({'scenario': scenario})

@app.route('/api/scenarios/<int:scenario_id>', methods=['GET'])
def get_scenario(scenario_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM scenarios WHERE id=?", (scenario_id,))
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

@app.route('/api/scenario_status', methods=['GET'])
def get_scenario_status():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT scenario_status.id, scenario_status.server_ip, config.server_port, config.server_name, scenario_status.project_id, projects.project_name, scenario_status.scenario_id, scenario_status.status, scenario_status.process_id FROM scenario_status JOIN projects ON scenario_status.project_id = projects.project_id JOIN config ON scenario_status.server_ip = config.server_ip;")
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
def create_task(scenario_id):
    req_data = request.get_json()
    server_ip = req_data.get('server_ip')
    port = req_data.get('port')
    project_id = req_data.get('project_id')
    use_case_function = None
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM scenario_status WHERE server_ip=? AND project_id=? AND scenario_id=?", (server_ip, project_id, scenario_id,))
    row = c.fetchone()
    if row[0] == 0:
        c.execute("INSERT INTO scenario_status (server_ip, project_id, scenario_id, status) VALUES (?, ?, ?, ?)", (server_ip, project_id, scenario_id, 1))
    else:
        c.execute("UPDATE scenario_status SET status=? WHERE server_ip=? AND project_id=? AND scenario_id=?", (1, server_ip, project_id, scenario_id))
    conn.commit()
    conn.close()
    # Call the appropriate use case function based on the scenario_id
    if scenario_id == 1:
        use_case_function_name = "use_case_1"
        use_case_function = globals().get(use_case_function_name)
    elif scenario_id == 2:
        # Set the payload for the request
        payload = {
            'module_name': 'modules.use_cases',
            'sim_function_name': f"use_case_{scenario_id}_sim_user",
            'function_name': f"use_case_{scenario_id}",
            'filename': f"use_case_{scenario_id}",
            'server_ip': server_ip,
            'server_port': port,
            'project_id': project_id,
            'state': 'on',
            'duration': 300,
            'sleep': 300
        }
        # Make the request to create the function file
        response = requests.post(f'http://localhost:8080/api/create-function-file/{scenario_id}', json=payload)
        
        # Call the /api/run_script endpoint to start the use_case_2.py script
        data = {
            'script_path': 'use_case_2.py',
            'args': [project_id, str(scenario_id)],
            'project_id': project_id,
            'scenario_id': scenario_id
        }
        response = requests.post('http://localhost:8080/api/run_script', json=data)
        if response.status_code != 200:
            return jsonify({'error': 'Could not start use_case_2 script.'}), 500
        # Update the scenario status table with the process ID
        else:
            response_data = response.json()
            pid = response_data.get('pid')
            project_id = response_data.get('project_id')
            scenario_id = response_data.get('scenario_id')
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE scenario_status SET status=?, process_id=? WHERE server_ip=? AND project_id=? AND scenario_id=?", (2, pid, server_ip, project_id, scenario_id))
            conn.commit()
            conn.close()
    elif scenario_id == 3:
        # Set the payload for the request
        payload = {
            'module_name': 'modules.use_cases',
            'sim_function_name': f"use_case_{scenario_id}_sim_user",
            'function_name': f"use_case_{scenario_id}",
            'filename': f"use_case_{scenario_id}",
            'server_ip': server_ip,
            'server_port': port,
            'project_id': project_id,
            'state': 'on',
            'duration': 300,
            'sleep': 300
        }
        # Make the request to create the function file
        response = requests.post(f'http://localhost:8080/api/create-function-file/{scenario_id}', json=payload)
        
        # Call the /api/run_script endpoint to start the use_case_3.py script
        data = {
            'script_path': 'use_case_3.py',
            'args': [project_id, str(scenario_id)],
            'project_id': project_id,
            'scenario_id': scenario_id
        }
        response = requests.post('http://localhost:8080/api/run_script', json=data)
        if response.status_code != 200:
            return jsonify({'error': 'Could not start use_case_2 script.'}), 500
        # Update the scenario status table with the process ID
        else:
            response_data = response.json()
            pid = response_data.get('pid')
            project_id = response_data.get('project_id')
            scenario_id = response_data.get('scenario_id')
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE scenario_status SET status=?, process_id=? WHERE server_ip=? AND project_id=? AND scenario_id=?", (2, pid, server_ip, project_id, scenario_id))
            conn.commit()
            conn.close()
    elif scenario_id == 4:
        # Set the payload for the request
        payload = {
            'module_name': 'modules.use_cases',
            'sim_function_name': f"use_case_{scenario_id}_sim_user",
            'function_name': f"use_case_{scenario_id}",
            'filename': f"use_case_{scenario_id}",
            'server_ip': server_ip,
            'server_port': port,
            'project_id': project_id,
            'state': 'on',
            'duration': 300,
            'sleep': 300
        }
        # Make the request to create the function file
        response = requests.post(f'http://localhost:8080/api/create-function-file/{scenario_id}', json=payload)
        data = {
            'script_path': 'use_case_4.py',
            'args': [project_id, str(scenario_id)],
            'project_id': project_id,
            'scenario_id': scenario_id
        }
        response = requests.post('http://localhost:8080/api/run_script', json=data)
        if response.status_code != 200:
            return jsonify({'error': 'Could not start use_case_4 script.'}), 500
        else:
            response_data = response.json()
            pid = response_data.get('pid')
            project_id = response_data.get('project_id')
            scenario_id = response_data.get('scenario_id')
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE scenario_status SET status=?, process_id=? WHERE server_ip=? AND project_id=? AND scenario_id=?", (2, pid, server_ip, project_id, scenario_id))
            conn.commit()
            conn.close()
    else:
        return jsonify({'error': 'Invalid scenario ID.'}), 400
    if use_case_function is not None:
        success = use_case_function(server_ip, port, project_id, 'on')
        if success:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE scenario_status SET status=? WHERE server_ip=? AND project_id=? AND scenario_id=?", (2, server_ip, project_id, scenario_id))
            conn.commit()
            conn.close()
    scenario = {
        'running': True
    }
    return jsonify({'scenario': scenario}), 201

@app.route('/api/tasks/<int:scenario_id>', methods=['DELETE'])
def delete_task(scenario_id):
    req_data = request.get_json()
    server_ip = req_data.get('server_ip')
    port = req_data.get('port')
    project_id = req_data.get('project_id')
    conn = sqlite3.connect(DB_PATH)
    status = '3'
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM scenario_status WHERE server_ip=? AND project_id=? AND scenario_id=?", (server_ip, project_id, scenario_id,))
    row = c.fetchone()
    if row[0] == 0:
        c.execute("INSERT INTO scenario_status (server_ip, project_id, scenario_id, status) VALUES (?, ?, ?, ?)", (server_ip, project_id, scenario_id, status))
    else:
        c.execute("UPDATE scenario_status SET status=? WHERE server_ip=? AND project_id=? AND scenario_id=?", (status, server_ip, project_id, scenario_id))
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
        use_case_1(server_ip, port, project_id, 'off')
        # Call the /api/stop_script endpoint to stop the script
        data = {
            'project_id': project_id,
            'scenario_id': scenario_id
        }
        response = requests.post('http://localhost:8080/api/stop_script', json=data)
        if response.status_code != 200:
            return jsonify({'error': 'Could not stop script.'}), 500
        else:
            status = 0
    elif scenario_id == 3:
        use_case_3(server_ip, port, project_id, 'off')
        use_case_4_sim_user(server_ip, port, project_id, 'off')
        # Call the /api/stop_script endpoint to stop the script
        data = {
            'project_id': project_id,
            'scenario_id': scenario_id
        }
        response = requests.post('http://localhost:8080/api/stop_script', json=data)
        if response.status_code != 200:
            return jsonify({'error': 'Could not stop script.'}), 500
        else:
            status = 0
    elif scenario_id == 4:
        use_case_4(server_ip, port, project_id, 'off')
        # Call the /api/stop_script endpoint to stop the script
        data = {
            'project_id': project_id,
            'scenario_id': scenario_id
        }
        response = requests.post('http://localhost:8080/api/stop_script', json=data)
        if response.status_code != 200:
            return jsonify({'error': 'Could not stop script.'}), 500
        else:
            status = 0
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE scenario_status SET status=? WHERE server_ip=? AND project_id=? AND scenario_id=?", (status, server_ip, project_id, scenario_id))
    conn.commit()
    conn.close()
    return jsonify({'scenario': "stopped"}), 201
    
@app.route('/api/create-function-file/<int:scenario_id>', methods=['POST'])
def create_function_file_endpoint(scenario_id):
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
                f.write(f"import time\nimport schedule\nfrom datetime import datetime\nfrom {module_name} import {function_name}, {sim_function_name}\n\n")
                f.write(f"{sim_function_name}('{server_ip}', {server_port}, '{project_id}', 'on')\n\n")
                f.write(f"def run_task():\n")
                f.write(f"\t{function_name}('{server_ip}', {server_port}, '{project_id}', 'on')\n")
                f.write(f"\ttime.sleep(3600)\n")
                f.write(f"\t{function_name}('{server_ip}', {server_port}, '{project_id}', 'off')\n")
                f.write(f"\n\nschedule.every().day.at('8:00').do(run_task)\n\n")
                f.write(f"while True:\n\tschedule.run_pending()\n\tnow = datetime.now().strftime('%Y-%m-%d %H:%M:%S')\n\tprint(f'Waiting for scheduled task for {function_name}...')\n\ttime.sleep(60)\n")
        elif scenario_id == 3: 
            with open(filename, 'w') as f:
                f.write(f"import time\nfrom {module_name} import {function_name}, use_case_4_sim_user\n\n")
                f.write(f"use_case_4_sim_user('{server_ip}', {server_port}, '{project_id}', 'on')\n\nset_link = 1\n")
                f.write(f"def run_task():\n")
                f.write(f"\twhile True:\n")
                f.write(f"\t\tfor i in range(30):\n")
                f.write(f"\t\t\tset_link = 2 if i % 2 == 0 else 1\n")
                f.write(f"\t\t\t{function_name}('{server_ip}', {server_port}, '{project_id}', 'on', set_link)\n")
                f.write(f"\t\t\ttime.sleep(30)\n")
                f.write(f"\t\t\t{function_name}('{server_ip}', {server_port}, '{project_id}', 'off', set_link)\n")
                f.write(f"\t\t\ttime.sleep(15)\n")
                f.write(f"run_task()")
        elif scenario_id == 4: 
            with open(filename, 'w') as f:
                f.write(f"import time\nimport schedule\nfrom datetime import datetime\nfrom {module_name} import {function_name}, {sim_function_name}\n\n")
                f.write(f"{sim_function_name}('{server_ip}', {server_port}, '{project_id}', 'on')\n\nset_link = 1\n")
                f.write(f"def run_task():\n")
                f.write(f"\tfor i in range(120):\n")
                f.write(f"\t\tset_link = 2 if i % 2 == 0 else 1\n")
                f.write(f"\t\t{function_name}('{server_ip}', {server_port}, '{project_id}', 'on', set_link)\n")
                f.write(f"\t\ttime.sleep(120)\n")
                f.write(f"\t\t{function_name}('{server_ip}', {server_port}, '{project_id}', 'off', set_link)\n")
                f.write(f"\t\ttime.sleep(15)\n")
                f.write(f"\n\nschedule.every().day.at('11:00').do(run_task)\n\n")
                f.write(f"while True:\n\tschedule.run_pending()\n\tnow = datetime.now().strftime('%Y-%m-%d %H:%M:%S')\n\tprint(f'Waiting for scheduled task {function_name}...')\n\ttime.sleep(60)\n")
        else:
            return jsonify({'error': f'Invalid use case ID {scenario_id}.'})
        return jsonify({'filename': filename})
    except ModuleNotFoundError:
        return jsonify({'error': f'Module {module_name} not found.'})
    except AttributeError:
        return jsonify({'error': f'Function {function_name} not found in module {module_name}.'})

@app.route('/api/run_script', methods=['POST'])
def run_script():
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
def stop_script():
    # Get the project ID and scenario ID from the request body
    project_id = str(request.json.get('project_id'))
    scenario_id = str(request.json.get('scenario_id'))
    # Get the process ID from the scenario status table
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT process_id FROM scenario_status WHERE project_id=? AND scenario_id=?", (project_id, scenario_id,))
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
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE scenario_status SET process_id = NULL WHERE project_id = ? AND scenario_id = ?", (project_id, scenario_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Process stopped successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop_process', methods=['POST'])
def stop_process():
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
def process_info():
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
    conn = sqlite3.connect(DB_PATH)
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
