import os
import subprocess

# Ruta a la carpeta de los módulos
addons_dir = '/opt/sources/odoo170/src/addons-custom/addons-inpl'  # Ajusta esta ruta a la ubicación de tu carpeta

# Lista todos los módulos en la carpeta
modules = [name for name in os.listdir(addons_dir) if os.path.isdir(os.path.join(addons_dir, name))]

# Une los nombres de los módulos en una cadena separada por comas
modules_str = ','.join(modules)

# Construye el comando de odoo-bin con el parámetro -i
command = f'-c /opt/odoo/sources/odoo170/conf/odoo.conf -d inplastvaciocopia -i {modules_str}'

# Imprime el comando (para verificación) y luego lo ejecuta
print(f"Ejecutando comando: {command}")
subprocess.run(command, shell=True)
