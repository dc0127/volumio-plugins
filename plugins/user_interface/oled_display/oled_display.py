#!/usr/bin/env python3

import sys,io,os,threading,time,datetime,json,subprocess
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1322
from PIL import Image, ImageDraw, ImageFont

class OledDisplay(threading.Thread):
    DISPLAY_FPS = 20
    MOVE_PIXEL_PER_SECOND = 50
    MOVE_TEXT_DELAY = 5

    def __init__(self):
        threading.Thread.__init__(self)
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding="utf8")
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer,encoding="utf8")
        serial = spi(device=0,port=0)
        self.device = ssd1322(serial_interface = serial, mode = "1")
        self.icon_font = "iconfont.ttf"
        self.text_font = "NotoSansCJKsc-Regular.otf"
        self.service_status = "start"
        self.uri = ""
        self.status_thread = StatusThread()
        self.status_thread.start()

    def __refresh_status(self):
        try:
            status= self.status_thread.get_status()

            uri = status["uri"]
            if self.uri != uri:
                self.uri = uri
                self.__reset_title(status["title"])
                self.__reset_artist(status["artist"])

            self.status = status["status"]
            self.random = status["random"]
            self.repeat = status["repeat"]
            duration = status["duration"]
            seek = status["seek"]
            self.bar = (seek,duration*1000)
        except Exception as err:
            self.service_status = "error"

    def run(self):
        while True:
            self.__display()
            time.sleep(1/self.DISPLAY_FPS)

    def __reset_title(self,title):
        self.title = title
        self.title_cur_pos = 0
        self.__title_delay = 0

    def __reset_artist(self,artist):
        self.artist = artist
        self.artist_cur_pos = 0
        self.__artist_delay = 0

    def __make_font(self, name, size):
        font_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "fonts", name))
        return ImageFont.truetype(font_path, size)

    def __draw_status(self, text):
        font = self.__make_font(self.icon_font,48)
        self.draw.text((0, -2), text, fill="white", font=font)

    def __draw_text(self, text, text_size,text_image_height,target_text_area,start):
        text_len = len(text)
        text_image_width = text_len * text_size
        font = self.__make_font(self.text_font,text_size)
        text_image = Image.new("1", (text_image_width,text_image_height))
        draw = ImageDraw.Draw(text_image)
        draw.text((0, -5), text, fill="white", font=font)
        self.blank_image = Image.new("1", (50, text_image_height))
        self.__paste_text(text_image,target_text_area,start)

    def __get_title_position(self):
        tmp_pos = self.title_cur_pos
        if self.__title_delay < self.MOVE_TEXT_DELAY:
            self.__title_delay +=  self.MOVE_TEXT_DELAY/self.DISPLAY_FPS
        else:
            self.title_cur_pos += self.MOVE_PIXEL_PER_SECOND / self.DISPLAY_FPS
        return tmp_pos//1

    def __get_artist_position(self):
        tmp_pos = self.artist_cur_pos
        if self.__artist_delay < self.MOVE_TEXT_DELAY:
            self.__artist_delay +=  self.MOVE_TEXT_DELAY/self.DISPLAY_FPS
        else:
            self.artist_cur_pos += self.MOVE_PIXEL_PER_SECOND / self.DISPLAY_FPS
        return tmp_pos//1

    def __paste_text(self,text_image,target_text_area,start):
        if text_image.width > target_text_area[2] - target_text_area[0]:
            self.__crop_text(text_image,target_text_area,start, target_text_area[2] - target_text_area[0])
        else:
            self.__center_text(text_image,target_text_area)

    def  __draw_title(self, text):
        text_size = 22
        text_image_height = 29
        target_text_area = (55, 0, 225, text_image_height)
        self.__draw_text(text,text_size,text_image_height,target_text_area,self.__get_title_position())

    def __draw_artist(self, text):
        text_size = 15
        text_image_height = 20
        target_text_area = (55, 30, 225, 30+text_image_height)
        self.__draw_text(text,text_size,text_image_height,target_text_area,self.__get_artist_position())

    def __draw_random(self,  text):
        self.draw.text((235, 2), text, fill="white", font=self.__make_font(self.icon_font,20))

    def __draw_repeat(self, text):
        self.draw.text((235,20), text, fill="white", font=self.__make_font(self.icon_font,20))

    def __draw_bar(self):
        bar_start = 5
        bar_end = 250
        bar_width = bar_end - bar_start
        progress = bar_width * self.bar[0]/self.bar[1]
        bar_current = bar_start + progress
        if bar_current > bar_end:
            bar_current = bar_end
        self.draw.line([(bar_start,55),(bar_current,55)], fill="white", width=5)

    def __draw_banner(self):
        text_size =40
        font = self.__make_font(self.text_font,text_size)
        text_image_size = self.draw.textsize(self.banner, font=font)
        x=(self.device.width-text_image_size[0])//2
        y=(self.device.height-text_image_size[1])//2
        self.draw.text((x, y), self.banner, fill="white", font=font)

    def __crop_text(self,text_image,target_text_area,start, width):
        if (start + width) < text_image.width:
            crop_box = (start, 0, start + width, text_image.height)
            self.image.paste(text_image.crop(crop_box), target_text_area)
            #print("<",start + width,text_image.width)
        else:
            crop_box = (start, 0, text_image.width, text_image.height)
            ftont_image = text_image.crop(crop_box)
            front_box = self.__get_front_image_box(ftont_image,target_text_area)
            self.image.paste(ftont_image, front_box)

            blank_box = self.__get_append_image_box(front_box, self.blank_image)
            self.image.paste(self.blank_image, blank_box)
            crop_box = (0, 0, target_text_area[2] - blank_box[2], text_image.height)
            end_image = text_image.crop(crop_box)
            end_box = self.__get_append_image_box(blank_box, end_image)
            self.image.paste(end_image, end_box)
            #print(">",start + width,text_image.width)

    def __center_text(self,text_image,target_text_area):
        self.image.paste(text_image, self.__get_center_image_box(text_image,target_text_area))

    def __get_center_image_box(self,image,target_text_area):
        x0 = target_text_area[0] + (target_text_area[2] - target_text_area[0] - image.width) // 2
        return (x0, target_text_area[1], x0 + image.width, target_text_area[3])

    def __get_front_image_box(self,image,target_text_area):
        return (target_text_area[0], target_text_area[1], target_text_area[0] + image.width, target_text_area[3])

    def __get_append_image_box(self,front_box, image):
        return (front_box[2], front_box[1], front_box[2] + image.width, front_box[3])

    def __display(self):
        self.image = Image.new(self.device.mode, self.device.size)
        self.draw = ImageDraw.Draw(self.image)
        if self.service_status == "start":
            self.banner = "Starting..."
            self.__draw_banner()
        elif self.service_status == "stop":
            self.banner = "Stopping..."
            self.__draw_banner()
        elif self.service_status == "run":
            self.__refresh_status()
            # 绘制播放图标
            if self.status == "play":
                self.__draw_status("\ue63d")
            else:
                self.__draw_status("\ue67d")
            # 绘制随机图标
            if self.random:
                self.__draw_random("\ue7b8")
            # 绘制重复图标
            if self.repeat:
                self.__draw_repeat("\ue614")
            # 绘制标题
            self.__draw_title(self.title)
            # 绘制艺术家
            self.__draw_artist(self.artist)
            # 绘制时间进度条
            self.__draw_bar()
        else:
            self.banner = self.service_status
            self.__draw_banner()

        self.device.display(self.image)

class StatusThread(threading.Thread):
    STATUS_REFRESH_INTERVAL = 1
    __status = None

    def run(self):
        while True:
            popen = subprocess.Popen("volumio status", stdout=subprocess.PIPE,shell=True)
            data = popen.stdout.read()
            self.__status = json.loads(str(data,encoding="utf-8"))
            time.sleep(self.STATUS_REFRESH_INTERVAL)

    def get_status(self):
        return self.__status


oled = OledDisplay()
oled.start()

while True:
    #command = input()
    time.sleep(1)
    command = "run"
    oled.service_status = command

