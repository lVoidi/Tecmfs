#!/usr/bin/env python3
"""
Script principal para ejecutar el TECMFS Controller Node
"""

import uvicorn
import sys
import os

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
        uvicorn.run(
            "controller.main:app",
            host=HOST,
            port=PORT,
            reload=DEBUG
        )
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario")
    except Exception as e:
        print(f"Error iniciando servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 