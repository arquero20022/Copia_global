
import subprocess
import sys
import importlib

def check_and_install_tkinter():
    try:
        # Intentamos importar tkinter
        import tkinter
        print("Tkinter ya está instalado.")
    except ImportError:
        print("Tkinter no está instalado. Intentando instalarlo...")

        # Actualizar la lista de paquetes
        try:
            subprocess.check_call(['sudo', 'apt-get', 'update'])
        except subprocess.CalledProcessError as e:
            print(f"Error al actualizar los paquetes: {e}")
            sys.exit(1)

        # Instalar tkinter
        try:
            subprocess.check_call(['sudo', 'apt-get', 'install', '-y', 'python3-tk'])
            print("Tkinter ha sido instalado exitosamente.")
        except subprocess.CalledProcessError as e:
            print(f"Error al instalar tkinter: {e}")
            sys.exit(1)

# Llamamos a la función para verificar e instalar tkinter
check_and_install_tkinter()

# Aquí iría el resto de tu código
from designer import ReportDesigner
import tkinter as tk

if __name__ == "__main__":
    app = ReportDesigner()
    app.mainloop()