#!/usr/bin/env python3
import threading,time

class mainThread(threading.Thread):
    def run(self):
        status = StatusThread()
        status.start()
        text = TextThread()
        text.start()
        i = 0
        while True:
            time.sleep(0.1)
            print("main",status.status,text.pos)
            if i%10 == 0:
                text.set_length(100)
            i += 1

class StatusThread(threading.Thread):
    status = "play"
    def run(self):
        while True:
            time.sleep(1)

class TextThread(threading.Thread):
    pos = 0
    length = 50
    def set_length(self,length):
        self.length = length
        self.pos = 0

    def run(self):
        while True:
            time.sleep(0.1)
            self.pos += 1


oled = mainThread()
oled.start()
