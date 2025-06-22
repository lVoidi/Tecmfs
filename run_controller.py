#!/usr/bin/env python3
"""
Script principal para ejecutar el TECMFS Controller Node
"""

import uvicorn
import sys
import os
import argparse

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controller.main import app
from controller.config.settings import HOST, PORT, DEBUG

def main():
    """Función principal para ejecutar el servidor"""
    print("Iniciando TECMFS Controller Node...")
    print(f"Servidor en: http://{HOST}:{PORT}")
    print(f"Modo debug: {DEBUG}")
    print("Documentación API: http://localhost:8000/docs")
    print("=" * 50)
    
    try:
        parser = argparse.ArgumentParser(description="Run the TECMFS Controller Node.")
        parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to.")
        parser.add_argument("--port", type=int, default=8000, help="Port to run the server on.")
        
        args = parser.parse_args()

        print(f"Starting TECMFS Controller on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario")
    except Exception as e:
        print(f"Error iniciando servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 