#!/usr/bin/env python3

import io
import json
import os
import subprocess
import sys
import threading
import time

from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322


class OledDisplay(threading.Thread):
    # 显示刷新率
    DISPLAY_FPS = 20
    # 文字每秒滚动的像素数，决定滚动文字的速度
    MOVE_PIXEL_PER_SECOND = 50
    # 开始播放音轨后，如果标题文字过长，延迟几秒后再滚动文字
    MOVE_TEXT_DELAY = 5

    def __init__(self):
        threading.Thread.__init__(self)
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf8")
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf8")
        serial = spi(device=0, port=0)
        self._device = ssd1322(serial_interface=serial, mode="1")
        self._display_mode = "start"
        self.__icon_font = "iconfont.ttf"
        self.__text_font = "NotoSansCJKsc-Regular.otf"
        self.__uri = ""
        self.__status_monitor = StatusMonitor()
        self.__status_monitor.start()

    def run(self):
        while True:
            self._display()
            time.sleep(1 / self.DISPLAY_FPS)

    def _display(self):
        self.__image = Image.new(self._device.mode, self._device.size)
        self.__draw = ImageDraw.Draw(self.__image)
        if self._display_mode == "start":
            self._banner = "Starting..."
            self._draw_banner()
        elif self._display_mode == "stop":
            self._banner = "Stopping..."
            self._draw_banner()
        elif self._display_mode == "run":
            self._refresh_status()
            # 绘制播放图标
            if self._status == "play":
                self._draw_status("\ue63d")
            else:
                self._draw_status("\ue67d")
            # 绘制随机图标
            if self._random:
                self._draw_random("\ue7b8")
            # 绘制重复图标
            if self._repeat:
                self._draw_repeat("\ue614")
            # 绘制标题
            self._draw_title(self._title)
            # 绘制艺术家
            self._draw_artist(self._artist)
            # 绘制时间进度条
            self._draw_bar()
        else:
            self._banner = self._display_mode
            self._draw_banner()

        self._device.display(self.__image)

    def _refresh_status(self):
        status = self.__status_monitor.get_status()
        uri = status["uri"]
        if self.__uri != uri:
            self.__uri = uri
            self.__reset_title(status["title"])
            self.__reset_artist(status["artist"])

        self._status = status["status"]
        self._random = status["random"]
        self._repeat = status["repeat"]
        duration = status["duration"]
        seek = status["seek"]
        self._bar = (seek, duration * 1000)

    def __reset_title(self, title):
        self._title = title
        self.__title_cur_pos = 0
        self.__title_delay = 0

    def __reset_artist(self, artist):
        self._artist = artist
        self.__artist_cur_pos = 0
        self.__artist_delay = 0

    @staticmethod
    def _make_font(name, size):
        font_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "fonts", name))
        return ImageFont.truetype(font_path, size)

    def _draw_status(self, text):
        font = self._make_font(self.__icon_font, 48)
        self.__draw.text((0, -2), text, fill="white", font=font)

    def __draw_text(self, text, text_size, text_image_height, target_text_area, start):
        font = self._make_font(self.__text_font, text_size)
        text_image_size = font.getsize(text)
        text_image = Image.new("1", text_image_size)
        draw = ImageDraw.Draw(text_image)
        draw.text((0, -5), text, fill="white", font=font)
        print(text_image, draw.textsize(text, font=font))
        self.__blank_image = Image.new("1", (50, text_image_size[1]))
        self.__paste_text(text_image, target_text_area, start)

    def _draw_title(self, text):
        text_size = 22
        font = self._make_font(self.__text_font, text_size)
        text_image_size = font.getsize(text)
        target_text_area = (55, 0, 225, text_image_size[1])
        text_image = Image.new("1", text_image_size)
        draw = ImageDraw.Draw(text_image)
        draw.text((0, -5), text, fill="white", font=font)
        print(text_image, draw.textsize(text, font=font))
        self.__blank_image = Image.new("1", (50, text_image_size[1]))
        self.__paste_text(text_image, target_text_area, self.__get_title_position())

    def _draw_artist(self, text):
        text_size = 15
        font = self._make_font(self.__text_font, text_size)
        text_image_size = font.getsize(text)
        target_text_area = (55, 30, 225, 30 + text_image_size[1])
        text_image = Image.new("1", text_image_size)
        draw = ImageDraw.Draw(text_image)
        draw.text((0, -5), text, fill="white", font=font)
        print(text_image, draw.textsize(text, font=font))
        self.__blank_image = Image.new("1", (50, text_image_size[1]))
        self.__paste_text(text_image, target_text_area, self.__get_artist_position())

    def _draw_random(self, text):
        self.__draw.text((235, 2), text, fill="white", font=self._make_font(self.__icon_font, 20))

    def _draw_repeat(self, text):
        self.__draw.text((235, 20), text, fill="white", font=self._make_font(self.__icon_font, 20))

    def _draw_bar(self):
        bar_start = 5
        bar_end = 250
        bar_width = bar_end - bar_start
        progress = bar_width * self._bar[0] / self._bar[1]
        bar_current = bar_start + progress
        if bar_current > bar_end:
            bar_current = bar_end
        self.__draw.line([(bar_start, 55), (bar_current, 55)], fill="white", width=5)

    def _draw_banner(self):
        text_size = 40
        font = self._make_font(self.__text_font, text_size)
        text_image_size = self.__draw.textsize(self._banner, font=font)
        x = (self._device.width - text_image_size[0]) // 2
        y = (self._device.height - text_image_size[1]) // 2
        self.__draw.text((x, y), self._banner, fill="white", font=font)

    def __get_title_position(self):
        tmp_pos = self.__title_cur_pos
        if self.__title_delay < self.MOVE_TEXT_DELAY:
            self.__title_delay += self.MOVE_TEXT_DELAY / self.DISPLAY_FPS
        else:
            self.__title_cur_pos += self.MOVE_PIXEL_PER_SECOND / self.DISPLAY_FPS
        return tmp_pos // 1

    def __get_artist_position(self):
        tmp_pos = self.__artist_cur_pos
        if self.__artist_delay < self.MOVE_TEXT_DELAY:
            self.__artist_delay += self.MOVE_TEXT_DELAY / self.DISPLAY_FPS
        else:
            self.__artist_cur_pos += self.MOVE_PIXEL_PER_SECOND / self.DISPLAY_FPS
        return tmp_pos // 1

    def __paste_text(self, text_image, target_text_area, start):
        if text_image.width > target_text_area[2] - target_text_area[0]:
            self.__crop_text(text_image, target_text_area, start, target_text_area[2] - target_text_area[0])
        else:
            self.__center_text(text_image, target_text_area)

    def __crop_text(self, text_image, target_text_area, start, width):
        if (start + width) < text_image.width:
            crop_box = (start, 0, start + width, text_image.height)
            self.__image.paste(text_image.crop(crop_box), target_text_area)
            # print("<",start + width,text_image.width)
        else:
            crop_box = (start, 0, text_image.width, text_image.height)
            ftont_image = text_image.crop(crop_box)
            front_box = self.__get_front_image_box(ftont_image, target_text_area)
            self.__image.paste(ftont_image, front_box)

            blank_box = self.__get_append_image_box(front_box, self.__blank_image)
            self.__image.paste(self.__blank_image, blank_box)
            crop_box = (0, 0, target_text_area[2] - blank_box[2], text_image.height)
            end_image = text_image.crop(crop_box)
            end_box = self.__get_append_image_box(blank_box, end_image)
            self.__image.paste(end_image, end_box)
            # print(">",start + width,text_image.width)

    def __center_text(self, text_image, target_text_area):
        self.__image.paste(text_image, self.__get_center_image_box(text_image, target_text_area))
        print(text_image, self.__get_center_image_box(text_image, target_text_area), target_text_area)

    @staticmethod
    def __get_center_image_box(image, target_text_area):
        x0 = target_text_area[0] + (target_text_area[2] - target_text_area[0] - image.width) // 2
        return x0, target_text_area[1], x0 + image.width, target_text_area[3]

    @staticmethod
    def __get_front_image_box(image, target_text_area):
        return target_text_area[0], target_text_area[1], target_text_area[0] + image.width, target_text_area[3]

    @staticmethod
    def __get_append_image_box(front_box, image):
        return front_box[2], front_box[1], front_box[2] + image.width, front_box[3]


class StatusMonitor(threading.Thread):
    STATUS_REFRESH_INTERVAL = 1
    __status = None

    def run(self):
        while True:
            popen = subprocess.Popen("volumio status", stdout=subprocess.PIPE, shell=True)
            data = popen.stdout.read()
            self.__status = json.loads(str(data, encoding="utf-8"))
            time.sleep(self.STATUS_REFRESH_INTERVAL)

    def get_status(self):
        return self.__status


def main():
    oled = OledDisplay()
    oled.start()

    while True:
        # command = input()
        time.sleep(1)
        command = "run"
        oled._display_mode = command


if __name__ == '__main__':
    main()
