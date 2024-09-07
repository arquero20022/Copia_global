import tkinter as tk
from tkinter import ttk, messagebox
import paramiko
import os
from datetime import datetime

CONFIG_FILE_PATH = "config.txt"


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


def create_ssh_client(remote_host, remote_port, remote_user, ssh_key_path, ssh_key_password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    private_key = paramiko.RSAKey.from_private_key_file(ssh_key_path, password=ssh_key_password)
    client.connect(remote_host, port=remote_port, username=remote_user, pkey=private_key)
    return client


def list_remote_databases(ssh, db_port):
    command = f"psql -p {db_port} -lqt | awk '{{print $1}}' | grep -vwE 'template0|template1|postgres|^$'"
    stdin, stdout, stderr = ssh.exec_command(command)
    databases = stdout.read().decode().splitlines()
    return databases


def check_remote_db_exists(ssh, db_name, db_port):
    command = f"psql -p {db_port} -lqt | awk '{{print $1}}' | grep -qw {db_name}"
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout.channel.recv_exit_status() == 0


def run_manager_remote_database():
    root = tk.Toplevel()
    root.title("Manager Remote Database")

    window_width = 600
    window_height = 600
    root.geometry(f'{window_width}x{window_height}+0+0')

    # Cargar configuración de empresas
    companies = load_company_config()

    # Componentes UI
    company_label = ttk.Label(root, text="Selecciona la empresa:")
    company_label.pack(padx=10, pady=5)

    company_dropdown = ttk.Combobox(root, values=list(companies.keys()), state="readonly")
    company_dropdown.pack(padx=10, pady=5)

    ssh_password_label = ttk.Label(root, text="Contraseña de la clave SSH:")
    ssh_password_label.pack(padx=10, pady=5)

    ssh_password_var = tk.StringVar()
    ssh_password_entry = ttk.Entry(root, textvariable=ssh_password_var, show="*")
    ssh_password_entry.pack(padx=10, pady=5)

    # Frame para acciones después de la conexión
    action_frame = ttk.Frame(root)
    action_frame.pack(padx=10, pady=10, fill="both", expand=True)

    db_action_var = tk.StringVar(value="c")
    db_action_frame = ttk.LabelFrame(action_frame, text="Acción a realizar")
    db_action_frame.pack(padx=10, pady=10, fill="x")

    copy_radiobutton = ttk.Radiobutton(db_action_frame, text="Copiar a nuevo desarrollo", variable=db_action_var,
                                       value="c", command=lambda: toggle_fields("c"))
    replace_radiobutton = ttk.Radiobutton(db_action_frame, text="Reemplazar base de datos de desarrollo",
                                          variable=db_action_var, value="r", command=lambda: toggle_fields("r"))
    copy_radiobutton.pack(anchor='w', padx=10, pady=5)
    replace_radiobutton.pack(anchor='w', padx=10, pady=5)

    # Labels y entradas para bases de datos y nombres
    db_pro_label = ttk.Label(action_frame, text="Base de Datos Producción:")
    db_dev_label = ttk.Label(action_frame, text="Base de Datos Desarrollo:")
    new_db_name_label = ttk.Label(action_frame, text="Nuevo Nombre de Base de Datos:")

    db_pro_dropdown = ttk.Combobox(action_frame, state="readonly")
    db_dev_dropdown = ttk.Combobox(action_frame, state="readonly")
    new_db_name_entry = ttk.Entry(action_frame)

    def toggle_fields(action):
        """Función para mostrar/ocultar campos según la acción seleccionada."""
        if action == "c":
            # Mostrar campos para copiar a nuevo desarrollo
            db_pro_label.pack(padx=10, pady=5)
            db_pro_dropdown.pack(padx=10, pady=5)
            new_db_name_label.pack(padx=10, pady=5)
            new_db_name_entry.pack(padx=10, pady=5)

            # Ocultar campos de reemplazo
            db_dev_label.pack_forget()
            db_dev_dropdown.pack_forget()

        elif action == "r":
            # Mostrar campos para reemplazar desarrollo
            db_pro_label.pack(padx=10, pady=5)
            db_pro_dropdown.pack(padx=10, pady=5)
            db_dev_label.pack(padx=10, pady=5)
            db_dev_dropdown.pack(padx=10, pady=5)

            # Ocultar campo de nuevo nombre
            new_db_name_label.pack_forget()
            new_db_name_entry.pack_forget()

    def connect_to_remote():
        selected_company_name = company_dropdown.get()
        ssh_key_password = ssh_password_var.get()

        if not selected_company_name or not ssh_key_password:
            messagebox.showwarning("Advertencia", "Por favor, selecciona una empresa e ingresa la contraseña SSH.")
            return

        selected_company = companies[selected_company_name]
        remote_host = selected_company['REMOTE_HOST']
        remote_port = int(selected_company['REMOTE_PORT'])
        odoo_version = selected_company['ODOO_VERSION']  # Obtener la versión de Odoo
        ssh_key_path = os.path.expanduser("~/.ssh/adrian")
        remote_user = "odoo"

        try:
            ssh = create_ssh_client(remote_host, remote_port, remote_user, ssh_key_path, ssh_key_password)
            messagebox.showinfo("Conexión exitosa", "Conexión establecida con el servidor remoto.")

            db_port_origin = selected_company['DB_PORT']
            db_port_dest = "5433"

            databases_origin = list_remote_databases(ssh, db_port_origin)
            databases_dest = list_remote_databases(ssh, db_port_dest)

            # Rellenar los desplegables con bases de datos
            db_pro_dropdown['values'] = databases_origin
            db_dev_dropdown['values'] = databases_dest
            db_pro_dropdown.set('')
            db_dev_dropdown.set('')
            new_db_name_entry.delete(0, tk.END)

            def execute_remote_action():
                action = db_action_var.get()
                selected_db_pro = db_pro_dropdown.get()
                selected_db_dev = db_dev_dropdown.get()
                new_db_name = new_db_name_entry.get()

                if action == "r" and selected_db_pro and selected_db_dev:
                    replace_database(ssh, db_port_origin, db_port_dest, selected_db_pro, selected_db_dev, odoo_version)
                elif action == "c" and selected_db_pro and new_db_name:
                    copy_database(ssh, db_port_origin, db_port_dest, selected_db_pro, new_db_name, odoo_version)
                ssh.close()

            execute_button = ttk.Button(action_frame, text="Ejecutar Acción", command=execute_remote_action)
            execute_button.pack(padx=10, pady=10, fill='x')

        except paramiko.ssh_exception.AuthenticationException:
            messagebox.showerror("Error de autenticación", "Contraseña SSH incorrecta o autenticación fallida.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar al servidor remoto: {e}")

    connect_button = ttk.Button(root, text="Conectar", command=connect_to_remote)
    connect_button.pack(padx=10, pady=10, fill='x')

    exit_button = ttk.Button(root, text="Salir", command=root.destroy)
    exit_button.pack(padx=10, pady=10, fill='x')

    toggle_fields("c")  # Mostrar campos iniciales para copiar
    root.mainloop()


def replace_database(ssh, db_port_origin, db_port_dest, selected_db_pro, selected_db_dev, odoo_version):
    try:
        action_script = f"""
        LOG_FILE="copias_PRO2DEV_log"

        log() {{
            echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
        }}

        log "Deteniendo la instancia de Odoo..."
        sudo systemctl stop odoo{odoo_version}dev

        log "Eliminando la base de datos {selected_db_dev}..."
        dropdb -p {db_port_dest} {selected_db_dev}

        log "Creando la nueva base de datos {selected_db_dev}..."
        createdb -p {db_port_dest} {selected_db_dev}

        log "Copiando el filestore de producción a desarrollo..."
        sudo cp -a /opt/odoo/odoo{odoo_version}/attachments/filestore/{selected_db_pro} /opt/odoo/odoo{odoo_version}dev/attachments/filestore/{selected_db_dev}

        log "Realizando el dump de la base de datos de producción..."
        pg_dump -p {db_port_origin} -Fc -Z4 -Od {selected_db_pro} > {selected_db_dev}.dmp

        log "Restaurando la base de datos en desarrollo..."
        pg_restore -j 4 -p {db_port_dest} -Od {selected_db_dev} {selected_db_dev}.dmp

        log "Ejecutando comandos adicionales en la base de datos {selected_db_dev}..."
        psql -p {db_port_dest} {selected_db_dev} <<EOF_SQL
        UPDATE ir_cron SET active = false;
        UPDATE ir_mail_server SET active = false;
        DELETE FROM ir_config_parameter WHERE key IN ('database.enterprise_code', 'odoo_ocn.project_id', 'mail_mobile.enable_ocn');
        EOF_SQL

        log "Iniciando de nuevo la instancia de Odoo..."
        sudo systemctl start odoo{odoo_version}dev

        log "Eliminando el archivo dump {selected_db_dev}.dmp..."
        rm -f {selected_db_dev}.dmp

        log "Proceso completado."
        """

        stdin, stdout, stderr = ssh.exec_command(action_script)
        stdout.channel.recv_exit_status()  # Wait for the command to complete

        logs = stdout.read().decode()
        messagebox.showinfo("Operación completada", f"Reemplazo de base de datos completado:\n{logs}")

    except Exception as e:
        messagebox.showerror("Error", f"Error al reemplazar la base de datos: {e}")


def copy_database(ssh, db_port_origin, db_port_dest, selected_db_pro, new_db_name, odoo_version):
    try:
        action_script = f"""
        LOG_FILE="copias_PRO2DEV_log"

        log() {{
            echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
        }}

        log "Creando la nueva base de datos {new_db_name}..."
        createdb -p {db_port_dest} {new_db_name}

        log "Copiando el filestore de producción a desarrollo..."
        cp -a /opt/odoo/odoo{odoo_version}/attachments/filestore/{selected_db_pro} /opt/odoo/odoo{odoo_version}dev/attachments/filestore/{new_db_name}

        log "Realizando el dump de la base de datos de producción..."
        pg_dump -p {db_port_origin} -Fc -Z4 -Od {selected_db_pro} > {new_db_name}.dmp

        log "Restaurando la base de datos en desarrollo..."
        pg_restore -j 4 -p {db_port_dest} -Od {new_db_name} {new_db_name}.dmp

        log "Ejecutando comandos adicionales en la base de datos {new_db_name}..."
        psql -p {db_port_dest} {new_db_name} <<EOF_SQL
        UPDATE ir_cron SET active = false;
        UPDATE ir_mail_server SET active = false;
        DELETE FROM ir_config_parameter WHERE key IN ('database.enterprise_code', 'odoo_ocn.project_id', 'mail_mobile.enable_ocn');
        EOF_SQL

        log "Iniciando de nuevo la instancia de Odoo..."
        sudo systemctl start odoo{odoo_version}dev

        log "Eliminando el archivo dump {new_db_name}.dmp..."
        rm -f {new_db_name}.dmp

        log "Proceso completado."
        """

        stdin, stdout, stderr = ssh.exec_command(action_script)
        stdout.channel.recv_exit_status()  # Wait for the command to complete

        logs = stdout.read().decode()
        messagebox.showinfo("Operación completada", f"Copia de base de datos completada:\n{logs}")

    except Exception as e:
        messagebox.showerror("Error", f"Error al copiar la base de datos: {e}")

