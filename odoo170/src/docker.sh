#!/bin/bash
# set -ux

# Este script será ejecutado al inicio de arrancar el docker,
# se ejecutará con permisos de root y su finalidad es hacer lo que se
# necesite para que funcione Odoo y sea algo excepcional, como instalar
# alguna librería o pip adicional extra. Se instalará en la imagen docker
# y será persistente mientras no se destruya la imagen, bien por actualización
# o de forma manual. Se incluyen abajo ejemplos de apt, pip y npm.

# # apt
# packages=('package1' 'package2' 'package3')
# installed_packages=$(dpkg --get-selections | grep -iFw install | cut -f 1)
# install=()
# for package in "${packages[@]}"; do
#   if ! echo "${installed_packages}" | grep -iFq "${package}"; then
#     install+=("${package}")
#   fi
# done
# if [[ ${#install[@]} -gt 0 ]]; then
#   apt update && apt install -y --no-install-suggests --no-install-recommends "${install[@]}"
# fi

# # pip
# # pip2 para python2
# packages=('package1' 'package2' 'package3==1.5')
# installed_packages=$(pip freeze)
# install=()
# for package in "${packages[@]}"; do
#   if ! echo "${installed_packages}" | grep -iq "^${package}==\|^${package}"; then
#     install+=("${package}")
#   fi
# done
# if [[ ${#install[@]} -gt 0 ]]; then
#   pip install --no-cache-dir "${install[@]}"
# fi

# # npm
# packages=('package1' 'package2' 'less@<4')
# installed_packages=$(npm ls -glp --depth=0 | tail -n +2 | cut -d: -f2)
# install=()
# for package in "${packages[@]}"; do
#   if ! echo "${installed_packages}" | grep -iq "^${package}@\|^${package}"; then
#     install+=("${package}")
#   fi
# done
# if [[ ${#install[@]} -gt 0 ]]; then
#   npm install -g "${install[@]}"
# fi
