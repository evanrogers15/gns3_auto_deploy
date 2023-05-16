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
    project_id TEXT,
    project_name TEXT,
    project_status TEXT,
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
# Create the scenarios table
conn.execute('''
CREATE TABLE IF NOT EXISTS scenarios (
    id INTEGER PRIMARY KEY,
    scenario_name TEXT,
    scenario_description TEXT
);
''')
conn.execute('''
CREATE TABLE IF NOT EXISTS scenario_status (
  id INTEGER PRIMARY KEY,
  server_ip TEXT,
  project_id INTEGER,
  scenario_id INTEGER,
  status INTEGER,
  process_id INTEGER,
  FOREIGN KEY(project_id) REFERENCES config(project_id),
  FOREIGN KEY(server_ip) REFERENCES config(server_ip),
  FOREIGN KEY(scenario_id) REFERENCES scenarios(id)
);
''')

# Create the trigger on the config table
conn.execute('''
CREATE TRIGGER IF NOT EXISTS config_limit AFTER INSERT ON config
BEGIN
    DELETE FROM config WHERE id NOT IN (SELECT id FROM config ORDER BY id DESC LIMIT 10);
END;
''')

conn.execute('''INSERT INTO scenarios (scenario_name, scenario_description)
                VALUES ('Use Case #1', 'Start / Stop Manually: This use case will cause a client in Site-4 to simulate real traffic across the SDWAN while flooding the upstream vEdge with discards to a server in Site-1 while also causing 10% packet loss to the links between vEdge-Site-4 and the ISP routers.')''')

conn.execute('''INSERT INTO scenarios (scenario_name, scenario_description)
                VALUES ('Use Case #2', 'Offloads Use Case #1 to the local machine, starts the client generating normal traffic then schedules degradation that will occur every day at 5PM for 1 hour until Use Case is stopped.')''')

conn.execute('''INSERT INTO scenarios (scenario_name, scenario_description)
                VALUES ('Use Case #3', 'Start / Stop Manually: Use Case that will simulate real user traffic from site 2 and alternate flapping WAN links for Site 2 every 60 seconds that will cause AppNeta to alert on exccesive route changes.')''')

conn.execute('''INSERT INTO scenarios (scenario_name, scenario_description)
                VALUES ('Use Case #4', 'Offloads Use Case #3 to the local machine that will simulate real user traffic from site 2 and alternate flapping WAN links for Site 2 every 60 seconds and schedules to run for 1 hour then reoccur every day at 8PM until Use Case is stopped..')''')

# Commit the changes and close the connection
conn.commit()
conn.close()
