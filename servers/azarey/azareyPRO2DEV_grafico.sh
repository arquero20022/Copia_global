#!/bin/bash

# Verificar que zenity esté instalado
if ! command -v zenity &> /dev/null; then
    echo "Zenity no está instalado. Por favor, instálalo e intenta nuevamente."
    exit 1
fi

# Definir variables
REMOTE_USER="odoo"
REMOTE_HOST="195.170.165.86"
REMOTE_PORT="2228"
SSH_KEY="~/.ssh/adrian"
REMOTE_SCRIPT="todev.sh"


# Valores estáticos
odoo_version="170"
puerto_origen="5432"
puerto_destino="5433"

# Función para validar entradas
validate_input() {
    while [[ -z "$1" ]]; do
        input_value=$(zenity --entry --title "Entrada requerida" --text "$2")
        set -- "$input_value" "$2"
    done
    eval "$3='$1'"
}

# Función para listar bases de datos en el servidor remoto
list_databases() {
    local db_port="$1"
    ssh -i $SSH_KEY -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "psql -p $db_port -lqt | awk '{print \$1}' | grep -vwE 'template0|template1|postgres|^$'"
}

# Función para comprobar si una base de datos existe en el servidor remoto
check_db_exists() {
    local db_name="$1"
    local db_port="$2"
    ssh -i $SSH_KEY -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "psql -p $db_port -lqt | awk '{print \$1}' | grep -qw $db_name"
}

# Función para seleccionar una base de datos de una lista
select_database() {
    local db_port="$1"
    options=($(list_databases "$db_port"))
    db_name=$(zenity --list --title "Seleccione una base de datos" --column "Bases de datos" "${options[@]}")
    echo "$db_name"
}

# Obtener la fecha actual en el formato deseado
fecha_actual=$(date +'%d%m')

# Preguntar al usuario si desea reemplazar una base de datos o hacer una copia
action=$(zenity --list --radiolist --title "Seleccione una opción" --text "¿Desea reemplazar una base de datos existente o Crear una nueva con datos de PRODUCCION en DESARROLLO con un nuevo nombre?" --column "Seleccione" --column "Acción" TRUE "Reemplazar" FALSE "Crear")

case $action in
    "Reemplazar")
        # Opción de reemplazar una base de datos existente
        zenity --info --text "Seleccione la base de datos de producción (PRO):"
        db_pro=$(select_database "$puerto_origen")
        
        while true; do
            if check_db_exists "$db_pro" "$puerto_origen"; then
                break
            else
                zenity --error --text "La base de datos $db_pro no existe en el puerto $puerto_origen. Por favor, seleccione un nombre válido."
                db_pro=$(select_database "$puerto_origen")
            fi
        done

        zenity --info --text "Seleccione la base de datos de desarrollo (DEV):"
        db_dev=$(select_database "$puerto_destino")

        while true; do
            if check_db_exists "$db_dev" "$puerto_destino"; then
                break
            else
                zenity --error --text "La base de datos $db_dev no existe en el puerto $puerto_destino. Por favor, seleccione un nombre válido."
                db_dev=$(select_database "$puerto_destino")
            fi
        done

        backup_dev=$(zenity --question --title "Respaldo" --text "¿Desea realizar un respaldo de la base de datos de desarrollo antes de reemplazarla?" --ok-label "Sí" --cancel-label "No")
        if [[ $? -eq 0 ]]; then
            db_backup="${db_dev}_backup_${fecha_actual}"
            backup_db="s"
        else
            backup_db="n"
        fi

        db_dev_new="$db_dev"
        eliminar_db_dev="s"
        ;;

    "Crear")
        # Opción de hacer una copia de producción a desarrollo con un nuevo nombre
        zenity --info --text "Seleccione la base de datos de producción (PRO):"
        db_pro=$(select_database "$puerto_origen")
        
        while true; do
            if check_db_exists "$db_pro" "$puerto_origen"; then
                break
            else
                zenity --error --text "La base de datos $db_pro no existe en el puerto $puerto_origen. Por favor, seleccione un nombre válido."
                db_pro=$(select_database "$puerto_origen")
            fi
        done

        db_dev_new_base=$(zenity --entry --title "Nueva base de datos de desarrollo" --text "Ingrese el nombre para la nueva base de datos de desarrollo:")
        validate_input "$db_dev_new_base" "Ingrese el nombre para la nueva base de datos de desarrollo:" db_dev_new_base
        
        while true; do
            if check_db_exists "${db_dev_new_base}_${fecha_actual}" "$puerto_destino"; then
                zenity --error --text "La base de datos ${db_dev_new_base}_${fecha_actual} ya existe en el puerto $puerto_destino. Por favor, ingrese un nombre que no exista."
                db_dev_new_base=$(zenity --entry --title "Nueva base de datos de desarrollo" --text "Ingrese el nombre para la nueva base de datos de desarrollo:")
                validate_input "$db_dev_new_base" "Ingrese el nombre para la nueva base de datos de desarrollo:" db_dev_new_base
            else
                break
            fi
        done

        db_dev_new="${db_dev_new_base}_${fecha_actual}"
        eliminar_db_dev="n"
        db_dev="db_dev_new"  # No necesitamos db_dev en este caso
        ;;

    *)
        zenity --error --text "Opción no válida. Saliendo."
        exit 1
        ;;
esac

# Preguntar al usuario si desea ejecutar el script
if [[ $action == "Reemplazar" ]]; then
    zenity --question --title "Confirmación" --text "¿Está seguro que quiere reemplazar el contenido de la base de datos de DESARROLLO: ($db_dev) por el contenido de la base de datos de PRODUCCION: ($db_pro)?"
else
    zenity --question --title "Confirmación" --text "¿Desea crear la base de datos en DESARROLLO: ($db_dev_new) con los datos de la base de datos de PRODUCCION: ($db_pro)?"
fi

if [[ $? -eq 0 ]]; then
    # Conectar al servidor remoto y crear el archivo todev.sh
    ssh -i $SSH_KEY -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST <<EOF
cat > $REMOTE_SCRIPT <<'EOL'
#!/bin/bash

# Nombre del archivo de log
LOG_FILE="copias_PRO2DEV_log"

# Función para escribir en el log
log() {
    echo "\$(date +'%Y-%m-%d %H:%M:%S') - \$1" >> \$LOG_FILE
}

# Recibir parámetros
odoo_version=\$1
puerto_origen=\$2
puerto_destino=\$3
db_pro=\$4
db_dev=\$5
db_dev_new=\$6
eliminar_db_dev=\$7
backup_db=\$8
db_backup=\$9

# Detener la instancia de Odoo a eliminar
log "######################## NUEVO INICIO DE SCRIPT ########################"
log "Deteniendo la instancia de Odoo odoo\${odoo_version}dev..."
sudo su <<EOF_INNER
systemctl stop odoo\${odoo_version}dev
exit
EOF_INNER

# Realizar respaldo si se seleccionó
if [ "\$backup_db" == "s" ]; then
    log "Realizando respaldo de la base de datos \${db_dev}..."
    pg_dump -p \${puerto_destino} -Fc -Z4 -Od \${db_dev} > \${db_backup}.dmp
    log "Respaldo completado: \${db_backup}.dmp"
fi

# Eliminar la base de datos DEV si el usuario eligió eliminarla
if [ "\$eliminar_db_dev" == "s" ]; then
    log "Eliminando la base de datos \${db_dev}..."
    dropdb -p \${puerto_destino} \${db_dev}
    
    # Limpiar el filestore de la instancia
    log "Limpiando el filestore de la instancia..."
    sudo su <<EOF_INNER
    rm -rf /opt/odoo/odoo\${odoo_version}dev/attachments/filestore/\${db_dev}
    exit
EOF_INNER
else
    log "No se eliminará la base de datos \${db_dev}."
fi

# Crear la nueva base de datos DEV_neutralizada
log "Creando la nueva base de datos \${db_dev_new}..."
createdb -p \${puerto_destino} \${db_dev_new}

# Copiar el filestore deseado
log "Copiando el filestore de producción a desarrollo..."
sudo su <<EOF_INNER
cp -a /opt/odoo/odoo\${odoo_version}/attachments/filestore/\${db_pro} /opt/odoo/odoo\${odoo_version}dev/attachments/filestore/\${db_dev_new}
exit
EOF_INNER

# Realizar el dump de la base de datos
log "Realizando el dump de la base de datos de producción..."
pg_dump -p \${puerto_origen} -Fc -Z4 -Od \${db_pro} > \${db_dev_new}.dmp

# Restaurar la base de datos
log "Restaurando la base de datos en desarrollo..."
pg_restore -j 4 -p \${puerto_destino} -Od \${db_dev_new} \${db_dev_new}.dmp

# Ejecutar comandos adicionales en la base de datos restaurada
log "Ejecutando comandos adicionales en la base de datos \${db_dev_new}..."
psql -p \${puerto_destino} \${db_dev_new} <<EOF_SQL
UPDATE ir_cron SET active = false;
UPDATE ir_mail_server SET active = false;
DELETE FROM ir_config_parameter WHERE key IN ('database.enterprise_code', 'odoo_ocn.project_id', 'mail_mobile.enable_ocn');
EOF_SQL

# Iniciar de nuevo Odoo
log "Iniciando de nuevo la instancia de Odoo odoo\${odoo_version}dev..."
sudo su <<EOF_INNER
systemctl start odoo\${odoo_version}dev
exit
EOF_INNER

# Eliminar el dump después de restaurar la base de datos
log "Eliminando el archivo dump \${db_dev_new}.dmp..."
rm -f \${db_dev_new}.dmp

log "Proceso completado."
EOL
chmod +x $REMOTE_SCRIPT
EOF

    # Ejecutar el script en el servidor remoto con los parámetros proporcionados
    ssh -i $SSH_KEY -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST <<EOF
./$REMOTE_SCRIPT $odoo_version $puerto_origen $puerto_destino $db_pro $db_dev $db_dev_new $eliminar_db_dev $backup_db $db_backup
# Borrar el archivo después de la ejecución
rm -f $REMOTE_SCRIPT
EOF
    zenity --info --text "El script se ha ejecutado y eliminado correctamente."

else
    zenity --info --text "El script no se ha ejecutado. El archivo $REMOTE_SCRIPT sigue en el servidor."
fi

