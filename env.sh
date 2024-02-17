#!/usr/bin/env bash

# based on linux distro, you need to have installed python3-venv package
# sudo pacman -S python3-venv   # archlinux
# sudo apt install python3-venv -y

# if WORKDIR is set, use it, otherwise running from local dir
if [ -z ${WORKDIR+x} ]; then
    #echo "var is unset";
    export WORKDIR="."
# else
#     # echo "var is set to '$WORKDIR'";
#     export WORKDIR="/home/pi/pv_heater_optimizer"
fi

export CONFIG_FILE="$WORKDIR/Files/config-private.yaml"

python -m venv venv
# echo $WORKDIR
source $WORKDIR/venv/bin/activate 2>&1 > /dev/null
#python3 -m pip install -r $WORKDIR/Files/requirements.txt 2>&1 > /dev/null
