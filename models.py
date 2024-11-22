from pydantic import BaseModel, Field

class ipinput(BaseModel):
    ip_address : str
    username : str = Field(default="azureuser")
    password : str = Field(default="MyPassword123")

class vmcreation(BaseModel):
    vm_count : int
    rg : str
    username : str = Field(default="azureuser")
    password : str = Field(default="MyPassword123")
    location: str = Field(default="centralindia")
    vm_size: str = Field(default="Standard_B2s_v2")

class joinNode(BaseModel):
    ip_address : str
    username : str = Field(default="azureuser")
    password : str = Field(default="MyPassword123")
    token : str
    server_ip : str

class deploypg(BaseModel):
    ip_address: str
    username: str = Field(default="azureuser")
    password: str = Field(default="MyPassword123")
    user_name: str = Field(default="user")
    db_name: str = Field(default="db")
    db_password: str = Field(default="password")
    storage_size: str = Field(default="1Gi")
    nodeport: int = Field(default=30000)
    replica_count: int = Field(default=1)
    autoscaling_enabled: bool = Field(default=False)
    min_replicas: int = Field(default=1)
    max_replicas: int = Field(default=3)
    cpu_utilization: int = Field(default=80)

