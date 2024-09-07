#!/bin/bash

# Script para establecer múltiples túneles SSH y descargar un archivo

# Definir la contraseña
PASSWORD='Ent3rprisa$x'

# Dirección del servidor y usuario
SERVER="82.223.3.191"
PORT="22022"
USER="root"
REMOTE_PATH="/tmp/res_partner.csv"
LOCAL_PATH="$HOME/Descargas/res_partner.csv"

# Ejecutar el comando SSH con sshpass para establecer túneles SSH
sshpass -p "$PASSWORD" ssh -L8169:localhost:8169 -L 8069:localhost:8069 -L 5432:localhost:5432 -L 10000:localhost:10000 $USER@$SERVER -p $PORT &

# Esperar un momento para asegurarse de que el túnel se establezca
sleep 5

# Descargar el archivo desde el servidor a la carpeta /Descargas
sshpass -p "$PASSWORD" scp -P $PORT $USER@$SERVER:$REMOTE_PATH $LOCAL_PATH

# Finalizar
echo "Archivo descargado en $LOCAL_PATH"

