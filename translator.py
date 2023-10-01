from googletrans import Translator
import matplotlib.pyplot as plt
import numpy as np
from tkinter import *
import tkinter as tk
from PIL import ImageTk, Image
import mss
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'


def threshold(img):
    # preprocess
    threshold = 120
    img = img.convert('L')
    img = img.point(lambda p: 255 if p> threshold else 0)
    img = img.convert('1')
    return img


class MainWindow:
    def __init__(self, w, h, title='main window') -> None:
        self.w = w
        self.h = h
        self.root = Tk()
        self.grid_window = None
        self.scr = mss.mss()
        self.translator = Translator()


    def start(self):
        self.root.geometry(f'{self.w}x{self.h}')
        self.root.attributes('-topmost',True)
        self.root.configure(bg='lightgray')

        start_grid_btn = Button(self.root, text = 'Select Area To Translate', bd = '3', command = self.start_grid)
        start_grid_btn.pack(side='top', pady=5) 
        self.text_field = Text(self.root, height = 100, width = 100)
        self.text_field.configure(font=('Helvetica bold',8))
        self.text_field.pack(side='bottom')
        self.root.mainloop()

    def display_image(self, event=None):
        img = self.scr.grab(self.capture_box)
        img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        img.save('image.png')
        img = ImageTk.PhotoImage(img)
        print(img)
        label = Label(self.root, image = img)
        label.pack(pady=10, padx=10, side='bottom')

    def translate(self, old=None):
        img = self.scr.grab(self.capture_box)
        img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        if old is None or (list(threshold(img).getdata()) != list(threshold(old).getdata())):
            # current = np.array(img)
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
            original_text = pytesseract.image_to_string(img)
            translation = self.translator.translate(original_text)
            self.text_field.insert(tk.END, translation.text)
            self.text_field.see('end')
        self.root.after(100, self.translate, img)


    def start_grid(self):
        self.grid_window = Toplevel(self.root)
        self.grid_window.overrideredirect(True)
        self.root.attributes('-topmost',True)
        self.grid_window.state('zoomed')

        self.grid_window.configure(bg='white')
        self.grid_window.attributes('-alpha', 0.3)

        w = self.grid_window.winfo_width()
        h = self.grid_window.winfo_height()
        self.c = Canvas(self.grid_window, height= h, width= w, bg='white')
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
        self.translate()

    def close_grid(self):
        self.grid_window.destroy()


if __name__ == '__main__':
    root = MainWindow(350, 300)
    root.start()
