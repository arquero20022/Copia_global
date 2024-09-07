import os
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2

def delete_database(dbname):
    try:
        # Intenta eliminar la base de datos
        drop_db_command = [
            "dropdb",
            "-h", "postgres",
            "-U", "odoo",
            "-p", "5432",
            dbname
        ]
        subprocess.run(drop_db_command, check=True)
        messagebox.showinfo("Éxito", f"Base de datos {dbname} eliminada exitosamente.")
    except subprocess.CalledProcessError:
        messagebox.showwarning("Aviso", f"La base de datos {dbname} no existe o no pudo ser eliminada.")

def delete_filestore(filestore_path, dbname):
    # Eliminar la carpeta filestore si existe
    if os.path.exists(filestore_path):
        shutil.rmtree(filestore_path)
        messagebox.showinfo("Éxito", f"Carpeta filestore para {dbname} eliminada exitosamente.")
    else:
        messagebox.showwarning("Aviso", f"No se encontró una carpeta filestore para {dbname}.")

def list_filestore_names(local_path):
    # Obtener los nombres de las carpetas en el filestore
    filestore_path = os.path.join(local_path, "filestore")
    try:
        return [name for name in os.listdir(filestore_path) if os.path.isdir(os.path.join(filestore_path, name))]
    except FileNotFoundError:
        messagebox.showerror("Error", "No se encontró el directorio filestore.")
        return []

def run_manager_local_database():
    root = tk.Toplevel()
    root.title("Manager Local Database")

    window_width = 400
    window_height = 300
    root.geometry(f'{window_width}x{window_height}+0+0')

    db_port = 5432

    # Opciones de versión de Odoo
    odoo_versions = ["80", "90", "100", "110", "120", "130", "140", "150", "160", "170"]

    # Selección de versión de Odoo
    version_label = ttk.Label(root, text="Selecciona la versión de Odoo:")
    version_label.pack(padx=10, pady=10)

    version_var = tk.StringVar()
    version_dropdown = ttk.Combobox(root, values=odoo_versions, state="readonly", textvariable=version_var)
    version_dropdown.pack(padx=10, pady=10)

    database_dropdown = ttk.Combobox(root, state="readonly")
    database_dropdown.pack(padx=10, pady=10)

    def update_filestore_list(*args):
        selected_version = version_var.get()
        if selected_version:
            local_path = f"/opt/sources/odoo{selected_version}/attachments"
            databases = list_filestore_names(local_path)
            database_dropdown['values'] = databases
            database_dropdown.set('')

    version_var.trace('w', update_filestore_list)

    def delete_selected_database_and_filestore():
        selected_version = version_var.get()
        dbname = database_dropdown.get()
        if selected_version and dbname:
            local_path = f"/opt/sources/odoo{selected_version}/attachments"
            filestore_path = os.path.join(local_path, "filestore", dbname)

            result = messagebox.askyesno("Confirmación", f"¿Estás seguro de que deseas eliminar la base de datos '{dbname}' y su filestore?")
            if result:
                delete_database(dbname)
                delete_filestore(filestore_path, dbname)
                # Actualizar la lista de bases de datos después de la eliminación
                update_filestore_list()
        else:
            messagebox.showwarning("Advertencia", "Por favor selecciona una versión y una base de datos.")

    delete_button = ttk.Button(root, text="Eliminar", command=delete_selected_database_and_filestore)
    delete_button.pack(padx=10, pady=10, fill='x')

    exit_button = ttk.Button(root, text="Salir", command=root.destroy)
    exit_button.pack(padx=10, pady=10, fill='x')

    root.mainloop()
