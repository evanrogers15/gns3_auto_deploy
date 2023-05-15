# Deployment Settings
project_name = "arista_deploy"
vedge_count = 0
client_every = 1
configure_mgmt_tap = 0
tap_name = 'tap1'
mgmt_network_address = '172.16.3.'

# Controls -- Set desired action value to 1
deploy_new_gns3_project = 1
use_existing_gns3_project = 0
cleanup_gns3 = 0
test_lab = 0

# region GNS3 Server Definition
er_test_lab_02 = [
 {
     "GNS3 Server": "100.92.8.44",
     "Management GNS3": "100.101.213.21",
     "Workload GNS3": "100.92.8.44",
     "Server Name": "er_test_lab_02",
     "Server Port": "80",
     "vManage API IP": "100.92.8.44"
 }
]
er_test_gns3_02 = [
 {
     "GNS3 Server": "100.96.248.43",
     "Management GNS3": "100.101.213.21",
     "Workload GNS3": "100.92.8.44",
     "Server Name": "er_test_lab_02",
     "Server Port": "80",
     "vManage API IP": "100.92.8.44"
 }
]
boot_pod1_4_sdwan_server = [
 {
     "GNS3 Server": "100.101.213.21",
     "Management GNS3": "100.101.213.21",
     "Workload GNS3": "100.92.8.44",
     "Server Name": "boot-pod1-4-sdwan-server",
     "Server Port": "80",
     "vManage API IP": "100.92.8.44"
 }
]
local_server = [
 {
     "GNS3 Server": "127.0.0.1",
     "Server Name": "boot-pod1-4-sdwan-server",
     "Server Port": "80",
     "vManage API IP": "172.16.2.2"
 }
]
ss_lab_gns3_01 = [
 {
     "GNS3 Server": "10.210.242.19",
     "Server Name": "ss-lab-gns3-01",
     "Server Port": "80",
     "vManage API IP": "172.16.2.2"
 }
]
er_test_01 = [
 {
     "GNS3 Server": "10.210.242.13",
     "Server Name": "er-test-01",
     "Server Port": "80",
     "vManage API IP": "172.16.2.2"
 }
]

# endregion
gns3_server_data = er_test_01

# region City Data
city_data = {
        "vEdge_001": {"city": "NewYork", "latitude": 40.712776, "longitude": -74.005974},
        "vEdge_002": {"city": "LosAngeles", "latitude": 34.052235, "longitude": -118.243683},
        "vEdge_003": {"city": "Chicago", "latitude": 41.878113, "longitude": -87.629799},
        "vEdge_004": {"city": "Houston", "latitude": 29.760427, "longitude": -95.369804},
        "vEdge_005": {"city": "Phoenix", "latitude": 33.448376, "longitude": -112.074036},
        "vEdge_006": {"city": "Philadelphia", "latitude": 39.952583, "longitude": -75.165222},
        "vEdge_007": {"city": "SanAntonio", "latitude": 29.424122, "longitude": -98.493628},
        "vEdge_008": {"city": "SanDiego", "latitude": 32.715736, "longitude": -117.161087},
        "vEdge_009": {"city": "Dallas", "latitude": 32.776665, "longitude": -96.796989},
        "vEdge_010": {"city": "SanJose", "latitude": 37.338207, "longitude": -121.886329},
        "vEdge_011": {"city": "Paris", "latitude": 48.856613, "longitude": 2.352222},
        "vEdge_012": {"city": "London", "latitude": 51.507351, "longitude": -0.127758},
        "vEdge_013": {"city": "Barcelona", "latitude": 41.385064, "longitude": 2.173404},
        "vEdge_014": {"city": "Rome", "latitude": 41.902782, "longitude": 12.496366},
        "vEdge_015": {"city": "Berlin", "latitude": 52.520008, "longitude": 13.404954},
        "vEdge_016": {"city": "Vienna", "latitude": 48.208176, "longitude": 16.373819},
        "vEdge_017": {"city": "Amsterdam", "latitude": 52.370216, "longitude": 4.895168},
        "vEdge_018": {"city": "Munich", "latitude": 48.135125, "longitude": 11.581981},
        "vEdge_019": {"city": "Madrid", "latitude": 40.416775, "longitude": -3.703790},
        "vEdge_020": {"city": "Zurich", "latitude": 47.376887, "longitude": 8.541694},
        "vEdge_021": {"city": "Edinburgh", "latitude": 55.953251, "longitude": -3.188267},
        "vEdge_022": {"city": "Athens", "latitude": 37.983810, "longitude": 23.727539},
        "vEdge_023": {"city": "Dublin", "latitude": 53.349805, "longitude": -6.260310},
        "vEdge_024": {"city": "Stockholm", "latitude": 59.329323, "longitude": 18.068581},
        "vEdge_025": {"city": "Brussels", "latitude": 50.850346, "longitude": 4.351721},
        "vEdge_026": {"city": "Copenhagen", "latitude": 55.676097, "longitude": 12.568337},
        "vEdge_027": {"city": "Oslo", "latitude": 59.913869, "longitude": 10.752245},
        "vEdge_028": {"city": "Helsinki", "latitude": 60.169856, "longitude": 24.938379},
        "vEdge_029": {"city": "Lisbon", "latitude": 38.722252, "longitude": -9.139337},
        "vEdge_030": {"city": "Venice", "latitude": 45.440847, "longitude": 12.315515},
        "vEdge_031": {"city": "Mumbai", "latitude": 19.076090, "longitude": 72.877426},
        "vEdge_032": {"city": "Delhi", "latitude": 28.704060, "longitude": 77.102493},
        "vEdge_033": {"city": "Bangalore", "latitude": 12.971599, "longitude": 77.594566},
        "vEdge_034": {"city": "Hyderabad", "latitude": 17.385044, "longitude": 78.486671},
        "vEdge_035": {"city": "Chennai", "latitude": 13.082680, "longitude": 80.270721},
        "vEdge_036": {"city": "Kolkata", "latitude": 22.572645, "longitude": 88.363892},
        "vEdge_037": {"city": "Ahmedabad", "latitude": 23.022505, "longitude": 72.571365},
        "vEdge_038": {"city": "Pune", "latitude": 18.520430, "longitude": 73.856743},
        "vEdge_039": {"city": "Jaipur", "latitude": 26.912434, "longitude": 75.787271},
        "vEdge_040": {"city": "Lucknow", "latitude": 26.846693, "longitude": 80.946166},
        "vEdge_041": {"city": "Kanpur", "latitude": 26.449923, "longitude": 80.331871},
        "vEdge_042": {"city": "Nagpur", "latitude": 21.145800, "longitude": 79.088155},
        "vEdge_043": {"city": "Visakhapatnam", "latitude": 17.686815, "longitude": 83.218483},
        "vEdge_044": {"city": "Bhopal", "latitude": 23.259933, "longitude": 77.412615},
        "vEdge_045": {"city": "Patna", "latitude": 25.594095, "longitude": 85.137566},
        "vEdge_046": {"city": "Sydney", "latitude": -33.865143, "longitude": 151.209900},
        "vEdge_047": {"city": "Melbourne", "latitude": -37.813628, "longitude": 144.963058},
        "vEdge_048": {"city": "Brisbane", "latitude": -27.469771, "longitude": 153.025124},
        "vEdge_049": {"city": "Perth", "latitude": -31.953512, "longitude": 115.857048},
        "vEdge_050": {"city": "Adelaide", "latitude": -34.928499, "longitude": 138.600746},
        "vEdge_051": {"city": "GoldCoast", "latitude": -28.016666, "longitude": 153.399994},
        "vEdge_052": {"city": "Newcastle", "latitude": -32.926689, "longitude": 151.778916},
        "vEdge_053": {"city": "Canberra", "latitude": -35.282001, "longitude": 149.128998},
        "vEdge_054": {"city": "Wollongong", "latitude": -34.424999, "longitude": 150.893555},
        "vEdge_055": {"city": "Geelong", "latitude": -38.149918, "longitude": 144.361718},
        "vEdge_056": {"city": "Hobart", "latitude": -42.882137, "longitude": 147.327194},
        "vEdge_057": {"city": "Townsville", "latitude": -19.258965, "longitude": 146.816956},
        "vEdge_058": {"city": "Cairns", "latitude": -16.920334, "longitude": 145.770889},
        "vEdge_059": {"city": "Toowoomba", "latitude": -27.560560, "longitude": 151.953796},
        "vEdge_060": {"city": "Darwin", "latitude": -12.462827, "longitude": 130.841782},
        "vEdge_061": {"city": "Berlin", "latitude": 52.520008, "longitude": 13.404954},
        "vEdge_062": {"city": "Hamburg", "latitude": 53.551086, "longitude": 9.993682},
        "vEdge_063": {"city": "Munich", "latitude": 48.135125, "longitude": 11.581981},
        "vEdge_064": {"city": "Cologne", "latitude": 50.937531, "longitude": 6.960279},
        "vEdge_065": {"city": "Frankfurt", "latitude": 50.110924, "longitude": 8.682127},
        "vEdge_066": {"city": "Stuttgart", "latitude": 48.775846, "longitude": 9.182932},
        "vEdge_067": {"city": "Dusseldorf", "latitude": 51.227741, "longitude": 6.773456},
        "vEdge_068": {"city": "Dortmund", "latitude": 51.513587, "longitude": 7.465298},
        "vEdge_069": {"city": "Essen", "latitude": 51.458426, "longitude": 7.014088},
        "vEdge_070": {"city": "Leipzig", "latitude": 51.339695, "longitude": 12.373075},
        "vEdge_071": {"city": "Bremen", "latitude": 53.079296, "longitude": 8.801694},
        "vEdge_072": {"city": "Dresden", "latitude": 51.050409, "longitude": 13.737262},
        "vEdge_073": {"city": "Hanover", "latitude": 52.375892, "longitude": 9.732010},
        "vEdge_074": {"city": "Nuremberg", "latitude": 49.452030, "longitude": 11.076750},
        "vEdge_075": {"city": "Duisburg", "latitude": 51.434407, "longitude": 6.762329},
        "vEdge_076": {"city": "Saskatoon", "latitude": 52.1332, "longitude": -106.6700},
        "vEdge_077": {"city": "Regina", "latitude": 50.4452, "longitude": -104.6189},
        "vEdge_078": {"city": "Sherbrooke", "latitude": 45.4000, "longitude": -71.9000},
        "vEdge_079": {"city": "St.John's", "latitude": 47.5615, "longitude": -52.7126},
        "vEdge_080": {"city": "Saguenay", "latitude": 48.4168, "longitude": -71.0682},
        "vEdge_081": {"city": "Trois-Rivieres", "latitude": 46.3508, "longitude": -72.5461},
        "vEdge_082": {"city": "Kelowna", "latitude": 49.8879, "longitude": -119.4960},
        "vEdge_083": {"city": "Abbotsford", "latitude": 49.0579, "longitude": -122.2526},
        "vEdge_084": {"city": "Kingston", "latitude": 44.2312, "longitude": -76.4860},
        "vEdge_085": {"city": "Guelph", "latitude": 43.5448, "longitude": -80.2482},
        "vEdge_086": {"city": "Moncton", "latitude": 46.0878, "longitude": -64.7782},
        "vEdge_087": {"city": "Thunder Bay", "latitude": 48.3809, "longitude": -89.2477},
        "vEdge_088": {"city": "Saint John", "latitude": 45.2733, "longitude": -66.0633},
        "vEdge_089": {"city": "Peterborough", "latitude": 44.3000, "longitude": -78.3167},
        "vEdge_090": {"city": "Lethbridge", "latitude": 49.6935, "longitude": -112.8418},
        "vEdge_091": {"city": "BuenosAires", "latitude": -34.6037, "longitude": -58.3816},
        "vEdge_092": {"city": "Rio de Janeiro", "latitude": -22.9068, "longitude": -43.1729},
        "vEdge_093": {"city": "Lima", "latitude": -12.0464, "longitude": -77.0428},
        "vEdge_094": {"city": "Bogota", "latitude": 4.7109, "longitude": -74.0721},
        "vEdge_095": {"city": "Santiago", "latitude": -33.4489, "longitude": -70.6693},
        "vEdge_096": {"city": "Brasilia", "latitude": -15.7942, "longitude": -47.8822},
        "vEdge_097": {"city": "Salvador", "latitude": -12.9722, "longitude": -38.5014},
        "vEdge_098": {"city": "Fortaleza", "latitude": -3.7319, "longitude": -38.5267},
        "vEdge_099": {"city": "Recife", "latitude": -8.0543, "longitude": -34.8813},
        "vEdge_100": {"city": "Montevideo", "latitude": -34.9011, "longitude": -56.1645},
        "vEdge_101": {"city": "SaoPaulo", "latitude": -23.5505, "longitude": -46.6333},
    }
delete_node_name = ''
# endregion
