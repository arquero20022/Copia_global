#!/bin/bash

# Script para establecer múltiples túneles SSH

# Definir la contraseña
PASSWORD='Ent3rprisa$x'

# Ejecutar el comando SSH con sshpass
sshpass -p "$PASSWORD" ssh -L 8069:localhost:8069 \
    -L 8200:localhost:8200 \
    -L 9001:localhost:9001 \
    -L 9002:localhost:9002 \
    -L 9003:localhost:9003 \
    -L 9004:localhost:9004 \
    -L 9005:localhost:9005 \
    -L 9006:localhost:9006 \
    -L 5432:localhost:5432 \
    -L 10000:localhost:10000 \
    -L 5555:localhost:5555 \
    -p 22022 root@82.223.3.67

