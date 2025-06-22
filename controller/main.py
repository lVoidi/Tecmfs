from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import uvicorn
from typing import List, Optional
import os
import json
from datetime import datetime

from .raid5 import RAID5Manager
from .schemas import FileMetadata, SystemStatus, FileUploadResponse, FileBlockStatus

app = FastAPI(title="TECMFS Controller", version="1.0.0")

# Inicializar el gestor RAID 5
raid_manager = RAID5Manager()

@app.get("/")
async def root():
    """Endpoint raíz para verificar que el servidor está funcionando"""
    return {"message": "TECMFS Controller Node", "status": "running"}

@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Obtener el estado del sistema RAID 5"""
    try:
        status = raid_manager.get_system_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")

@app.get("/status/blocks", response_model=List[FileBlockStatus])
async def get_block_status():
    """Obtener el estado detallado de todos los bloques de todos los archivos."""
    try:
        block_details = raid_manager.get_all_blocks_status()
        return block_details
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado de los bloques: {str(e)}")

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Subir un archivo al sistema RAID 5"""
    try:
        # Leer el contenido del archivo
        content = await file.read()
        
        # Verificar que el archivo tenga nombre
        if not file.filename:
            raise HTTPException(status_code=400, detail="El archivo debe tener un nombre")
        
        # Guardar el archivo usando RAID 5
        file_id = raid_manager.store_file(file.filename, content)
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            size=len(content),
            uploaded_at=datetime.now().isoformat(),
            message="Archivo subido exitosamente"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {str(e)}")

@app.get("/files", response_model=List[FileMetadata])
async def list_files():
    """Listar todos los archivos almacenados"""
    try:
        files = raid_manager.list_files()
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando archivos: {str(e)}")

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """Descargar un archivo por su ID"""
    try:
        file_data = raid_manager.retrieve_file(file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        # Crear un archivo temporal para la descarga
        temp_path = f"temp_{file_id}"
        with open(temp_path, "wb") as f:
            f.write(file_data['content'])
        
        return FileResponse(
            path=temp_path,
            filename=file_data['filename'],
            media_type='application/octet-stream'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error descargando archivo: {str(e)}")

@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Eliminar un archivo del sistema"""
    try:
        success = raid_manager.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        return {"message": "Archivo eliminado exitosamente", "file_id": file_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando archivo: {str(e)}")

@app.get("/search")
async def search_files(query: str):
    """Buscar archivos por nombre"""
    try:
        results = raid_manager.search_files(query)
        return {"query": query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error buscando archivos: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 