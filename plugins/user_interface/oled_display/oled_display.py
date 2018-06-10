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
    DISPLAY_FPS = 25

    # 空白图片宽度（单位：像素）
    BLANK_IMAGE_WIDTH = 50

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
        self.title_text_window = TextWindow(self.DISPLAY_FPS)
        self.artist_text_window = TextWindow(self.DISPLAY_FPS)

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
            self._title = status["title"]
            self.title_text_window.reset()
            self._artist = status["artist"]
            self.artist_text_window.reset()

        self._status = status["status"]
        self._random = status["random"]
        self._repeat = status["repeat"]
        duration = status["duration"]
        seek = status["seek"]
        self._bar = (seek, duration * 1000)

    @staticmethod
    def _make_font(name, size):
        font_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "fonts", name))
        return ImageFont.truetype(font_path, size)

    def _draw_status(self, text):
        font = self._make_font(self.__icon_font, 48)
        self.__draw.text((0, -2), text, fill="white", font=font)

    def _draw_title(self, text):
        text_size = 22
        font = self._make_font(self.__text_font, text_size)
        text_image_size = font.getsize(text)
        target_text_area = (55, 0, 225, text_image_size[1])
        text_image = Image.new("1", text_image_size)
        draw = ImageDraw.Draw(text_image)
        draw.text((0, -5), text, fill="white", font=font)
        self.__paste_text(text_image, target_text_area, self.title_text_window)

    def _draw_artist(self, text):
        text_size = 15
        font = self._make_font(self.__text_font, text_size)
        text_image_size = font.getsize(text)
        target_text_area = (55, 30, 225, 30 + text_image_size[1])
        text_image = Image.new("1", text_image_size)
        draw = ImageDraw.Draw(text_image)
        draw.text((0, -5), text, fill="white", font=font)
        self.__paste_text(text_image, target_text_area, self.artist_text_window)

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

    def __paste_text(self, text_image, target_text_area, text_window):
        if text_image.width > target_text_area[2] - target_text_area[0]:
            self.__crop_text(text_image, target_text_area, text_window)
        else:
            self.__center_text(text_image, target_text_area)

    def __crop_text(self, text_image, target_text_area, text_window):
        text_image_with_blank = Image.new("1", (text_image.width + self.BLANK_IMAGE_WIDTH, text_image.height))
        text_image_with_blank.paste(text_image, (0, 0, text_image.width, text_image.height))

        text_window.image_width = text_image_with_blank.width
        text_area_width = target_text_area[2] - target_text_area[0]

        if (text_window.get_position() + text_area_width) < text_image_with_blank.width:
            crop_box = (text_window.get_position(), 0,
                        text_window.get_position() + text_area_width, text_image_with_blank.height)
            self.__image.paste(text_image_with_blank.crop(crop_box), target_text_area)
        else:
            crop_box = (text_window.get_position(), 0, text_image_with_blank.width, text_image_with_blank.height)
            front_image = text_image_with_blank.crop(crop_box)
            front_box = (target_text_area[0], target_text_area[1],
                         target_text_area[0] + front_image.width, target_text_area[3])
            self.__image.paste(front_image, front_box)

            crop_box = (0, 0, target_text_area[2] - front_box[2], text_image_with_blank.height)
            end_image = text_image_with_blank.crop(crop_box)
            end_box = (front_box[2], front_box[1], front_box[2] + end_image.width, front_box[3])
            self.__image.paste(end_image, end_box)

        text_window.move()

    def __center_text(self, text_image, target_text_area):
        x0 = target_text_area[0] + (target_text_area[2] - target_text_area[0] - text_image.width) // 2
        self.__image.paste(text_image, (x0, target_text_area[1], x0 + text_image.width, target_text_area[3]))


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


class TextWindow(object):
    # 文字每秒滚动的像素数，决定滚动文字的速度
    MOVE_PIXEL_PER_SECOND = 50
    # 开始播放音轨后，如果标题文字过长，延迟几秒后再滚动文字
    MOVE_TEXT_DELAY = 5

    __cur_pos = 0
    __delay = 0
    image_width = 0

    def __init__(self, fps):
        self.__fps = fps

    def reset(self):
        self.__cur_pos = 0
        self.__delay = 0

    def move(self):
        if self.__delay < self.MOVE_TEXT_DELAY:
            self.__delay += self.MOVE_TEXT_DELAY / self.__fps
        else:
            self.__cur_pos += self.MOVE_PIXEL_PER_SECOND / self.__fps

        if self.__cur_pos > self.image_width:
            self.reset()

    def get_position(self):
        return self.__cur_pos // 1


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
