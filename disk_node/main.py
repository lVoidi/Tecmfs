import fastapi
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import binascii
import argparse
import xml.etree.ElementTree as ET
from threading import Lock

app = FastAPI(title="TECMFS Disk Node", version="1.1.0")

# --- Global Configuration ---
class DiskConfig:
    def __init__(self):
        self.storage_path = ""
        self.capacity_bytes = 0
        self.used_space_bytes = 0
        self.port = 0
        self.lock = Lock()

config = DiskConfig()

# --- Pydantic model for storing data ---
class StoreData(BaseModel):
    block_id: str
    data: str # Hex-encoded data

def get_directory_size(path):
    """Calculates the total size of all files in a directory."""
    total_size = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total_size += entry.stat().st_size
    except FileNotFoundError:
        return 0
    return total_size

@app.on_event("startup")
async def startup_event():
    """Ensure the storage directory exists and calculate initial used space."""
    if not os.path.exists(config.storage_path):
        try:
            os.makedirs(config.storage_path)
            print(f"Directorio de almacenamiento creado en: {config.storage_path}")
        except OSError as e:
            print(f"Error creando directorio de almacenamiento {config.storage_path}: {e}")
            raise
    
    # Calculate initial used space
    config.used_space_bytes = get_directory_size(config.storage_path)
    print(f"Espacio inicial utilizado: {config.used_space_bytes / (1024*1024):.2f} MB")
    print(f"Capacidad total del disco: {config.capacity_bytes / (1024*1024):.2f} MB")

@app.get("/")
def read_root():
    """Root endpoint to check if the node is alive and show status."""
    return {
        "message": "Disk Node is running",
        "storage_path": config.storage_path,
        "capacity_bytes": config.capacity_bytes,
        "used_space_bytes": config.used_space_bytes,
        "available_space_bytes": config.capacity_bytes - config.used_space_bytes
    }

@app.post("/store", status_code=201)
async def store_block(payload: StoreData):
    """Stores a block of data, checking for available space first."""
    try:
        data_bytes = binascii.unhexlify(payload.data)
        block_size = len(data_bytes)

        with config.lock:
            # Check for available space
            if config.used_space_bytes + block_size > config.capacity_bytes:
                raise HTTPException(
                    status_code=507, 
                    detail="Insufficient storage space on this disk node."
                )

            block_path = os.path.join(config.storage_path, payload.block_id)
            with open(block_path, "wb") as f:
                f.write(data_bytes)
            
            # Update used space
            config.used_space_bytes += block_size

        return {"message": "Block stored successfully", "block_id": payload.block_id}
    except binascii.Error as e:
        raise HTTPException(status_code=400, detail=f"Invalid hex data: {e}")
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Could not write to block file: {e}")

@app.get("/retrieve/{block_id}")
async def retrieve_block(block_id: str):
    """Retrieves a block of data by its ID."""
    block_path = os.path.join(config.storage_path, block_id)
    if not os.path.exists(block_path):
        raise HTTPException(status_code=404, detail="Block not found")
    try:
        with open(block_path, "rb") as f:
            data = f.read()
        return {"block_id": block_id, "data": binascii.hexlify(data).decode()}
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Could not read block file: {e}")

@app.delete("/delete/{block_id}", status_code=200)
async def delete_block(block_id: str):
    """Deletes a block of data by its ID."""
    block_path = os.path.join(config.storage_path, block_id)
    if not os.path.exists(block_path):
        raise HTTPException(status_code=404, detail="Block not found")
    try:
        block_size = os.path.getsize(block_path)
        with config.lock:
            os.remove(block_path)
            # Update used space
            config.used_space_bytes -= block_size
        return {"message": "Block deleted successfully", "block_id": block_id}
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Could not delete block file: {e}")

def main():
    """Main function to parse config and run the server."""
    parser = argparse.ArgumentParser(description="Run a TECMFS Disk Node server from an XML config file.")
    parser.add_argument("--config", type=str, required=True, help="Path to the XML configuration file.")
    args = parser.parse_args()

    try:
        tree = ET.parse(args.config)
        root = tree.getroot()
        
        config.port = int(root.find('server/port').text)
        config.storage_path = root.find('storage/path').text
        capacity_mb = int(root.find('storage/capacity_mb').text)
        config.capacity_bytes = capacity_mb * 1024 * 1024
        
    except (ET.ParseError, FileNotFoundError, AttributeError, ValueError) as e:
        print(f"Error parsing XML config file '{args.config}': {e}")
        return

    print(f"Iniciando Disk Node desde '{args.config}' en el puerto {config.port}...")
    print(f"Usando directorio de almacenamiento: {config.storage_path}")
    
    uvicorn.run(app, host="0.0.0.0", port=config.port)

if __name__ == "__main__":
    main() 