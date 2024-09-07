import psycopg2
from psycopg2 import sql

def list_databases(user, host, port):
    # Conectar al servidor PostgreSQL
    conn = psycopg2.connect(dbname='postgres', user=user, host=host, port=port)
    conn.autocommit = True
    cursor = conn.cursor()

    # Obtener la lista de bases de datos
    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    databases = cursor.fetchall()

    # Mostrar las bases de datos
    print("Bases de datos existentes:")
    for db in databases:
        print(f"- {db[0]}")

    # Cerrar la conexión
    cursor.close()
    conn.close()

    return [db[0] for db in databases]

def check_database_exists(dbname, databases):
    return dbname in databases

# Parámetros de conexión
user = "odoo"
host = "postgres"
port = "5432"

# Listar bases de datos
existing_databases = list_databases(user, host, port)

# Pedir al usuario que ingrese el nombre de la base de datos
dbname_to_check = input("Introduce el nombre de la base de datos que deseas comprobar: ")

# Comprobación
if check_database_exists(dbname_to_check, existing_databases):
    print(f"La base de datos '{dbname_to_check}' existe.")
else:
    print(f"La base de datos '{dbname_to_check}' no existe.")
