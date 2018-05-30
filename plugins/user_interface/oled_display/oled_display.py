#!/usr/bin/env python3

import sys,io,os
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1322
from PIL import ImageFont

class OledDisplay:

    device = None
    icon_font = "iconfont.ttf"
    text_font = "NotoSansCJKsc-Regular.otf"

    def __init__(self):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding="utf8")
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer,encoding="utf8")
        serial = spi(device=0,port=0)
        self.device = ssd1322(serial_interface = serial, mode = "1")

    def make_font(self, name, size):
        font_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "fonts", name))
        return ImageFont.truetype(font_path, size)

    def draw_play(self, draw, text):
        font = self.make_font(self.icon_font,48)
        draw.text((0, -2), text, fill="white", font=font)

    def draw_title(self, draw, text):
        font = self.make_font(self.text_font,20)
        text_size = draw.textsize(text, font=font)
        text_width = text_size[0]
        device_width = self.device.size[0]
        text_pos_w = (device_width-text_width)/2
        draw.text((text_pos_w, 0), text, fill="white", font=font)

    def draw_artist(self, draw, text):
        font = self.make_font(self.text_font,15)
        text_size = draw.textsize(text, font=font)
        text_width = text_size[0]
        device_width = self.device.size[0]
        text_pos_w = (device_width-text_width)/2
        draw.text((text_pos_w, 25), text, fill="white", font=font)

    def draw_random(self, draw, text):
        draw.text((235, 2), text, fill="white", font=self.make_font(self.icon_font,20))

    def draw_repeat(self, draw, text):
        draw.text((235,20), text, fill="white", font=self.make_font(self.icon_font,20))

    def draw_bar(self, draw):
        draw.line([(5,55),(156,55)], fill="white", width=5)

    def display(self, data):
        with canvas(self.device) as draw:
            # 绘制播放图标
            self.draw_play(draw, "\ue63d")
            # 绘制标题
            self.draw_title(draw, "生命中的精灵")
            # 绘制艺术家
            self.draw_artist(draw, "李宗盛")
            # 绘制随机图标
            self.draw_random(draw, "\ue7b8")
            # 绘制重复图标
            self.draw_repeat(draw, "\ue614")
            # 绘制时间进度条
            self.draw_bar(draw)


oled = OledDisplay()

while True:
    data = input()
    oled.display('{"status":"play","position":0,"title":"你怎么舍得我难过 ","artist":"黄品源","album":"情歌101","albumart":"/albumart?cacheid=973&web=%E9%BB%84%E5%93%81%E6%BA%90/%E6%83%85%E6%AD%8C101/extralarge&path=%2FNAS%2Fmusic%2FPop%2F%E6%83%85%E6%AD%8C101(Disc%201)&metadata=true","uri":"mnt/NAS/music/Pop/情歌101(Disc 1)/01 黄品源 - 你怎么舍得我难过 .m4a","trackType":"m4a","seek":464,"duration":294,"samplerate":"44.1 KHz","bitdepth":"16 bit","channels":2,"random":false,"repeat":false,"repeatSingle":false,"consume":false,"volume":0,"mute":false,"stream":"m4a","updatedb":false,"volatile":false,"service":"mpd"}')
