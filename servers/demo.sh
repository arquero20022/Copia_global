#!/bin/bash

# Script para establecer múltiples túneles SSH

# Definir la contraseña
PASSWORD='Ent3rprisa$x'

# Ejecutar el comando SSH con sshpass
sshpass -p "$PASSWORD" ssh -L8169:localhost:8169 -L 8069:localhost:8069 -L 5432:localhost:5432 -L 10000:localhost:10000 root@185.47.131.223 -p 22022

