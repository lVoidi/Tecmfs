import os
from typing import List

# Configuración del servidor
HOST = "0.0.0.0"
PORT = 8000
DEBUG = True

# Configuración RAID 5
BLOCK_SIZE = 4096  # 4KB
NUM_DISKS = 4
MIN_DISKS_FOR_RAID5 = 4

# Configuración de Disk Nodes
DISK_NODES = [
    {"id": "disk_1", "url": "http://localhost:8001", "port": 8001},
    {"id": "disk_2", "url": "http://localhost:8002", "port": 8002},
    {"id": "disk_3", "url": "http://localhost:8003", "port": 8003},
    {"id": "disk_4", "url": "http://localhost:8004", "port": 8004},
]

# Configuración de almacenamiento
METADATA_FILE = "metadata.json"
TEMP_DIR = "temp"
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB

# Configuración de timeout para llamadas HTTP
HTTP_TIMEOUT = 30

# Configuración de logs
LOG_LEVEL = "INFO"
LOG_FILE = "controller.log" 