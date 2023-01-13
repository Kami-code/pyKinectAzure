# coding=gbk
# 参考 https://zhuanlan.zhihu.com/p/359971449,
# https://github.com/dmnfarrell/tkintertable/wiki/Usage
# https://github.com/dmnfarrell/tkintertable/issues/47
import json
import random
import re
import time
import webbrowser

import requests
import yaml
from tkintertable import TableCanvas
from tkinter import *
import tkinter
import threading
import os



def fn_get(str):
    def get():
        r = requests.get(url=f'http://127.0.0.1:5050/{str}', timeout=5)
        if r.status_code == 200:
            result = json.loads(r.content.decode())
            print(f"result = {result}")
    return get

shot_index = 0

def fn_shot():
    def shot():
        global shot_index
        print(f"shot_index = {shot_index}")
        r = requests.get(url=f'http://127.0.0.1:5050/shot/{shot_index}', timeout=15)
        shot_index += 1
        if r.status_code == 200:
            result = json.loads(r.content.decode())
            print(f"result = {result}")
    return shot


if __name__ == '__main__':
    master = tkinter.Tk()  # 主窗口
    master.geometry('300x200')

    frame1 = Frame(master)  # 子窗口
    frame2 = Frame(master)  # 子窗口
    frame3 = Frame(master)  # 子窗口
    frame4 = Frame(frame3)  # 子窗口
    frame1.pack(padx=1, pady=1, side='top')
    frame2.pack(padx=1, pady=1, side='top')
    frame3.pack(padx=1, pady=1, side='top')
    frame4.pack(padx=1, pady=1, side='right')

    frame4_left = Frame(frame4)
    frame4_right = Frame(frame4)

    frame4_left.pack(padx=1, pady=1, side='left')
    frame4_right.pack(padx=1, pady=1, side='left')

    frame1_left = Frame(frame1)
    frame1_left.pack(side='left')
    frame1_right = Frame(frame1)
    frame1_right.pack(side='left')

    list = Button(frame1_right, text="list device", command=fn_get("list"))
    list.pack(side='top')
    start = Button(frame1_right, text="start recording",
                          command=fn_get("start"))
    start.pack(side='top')
    stop = Button(frame1_right, text="stop recording", command=fn_get("stop"))
    stop.pack(side='top')
    stop = Button(frame1_right, text="shot", command=fn_shot())
    stop.pack(side='top')
    # 主进程运行master，子线程运行更新代码
    master.mainloop()
