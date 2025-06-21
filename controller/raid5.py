import hashlib
import json
import os
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import uuid

from .schemas import FileMetadata, SystemStatus, BlockInfo, DiskNodeInfo

class RAID5Manager:
    """Gestor del sistema RAID 5 para TECMFS"""
    
    def __init__(self, block_size: int = 4096, num_disks: int = 4):
        self.block_size = block_size  # 4KB por defecto
        self.num_disks = num_disks
        self.disk_nodes = {}  # {disk_id: DiskNodeInfo}
        self.file_metadata = {}  # {file_id: FileMetadata}
        self.metadata_file = "metadata.json"
        
        # Configurar nodos de disco (esto se conectará con los Disk Nodes de la Persona 2)
        self._setup_disk_nodes()
        self._load_metadata()
    
    def _setup_disk_nodes(self):
        """Configurar los nodos de disco (simulado por ahora)"""
        base_url = "http://localhost"
        for i in range(self.num_disks):
            disk_id = f"disk_{i+1}"
            port = 8001 + i  # Cada disco en puerto diferente
            self.disk_nodes[disk_id] = DiskNodeInfo(
                disk_id=disk_id,
                url=f"{base_url}:{port}",
                status="online",
                total_space=1024 * 1024 * 1024,  # 1GB
                used_space=0,
                available_space=1024 * 1024 * 1024
            )
    
    def _load_metadata(self):
        """Cargar metadatos desde archivo"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.file_metadata = data.get('files', {})
            except Exception as e:
                print(f"Error cargando metadatos: {e}")
    
    def _save_metadata(self):
        """Guardar metadatos a archivo"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump({'files': self.file_metadata}, f, indent=2)
        except Exception as e:
            print(f"Error guardando metadatos: {e}")
    
    def _calculate_parity(self, data_blocks: List[bytes]) -> bytes:
        """Calcular bloque de paridad usando XOR"""
        if not data_blocks:
            return b''
        
        parity = data_blocks[0]
        for block in data_blocks[1:]:
            # Asegurar que todos los bloques tengan la misma longitud
            if len(block) < len(parity):
                block = block + b'\x00' * (len(parity) - len(block))
            elif len(block) > len(parity):
                parity = parity + b'\x00' * (len(block) - len(parity))
            
            # XOR bit a bit
            parity = bytes(a ^ b for a, b in zip(parity, block))
        
        return parity
    
    def _distribute_blocks(self, data: bytes, stripe_number: int) -> Tuple[List[bytes], bytes]:
        """Distribuir datos en bloques y calcular paridad"""
        blocks = []
        
        # Dividir datos en bloques del tamaño especificado
        for i in range(0, len(data), self.block_size):
            block = data[i:i + self.block_size]
            # Rellenar el último bloque si es necesario
            if len(block) < self.block_size:
                block = block + b'\x00' * (self.block_size - len(block))
            blocks.append(block)
        
        # Calcular paridad
        parity_block = self._calculate_parity(blocks)
        
        return blocks, parity_block
    
    def _get_parity_disk(self, stripe_number: int) -> int:
        """Determinar qué disco contiene la paridad para una franja específica"""
        # Distribución rotativa de paridad (RAID 5)
        return stripe_number % self.num_disks
    
    def _get_block_id(self, file_id: str, block_index: str) -> str:
        """Generar ID único para un bloque"""
        return f"{file_id}_block_{block_index}"
    
    def store_file(self, filename: str, content: bytes) -> str:
        """Almacenar un archivo usando RAID 5"""
        # Generar ID único para el archivo
        file_id = str(uuid.uuid4())
        
        # Dividir datos en bloques y calcular paridad
        data_blocks, parity_block = self._distribute_blocks(content, 0)
        
        # Distribuir bloques entre discos
        block_ids = []
        parity_block_ids = []
        
        for i, block in enumerate(data_blocks):
            # Determinar disco para este bloque
            parity_disk = self._get_parity_disk(i)
            data_disks = [j for j in range(self.num_disks) if j != parity_disk]
            
            # Distribuir bloques de datos
            for j, data_block in enumerate(data_blocks):
                disk_index = data_disks[j % len(data_disks)]
                disk_id = f"disk_{disk_index + 1}"
                block_id = self._get_block_id(file_id, str(j))
                
                # Aquí se enviaría el bloque al Disk Node correspondiente
                # Por ahora, simulamos el almacenamiento
                self._store_block_to_disk(disk_id, block_id, data_block)
                block_ids.append(block_id)
            
            # Almacenar bloque de paridad
            parity_block_id = self._get_block_id(file_id, f"parity_{i}")
            parity_disk_id = f"disk_{parity_disk + 1}"
            self._store_block_to_disk(parity_disk_id, parity_block_id, parity_block)
            parity_block_ids.append(parity_block_id)
        
        # Crear metadatos del archivo
        file_metadata = FileMetadata(
            file_id=file_id,
            filename=filename,
            size=len(content),
            uploaded_at=datetime.now().isoformat(),
            blocks=block_ids,
            parity_blocks=parity_block_ids
        )
        
        # Guardar metadatos
        self.file_metadata[file_id] = file_metadata
        self._save_metadata()
        
        return file_id
    
    def _store_block_to_disk(self, disk_id: str, block_id: str, data: bytes):
        """Almacenar un bloque en un disco específico"""
        # Por ahora simulamos el almacenamiento
        # En la implementación real, esto haría una llamada HTTP al Disk Node
        print(f"Almacenando bloque {block_id} en disco {disk_id}")
        
        # Simular llamada HTTP al Disk Node
        try:
            disk_info = self.disk_nodes.get(disk_id)
            if disk_info and disk_info.status == "online":
                # Aquí iría la llamada real al Disk Node
                # response = requests.post(f"{disk_info.url}/store", 
                #                         json={"block_id": block_id, "data": data.hex()})
                pass
        except Exception as e:
            print(f"Error almacenando en disco {disk_id}: {e}")
    
    def retrieve_file(self, file_id: str) -> Optional[Dict]:
        """Recuperar un archivo del sistema RAID 5"""
        if file_id not in self.file_metadata:
            return None
        
        metadata = self.file_metadata[file_id]
        
        # Recuperar bloques de datos
        data_blocks = []
        for block_id in metadata.blocks:
            block_data = self._retrieve_block_from_disk(block_id)
            if block_data:
                data_blocks.append(block_data)
        
        # Si faltan bloques, intentar reconstruir usando paridad
        if len(data_blocks) < len(metadata.blocks):
            data_blocks = self._reconstruct_data(metadata)
        
        # Reconstruir archivo original
        if data_blocks:
            content = b''.join(data_blocks)
            # Remover padding del último bloque
            content = content.rstrip(b'\x00')
            
            return {
                'filename': metadata.filename,
                'content': content,
                'size': metadata.size
            }
        
        return None
    
    def _retrieve_block_from_disk(self, block_id: str) -> Optional[bytes]:
        """Recuperar un bloque de un disco"""
        # Simular recuperación de bloque
        # En la implementación real, esto haría una llamada HTTP al Disk Node
        print(f"Recuperando bloque {block_id}")
        return b'data_simulated'  # Datos simulados
    
    def _reconstruct_data(self, metadata: FileMetadata) -> List[bytes]:
        """Reconstruir datos usando bloques de paridad"""
        # Implementación de reconstrucción RAID 5
        # Por ahora retornamos datos simulados
        return [b'data_reconstructed'] * len(metadata.blocks)
    
    def delete_file(self, file_id: str) -> bool:
        """Eliminar un archivo del sistema"""
        if file_id not in self.file_metadata:
            return False
        
        metadata = self.file_metadata[file_id]
        
        # Eliminar bloques de datos
        for block_id in metadata.blocks + metadata.parity_blocks:
            self._delete_block_from_disk(block_id)
        
        # Eliminar metadatos
        del self.file_metadata[file_id]
        self._save_metadata()
        
        return True
    
    def _delete_block_from_disk(self, block_id: str):
        """Eliminar un bloque de un disco"""
        # Simular eliminación de bloque
        print(f"Eliminando bloque {block_id}")
    
    def list_files(self) -> List[FileMetadata]:
        """Listar todos los archivos almacenados"""
        return list(self.file_metadata.values())
    
    def search_files(self, query: str) -> List[FileMetadata]:
        """Buscar archivos por nombre"""
        results = []
        query_lower = query.lower()
        
        for metadata in self.file_metadata.values():
            if query_lower in metadata.filename.lower():
                results.append(metadata)
        
        return results
    
    def get_system_status(self) -> SystemStatus:
        """Obtener el estado del sistema RAID 5"""
        total_disks = len(self.disk_nodes)
        available_disks = sum(1 for disk in self.disk_nodes.values() if disk.status == "online")
        failed_disks = total_disks - available_disks
        
        total_space = sum(disk.total_space for disk in self.disk_nodes.values())
        used_space = sum(disk.used_space for disk in self.disk_nodes.values())
        available_space = total_space - used_space
        
        disk_status = {disk_id: disk.status for disk_id, disk in self.disk_nodes.items()}
        
        return SystemStatus(
            total_disks=total_disks,
            available_disks=available_disks,
            failed_disks=failed_disks,
            total_space=total_space,
            used_space=used_space,
            available_space=available_space,
            disk_status=disk_status
        ) 