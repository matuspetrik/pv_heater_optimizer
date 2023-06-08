#!/usr/bin/env bash

# based on linux distro, you need to have installed python3-venv package
# sudo pacman -S python3-venv   # archlinux
# sudo apt install python3-venv -y

export CONFIG_FILE="Files/config.yaml"

python -m venv venv
source venv/bin/activate
python3 -m pip install -r Files/requirements.txt
