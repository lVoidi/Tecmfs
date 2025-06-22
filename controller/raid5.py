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
                    loaded_files = data.get('files', {})
                    self.file_metadata = {
                        file_id: FileMetadata(**metadata)
                        for file_id, metadata in loaded_files.items()
                    }
            except Exception as e:
                print(f"Error cargando metadatos: {e}")
    
    def _save_metadata(self):
        """Guardar metadatos a archivo"""
        try:
            with open(self.metadata_file, 'w') as f:
                metadata_to_save = {
                    file_id: metadata.model_dump()
                    for file_id, metadata in self.file_metadata.items()
                }
                json.dump({'files': metadata_to_save}, f, indent=2)
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
        file_id = str(uuid.uuid4())
        
        # Dividir datos en franjas (stripes) y bloques
        stripes = [content[i:i+self.block_size * (self.num_disks - 1)] for i in range(0, len(content), self.block_size * (self.num_disks - 1))]
        
        block_locations = {}
        parity_locations = {}

        for i, stripe_data in enumerate(stripes):
            data_blocks, parity_block = self._distribute_blocks(stripe_data, i)
            
            parity_disk_index = self._get_parity_disk(i)
            data_disk_indices = [j for j in range(self.num_disks) if j != parity_disk_index]
            
            # Distribuir y almacenar bloques de datos
            for j, block_data in enumerate(data_blocks):
                disk_index = data_disk_indices[j]
                disk_id = f"disk_{disk_index + 1}"
                block_id = self._get_block_id(file_id, f"{i}_{j}")
                
                self._store_block_to_disk(disk_id, block_id, block_data)
                block_locations[block_id] = disk_id

            # Almacenar bloque de paridad
            parity_disk_id = f"disk_{parity_disk_index + 1}"
            parity_block_id = self._get_block_id(file_id, f"parity_{i}")
            self._store_block_to_disk(parity_disk_id, parity_block_id, parity_block)
            parity_locations[parity_block_id] = parity_disk_id

        # Crear metadatos del archivo
        file_metadata = FileMetadata(
            file_id=file_id,
            filename=filename,
            size=len(content),
            uploaded_at=datetime.now().isoformat(),
            blocks=block_locations,
            parity_blocks=parity_locations
        )
        
        # Guardar metadatos
        self.file_metadata[file_id] = file_metadata
        self._save_metadata()
        
        return file_id
    
    def _store_block_to_disk(self, disk_id: str, block_id: str, data: bytes):
        """Almacenar un bloque en un disco específico haciendo una llamada HTTP."""
        disk_info = self.disk_nodes.get(disk_id)
        if not disk_info or disk_info.status != "online":
            print(f"Error: Disco {disk_id} no está disponible.")
            return

        try:
            payload = {"block_id": block_id, "data": data.hex()}
            response = requests.post(f"{disk_info.url}/store", json=payload, timeout=5)
            response.raise_for_status()  # Lanza una excepción para errores HTTP (4xx o 5xx)
            print(f"Bloque {block_id} almacenado exitosamente en {disk_id}.")
        except requests.exceptions.RequestException as e:
            print(f"Error almacenando bloque {block_id} en disco {disk_id}: {e}")
            # Marcar el disco como offline si falla la conexión
            self.disk_nodes[disk_id].status = "offline"

    def retrieve_file(self, file_id: str) -> Optional[Dict]:
        """Recuperar un archivo del sistema RAID 5"""
        if file_id not in self.file_metadata:
            return None
        
        metadata = self.file_metadata[file_id]
        
        # Recuperar bloques de datos
        content_blocks = {}
        for block_id, disk_id in metadata.blocks.items():
            block_data = self._retrieve_block_from_disk(block_id, disk_id)
            if block_data:
                content_blocks[block_id] = block_data
        
        # Si faltan bloques, intentar reconstruir usando paridad
        if len(content_blocks) < len(metadata.blocks):
            # TODO: Implementar la reconstrucción de datos
            print("Faltan bloques, se necesita reconstrucción (no implementado)")
            # data_blocks = self._reconstruct_data(metadata)
            raise HTTPException(status_code=500, detail="Fallo de disco y la reconstrucción no está implementada.")

        # Reconstruir archivo original en orden
        sorted_block_ids = sorted(metadata.blocks.keys())
        full_content = b''.join(content_blocks[block_id] for block_id in sorted_block_ids)
        
        # Remover padding
        original_size = metadata.size
        full_content = full_content[:original_size]

        return {
            'filename': metadata.filename,
            'content': full_content,
        }
    
    def _retrieve_block_from_disk(self, block_id: str, disk_id: str) -> Optional[bytes]:
        """Recuperar un bloque de un disco específico."""
        disk_info = self.disk_nodes.get(disk_id)
        if not disk_info or disk_info.status != "online":
            print(f"Error: Disco {disk_id} no está disponible para leer el bloque {block_id}.")
            # Marcar como offline si no lo estaba ya
            if disk_info: self.disk_nodes[disk_id].status = "offline"
            return None

        try:
            response = requests.get(f"{disk_info.url}/retrieve/{block_id}", timeout=5)
            if response.status_code == 200:
                hex_data = response.json().get("data")
                return bytes.fromhex(hex_data)
            elif response.status_code == 404:
                print(f"Error: Bloque {block_id} no encontrado en disco {disk_id} donde debería estar.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error recuperando bloque {block_id} de {disk_id}: {e}")
            self.disk_nodes[disk_id].status = "offline"
        
        return None
    
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
        
        # Eliminar bloques de datos y paridad
        all_blocks = metadata.blocks | metadata.parity_blocks
        for block_id, disk_id in all_blocks.items():
            self._delete_block_from_disk(block_id, disk_id)
        
        # Eliminar metadatos
        del self.file_metadata[file_id]
        self._save_metadata()
        
        return True
    
    def _delete_block_from_disk(self, block_id: str, disk_id: str):
        """Eliminar un bloque de un disco específico."""
        disk_info = self.disk_nodes.get(disk_id)
        if not disk_info or disk_info.status != "online":
            print(f"Info: Disco {disk_id} ya no está disponible para borrar el bloque {block_id}.")
            return

        try:
            response = requests.delete(f"{disk_info.url}/delete/{block_id}", timeout=5)
            if response.status_code not in [200, 404]:
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error eliminando bloque {block_id} de {disk_id}: {e}")
            self.disk_nodes[disk_id].status = "offline"
    
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