

K3s Cluster Setup and PostgreSQL Deployment API Documentation:
=============================================================
Overview
========
This API provides a streamlined way to create a highly available Kubernetes (K3s) cluster on Azure VMs, install Helm, and deploy PostgreSQL using Helm charts.

Endpoints:
===========
1. Root Endpoint:
================
URL: /
Method: GET
Description: Health check for the API.



2. Create Virtual Machines
==========================
URL: /create-vms
Method: POST
Description: Creates VMs on Azure with a resource group, network security group (NSG), virtual network, and subnet.
Request Parameters:
vm_count: Number of VMs to create.
resource_group: Name of the Azure resource group.
location: Azure region (e.g., centralindia).
vm_size: Azure VM size (e.g., Standard_B1s).
username: Admin username for the VM.
password: Admin password for the VM.
response:
--------
{
  "status": "2 VMs created successfully with NSG and open ports",
  "vm_ips": [
    {"vm_name": "myVM-1", "public_ip": "x.x.x.x", "dns_name": "vm-dns-1"},
    {"vm_name": "myVM-2", "public_ip": "y.y.y.y", "dns_name": "vm-dns-2"}
  ]
}




3. Setup K3s on Primary Node:
============================
URL: /setup-k3s-primary
Method: POST
Description: Installs K3s on the primary node and retrieves the K3s token.
Request Parameters:
ip_address: Primary VM IP address.
username: VM username.
password: VM password.
Response:
--------
{
  "status": "K3s installed on primary node",
  "token": "abc123..."
}



4. Join Secondary Nodes to K3s
URL: /join-k3s-node
Method: POST
Description: Adds a secondary node to the K3s cluster using the primary node's token.
Request Parameters:
ip_address: Secondary VM IP address.
username: VM username.
password: VM password.
token: Token from the primary node.
server_ip: Primary node's IP address.
Response:
---------
{
  "status": "K3s installed on primary node",
  "token": "abc123..."
}



Here’s a simplified document explaining the FastAPI-based K3s Cluster Setup and PostgreSQL Deployment API.

K3s Cluster Setup and PostgreSQL Deployment API Documentation
Overview
This API provides a streamlined way to create a highly available Kubernetes (K3s) cluster on Azure VMs, install Helm, and deploy PostgreSQL using Helm charts.

Endpoints
1. Root Endpoint
URL: /
Method: GET
Description: Health check for the API.
Response:
json
Copy code
{
  "message": "K3s Cluster Setup API"
}
2. Create Virtual Machines
URL: /create-vms
Method: POST
Description: Creates VMs on Azure with a resource group, network security group (NSG), virtual network, and subnet.
Request Parameters:
vm_count: Number of VMs to create.
resource_group: Name of the Azure resource group.
location: Azure region (e.g., centralindia).
vm_size: Azure VM size (e.g., Standard_B1s).
username: Admin username for the VM.
password: Admin password for the VM.
Response:
json
Copy code
{
  "status": "2 VMs created successfully with NSG and open ports",
  "vm_ips": [
    {"vm_name": "myVM-1", "public_ip": "x.x.x.x", "dns_name": "vm-dns-1"},
    {"vm_name": "myVM-2", "public_ip": "y.y.y.y", "dns_name": "vm-dns-2"}
  ]
}
3. Setup K3s on Primary Node
URL: /setup-k3s-primary
Method: POST
Description: Installs K3s on the primary node and retrieves the K3s token.
Request Parameters:
ip_address: Primary VM IP address.
username: VM username.
password: VM password.
Response:
json
Copy code
{
  "status": "K3s installed on primary node",
  "token": "abc123..."
}
4. Join Secondary Nodes to K3s
URL: /join-k3s-node
Method: POST
Description: Adds a secondary node to the K3s cluster using the primary node's token.
Request Parameters:
ip_address: Secondary VM IP address.
username: VM username.
password: VM password.
token: Token from the primary node.
server_ip: Primary node's IP address.
Response:
--------
{
  "status": "Node joined to K3s cluster"
}



6. Clone Helm Chart Repository
URL: /Clone-helm-chart
Method: POST
Description: Clones the PostgreSQL Helm chart repository onto the VM.
Request Parameters:
ip_address: VM IP address.
username: VM username.
password: VM password.
Response:
---------
{
  "status": "success",
  "message": "Commands executed successfully."
}


7. Deploy PostgreSQL
URL: /deploy-postgres
Method: POST
Description: Deploys PostgreSQL on the K3s cluster using Helm.
Request Parameters:
ip_address: Primary node IP address.
username: VM username.
password: VM password.
user_name: PostgreSQL username.
db_name: PostgreSQL database name.
db_password: PostgreSQL password.
storage_size: Storage size (e.g., 10Gi).
nodeport: NodePort for PostgreSQL service.
replica_count: Number of replicas (default: 1).
autoscaling_enabled: Enable autoscaling (default: false).
min_replicas: Minimum replicas (default: 1).
max_replicas: Maximum replicas (default: 3).
cpu_utilization: CPU utilization threshold for autoscaling (default: 80).
Response:
---------
{
  "status": "success",
  "message": "PostgreSQL deployed successfully."
}


9. Install Monitoring
Endpoint:
POST /install-monitoring/

Description:
Installs Prometheus and Grafana on a remote Kubernetes cluster.

Request Parameters:

ip (string):
The IP address of the remote server hosting the Kubernetes cluster.

username (string):
The SSH username for connecting to the remote server.

password (string):
The SSH password for connecting to the remote server.
Response:
---------
{
  "message": "Prometheus and Grafana installed successfully.",
  "details": "<Command execution output>"
}







Steps to Execute
================
Create VMs using /create-vms.
Install K3s on the primary node using /setup-k3s-primary.
Join secondary nodes using /join-k3s-node.
Install Helm on the primary node using /install-helm.
Clone Helm chart repository using /Clone-helm-chart.
Deploy PostgreSQL using /deploy-postgres.



Technologies Used
==================
FastAPI: RESTful API framework.
Azure SDK for Python: Azure resource management.
K3s: Lightweight Kubernetes.
Helm: Kubernetes package manager.
Paramiko: Remote SSH execution.
pydantic :validations



Architecture Diagram
=======================
![alt text](<WhatsApp Image 2024-11-22 at 19.18.37_9151feda-1.jpg>)
