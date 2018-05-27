#!/usr/bin/env python3

import sys,io,os
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1322
from PIL import ImageFont


class OledDisplay:

    device = None
    fontFile = None

    def __init__(self):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer,encoding='utf8')
        serial = spi(device=0,port=0)
        self.device = ssd1322(serial)
        self.fontFile = os.path.dirname(os.path.abspath(__file__)) + "/Arial.ttf"


    def display(self,data):
        with canvas(self.device) as draw:
            font = ImageFont.truetype(self.fontFile, size=10)
            draw.text((0, 0), data, fill="white",font=font)


oled = OledDisplay()

while True:
    data = input()
    oled.display(data)
