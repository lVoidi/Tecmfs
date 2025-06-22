from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class FileMetadata(BaseModel):
    """Modelo para metadatos de archivos"""
    file_id: str
    filename: str
    size: int
    uploaded_at: str
    blocks: Dict[str, str]  # Mapeo de block_id a disk_id
    parity_blocks: Dict[str, str]  # Mapeo de parity_block_id a disk_id

class SystemStatus(BaseModel):
    """Modelo para el estado del sistema RAID 5"""
    total_disks: int
    available_disks: int
    failed_disks: int
    total_space: int
    used_space: int
    available_space: int
    disk_status: Dict[str, str]  # Estado de cada disco
    raid_level: str = "RAID 5"

class FileUploadResponse(BaseModel):
    """Modelo para respuesta de subida de archivo"""
    file_id: str
    filename: str
    size: int
    uploaded_at: str
    message: str

class BlockInfo(BaseModel):
    """Modelo para información de un bloque"""
    block_id: str
    disk_id: str
    data: bytes
    is_parity: bool = False

class DiskNodeInfo(BaseModel):
    """Modelo para información de un nodo de disco"""
    disk_id: str
    url: str
    status: str  # "online", "offline", "failed"
    total_space: int
    used_space: int
    available_space: int

class BlockStatus(BaseModel):
    block_id: str
    disk_id: str
    type: str  # 'data' o 'parity'

class FileBlockStatus(BaseModel):
    file_id: str
    filename: str
    blocks: List[BlockStatus] 