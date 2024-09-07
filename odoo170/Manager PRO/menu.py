import tkinter as tk
from tkinter import ttk
from to_me import run_to_me
from manager_local_database import run_manager_local_database
from manager_remote_database import run_manager_remote_database

def run_menu():
    # Inicializar Tkinter
    root = tk.Tk()
    root.title("Main Menu")

    # Configuración de tamaño de la ventana
    window_width = 300
    window_height = 200
    root.geometry(f'{window_width}x{window_height}+0+0')

    # Botón para ejecutar la aplicación principal
    to_me_button = ttk.Button(root, text="TO ME", command=run_to_me)
    to_me_button.pack(padx=10, pady=10, fill='x')

    # Botón para gestionar las bases de datos locales
    manager_db_button = ttk.Button(root, text="MANAGER LOCAL DATABASE", command=run_manager_local_database)
    manager_db_button.pack(padx=10, pady=10, fill='x')

    # Botón para gestionar las bases de datos remotas
    remote_db_button = ttk.Button(root, text="MANAGER REMOTE DATABASE", command=run_manager_remote_database)
    remote_db_button.pack(padx=10, pady=10, fill='x')

    # Botón de salir
    exit_button = ttk.Button(root, text="Salir", command=root.quit)
    exit_button.pack(padx=10, pady=10, fill='x')



    # Iniciar el bucle principal de Tkinter
    root.mainloop()

if __name__ == "__main__":
    run_menu()
