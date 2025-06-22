import fastapi
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import uvicorn
import os
import binascii
import argparse

app = FastAPI(title="TECMFS Disk Node", version="1.0.0")

# --- Global variable for storage path ---
STORAGE_PATH = ""

# --- Pydantic model for storing data ---
class StoreData(BaseModel):
    block_id: str
    data: str # Hex-encoded data

@app.on_event("startup")
async def startup_event():
    """Ensure the storage directory exists on startup."""
    global STORAGE_PATH
    if not os.path.exists(STORAGE_PATH):
        try:
            os.makedirs(STORAGE_PATH)
            print(f"Directorio de almacenamiento creado en: {STORAGE_PATH}")
        except OSError as e:
            print(f"Error creando directorio de almacenamiento {STORAGE_PATH}: {e}")
            raise

@app.get("/")
def read_root():
    """Root endpoint to check if the node is alive."""
    return {"message": "Disk Node is running", "storage_path": STORAGE_PATH}

@app.post("/store", status_code=201)
async def store_block(payload: StoreData):
    """Stores a block of data with a given ID."""
    block_path = os.path.join(STORAGE_PATH, payload.block_id)
    try:
        # Data is received as a hex string, so we decode it
        data_bytes = binascii.unhexlify(payload.data)
        with open(block_path, "wb") as f:
            f.write(data_bytes)
        return {"message": "Block stored successfully", "block_id": payload.block_id}
    except binascii.Error as e:
        raise HTTPException(status_code=400, detail=f"Invalid hex data: {e}")
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Could not write to block file: {e}")

@app.get("/retrieve/{block_id}")
async def retrieve_block(block_id: str):
    """Retrieves a block of data by its ID."""
    block_path = os.path.join(STORAGE_PATH, block_id)
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
    block_path = os.path.join(STORAGE_PATH, block_id)
    if not os.path.exists(block_path):
        raise HTTPException(status_code=404, detail="Block not found")
    try:
        os.remove(block_path)
        return {"message": "Block deleted successfully", "block_id": block_id}
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Could not delete block file: {e}")

def main():
    """Main function to run the server."""
    global STORAGE_PATH
    parser = argparse.ArgumentParser(description="Run a TECMFS Disk Node server.")
    parser.add_argument("--port", type=int, required=True, help="Port to run the server on.")
    parser.add_argument("--storage", type=str, required=True, help="Directory to store data blocks.")
    
    args = parser.parse_args()
    
    STORAGE_PATH = args.storage
    
    print(f"Iniciando Disk Node en el puerto {args.port}...")
    print(f"Usando directorio de almacenamiento: {STORAGE_PATH}")
    
    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main() 