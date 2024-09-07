#!/bin/bash

# Definir variables
REMOTE_USER="odoo"
REMOTE_HOST="195.170.165.91"
REMOTE_PORT="2228"
SSH_KEY="~/.ssh/adrian"
DB_NAME="PRO" # Cambia esto al nombre de la base de datos que deseas hacer dump
DB_PORT="5432"
LOCAL_PATH="$HOME/Descargas" # Ruta local donde deseas guardar el dump
REMOTE_DUMP_PATH="/tmp" # Directorio temporal en el servidor remoto para guardar el dump
DUMP_FILE="${DB_NAME}.dmp"

# Crear el dump de la base de datos en el servidor remoto
echo "Conectando al servidor remoto para crear un dump de la base de datos..."
ssh -i $SSH_KEY -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST <<EOF
pg_dump -p $DB_PORT -Fc -Z4 -Od $DB_NAME > $REMOTE_DUMP_PATH/$DUMP_FILE
EOF

# Descargar el dump a tu máquina local
echo "Descargando el dump a la máquina local..."
scp -i $SSH_KEY -P $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST:$REMOTE_DUMP_PATH/$DUMP_FILE $LOCAL_PATH/

# Eliminar el archivo dump del servidor remoto
echo "Eliminando el archivo dump del servidor remoto..."
ssh -i $SSH_KEY -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST <<EOF
rm -f $REMOTE_DUMP_PATH/$DUMP_FILE
EOF

echo "Proceso completado. El archivo se ha descargado a $LOCAL_PATH/$DUMP_FILE"

