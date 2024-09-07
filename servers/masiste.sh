#!/bin/bash

# Script para establecer múltiples túneles SSH

# Definir la contraseña
PASSWORD='Ent3rprisa$x'

# Ejecutar el comando SSH con sshpass
sshpass -p "$PASSWORD" ssh -L9002:localhost:9002 -L9001:localhost:9001 -L 9999:localhost:9999 -L 9001:localhost:9001 -L 9002:localhost:9002 -L 9021:localhost:9021 -L 8069:localhost:8069 -L 10000:localhost:10000 -L 5432:localhost:5432 root@82.223.46.138 -p 22022
