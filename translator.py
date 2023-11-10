from threading import Thread, Lock
from googletrans import Translator
import matplotlib.pyplot as plt
import cv2
import numpy as np
from tkinter import *
import tkinter as tk
from PIL import ImageTk, Image
import mss
import pytesseract
import time
import random
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

translator = Translator()
translated_text = []
share_lock = Lock()

def threshold(img):
    # preprocess
    threshold = 120
    img = img.convert('L')
    img = img.point(lambda p: 255 if p> threshold else 0)
    img = img.convert('1')
    return img


def remove_noise(image):
    return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 15)

def to_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def thresholding(image):
    return cv2.threshold(image, 0, 200, cv2.THRESH_OTSU)[1]

def sharpen(image):
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    sharpened = cv2.filter2D(image, -1, kernel)
    return sharpened

def preprocess(img):
    #img = remove_noise(img)
    #img = to_grayscale(img)
    img = sharpen(img)
    return img

def OCR_translate(capture_box):
    print("thread started ", capture_box)
    scr = mss.mss()
    while True:
        img = np.array(scr.grab(capture_box))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        img - preprocess(img)
        # # setting the OCR language target to turkish
        custom_config = r'-l tur --psm 6'
        original_text = pytesseract.image_to_string(img, config=custom_config)
        translation = translator.translate(original_text)
        #TODO: Cleanup the text
        with share_lock:
                translated_text.append(translation.text)
        #time.sleep(0.05)
    


class MainWindow:
    def __init__(self, w, h, title='main window') -> None:
        self.w = w
        self.h = h
        self.root = Tk()
        self.grid_window = None
        self.thread_started = False

        #debugging
        self.text = None


    def start(self):
        self.root.geometry(f'{self.w}x{self.h}')
        self.root.attributes('-topmost',True)
        self.root.configure(bg='lightgray')

        start_grid_btn = Button(self.root, text = 'Select Area To Translate', bd = '3', command = self.start_grid)
        start_grid_btn.pack(side='top', pady=5)
        
        # TODO: Change the text field to text label
        # self.text_field = Text(self.root, height = 100, width = 100)
        # self.text_field.configure(font=('Helvetica bold',8))
        self.text_field = Label(self.root, text="Translating....", 
                                font= ('Arial 9'), background='lightgray', 
                                justify='left', wraplength=300)

        self.text_field.pack(pady=10, padx=10, side=TOP, anchor='w')

        self.root.mainloop()

    def display_image(self, event=None):
        img = self.scr.grab(self.capture_box)
        img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        img.save('image.png')
        img = ImageTk.PhotoImage(img)
        label = Label(self.root, image = img)
        label.pack(pady=10, padx=10, side='bottom')



    def update_text(self, text):
        self.text_field.configure(text=text)

    def translate(self):
        if not self.thread_started:
            self.translation_thread = Thread(target=OCR_translate, args=(self.capture_box,), daemon=True)
            self.thread_started = True
            self.translation_thread.start()

        with share_lock:
            if translated_text:
                self.text = translated_text.pop(0)    

        self.update_text(self.text) 
        self.root.after(100, self.translate)


    def start_grid(self):
        if self.grid_window != None: 
            return
        
        self.grid_window = Toplevel(self.root)
        self.grid_window.overrideredirect(True)
        self.root.attributes('-topmost',True)
        self.grid_window.state('zoomed')

        self.grid_window.configure(bg='black')
        self.grid_window.attributes('-alpha', 0.3)

        w = self.grid_window.winfo_width()
        h = self.grid_window.winfo_height()
        self.c = Canvas(self.grid_window, height= h, width= w, bg='lightgray')
        self.c.pack(fill=tk.BOTH, expand=True)
        self.c.bind('<Configure>',       self.draw_lines)
        self.c.bind('<Button-1>',        self.get_mouse_pos)
        self.c.bind('<B1-Motion>',       self.draw_capture_box)
        self.c.bind('<ButtonRelease-1>', self.get_capture_box)

    
    def draw_lines(self, event=None):
        w = self.c.winfo_width() # Get current width of canvas
        h = self.c.winfo_height() # Get current height of canvas
        self.c.delete('grid_line') # Will only remove the grid_line
        fill_color = 'black'
        # Creates all vertical lines at intevals of 100
        for i in range(0, w, 10):
            lw = 1
            if i%100 == 0:
                lw=2
            self.c.create_line([(i, 0), (i, h)], width=lw, tag='grid_line', fill=fill_color)
        # Creates all horizontal lines at intevals of 100
        for i in range(0, h, 10):
            lw = 0.5
            if i%100 == 0:
                lw=2
            self.c.create_line([(0, i), (w, i)], width=lw, tag='grid_line', fill=fill_color)

    def get_mouse_pos(self, event=None):
        self.initX = event.x 
        self.initY = event.y

    def draw_capture_box(self, event=None):
        self.c.delete('capture_box')
        self.c.create_rectangle(self.initX, self.initY, event.x, event.y, 
                                outline='red', width=3, tag='capture_box')
        

    def get_capture_box(self, event=None):
        self.capture_box = (self.initX, self.initY, event.x, event.y)
        self.grid_window.destroy()
        self.grid_window = None
        self.translate()

    def close_grid(self):
        self.grid_window.destroy()


if __name__ == '__main__':
    root = MainWindow(350, 300)
    root.start()
