# main.py
from fastapi import FastAPI, HTTPException
import subprocess
import paramiko
from azure_config import compute_client, resource_client, network_client, subscription_id
import yaml
from pathlib import Path 


app = FastAPI()

@app.get("/")
async def root():
    return {"message": "K3s Cluster Setup API"}

# Endpoint to trigger VM creation
# centralindia myResourceGroup Standard_B1s azureuser MyPassword123
@app.post("/create-vms")
async def create_vms(vm_count: int, resource_group: str, location: str, vm_size: str, username: str, password: str):
    try:
        # Step 1: Create Resource Group
        resource_client.resource_groups.create_or_update(
            resource_group,
            {"location": location}
        )

        # Step 2: Create Network Security Group (NSG) with necessary inbound rules
        nsg_params = {
            "location": location,
            "security_rules": [
                {
                    "name": "AllowSSH",
                    "protocol": "Tcp",
                    "source_port_range": "*",
                    "destination_port_range": "22",
                    "source_address_prefix": "*",
                    "destination_address_prefix": "*",
                    "access": "Allow",
                    "priority": 100,
                    "direction": "Inbound"
                },
                {
                    "name": "AllowK3s",
                    "protocol": "Tcp",
                    "source_port_range": "*",
                    "destination_port_range": "6443",
                    "source_address_prefix": "*",
                    "destination_address_prefix": "*",
                    "access": "Allow",
                    "priority": 200,
                    "direction": "Inbound"
                },
                {
                    "name": "AllowPG",
                    "protocol": "Tcp",
                    "source_port_range": "*",
                    "destination_port_range": "30000",
                    "source_address_prefix": "*",
                    "destination_address_prefix": "*",
                    "access": "Allow",
                    "priority": 210,
                    "direction": "Inbound"
                },
            ]
        }
        nsg = network_client.network_security_groups.begin_create_or_update(
            resource_group,
            "myNSG",
            nsg_params
        ).result()

        # Step 3: Create Virtual Network and Subnet
        network_params = {
            "location": location,
            "address_space": {"address_prefixes": ["10.0.0.0/16"]}
        }
        network_client.virtual_networks.begin_create_or_update(
            resource_group,
            "myVnet",
            network_params
        ).result()

        subnet_params = {"address_prefix": "10.0.0.0/24"}
        subnet = network_client.subnets.begin_create_or_update(
            resource_group,
            "myVnet",
            "mySubnet",
            subnet_params
        ).result()

        # Step 4: Create VMs with unique Network Interfaces, Public IPs, and NSG
        vm_ips = []
        for i in range(vm_count):
            vm_name = f"myVM-{i+1}"

            # Create a unique Public IP with a DNS label for each VM
            dns_label = f"vm-dns-{i+1}-{resource_group.lower()}"
            public_ip_params = {
                "location": location,
                "sku": {"name": "Standard"},
                "public_ip_allocation_method": "Static",
                "dns_settings": {"domain_name_label": dns_label}  # DNS settings added here
            }
            public_ip = network_client.public_ip_addresses.begin_create_or_update(
                resource_group,
                f"myPublicIP-{i+1}",
                public_ip_params
            ).result()

            # Retrieve the fully qualified domain name (FQDN) after creation
            fqdn = public_ip.dns_settings.fqdn

            # Create unique Network Interface with NSG for each VM
            nic_name = f"myNic-{i+1}"
            nic_params = {
                "location": location,
                "ip_configurations": [{
                    "name": f"myIpConfig-{i+1}",
                    "subnet": {"id": subnet.id},
                    "public_ip_address": {"id": public_ip.id}
                }],
                "network_security_group": {"id": nsg.id}
            }
            nic = network_client.network_interfaces.begin_create_or_update(
                resource_group,
                nic_name,
                nic_params
            ).result()

            # Step 5: Create the VM with the unique NIC and Public IP
            vm_params = {
                "location": location,
                "hardware_profile": {"vm_size": vm_size},
                "storage_profile": {
                    "image_reference": {
                        "publisher": "Canonical",
                        "offer": "UbuntuServer",
                        "sku": "18.04-LTS",
                        "version": "latest"
                    }
                },
                "os_profile": {
                    "computer_name": vm_name,
                    "admin_username": username,
                    "admin_password": password
                },
                "network_profile": {
                    "network_interfaces": [{"id": nic.id}]
                }
            }

            compute_client.virtual_machines.begin_create_or_update(
                resource_group,
                vm_name,
                vm_params
            ).result()

            # Store the VM name, public IP, and FQDN
            vm_ips.append({"vm_name": vm_name, "public_ip": public_ip.ip_address, "dns_name": fqdn})

        return {"status": f"{vm_count} VMs created successfully with NSG and open ports", "vm_ips": vm_ips}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create VMs: {str(e)}")



    
def install_k3s_on_primary_node(ip_address, username, password):
    # SSH into the node and install k3s
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip_address, username=username, password=password)

    # K3s install command with embedded etcd for HA
    install_command = "curl -sfL https://get.k3s.io | sh -s - server --cluster-init --write-kubeconfig-mode 644"
    stdin, stdout, stderr = client.exec_command(install_command)
    print(stdout.read().decode())
    print(stderr.read().decode())

    # Retrieve the K3s token
    token_command = "sudo cat /var/lib/rancher/k3s/server/node-token"
    stdin, stdout, stderr = client.exec_command(token_command)
    token = stdout.read().decode().strip()
    error = stderr.read().decode().strip()

    client.close()

    if error:
        raise Exception(f"Error retrieving K3s token: {error}")

    return token

@app.post("/setup-k3s-primary")
async def setup_k3s_primary(ip_address: str, username: str, password: str):
    try:
        token = install_k3s_on_primary_node(ip_address, username, password)
        return {"status": "K3s installed on primary node", "token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set up K3s on primary node: {str(e)}")

def join_k3s_secondary_node(ip_address, username, password, token, server_ip):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip_address, username=username, password=password)

    # K3s agent join command
    join_command = f"curl -sfL https://get.k3s.io | K3S_URL=https://{server_ip}:6443 K3S_TOKEN={token} sh -s -"

    stdin, stdout, stderr = client.exec_command(join_command)
    print(stdout.read().decode())
    print(stderr.read().decode())
    client.close()

@app.post("/join-k3s-node")
async def join_k3s_node(ip_address: str, username: str, password: str, token: str, server_ip: str):
    try:
        join_k3s_secondary_node(ip_address, username, password, token, server_ip)
        return {"status": "Node joined to K3s cluster"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to join node to K3s cluster: {str(e)}")

# Add an endpoint to install Helm on the primary node.
def install_helm_on_node(ip_address, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip_address, username=username, password=password)

    # Command to install Helm
    helm_install_command = """
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    """

    stdin, stdout, stderr = client.exec_command(helm_install_command)
    print(stdout.read().decode())
    print(stderr.read().decode())
    client.close()

@app.post("/install-helm")
async def install_helm(ip_address: str, username: str, password: str):
    try:
        install_helm_on_node(ip_address, username, password)
        return {"status": "Helm installed on node"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to install Helm on node: {str(e)}")

# def add_helm_repo_and_update(ip_address, username, password):
#     client = paramiko.SSHClient()
#     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     client.connect(ip_address, username=username, password=password)

#     # Add and update CloudNativePG Helm repository
#     helm_repo_command = """
#     helm repo add cnpg https://cloudnative-pg.github.io/charts
#     helm repo update
#     helm install my-postgresql cnpg/cloudnative-pg --namespace default --create-namespace
#     """

#     stdin, stdout, stderr = client.exec_command(helm_repo_command)
#     print(stdout.read().decode())
#     print(stderr.read().decode())
#     client.close()

# @app.post("/add-helm-repo-cloudnativePG")
# async def add_helm_repo(ip_address: str, username: str, password: str):
#     try:
#         add_helm_repo_and_update(ip_address, username, password)
#         return {"status": "Helm repo added and updated"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to add Helm repo: {str(e)}")



# Endpoint to deploy CloudNativePG
# def deploy_cloudnativepg(ip_address, username, password):
#     client = paramiko.SSHClient()
#     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     client.connect(ip_address, username=username, password=password)

#     # Install CloudNativePG Helm chart
#     install_cnpg_command = """
#     helm install my-postgresql cnpg/cloudnative-pg --namespace default --create-namespace
#     """

#     stdin, stdout, stderr = client.exec_command(install_cnpg_command)
#     stdout_result = stdout.read().decode()
#     stderr_result = stderr.read().decode()

#     if stderr_result:
#         print("Error during deployment:", stderr_result)
#     else:
#         print("Deployment output:", stdout_result)

#     client.close()

# @app.post("/deploy-cloudnativepg")
# async def deploy_cloudnativepg_endpoint(ip_address: str, username: str, password: str):
#     try:
#         deploy_cloudnativepg(ip_address, username, password)
#         return {"status": "CloudNativePG deployed"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to deploy CloudNativePG: {str(e)}")

@app.post("/Clone-helm-chart/")
def clone_helm_chart(ip_address: str, username: str, password: str):
    try:
        # Establish SSH connection
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip_address, username=username, password=password)

        # Commands to execute
        commands = [
            "git clone https://github.com/Hemanth097/postgre-chart",           
        ]

        # Execute each command and capture the output
        for command in commands:
            stdin, stdout, stderr = client.exec_command(command)
            stdout_output = stdout.read().decode()
            stderr_output = stderr.read().decode()

            # Print outputs in the console
            print(f"Command: {command}")
            print(f"STDOUT:\n{stdout_output}")
            print(f"STDERR:\n{stderr_output}")

            # if stderr_output:
            #     raise Exception(f"Error executing {command}: {stderr_output}")

        # Close the connection
        client.close()  

        return {"status": "success", "message": "Commands executed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deploy-postgres/")
async def deploy_postgres(
    ip_address: str,
    username: str,
    password: str,
    user_name: str,
    db_name: str,
    db_password: str,
    storage_size: str,
    nodeport: str,
    replica_count: int = 1,
    autoscaling_enabled: bool = False,
    min_replicas: int = 1,
    max_replicas: int = 3,
    cpu_utilization: int = 80,
):
    try:
        

        # Establish SSH connection
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip_address, username=username, password=password)

        release_name = "postgres-chart"
        helm_chart_path = "./postgre-chart/postgres-chart-0.1.0.tgz"

        # Build Helm command with --set for dynamic values
        helm_command = (
            f"helm install {release_name} {helm_chart_path} "
            f"--set replicaCount={replica_count} "
            f"--set postgres.user={user_name} "
            f"--set postgres.password={db_password} "
            f"--set postgres.db={db_name} "
            f"--set postgres.storage.size={storage_size} "
            f"--set postgres.nodePort={nodeport} "
            f"--set service.type=NodePort "
            f"--set autoscaling.enabled={str(autoscaling_enabled).lower()} "
            f"--set autoscaling.minReplicas={min_replicas} "
            f"--set autoscaling.maxReplicas={max_replicas} "
            f"--set autoscaling.targetCPUUtilizationPercentage={cpu_utilization}"
        )

        # Single command to set KUBECONFIG and execute Helm
        command = (
            "export KUBECONFIG=/etc/rancher/k3s/k3s.yaml && " + helm_command
        )

        stdin, stdout, stderr = client.exec_command(command)
        stdout_output = stdout.read().decode()
        stderr_output = stderr.read().decode()

        # Log outputs
        print(f"Command: {command}")
        print(f"STDOUT:\n{stdout_output}")
        print(f"STDERR:\n{stderr_output}")

        # if stderr_output:
        #     raise Exception(f"Error executing {command}: {stderr_output}")

        # Close the connection
        client.close()

        return {"status": "success", "message": "PostgreSQL deployed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.post("/deploy_postgres/")
# async def deploy_postgres(ip_address: str, username: str, password: str, user_name : str, db_name : str, db_password :str, storage_size :str, nodeport :str):
#     try:
#         # Establish SSH connection
#         client = paramiko.SSHClient()
#         client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#         client.connect(ip_address, username=username, password=password)

#         values = {
#             "postgres": { 
#                 "user": user_name,
#                 "password": db_password,
#                 "db": db_name,
#                 "storage": {"size": storage_size},
#                 "nodePort": nodeport,
#             }
#         }

#         values_path = Path("temp-values.yaml")
#         with open(values_path, "w") as file:
#             yaml.dump(values, file, default_flow_style=False)
        
#         scp_command = f"scp temp-values.yaml {username}@{ip_address}:/tmp/temp-values.yaml"
#         subprocess.run(scp_command, shell=True, check=True)
        
#         release_name = "postgres-chart"
#         helm_chart_path = "./postgre-chart/postgres-chart-0.1.0.tgz"

#         helm_command = f"helm install {release_name} {helm_chart_path} --values /tmp/temp-values.yaml"

#         # Commands to execute
#         commands = [
#             "export KUBECONFIG=/etc/rancher/k3s/k3s.yaml",
#             helm_command,           
#         ]

#         # Execute each command and capture the output
#         for command in commands:
#             stdin, stdout, stderr = client.exec_command(command)
#             stdout_output = stdout.read().decode()
#             stderr_output = stderr.read().decode()

#             # Print outputs in the console
#             print(f"Command: {command}")
#             print(f"STDOUT:\n{stdout_output}")
#             print(f"STDERR:\n{stderr_output}")

#             if stderr_output:
#                 raise Exception(f"Error executing {command}: {stderr_output}")

#         # Close the connection
#         client.close()  

#         return {"status": "success", "message": "Commands executed successfully."}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    
    def execute_ssh_command(ip: str, username: str, password: str, commands: list):
        """Execute commands on a remote server via SSH."""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=ip, username=username, password=password)
            for command in commands:
                stdin, stdout, stderr = ssh.exec_command("export KUBECONFIG=/etc/rancher/k3s/k3s.yaml && "+ command)
                stdout.channel.recv_exit_status()  # Wait for command to finish
                output = stdout.read().decode()
                error = stderr.read().decode()
                print("stdout\n", output)
                print("error\n",error)
                # if error:
                #     raise Exception(f"Error executing command: {error}")
            ssh.close()
            return output
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/install-monitoring/")
    def install_monitoring(ip: str, username: str, password: str):
        """Install Prometheus and Grafana on the remote VM."""
        commands = [
            "helm repo add prometheus-community https://prometheus-community.github.io/helm-charts && helm repo update",
            "helm repo add grafana https://grafana.github.io/helm-charts && helm repo update",
            # Install Prometheus
            "helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace",
            # Install Grafana
            "helm install grafana grafana/grafana --namespace monitoring",
            # Change Grafana to NodePort
            "kubectl -n monitoring patch svc grafana --type='json' -p '[{\"op\":\"replace\",\"path\":\"/spec/type\",\"value\":\"NodePort\"}]'"
        ]
        
        # Execute the commands on the remote VM
        try:
            result = execute_ssh_command(ip, username, password, commands)
            return {"message": "Prometheus and Grafana installed successfully.", "details": result}
        except HTTPException as e:
            return {"error": e.detail}
        #