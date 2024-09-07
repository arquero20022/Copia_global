import paramiko
from scp import SCPClient
import os
from datetime import datetime
import getpass
import shutil
import subprocess
import time
from threading import Thread, Event

# Archivo de configuración que contiene los detalles de las empresas
CONFIG_FILE_PATH = "config.txt"

def load_company_config():
    """
    Carga la configuración de las empresas desde un archivo y devuelve un diccionario.
    """
    companies = {}
    try:
        with open(CONFIG_FILE_PATH, "r") as file:
            for line in file:
                parts = line.strip().split()
                company_info = {key.split(':')[0]: key.split(':')[1] for key in parts}
                company_name = company_info['nombre_empresa']
                companies[company_name] = company_info
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de configuración en {CONFIG_FILE_PATH}.")
    return companies

def save_company_config(companies):
    """
    Guarda la configuración de las empresas en un archivo.
    """
    with open(CONFIG_FILE_PATH, "w") as file:
        for company_name, info in companies.items():
            line = " ".join([f"{key}:{value}" for key, value in info.items()])
            file.write(line + "\n")

def create_new_company():
    """
    Solicita al usuario los detalles de la nueva empresa y la guarda en el archivo de configuración.
    """
    company_name = input("Introduce el nombre de la nueva empresa: ")
    remote_host = input("Introduce el REMOTE_HOST de la nueva empresa: ")
    odoo_version = input("Introduce el ODOO_VERSION de la nueva empresa: ")
    db_port = input("Introduce el DB_PORT de la nueva empresa: ")

    new_company_info = {
        "nombre_empresa": company_name,
        "REMOTE_HOST": remote_host,
        "ODOO_VERSION": odoo_version,
        "DB_PORT": db_port
    }

    return new_company_info

def select_company(companies):
    """
    Muestra una lista de empresas y permite al usuario seleccionar una o crear una nueva.
    """
    print("Empresas disponibles:")
    for i, company_name in enumerate(companies.keys(), 1):
        print(f"{i}. {company_name}")
    print(f"{len(companies) + 1}. Crear nueva empresa")

    while True:
        try:
            choice = int(input("Selecciona el número de la empresa a la que deseas conectarte: "))
            if 1 <= choice <= len(companies):
                selected_company = list(companies.keys())[choice - 1]
                return companies[selected_company]
            elif choice == len(companies) + 1:
                new_company_info = create_new_company()
                companies[new_company_info['nombre_empresa']] = new_company_info
                save_company_config(companies)
                print("Nueva empresa creada y guardada en la configuración.")
                return new_company_info
            else:
                print("Por favor, selecciona un número válido.")
        except ValueError:
            print("Por favor, introduce un número.")

def create_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return client

def execute_remote_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()  # Esperar a que el comando se complete
    if exit_status != 0:
        print(f"Error en el comando: {stderr.read().decode()}")
    return stdout, stderr

def get_remote_file_size(ssh, remote_path):
    """Calculate the size of a remote file using SSH."""
    command = f"stat -c %s {remote_path}"
    stdin, stdout, stderr = ssh.exec_command(command)
    size_str = stdout.read().decode().strip()
    return int(size_str)

def get_remote_directory_size(ssh, remote_path):
    """Calculate the total size of a remote directory using SSH."""
    command = f"du -sb {remote_path} | cut -f1"
    stdin, stdout, stderr = ssh.exec_command(command)
    size_str = stdout.read().decode().strip()
    return int(size_str)

def get_local_directory_size(local_path):
    """Calculate the total size of a local directory."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(local_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def scp_progress(filename, size, sent, label):
    """Display the progress of the SCP download."""
    progress = (sent / size) * 100 if size > 0 else 0
    print(f"\r{label} - {filename}: {progress:.2f}% completado", end='')

def monitor_progress(local_path, total_size, stop_event, label):
    """Monitor and print progress every second."""
    while not stop_event.is_set():
        local_size = get_local_directory_size(local_path)
        progress = (local_size / total_size) * 100 if total_size > 0 else 0
        print(f"\r{label}: {progress:.2f}% completado", end='')
        time.sleep(1)

def main():
    companies = load_company_config()
    if not companies:
        print("No hay empresas configuradas. Verifica el archivo de configuración.")
        return

    selected_company = select_company(companies)
    company_name = selected_company['nombre_empresa']
    remote_host = selected_company['REMOTE_HOST']
    odoo_version = selected_company['ODOO_VERSION']
    db_port = selected_company['DB_PORT']

    # Configurar rutas basadas en la empresa seleccionada
    ssh_key_path = os.path.expanduser("~/.ssh/adrian")
    remote_user = "odoo"
    remote_port = 2228
    remote_dump_path = "/tmp"  # Directorio temporal en el servidor remoto para guardar el dump
    dump_file = f"PRO_{company_name}_{datetime.now().strftime('%d%m')}.dmp"
    local_path = f"/opt/sources/odoo{odoo_version}/attachments"

    remote_filestore_path = f"/opt/odoo/odoo{odoo_version}/attachments/filestore/PRO"
    local_filestore_root = os.path.join(local_path, "filestore")
    local_filestore_path = os.path.join(local_filestore_root, "PRO")
    renamed_filestore_path = os.path.join(local_filestore_root,
                                          f"PRO_{company_name}_{datetime.now().strftime('%d%m')}")
    restore_db_name = f"PRO_{company_name}_{datetime.now().strftime('%d%m')}"

    # Solicitar la contraseña de la clave SSH si está cifrada
    try:
        ssh_key_password = getpass.getpass(prompt="Introduce la contraseña de la clave SSH: ")
    except getpass.GetPassWarning as e:
        print("Advertencia: No se puede desactivar el eco de la contraseña en este entorno.")

    # Crear un cliente SSH
    with create_ssh_client() as ssh:
        try:
            # Cargar la clave privada con la contraseña
            private_key = paramiko.RSAKey.from_private_key_file(ssh_key_path, password=ssh_key_password)

            # Conectar al servidor remoto
            print("Conectando al servidor remoto...")
            ssh.connect(remote_host, port=remote_port, username=remote_user, pkey=private_key)

            # Ejecutar pg_dump en el servidor remoto
            dump_command = f"pg_dump -p {db_port} -Fc -Z4 -Od PRO > {remote_dump_path}/{dump_file}"
            print("Creando dump de la base de datos en el servidor remoto...")
            execute_remote_command(ssh, dump_command)

            # Crear una sesión SCP para transferir el archivo de dump
            print("\nCalculando el tamaño del dump remoto...")
            dump_size = get_remote_file_size(ssh, f"{remote_dump_path}/{dump_file}")
            print(f"Tamaño del dump: {dump_size} bytes")

            print("\nDescargando el dump a la máquina local...")
            with SCPClient(ssh.get_transport(),
                           progress=lambda filename, size, sent: scp_progress(filename, size, sent, "Dump")) as scp:
                scp.get(f"{remote_dump_path}/{dump_file}", local_path)

            # Obtener el tamaño total del filestore antes de descargar
            print("\nCalculando el tamaño total del filestore remoto...")
            filestore_size = get_remote_directory_size(ssh, remote_filestore_path)
            print(f"Tamaño del filestore: {filestore_size} bytes")

            # Descargar el contenido del filestore directamente a filestore/PRO
            os.makedirs(local_filestore_root, exist_ok=True)  # Crear el directorio root si no existe

            # Monitor progress in a separate thread
            stop_event = Event()
            progress_thread = Thread(target=monitor_progress,
                                     args=(local_filestore_path, filestore_size, stop_event, "Filestore"))
            progress_thread.start()

            with SCPClient(ssh.get_transport()) as scp:
                scp.get(remote_filestore_path, local_filestore_root, recursive=True)

            # Stop progress monitoring
            stop_event.set()
            progress_thread.join()

            # Renombrar la carpeta PRO a filestore_nombreempresa_ddmm
            if os.path.exists(renamed_filestore_path):
                shutil.rmtree(renamed_filestore_path)

            os.rename(local_filestore_path, renamed_filestore_path)
            print(f"\nEl filestore se ha descargado y renombrado a {renamed_filestore_path}")

            # Eliminar el archivo dump del servidor remoto
            print("Eliminando el archivo dump del servidor remoto...")
            remove_command = f"rm -f {remote_dump_path}/{dump_file}"
            execute_remote_command(ssh, remove_command)

            print(f"Proceso completado. El archivo se ha descargado a {local_path}/{dump_file}")

        finally:
            # Asegurarse de que el cliente SSH se cierre adecuadamente
            ssh.close()

    # Comprobar si la base de datos ya existe y eliminarla si es necesario
    try:
        print("Comprobando si la base de datos ya existe...")
        check_db_command = [
            "psql",
            "-U", "odoo",
            "-h", "postgres",
            "-p", "5432",
            "-t", "-c", f"SELECT 1 FROM pg_database WHERE datname='{restore_db_name}'"
        ]
        result = subprocess.run(check_db_command, capture_output=True, text=True)

        if '1' in result.stdout:
            print("La base de datos ya existe. Eliminando...")
            drop_db_command = [
                "dropdb",
                "-h", "postgres",
                "-U", "odoo",
                "-p", "5432",
                restore_db_name
            ]
            subprocess.run(drop_db_command, check=True)
            print("Base de datos eliminada exitosamente.")
        else:
            print("La base de datos no existe. Procediendo con la creación.")

    except subprocess.CalledProcessError as e:
        print(f"Error al comprobar o eliminar la base de datos: {e}")

    # Crear la base de datos antes de la restauración
    try:
        print("Creando la base de datos...")
        create_db_command = [
            "createdb",
            "-h", "postgres",  # Usa el mismo host que en el comando que funciona
            "-U", "odoo",
            "-p", "5432",
            restore_db_name
        ]
        subprocess.run(create_db_command, check=True)
        print("Base de datos creada exitosamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error al crear la base de datos: {e}")

    # Ejecutar el comando pg_restore
    try:
        print("Ejecutando el comando pg_restore...")
        restore_command = [
            "pg_restore",
            "-j", "12",
            "-h", "postgres",
            "-U", "odoo",
            "-p", "5432",
            "-Od", restore_db_name,
            os.path.join(local_path, dump_file)
        ]
        subprocess.run(restore_command, check=True)
        print("Comando pg_restore ejecutado exitosamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el comando pg_restore: {e}")

    # Ejecutar los comandos SQL en la base de datos restaurada, uno por uno
    sql_commands = [
        "UPDATE ir_cron SET active = false;",
        "UPDATE ir_mail_server SET active = false;",
        "DELETE FROM ir_config_parameter WHERE key IN ('database.enterprise_code', 'odoo_ocn.project_id', 'mail_mobile.enable_ocn');"
    ]

    for command in sql_commands:
        try:
            print(f"Ejecutando SQL: {command.strip()}")
            psql_command = [
                "psql",
                "-U", "odoo",
                "-h", "postgres",
                "-p", "5432",
                "-d", restore_db_name,
                "-c", command
            ]
            subprocess.run(psql_command, check=True)
            print("Comando SQL ejecutado exitosamente.")
        except subprocess.CalledProcessError as e:
            print(f"Error al ejecutar el comando SQL: {e}")

    # Ejecutar el comando psql para listar las bases de datos
    try:
        print("Ejecutando el comando psql para listar las bases de datos...")
        psql_command = [
            "psql",
            "-U", "odoo",
            "-h", "postgres",
            "-p", "5432",
            "-l"
        ]
        subprocess.run(psql_command, check=True)
        print("Comando psql ejecutado exitosamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el comando psql: {e}")

if __name__ == "__main__":
    main()
