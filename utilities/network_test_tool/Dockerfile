FROM gns3/ubuntu:focal

RUN apt-get update && apt-get install -y snmp iperf3 nuttcp
RUN apt-get update && apt-get install -y python3-pip
RUN pip install --no-cache-dir --pre scapy[basic]

COPY netflow_forwarder_single.py /home/scripts/netflow_forwarder_single.py
COPY netflow_forwarder_dual.py /home/scripts/netflow_forwarder_dual.py
COPY traffic_generator.py /home/scripts/traffic_generator.py

WORKDIR /home

CMD ["bash"]