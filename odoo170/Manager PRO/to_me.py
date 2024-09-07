import psycopg2
import paramiko
from scp import SCPClient
import os
from datetime import datetime
import shutil
import subprocess
import time
from threading import Thread, Event
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
import sys

CONFIG_FILE_PATH = "config.txt"

class RedirectText(object):
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)

    def flush(self):
        pass

def load_company_config():
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
    with open(CONFIG_FILE_PATH, "w") as file:
        for company_name, info in companies.items():
            line = " ".join([f"{key}:{value}" for key, value in info.items()])
            file.write(line + "\n")

def create_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return client

def execute_remote_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"Error en el comando: {stderr.read().decode()}")
    return stdout, stderr

def format_size(bytes_size):
    if bytes_size < 1024**3:
        return f"{bytes_size / 1024**2:.2f} MB"
    else:
        return f"{bytes_size / 1024**3:.2f} GB"

def get_remote_file_size(ssh, remote_path):
    command = f"stat -c %s {remote_path}"
    stdin, stdout, stderr = ssh.exec_command(command)
    size_str = stdout.read().decode().strip()
    return int(size_str)

def get_remote_directory_size(ssh, remote_path):
    command = f"du -sb {remote_path} | cut -f1"
    stdin, stdout, stderr = ssh.exec_command(command)
    size_str = stdout.read().decode().strip()
    return int(size_str)

def get_local_directory_size(local_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(local_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def scp_progress(size, sent, progress_var):
    progress = (sent / size) * 100 if size > 0 else 0
    progress_var.set(f"{progress:.2f}% completado")

def monitor_progress(local_path, total_size, stop_event, progress_var):
    while not stop_event.is_set():
        local_size = get_local_directory_size(local_path)
        progress = (local_size / total_size) * 100 if total_size > 0 else 0
        progress_var.set(f"{progress:.2f}% completado")
        time.sleep(1)

def list_databases(user, host, port):
    try:
        conn = psycopg2.connect(dbname='postgres', user=user, host=host, port=port)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = cursor.fetchall()
        cursor.close()
        conn.close()
        return [db[0] for db in databases]
    except psycopg2.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return []

def check_database_exists(dbname, databases):
    return dbname in databases

def execute_task(selected_company_name, ssh_key_password, output_console, dump_progress_var, filestore_progress_var):
    companies = load_company_config()
    if not companies:
        output_console.insert(tk.END, "Error: No hay empresas configuradas. Verifica el archivo de configuración.\n")
        return

    selected_company = companies[selected_company_name]
    company_name = selected_company['nombre_empresa']
    remote_host = selected_company['REMOTE_HOST']
    odoo_version = selected_company['ODOO_VERSION']
    db_port = selected_company['DB_PORT']

    ssh_key_path = os.path.expanduser("~/.ssh/adrian")
    remote_user = "odoo"
    remote_port = 2228
    remote_dump_path = "/tmp"
    dump_file = f"PRO_{company_name}_{datetime.now().strftime('%d%m')}.dmp"
    local_path = f"/opt/sources/odoo{odoo_version}/attachments"

    remote_filestore_path = f"/opt/odoo/odoo{odoo_version}/attachments/filestore/PRO"
    local_filestore_root = os.path.join(local_path, "filestore")
    local_filestore_path = os.path.join(local_filestore_root, "PRO")
    renamed_filestore_path = os.path.join(local_filestore_root,
                                          f"PRO_{company_name}_{datetime.now().strftime('%d%m')}")
    restore_db_name = f"PRO_{company_name}_{datetime.now().strftime('%d%m')}"

    try:
        with create_ssh_client() as ssh:
            try:
                private_key = paramiko.RSAKey.from_private_key_file(ssh_key_path, password=ssh_key_password)
                output_console.insert(tk.END, "Conectando al servidor remoto...\n")
                ssh.connect(remote_host, port=remote_port, username=remote_user, pkey=private_key)
                dump_command = f"pg_dump -p {db_port} -Fc -Z4 -Od PRO > {remote_dump_path}/{dump_file}"
                output_console.insert(tk.END, "Creando dump de la base de datos en el servidor remoto...\n")
                execute_remote_command(ssh, dump_command)

                output_console.insert(tk.END, "\nCalculando el tamaño del dump remoto...\n")
                dump_size = get_remote_file_size(ssh, f"{remote_dump_path}/{dump_file}")
                output_console.insert(tk.END, f"Tamaño del dump: {format_size(dump_size)}\n")

                output_console.insert(tk.END, "\nDescargando el dump a la máquina local...\n")
                dump_progress_var.set("0% completado")
                with SCPClient(ssh.get_transport(),
                            progress=lambda filename, size, sent: scp_progress(size, sent, dump_progress_var)) as scp:
                    scp.get(f"{remote_dump_path}/{dump_file}", local_path)

                output_console.insert(tk.END, "\nCalculando el tamaño total del filestore remoto...\n")
                filestore_size = get_remote_directory_size(ssh, remote_filestore_path)
                output_console.insert(tk.END, f"Tamaño del filestore: {format_size(filestore_size)}\n")

                os.makedirs(local_filestore_root, exist_ok=True)

                stop_event = Event()
                filestore_progress_var.set("0% completado")
                progress_thread = Thread(target=monitor_progress,
                                        args=(local_filestore_path, filestore_size, stop_event, filestore_progress_var))
                progress_thread.start()

                with SCPClient(ssh.get_transport()) as scp:
                    scp.get(remote_filestore_path, local_filestore_root, recursive=True)

                stop_event.set()
                progress_thread.join()

                if os.path.exists(renamed_filestore_path):
                    shutil.rmtree(renamed_filestore_path)

                os.rename(local_filestore_path, renamed_filestore_path)
                output_console.insert(tk.END, f"\nEl filestore se ha descargado y renombrado a {renamed_filestore_path}\n")

                output_console.insert(tk.END, "Eliminando el archivo dump del servidor remoto...\n")
                remove_command = f"rm -f {remote_dump_path}/{dump_file}"
                execute_remote_command(ssh, remove_command)

                output_console.insert(tk.END, f"Proceso completado. El archivo se ha descargado a {local_path}/{dump_file}\n")

            finally:
                ssh.close()
    except paramiko.ssh_exception.SSHException:
        messagebox.showerror("Error", "Contraseña incorrecta para la clave SSH. Por favor, inténtelo de nuevo.")
        output_console.insert(tk.END, "Contraseña incorrecta para la clave SSH. Por favor, inténtelo de nuevo.\n")
        return

    try:
        output_console.insert(tk.END, "Listando bases de datos en el servidor local...\n")
        existing_databases = list_databases("odoo", "postgres", db_port)

        output_console.insert(tk.END, "Comprobando si la base de datos ya existe...\n")
        if check_database_exists(restore_db_name, existing_databases):
            output_console.insert(tk.END, "La base de datos ya existe. Eliminando...\n")
            try:
                drop_db_command = [
                    "dropdb",
                    "-h", "postgres",
                    "-U", "odoo",
                    "-p", "5432",
                    restore_db_name
                ]
                subprocess.run(drop_db_command, check=True)
                output_console.insert(tk.END, f"Base de datos {restore_db_name} eliminada exitosamente.\n")
            except subprocess.CalledProcessError as e:
                output_console.insert(tk.END, f"Error al eliminar la base de datos: {e}\n")
                return
        else:
            output_console.insert(tk.END, "La base de datos no existe. Procediendo con la creación.\n")

    except subprocess.CalledProcessError as e:
        output_console.insert(tk.END, f"Error al comprobar la existencia de la base de datos: {e}\n")

    try:
        list_databases("odoo", "postgres", db_port)
        output_console.insert(tk.END, "Creando la base de datos...\n")
        create_db_command = [
            "createdb",
            "-h", "postgres",
            "-U", "odoo",
            "-p", "5432",
            restore_db_name
        ]
        subprocess.run(create_db_command, check=True)
        output_console.insert(tk.END, f"Base de datos {restore_db_name} creada exitosamente.\n")
    except subprocess.CalledProcessError as e:
        output_console.insert(tk.END, f"Error al crear la base de datos: {e}\n")
        return

    try:
        output_console.insert(tk.END, "Ejecutando el comando pg_restore...\n")
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
        output_console.insert(tk.END, "Comando pg_restore ejecutado exitosamente.\n")
    except subprocess.CalledProcessError as e:
        output_console.insert(tk.END, f"Error al ejecutar el comando pg_restore: {e}\n")
        return

    sql_commands = [
        "UPDATE ir_cron SET active = false;",
        "UPDATE ir_mail_server SET active = false;",
        "DELETE FROM ir_config_parameter WHERE key IN ('database.enterprise_code', 'odoo_ocn.project_id', 'mail_mobile.enable_ocn');"
    ]

    for command in sql_commands:
        try:
            output_console.insert(tk.END, f"Ejecutando SQL: {command.strip()}\n")
            psql_command = [
                "psql",
                "-U", "odoo",
                "-h", "postgres",
                "-p", "5432",
                "-d", restore_db_name,
                "-c", command
            ]
            subprocess.run(psql_command, check=True)
            output_console.insert(tk.END, "Comando SQL ejecutado exitosamente.\n")
        except subprocess.CalledProcessError as e:
            output_console.insert(tk.END, f"Error al ejecutar el comando SQL: {e}\n")

    try:
        existing_databases = list_databases("odoo", "postgres", db_port)
        output_console.insert(tk.END, "Bases de datos existentes después del proceso:\n")
        for db in existing_databases:
            output_console.insert(tk.END, f"- {db}\n")

    except Exception as e:
        output_console.insert(tk.END, f"Error al listar bases de datos: {e}\n")

def run_to_me():
    root = tk.Toplevel()
    root.title("TO ME")

    window_width = 600
    window_height = 800
    root.geometry(f'{window_width}x{window_height}+0+0')

    companies = load_company_config()

    company_label = ttk.Label(root, text="Selecciona la empresa:")
    company_label.pack(padx=10, pady=5)

    company_dropdown = ttk.Combobox(root, values=list(companies.keys()), state="readonly")
    company_dropdown.pack(padx=10, pady=5)

    ssh_password_var = StringVar()
    ssh_password_label = ttk.Label(root, text="Contraseña de la clave SSH:")
    ssh_password_label.pack(padx=10, pady=5)
    ssh_password_entry = ttk.Entry(root, textvariable=ssh_password_var, show="*")
    ssh_password_entry.pack(padx=10, pady=5)

    add_company_button = ttk.Button(root, text="+", command=lambda: toggle_new_company_fields(root))
    add_company_button.pack(padx=10, pady=5)

    run_button = ttk.Button(root, text="Ejecutar", command=lambda: run_main(company_dropdown, ssh_password_var, output_console, dump_progress_var, filestore_progress_var))
    run_button.pack(padx=10, pady=5)

    new_company_fields = tk.Frame(root)
    new_company_name = StringVar()
    new_remote_host = StringVar()
    new_odoo_version = StringVar()
    new_db_port = StringVar()

    ttk.Label(new_company_fields, text="Nombre Empresa:").pack(anchor='w', padx=5, pady=2)
    ttk.Entry(new_company_fields, textvariable=new_company_name).pack(fill='x', padx=5, pady=2)

    ttk.Label(new_company_fields, text="Remote Host:").pack(anchor='w', padx=5, pady=2)
    ttk.Entry(new_company_fields, textvariable=new_remote_host).pack(fill='x', padx=5, pady=2)

    ttk.Label(new_company_fields, text="Odoo Version:").pack(anchor='w', padx=5, pady=2)
    ttk.Entry(new_company_fields, textvariable=new_odoo_version).pack(fill='x', padx=5, pady=2)

    ttk.Label(new_company_fields, text="DB Port:").pack(anchor='w', padx=5, pady=2)
    ttk.Entry(new_company_fields, textvariable=new_db_port).pack(fill='x', padx=5, pady=2)

    save_button = ttk.Button(new_company_fields, text="Guardar", command=lambda: save_new_company(companies, company_dropdown, new_company_name, new_remote_host, new_odoo_version, new_db_port, new_company_fields))
    save_button.pack(padx=5, pady=5)

    output_console = tk.Text(root, wrap='word', height=10)
    output_console.pack(padx=10, pady=5, fill='both', expand=True)

    dump_progress_var = StringVar(value="0% completado")
    filestore_progress_var = StringVar(value="0% completado")

    ttk.Label(root, text="Progreso del Dump:").pack(padx=10, pady=5)
    ttk.Label(root, textvariable=dump_progress_var).pack(padx=10, pady=5)

    ttk.Label(root, text="Progreso del Filestore:").pack(padx=10, pady=5)
    ttk.Label(root, textvariable=filestore_progress_var).pack(padx=10, pady=5)

    sys.stdout = RedirectText(output_console)
    sys.stderr = RedirectText(output_console)

def toggle_new_company_fields(parent):
    new_company_fields = parent.children['!frame']
    if not new_company_fields.winfo_ismapped():
        new_company_fields.pack(padx=10, pady=5)
    else:
        new_company_fields.pack_forget()

def save_new_company(companies, company_dropdown, new_company_name, new_remote_host, new_odoo_version, new_db_port, new_company_fields):
    company_name = new_company_name.get().strip()
    remote_host = new_remote_host.get().strip()
    odoo_version = new_odoo_version.get().strip()
    db_port = new_db_port.get().strip()

    if company_name and remote_host and odoo_version and db_port:
        new_company_info = {
            "nombre_empresa": company_name,
            "REMOTE_HOST": remote_host,
            "ODOO_VERSION": odoo_version,
            "DB_PORT": db_port
        }
        companies[company_name] = new_company_info
        save_company_config(companies)
        company_dropdown['values'] = list(companies.keys())
        company_dropdown.set(company_name)
        messagebox.showinfo("Info", "Nueva empresa creada y guardada en la configuración.")
        toggle_new_company_fields(new_company_fields.master)
    else:
        messagebox.showerror("Error", "Todos los campos deben ser completados.")

def run_main(company_dropdown, ssh_password_var, output_console, dump_progress_var, filestore_progress_var):
    selected_company_name = company_dropdown.get()
    ssh_key_password = ssh_password_var.get()
    if selected_company_name:
        task_thread = Thread(target=execute_task, args=(selected_company_name, ssh_key_password, output_console, dump_progress_var, filestore_progress_var))
        task_thread.start()
    else:
        messagebox.showwarning("Advertencia", "Por favor selecciona una empresa.")
