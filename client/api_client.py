import requests
import os
from typing import List, Dict, Optional

# --- Configuration ---
CONTROLLER_URL = "http://localhost:8000"

def get_files() -> Optional[List[Dict]]:
    """Fetches the list of all files from the controller."""
    try:
        response = requests.get(f"{CONTROLLER_URL}/files", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error getting files: {e}")
        return None

def upload_file(filepath: str) -> Optional[Dict]:
    """Uploads a single file to the controller."""
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return None
    
    filename = os.path.basename(filepath)
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f, 'application/octet-stream')}
            response = requests.post(f"{CONTROLLER_URL}/upload", files=files, timeout=300)
            response.raise_for_status()
            return response.json()
    except requests.RequestException as e:
        print(f"Error uploading file {filename}: {e}")
        return None

def download_file(file_id: str, filename: str, save_dir: str) -> Optional[str]:
    """Downloads a file from the controller and saves it."""
    save_path = os.path.join(save_dir, filename)
    try:
        with requests.get(f"{CONTROLLER_URL}/download/{file_id}", stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return save_path
    except requests.RequestException as e:
        print(f"Error downloading file {file_id}: {e}")
        return None

def delete_file(file_id: str) -> bool:
    """Deletes a file from the system via the controller."""
    try:
        response = requests.delete(f"{CONTROLLER_URL}/files/{file_id}", timeout=300)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Error deleting file {file_id}: {e}")
        return False

def search_files(query: str) -> Optional[List[Dict]]:
    """Searches for files on the controller."""
    try:
        params = {'query': query}
        response = requests.get(f"{CONTROLLER_URL}/search", params=params, timeout=10)
        response.raise_for_status()
        # The search endpoint returns a dict {"query": ..., "results": [...]}, we only need results
        return response.json().get("results")
    except requests.RequestException as e:
        print(f"Error searching for files: {e}")
        return None

def get_system_status() -> Optional[Dict]:
    """Gets the system status from the controller."""
    try:
        response = requests.get(f"{CONTROLLER_URL}/status", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error getting system status: {e}")
        return None

if __name__ == '__main__':
    # A simple test to check if the controller is running and list files
    print("--- Checking System Status ---")
    status = get_system_status()
    if status:
        print(status)
    else:
        print("Could not get system status. Is the controller running?")

    print("\n--- Listing Files ---")
    files_list = get_files()
    if files_list:
        for f in files_list:
            print(f"- {f['filename']} (ID: {f['file_id']})")
    else:
        print("Could not list files.") 