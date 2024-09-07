#!/bin/bash

# Script para establecer múltiples túneles SSH

# Definir la contraseña
PASSWORD='Ent3rprisa$x'

# Ejecutar el comando SSH con sshpass
sshpass -p "$PASSWORD" ssh -L 8069:localhost:8069 -L 5432:localhost:5432 -L 9001:localhost:9001 -L 9002:localhost:9002 -L 10000:localhost:10000 root@82.223.3.191 -p 22022


