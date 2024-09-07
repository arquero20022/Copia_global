#!/bin/bash

# Definir variables
REMOTE_USER="odoo"
REMOTE_HOST="195.170.165.91"
REMOTE_PORT="2228"
SSH_KEY="~/.ssh/adrian"
REMOTE_CONF_FILE="odoo170dev/conf/odoo170dev.conf" # Cambia esta ruta al archivo de configuración en el servidor remoto

# Función para obtener la contraseña de admin desde el servidor remoto
obtener_contraseña_admin() {
    admin_password=$(ssh -i $SSH_KEY -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "grep 'admin_passwd' $REMOTE_CONF_FILE | cut -d '=' -f2 | tr -d ' '")
    echo "La contraseña del admin es: $admin_password"
}

# Ejecutar la función
obtener_contraseña_admin

