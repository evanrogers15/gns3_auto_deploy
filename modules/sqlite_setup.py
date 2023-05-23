import sqlite3
# Define the database file path
DB_PATH = 'gns3.db'

# Create a new database file if it doesn't exist
conn = sqlite3.connect(DB_PATH)
conn.close()

# Open a connection to the database
conn = sqlite3.connect(DB_PATH)

# Create the config table
conn.execute('''
CREATE TABLE IF NOT EXISTS config (
    id INTEGER PRIMARY KEY,
    server_name TEXT,
    server_ip TEXT,
    server_port INTEGER,
    project_list TEXT,
    project_names TEXT,
    project_status TEXT,
    project_name TEXT,
    project_id TEXT,
    site_count INTEGER,
    tap_name TEXT,
    vmanage_api_ip TEXT
);
''')
# Create the projects table
conn.execute('''
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    server_name TEXT,
    server_ip TEXT,
    server_port INTEGER,
    project_id INTEGER,
    project_name TEXT,
    project_status TEXT
);
''')
# Create the deployments table
conn.execute('''
CREATE TABLE IF NOT EXISTS deployments (
    id INTEGER PRIMARY KEY,
    timestamp TEXT, 
    server_name TEXT,
    server_ip TEXT,
    project_name TEXT,
    deployment_type TEXT,
    deployment_status TEXT,
    deployment_step TEXT,
    log_message TEXT
);
''')
# Create the uc_config table
conn.execute('''
CREATE TABLE IF NOT EXISTS uc_config (
    id INTEGER PRIMARY KEY,
    server_name TEXT,
    server_ip TEXT,
    server_port INTEGER,
    project_list TEXT,
    project_id INTEGER,
    project_name TEXT,
    project_status TEXT
);
''')
# Create the uc_projects table
conn.execute('''
CREATE TABLE IF NOT EXISTS uc_projects (
    id INTEGER PRIMARY KEY,
    server_name TEXT,
    server_ip TEXT,
    server_port INTEGER,
    project_id INTEGER,
    project_name TEXT,
    project_status TEXT
);
''')
# Create the uc_scenarios table
conn.execute('''
CREATE TABLE IF NOT EXISTS uc_scenarios (
    id INTEGER PRIMARY KEY,
    scenario_name TEXT,
    scenario_description TEXT
);
''')
conn.execute('''
CREATE TABLE IF NOT EXISTS uc_scenario_status (
  id INTEGER PRIMARY KEY,
  server_ip TEXT,
  project_id INTEGER,
  scenario_id INTEGER,
  status INTEGER,
  process_id INTEGER,
  FOREIGN KEY(project_id) REFERENCES uc_config(project_id),
  FOREIGN KEY(server_ip) REFERENCES uc_config(server_ip),
  FOREIGN KEY(scenario_id) REFERENCES uc_scenarios(id)
);
''')

# Create the trigger on the uc_config table
conn.execute('''
CREATE TRIGGER IF NOT EXISTS config_limit AFTER INSERT ON uc_config
BEGIN
    DELETE FROM uc_config WHERE id NOT IN (SELECT id FROM uc_config ORDER BY id DESC LIMIT 10);
END;
''')

conn.execute('''INSERT INTO uc_scenarios (scenario_name, scenario_description)
                VALUES ('Use Case #1', 'Start / Stop Manually: Causes a 5% degradation to the "biz-internet" uplink on the Site-1 vEdge as well as starting variable traffic from all site clients.')''')

conn.execute('''INSERT INTO uc_scenarios (scenario_name, scenario_description)
                VALUES ('Use Case #2', 'Start / Stop Manually: Causes a 5% degradation to all "biz-internet" uplinks inside of the deployment as well as starting variable traffic from all site clients. ')''')

conn.execute('''INSERT INTO uc_scenarios (scenario_name, scenario_description)
                VALUES ('Use Case #3', 'Start / Stop Manually: Use Case that will simulate real user traffic from site 2 and alternate flapping WAN links for Site 2 every 60 seconds that will cause AppNeta to alert on exccesive route changes.')''')

conn.execute('''INSERT INTO uc_scenarios (scenario_name, scenario_description)
                VALUES ('Use Case #4', 'Offloads Use Case #3 to the local machine that will simulate real user traffic from site 2 and alternate flapping WAN links for Site 2 every 60 seconds and schedules to run for 1 hour then reoccur every day at 8PM until Use Case is stopped..')''')

# Commit the changes and close the connection
conn.commit()
conn.close()
