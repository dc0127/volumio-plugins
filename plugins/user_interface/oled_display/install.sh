#!/bin/bash

echo "Installing oled display Dependencies"
sudo apt-get update
# Install the required packages via apt-get
sudo apt-get install -y python3 python3-dev python3-pip libfreetype6-dev libjpeg-dev zlib1g-dev build-essential raspi-config
sudo -H pip3 install --upgrade luma.oled Pillow

# If you need to differentiate install for armhf and i386 you can get the variable like this
#DPKG_ARCH=`dpkg --print-architecture`
# Then use it to differentiate your install

#requred to end the plugin install
echo "plugininstallend"
