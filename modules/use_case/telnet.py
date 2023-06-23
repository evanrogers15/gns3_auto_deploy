import telnetlib
import socket
import time

from modules.gns3.gns3_actions_old import restart_node

def is_node_responsive(host, port):
    try:
        tn = telnetlib.Telnet()
        tn.open(host, port, timeout=2)
        tn.write(b'\x03')
        time.sleep(1)  # Add a delay before reading the response
        if tn.sock_avail():
            response = tn.read_until(b"\n", timeout=2)
            #tn.close()
            if response == b'':
                raise socket.timeout("Timeout waiting for response")
            return True
        else:
            raise socket.timeout("No response received")
    except (socket.timeout, socket.error) as e:
        #print(f"Error connecting to node: {e}")
        return False

def run_telnet_command(server, port, project_id, node_id, console, state, command=None):
    if not is_node_responsive(server, console):
        restart_node(server, port, project_id, node_id)
    tn = telnetlib.Telnet(server, console, timeout=1)
    if state == "on":
        tn.write(command.encode('utf-8') + b'\n')
        output = tn.read_until(b'\n', timeout=2).decode('utf-8').strip()
    elif state == "off":
        tn.write(b'\x03')
        output = tn.read_until(b'\n', timeout=2).decode('utf-8').strip()
    else:
        print("Invalid state value")
        return None
