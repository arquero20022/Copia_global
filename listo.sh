#!/bin/bash

# Verifica si se proporcionan los argumentos correctos
if [ "$#" -ne 2 ]; then
    echo "Uso: $0 <directorio_origen> <directorio_destino>"
    exit 1
fi

# Asigna los argumentos a variables
SRC_DIR=$1
DEST_DIR=$2

# Verifica si el directorio origen existe
if [ ! -d "$SRC_DIR" ]; then
    echo "El directorio origen no existe: $SRC_DIR"
    exit 2
fi

# Crear el directorio destino si no existe
mkdir -p "$DEST_DIR"

# Convertir todos los enlaces simbólicos en archivos normales en el directorio origen
find "$SRC_DIR" -type l -print0 | while IFS= read -r -d $'\0' link; do
    target=$(readlink "$link")  # Encuentra el archivo original al que apunta el enlace
    if [ -f "$target" ]; then
        cp --remove-destination "$target" "$link"  # Copia el archivo sobre el enlace
        echo "Reemplazado: $link -> $target"
    else
        echo "El archivo objetivo no existe: $target"
    fi
done

# Copiar el directorio origen al destino
rsync -avz "$SRC_DIR/" "$DEST_DIR/"

echo "Operación completada. Directorio copiado de '$SRC_DIR' a '$DEST_DIR'."
