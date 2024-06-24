import tkinter
import tkinter.messagebox
import struct
import numpy as np
from PIL import Image, ImageTk
import re
import cv2
import time
import sys
import platform
import tkinter as tk
from tkinter import messagebox, filedialog
import socket
import threading
import paramiko
root = tkinter.Tk()
# 画面周期
IDLE = 0.05
# 放缩大小
scale = 1
# 原传输画面尺寸
fixw, fixh = 0, 0
# 放缩标志
wscale = False
# 屏幕显示画布
showcan = None
# socket缓冲区大小
bufsize = 10240
# 线程
th = None
# socket
soc = None
# socks5
socks5 = None
IP = '192.168.242.128'
# 平台
PLAT = b''
if sys.platform == "win32":
    PLAT = b'win'
elif sys.platform == "darwin":
    PLAT = b'osx'
elif platform.system() == "Linux":
    PLAT = b'x11'
# 初始化socket
def SetSocket():
    global soc, host_en  # 声明全局变量 soc 和 host_en
    def byipv4(ip, port):
        """
        构造IPv4地址的字节流格式。
        Args:- ip: IPv4地址的列表，如 [192, 168, 0, 1]- port: 端口号
        Returns:- IPv4地址的字节流
        """
        return struct.pack(">BBBBBBBBH", 5, 1, 0, 1, ip[0], ip[1], ip[2], ip[3], port)
    def byhost(host, port):
        """
        构造域名地址的字节流格式。
        Args:- host: 域名- port: 端口号
        Returns:- 域名地址的字节流
        """
        d = struct.pack(">BBBB", 5, 1, 0, 3)  # SOCKS5协议版本号和命令类型
        blen = len(host)
        d += struct.pack(">B", blen)  # 域名长度
        d += host.encode()  # 域名编码
        d += struct.pack(">H", port)  # 端口号
        return d
    host = host_en.get()  # 获取主机地址输入框的值
    if host is None:
        tkinter.messagebox.showinfo('提示', 'Host设置错误！')  # 弹出提示框，提示主机地址设置错误
        return
    hs = host.split(":")  # 按冒号分割主机地址和端口号
    if len(hs) != 2:
        tkinter.messagebox.showinfo('提示', 'Host设置错误！')  # 主机地址格式错误，弹出提示框
        return
    if socks5 is not None:  # 如果使用了SOCKS5代理
        ss = socks5.split(":")  # 按冒号分割代理地址和端口号
        if len(ss) != 2:
            tkinter.messagebox.showinfo('提示', '代理设置错误！')  # 代理地址格式错误，弹出提示框
            return
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建TCP套接字
        soc.connect((ss[0], int(ss[1])))  # 连接到SOCKS5代理服务器
        soc.sendall(struct.pack(">BB", 5, 0))  # 发送SOCKS5协议版本号和认证方法
        recv = soc.recv(2)  # 接收代理服务器的响应
        if recv[1] != 0:
            tkinter.messagebox.showinfo('提示', '代理回应错误！')  # 代理服务器认证方法错误，弹出提示框
            return
        if re.match(r'^\d+?\.\d+?\.\d+?\.\d+?:\d+$', host) is None:
            # 如果主机是域名地址
            hand = byhost(hs[0], int(hs[1]))  # 构造域名地址的字节流
            soc.sendall(hand)  # 发送域名地址的字节流
        else:
            # 如果主机是IP地址
            ip = [int(i) for i in hs[0].split(".")]  # 将IP地址字符串转换为整数列表
            port = int(hs[1])  # 端口号
            hand = byipv4(ip, port)  # 构造IPv4地址的字节流
            soc.sendall(hand)  # 发送IPv4地址的字节流
        # 接收代理服务器的回应
        rcv = b''
        while len(rcv) != 10:
            rcv += soc.recv(10 - len(rcv))  # 循环接收10字节的代理服务器回应
        if rcv[1] != 0:
            tkinter.messagebox.showinfo('提示', '代理回应错误！')  # 代理服务器回应错误，弹出提示框
            return
    else:  # 如果没有使用SOCKS5代理
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建TCP套接字
        soc.connect((hs[0], int(hs[1])))  # 直接连接到指定的主机地址和端口号
        bectrlIP = hs[0]

def SetScale(x):
    global scale, wscale
    scale = float(x) / 100  # 将传入的参数 x 转换为浮点数，并计算比例（百分比）
    wscale = True  # 设置 wscale 标志为 True，表示比例已经设置
def ShowProxy():
    # 显示代理设置窗口
    global root  # 声明全局变量 root
    def set_s5_addr():
        """
        获取并设置 SOCKS5 代理地址。从输入框 s5_en 中获取地址，如果地址为空，则将 socks5 设置为 None。
        """
        global socks5  # 声明全局变量 socks5
        socks5 = s5_en.get()  # 获取输入框 s5_en 中的内容
        if socks5 == "":
            socks5 = None  # 如果输入框内容为空，将 socks5 设置为 None
        pr.destroy()  # 销毁代理设置窗口
    pr = tkinter.Toplevel(root)  # 创建顶级窗口 pr，作为代理设置窗口
    s5v = tkinter.StringVar()  # 创建一个 tkinter 字符串变量 s5v，用于与 Entry 组件关联
    s5_lab = tkinter.Label(pr, text="Socks5 Host:")  # 创建标签，显示"Socks5 Host:"
    s5_en = tkinter.Entry(pr, show=None, font=('Arial', 14), textvariable=s5v)  # 创建输入框，显示输入的 SOCKS5 地址
    s5_btn = tkinter.Button(pr, text="OK", command=set_s5_addr)  # 创建按钮，点击后执行 set_s5_addr 函数
    s5_lab.grid(row=0, column=0, padx=10, pady=10, ipadx=0, ipady=0)  # 设置标签的位置和填充
    s5_en.grid(row=0, column=1, padx=10, pady=10, ipadx=40, ipady=0)  # 设置输入框的位置和填充
    s5_btn.grid(row=1, column=0, padx=10, pady=10, ipadx=30, ipady=0)  # 设置按钮的位置和填充
    s5v.set("127.0.0.1:88")  # 设置输入框的默认值为"127.0.0.1:88"
def ShowScreen():
    global showcan, root, soc, th, wscale
    if showcan is None:
        wscale = True  # 设置 wscale 标志为 True，用于屏幕显示
        showcan = tkinter.Toplevel(root)  # 创建顶级窗口 showcan，用于显示屏幕内容
        th = threading.Thread(target=run)  # 创建线程 th，用于运行屏幕显示函数 run
        th.start()  # 启动线程 th，开始显示屏幕内容
    else:
        soc.close()  # 关闭当前的 socket 连接
        showcan.destroy()  # 销毁显示屏幕的窗口 showcan
class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("聊天应用")
        # 创建GUI组件
        self.message_label = tk.Label(root, text="消息:")
        self.message_label.grid(row=0, column=0, padx=10, pady=10)
        self.message_entry = tk.Entry(root, width=50)
        self.message_entry.grid(row=0, column=1, padx=10, pady=10)
        self.send_button = tk.Button(root, text="发送消息", command=self.send_message)
        self.send_button.grid(row=0, column=2, padx=10, pady=10)
        self.file_label = tk.Label(root, text="文件:")
        self.file_label.grid(row=1, column=0, padx=10, pady=10)
        self.file_entry = tk.Entry(root, width=50, )
        self.file_entry.grid(row=1, column=1, padx=10, pady=10)
        self.browse_button = tk.Button(root, text="浏览", command=self.browse_file)
        self.browse_button.grid(row=1, column=2, padx=10, pady=10)
        self.sendfile_button = tk.Button(root, text="发送文件", command=self.send_file)
        self.sendfile_button.grid(row=2, column=1, padx=10, pady=10)
        # 创建一个文本框显示接收到的消息
        self.receive_text = tk.Text(root, width=60, height=10)
        self.receive_text.grid(row=3, columnspan=3, padx=10, pady=10)
        # 启动一个线程用于接收消息
        self.receive_thread = threading.Thread(target=self.receive_message_thread, daemon=True)
        self.receive_thread.start()
        # 启动一个线程用于接收文件
        self.receive_file_thread = threading.Thread(target=self.receive_file_thread, daemon=True)
        self.receive_file_thread.start()

    def send_message(self):
        message = self.message_entry.get()
        self.message_entry.delete(0, 'end')  # 清空输入框
        # 在这里添加发送消息的代码
        # 示例中使用UDP协议发送消息
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            dest_addr = (becontrolIP, 12345)  # 目标IP地址和端口号
            #print(controlIP)
            #print(dest_addr)
            sock.sendto(message.encode('utf-8'), dest_addr)
            message = f"{IP}发送消息: {message}\n"
            self.receive_text.insert('end', message)
            self.receive_text.see('end')  # 滚动到最新消息处
            sock.close()
        except Exception as e:
            messagebox.showerror("错误", f"发送消息失败: {str(e)}")
    def browse_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_entry.delete(0, 'end')
            self.file_entry.insert(0, file_path)
    def send_file(self):
        file_path = self.file_entry.get()
        if not file_path:
            messagebox.showerror("错误", "请选择要发送的文件。")
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dest_addr = (becontrolIP, 54321)  # 目标IP地址和端口号
            sock.connect(dest_addr)
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(1024)
                    if not data:
                        break
                    sock.sendall(data)
            sock.close()
            messagebox.showinfo("成功", "文件发送成功。")
        except Exception as e:
            messagebox.showerror("错误", f"发送文件失败: {str(e)}")

    def receive_file_thread(self):
        try:
            sock_file = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_file.bind(('0.0.0.0', 54321))
            sock_file.listen(1)
            conn, addr = sock_file.accept()
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", initialdir="~/Desktop")
            if file_path:
                with open(file_path, 'wb') as f:
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        f.write(data)
                messagebox.showinfo("成功", "文件接收成功。")
            conn.close()
            sock_file.close()
        except Exception as e:
            messagebox.showerror("错误", f"接收文件失败: {str(e)}")
    def receive_message_thread(self):
        # 在这里添加接收消息的代码
        # 示例中使用UDP协议接收消息
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            listen_addr = ('0.0.0.0', 12345)  # 监听所有地址的端口12345
            sock.bind(listen_addr)
            while True:
                data, addr = sock.recvfrom(1024)
                message = f"来自 {addr} 的消息: {data.decode('utf-8')}\n"
                self.receive_text.insert('end', message)
                self.receive_text.see('end')  # 滚动到最新消息处
            sock.close()
        except Exception as e:
            messagebox.showerror("错误", f"接收消息失败: {str(e)}")
def Chat():
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
def comunication():
    # 创建一个IPv4的UDP套接字
    global host_en
    host = host_en.get()  # 获取主机地址输入框的值
    hs = host.split(":")  # 按冒号分割主机地址和端口号
    # print(hs)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 构造数据包
    message = "开始通信"
    global becontrolIP
    becontrolIP =  hs[0]
    dest_addr = (becontrolIP, 12344)  # 目标IP地址和端口号
    # 发送数据包，需要将消息编码为字节串
    sock.sendto(message.encode('utf-8'), dest_addr)
    threading.Thread(target=Chat).start()
    # 关闭套接字
    sock.close()
# 创建一个 Tkinter 字符串变量，用于管理 host_en 中的文本内容
val = tkinter.StringVar()
# 创建一个标签，显示文本 "Host:"
host_lab = tkinter.Label(root, text="Host:")
# 创建一个单行文本输入框，设置字体为 Arial 14 号，绑定到 val 变量
host_en = tkinter.Entry(root, show=None, font=('Arial', 14), textvariable=val)
# 创建一个标签，显示文本 "Scale:"
sca_lab = tkinter.Label(root, text="Scale:")
# 创建一个水平滑动条，范围从 10 到 100，显示刻度值，初始值为 100，分辨率为 0.1，调用 SetScale 函数
sca = tkinter.Scale(root, from_=10, to=100, orient=tkinter.HORIZONTAL, length=100,
                    showvalue=100, resolution=0.1, tickinterval=50, command=SetScale)
# 创建一个按钮，显示文本 "代理"，点击时调用 ShowProxy 函数
proxy_btn = tkinter.Button(root, text="代理", command=ShowProxy)
# 创建一个按钮，显示文本 "连接远程桌面"，点击时调用 ShowScreen 函数
show_btn = tkinter.Button(root, text="连接远程桌面", command=ShowScreen)
com_btn = tkinter.Button(root, text="开启通信", command=comunication)
# 将 host_lab 放置在网格中第 0 行第 0 列，设置边距 padx=10, pady=10，内部边距 ipadx=0, ipady=0
host_lab.grid(row=0, column=0, padx=10, pady=10, ipadx=0, ipady=0)
# 将 host_en 放置在网格中第 0 行第 1 列，设置边距 padx=0, pady=0，内部边距 ipadx=40, ipady=0
host_en.grid(row=0, column=1, padx=0, pady=0, ipadx=40, ipady=0)
# 将 sca_lab 放置在网格中第 1 行第 0 列，设置边距 padx=10, pady=10，内部边距 ipadx=0, ipady=0
sca_lab.grid(row=1, column=0, padx=10, pady=10, ipadx=0, ipady=0)
# 将 sca 放置在网格中第 1 行第 1 列，设置边距 padx=0, pady=0，内部边距 ipadx=100, ipady=0
sca.grid(row=1, column=1, padx=0, pady=0, ipadx=100, ipady=0)
# 将 proxy_btn 放置在网格中第 2 行第 0 列，设置边距 padx=0, pady=10，内部边距 ipadx=30, ipady=0
proxy_btn.grid(row=2, column=0, padx=0, pady=10, ipadx=30, ipady=0)
# 将 show_btn 放置在网格中第 2 行第 1 列，设置边距 padx=0, pady=10，内部边距 ipadx=30, ipady=0
show_btn.grid(row=2, column=1, padx=0, pady=10, ipadx=30, ipady=0)
# 将 ftp_btn 放置在网格中第 3 行第 0 列，设置边距 padx=0, pady=10，内部边距 ipadx=30, ipady=0
com_btn.grid(row=2, column=2, padx=0, pady=10, ipadx=30, ipady=0)
# 将 ftp_btn 放置在网格中第 3 行第 0 列，设置边距 padx=0, pady=10，内部边距 ipadx=30, ipady=0
# 设置 sca 的初始值为 100
sca.set(100)
# 设置 val 的初始值为 '127.0.0.1:80'
val.set('127.0.0.1:80')
# 记录当前时间戳，用于发送消息时的时间间隔控制
last_send = time.time()
def BindEvents(canvas):
    global soc, scale
    '''
    处理事件绑定函数，将鼠标和键盘事件绑定到指定的画布上。
    Args:- canvas: 要绑定事件的 tkinter 画布对象
    '''
    def EventDo(data):
        '''发送事件数据到服务器
        Args:- data: 要发送的事件数据
        '''
        soc.sendall(data)
    # 鼠标左键按下事件处理函数
    def LeftDown(e):
        '''
        处理鼠标左键按下事件
        Args:- e: 事件对象，包含有关事件的信息
        '''
        return EventDo(struct.pack('>BBHH', 1, 100, int(e.x / scale), int(e.y / scale)))
    # 鼠标左键释放事件处理函数
    def LeftUp(e):
        return EventDo(struct.pack('>BBHH', 1, 117, int(e.x / scale), int(e.y / scale)))
    canvas.bind(sequence="<1>", func=LeftDown)  # 绑定鼠标左键按下事件
    canvas.bind(sequence="<ButtonRelease-1>", func=LeftUp)  # 绑定鼠标左键释放事件
    # 鼠标右键按下事件处理函数
    def RightDown(e):
        return EventDo(struct.pack('>BBHH', 3, 100, int(e.x / scale), int(e.y / scale)))
    # 鼠标右键释放事件处理函数
    def RightUp(e):
        return EventDo(struct.pack('>BBHH', 3, 117, int(e.x / scale), int(e.y / scale)))
    canvas.bind(sequence="<3>", func=RightDown)  # 绑定鼠标右键按下事件
    canvas.bind(sequence="<ButtonRelease-3>", func=RightUp)  # 绑定鼠标右键释放事件
    # 鼠标滚轮事件处理函数
    if PLAT == b'win' or PLAT == 'osx':
        # windows/mac
        def Wheel(e):
            '''
            处理鼠标滚轮事件（Windows 和 macOS）
            '''
            if e.delta < 0:
                return EventDo(struct.pack('>BBHH', 2, 0, int(e.x / scale), int(e.y / scale)))
            else:
                return EventDo(struct.pack('>BBHH', 2, 1, int(e.x / scale), int(e.y / scale)))
        canvas.bind(sequence="<MouseWheel>", func=Wheel)  # 绑定鼠标滚轮事件
    elif PLAT == b'x11':
        # Linux
        def WheelDown(e):
            '''
            处理鼠标滚轮向下滚动事件（Linux）
            '''
            return EventDo(struct.pack('>BBHH', 2, 0, int(e.x / scale), int(e.y / scale)))
        def WheelUp(e):
            '''
            处理鼠标滚轮向上滚动事件（Linux）
            '''
            return EventDo(struct.pack('>BBHH', 2, 1, int(e.x / scale), int(e.y / scale)))
        canvas.bind(sequence="<Button-4>", func=WheelUp)  # 绑定鼠标滚轮向上滚动事件
        canvas.bind(sequence="<Button-5>", func=WheelDown)  # 绑定鼠标滚轮向下滚动事件
    # 鼠标移动事件处理函数
    # 每隔 100ms 发送一次
    def Move(e):
        '''
        处理鼠标移动事件
        '''
        global last_send
        cu = time.time()
        if cu - last_send > IDLE:
            last_send = cu
            sx, sy = int(e.x / scale), int(e.y / scale)
            return EventDo(struct.pack('>BBHH', 4, 0, sx, sy))
    canvas.bind(sequence="<Motion>", func=Move)  # 绑定鼠标移动事件
    # 键盘按键按下事件处理函数
    def KeyDown(e):
        '''
        处理键盘按键按下事件
        '''
        return EventDo(struct.pack('>BBHH', e.keycode, 100, int(e.x / scale), int(e.y / scale)))
    # 键盘按键释放事件处理函数
    def KeyUp(e):
        '''
        处理键盘按键释放事件
        '''
        return EventDo(struct.pack('>BBHH', e.keycode, 117, int(e.x / scale), int(e.y / scale)))
    canvas.bind(sequence="<KeyPress>", func=KeyDown)  # 绑定键盘按键按下事件
    canvas.bind(sequence="<KeyRelease>", func=KeyUp)  # 绑定键盘按键释放事件
def run():
    global wscale, fixh, fixw, soc, showcan
    # 设置套接字连接
    SetSocket()
    # 发送平台信息
    soc.sendall(PLAT)
    # 接收图像长度信息
    lenb = soc.recv(5)
    imtype, le = struct.unpack(">BI", lenb)
    # 接收图像数据
    imb = b''
    while le > bufsize:
        t = soc.recv(bufsize)
        imb += t
        le -= len(t)
    while le > 0:
        t = soc.recv(le)
        imb += t
        le -= len(t)
    # 解码图像数据为 NumPy 数组
    data = np.frombuffer(imb, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    # 获取图像高度和宽度
    h, w, _ = img.shape
    fixh, fixw = h, w
    # 将图像从 OpenCV 格式转换为 tkinter 可用的格式
    imsh = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
    imi = Image.fromarray(imsh)
    imgTK = ImageTk.PhotoImage(image=imi)
    # 创建 tkinter 画布并绑定事件处理函数
    cv = tkinter.Canvas(showcan, width=w, height=h, bg="white")
    cv.focus_set()
    BindEvents(cv)
    cv.pack()
    cv.create_image(0, 0, anchor=tkinter.NW, image=imgTK)
    # 根据缩放比例调整画布大小
    h = int(h * scale)
    w = int(w * scale)
    # 循环接收并显示图像
    while True:
        if wscale:
            # 根据缩放比例调整画布大小
            h = int(fixh * scale)
            w = int(fixw * scale)
            cv.config(width=w, height=h)
            wscale = False
        try:
            # 接收图像长度信息
            lenb = soc.recv(5)
            imtype, le = struct.unpack(">BI", lenb)
            # 接收图像数据
            imb = b''
            while le > bufsize:
                t = soc.recv(bufsize)
                imb += t
                le -= len(t)
            while le > 0:
                t = soc.recv(le)
                imb += t
                le -= len(t)
            # 解码图像数据为 NumPy 数组
            data = np.frombuffer(imb, dtype=np.uint8)
            ims = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if imtype == 1:
                # 全图传输
                img = ims
            else:
                # 差异图像传输，进行异或操作
                img = img ^ ims
            # 将图像调整大小并转换为 tkinter 可用的格式
            imt = cv2.resize(img, (w, h))
            imsh = cv2.cvtColor(imt, cv2.COLOR_RGB2RGBA)
            imi = Image.fromarray(imsh)
            imgTK.paste(imi)
        except Exception as e:
            # 发生异常时，关闭显示窗口并重新启动显示功能
            showcan = None
            ShowScreen()
            return
# 主程序运行入口
root.mainloop()
