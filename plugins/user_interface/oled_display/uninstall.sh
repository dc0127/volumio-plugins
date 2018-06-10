#!/bin/bash

# Uninstall dependendencies
sudo -H pip3 uninstall luma.oled Pillow
sudo apt-get remove -y python3 python3-dev python3-pip libfreetype6-dev libjpeg-dev zlib1g-dev build-essential raspi-config

echo "Done"
echo "pluginuninstallend"
