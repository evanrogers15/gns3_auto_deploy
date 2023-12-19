**Components:**

- Docker
- python
- Flask - Web Framework for UI and API endpoints
- SQLite3 - Database used for configurations and logs

## Github Project Layout:

## Misc - Temporary staging directory for me

## Modules - Python Modules

### configs - Device specific directories containing files that have been templatized for device configuration

### arista

### cisco_iou

### fortigate

### versa

### viptela

### deployment - Functions for different deployment versions

- arista_evpn_deploy.py - Contains the deployment workflow for deploying the Arista EVPN GNS3 Lab
- versa_appneta_deployment.py - Contains the deployment workflow for deploying the Versa GNS3 Lab
- viptela_cedge_appneta_deployment.py - Contains the deployment workflow for deploying the Viptela cEdge version of the lab
- viptela_vedge_appneta_deployment.py - Contains the deployment workflow for deploying the Viptela vEdge version of the lab

### gns3 - Functions used to interact with GNS3

- gns3_actions.py - Contains functions that create, delete, modify different components in GNS3
- gns3_dynamic_data.py - Contains functions used by the deployment mechanisms to generate the dynamic data (IP addresses, coordinates for node placement, etc)
- gns3_query.py - Contains functions used to query different components of GNS3
- gns3_variables.py - Variables used in the deployment and application that are static. (Templates, Passwords, Names, etc)

### setup - Functions to configure initial services for the application

- sqlite_setup.py - Functions to setup the SQLite database, schemas, and tables

### use_case - Functions used to trigger predefined use cases

- use_cases.py

### vendor_specific_actions - Functions to interact with vendor APIs

- appneta_actions.py - Contains function that will configure the AppNeta monitoring points (IP addressing, routing, connecting to instance)
- versa_actions.py - Contains Versa specific API functions used to configure the Versa Director
- viptela_actions.py - Contains Viptela specific API functions used to configure the Viptela vManage

## Templates - HTML templates used by Flask to render the Web UI

### deployment - HTML files for the deployment pages of each version

- create_arista_evpn.html
- create_versa_appneta_sdwan.html
- create_viptela_cedge_appneta_sdwan.html
- create_viptela_vedge_appneta_sdwan.html

### use_case - HTML files for the use case pages

- uc_local.html - Used to control the use cases of the server local to the application deployment
- uc_remote.html - Used to control the use cases of remote servers
- uc_scenarios.html - Depracated
- **main.html - Main HTML page which contains links to the different deployment types and other helpful information**

## app.py - Contains the main of the application as well as all the Flask rendering and API endpoints

## Dockerfile - Used to build the Docker image

## README.md

## requirements.txt

Example workflow of the application deploying the Versa Lab:

1. Deploy application by using Docker - docker run -d -p 8085:8080 evanrogers719/gns3_auto_deploy:latest
    1. This will deploy the application and expose the container on port 8080 of the host, browse host_ip:8080 to access the app
    2. User selects the Versa version of deployment
    3. User enters required information and uploads needed device images if they dont exists on the GNS3 server
2. When the user clicks “Start Deployment”
    1. The javascript on the HTML page will first issue a call to the /api/config endpoint which places the values into the SQL database as well as handles the GNS3 project creation
    2. Once that call is returned successfully, the javascript makes another API call to the specific endpoint of the requested environment type (/api/tasks/start_versa_appneta_deploy)
    3. This will then call the function named *versa_appneta_deploy* contained in the file *modules/deployment/versa_appneta_deployment* 
    4. Then the javascript starts streaming the contents of the deployment logging table to the table on the page and refreshing every second.
3. The versa_appneta_deployment function then proceeds as such:
    1. It pulls data from the config table of the database
    2. It sets any variables necessary based on the user provided data
    3. Deletes any templates that would be used by the deployment and recreates them with the specified values
    4. Creates the dynamic networking objects
    5. Deploys the nodes into the lab environment
    6. Connects the nodes
    7. Creates the drawings
    8. Deploys the dynamically generated network files to the devices via GNS3 API
    9. Starts the nodes
    10. Deploys the clients
    11. Configures the base configuration on the Versa components utilizing telnet consoles
    12. Configures the Versa Director via API
    13. Onboards the Versa SDWAN site devices
    14. Configures the AppNeta Monitoring points