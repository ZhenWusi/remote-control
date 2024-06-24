import struct  # 导入结构化数据处理模块
import socket  # 导入套接字编程模块
from PIL import ImageGrab  # 导入截图模块
import cv2  # 导入计算机视觉库OpenCV
import numpy as np  # 导入数值计算库NumPy
import threading  # 导入线程模块
import time  # 导入时间模块
import pyautogui as ag  # 导入自动化控制库PyAutoGUI
import mouse  # 导入鼠标操作库
from _keyboard import getKeycodeMapping  # 导入键盘映射获取函数
import tkinter as tk
from tkinter import messagebox, filedialog
import socket
import threading
# 画面更新周期（秒）
IDLE = 0.05
# 鼠标滚轮灵敏度
SCROLL_NUM = 5
# Socket 缓冲大小
bufsize = 1024
# 监听的主机和端口
host = ('0.0.0.0', 80)
# 创建 TCP 套接字
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind(host)
soc.listen(1)
# 图像压缩质量，1-100 数值越小，压缩比越高，图片质量损失越严重
IMQUALITY = 50
# 线程锁，用于保护全局变量 img 和 imbyt
lock = threading.Lock()
IP = '192.168.242.129'
def ctrl(conn):
    '''
    读取控制命令，并在本机还原操作

    Args:
    - conn: 客户端连接的套接字对象
    '''
    keycodeMapping = {}  # 初始化键盘映射字典
    def Op(key, op, ox, oy):
        # print(key, op, ox, oy)
        if key == 4:
            # 鼠标移动
            mouse.move(ox, oy)
        elif key == 1:
            if op == 100:
                # 左键按下
                ag.mouseDown(button=ag.LEFT)
            elif op == 117:
                # 左键弹起
                ag.mouseUp(button=ag.LEFT)
        elif key == 2:
            # 滚轮事件
            if op == 0:
                # 向上
                ag.scroll(-SCROLL_NUM)
            else:
                # 向下
                ag.scroll(SCROLL_NUM)
        elif key == 3:
            # 鼠标右键
            if op == 100:
                # 右键按下
                ag.mouseDown(button=ag.RIGHT)
            elif op == 117:
                # 右键弹起
                ag.mouseUp(button=ag.RIGHT)
        else:
        # 如果不是鼠标或者特定按键操作，则执行键盘事件
        # 从键盘映射字典中获取对应的键值
            k = keycodeMapping.get(key)
        # 如果获取到了键值
            if k is not None:
                if op == 100:
                    # 按键按下
                    ag.keyDown(k)
                elif op == 117:
                    # 按键弹起
                    ag.keyUp(k)
    try:
        plat = b''  # 初始化一个空字节串，用于存储平台标识数据
        while True:
            # 持续接收数据，直到接收到3个字节为止
            plat += conn.recv(3 - len(plat))
            if len(plat) == 3:
                break  # 当接收到3个字节后，停止接收
        print("Plat:", plat.decode())  # 打印接收到的平台标识数据
        keycodeMapping = getKeycodeMapping(plat)  # 根据平台标识获取键盘映射
        base_len = 6  # 基本命令长度为6个字节
        while True:
            cmd = b''  # 初始化一个空字节串，用于存储接收到的命令数据
            rest = base_len - 0  # 计算还需要接收的字节数
            while rest > 0:
                # 持续接收数据，直到接收到base_len个字节为止
                cmd += conn.recv(rest)
                rest -= len(cmd)
            key = cmd[0]  # 提取命令中的按键信息
            op = cmd[1]  # 提取命令中的操作码信息
            x = struct.unpack('>H', cmd[2:4])[0]  # 提取命令中的x坐标信息
            y = struct.unpack('>H', cmd[4:6])[0]  # 提取命令中的y坐标信息
            Op(key, op, x, y)  # 调用Op函数执行相应的操作
    except:
        return  # 捕获异常并结束函数执行
# 压缩后np图像
img = None
# 编码后的图像
imbyt = None
def handle(conn):
    global img, imbyt  # 声明全局变量，用于存储图像数据和编码后的图像字节流
    lock.acquire()  # 获取锁，确保在修改全局变量时的线程安全性
    if imbyt is None:
        # 如果编码后的图像字节流为空，则进行初始化
        imorg = np.asarray(ImageGrab.grab())  # 使用PIL库获取屏幕截图，并转换为NumPy数组
        _, imbyt = cv2.imencode(".jpg", imorg, [cv2.IMWRITE_JPEG_QUALITY, IMQUALITY])
        # 使用OpenCV将NumPy数组编码为JPEG格式的图像字节流，并设定图像质量
        imnp = np.asarray(imbyt, np.uint8)  # 将编码后的字节流转换为NumPy数组
        img = cv2.imdecode(imnp, cv2.IMREAD_COLOR)  # 使用OpenCV解码图像字节流为BGR颜色空间的图像
    lock.release()  # 释放锁，允许其他线程修改全局变量
    lenb = struct.pack(">BI", 1, len(imbyt))  # 构造消息长度信息，前导1表示编码图像
    conn.sendall(lenb)  # 发送消息长度信息
    conn.sendall(imbyt)  # 发送编码后的图像字节流
    while True:
        # 修复Linux下的问题，确保间隔一定时间再次截取屏幕
        time.sleep(IDLE)
        gb = ImageGrab.grab()  # 再次获取屏幕截图
        imgnpn = np.asarray(gb)  # 将截图转换为NumPy数组
        _, timbyt = cv2.imencode(".jpg", imgnpn, [cv2.IMWRITE_JPEG_QUALITY, IMQUALITY])
        # 使用OpenCV将新截图编码为JPEG格式的图像字节流，并设定图像质量
        imnp = np.asarray(timbyt, np.uint8)  # 将编码后的新图像字节流转换为NumPy数组
        imgnew = cv2.imdecode(imnp, cv2.IMREAD_COLOR)
        # 使用OpenCV解码新的图像字节流为BGR颜色空间的图像
        # 计算图像差异，即当前图像与上一帧图像的异或操作
        imgs = imgnew ^ img
        if (imgs != 0).any():
            # 如果图像差异不全为0，表示画面有变化
            pass  # 可以在这里加入处理画面变化的逻辑，例如发送差异化图像
        else:
            continue  # 如果画面没有变化，则继续下一次循环
        imbyt = timbyt  # 更新全局变量中的编码后的图像字节流为新截图的字节流
        img = imgnew  # 更新全局变量中的图像为新截图的图像
        _, imb = cv2.imencode(".png", imgs)  # 使用OpenCV将图像差异编码为PNG格式的图像字节流
        l1 = len(imbyt)  # 计算原编码图像的大小
        l2 = len(imb)  # 计算差异化图像的大小
        if l1 > l2:
            # 如果原编码图像的大小大于差异化图像的大小
            lenb = struct.pack(">BI", 0, l2)  # 构造消息长度信息，前导0表示差异化图像
            conn.sendall(lenb)  # 发送消息长度信息
            conn.sendall(imb)  # 发送差异化图像的字节流
        else:
            lenb = struct.pack(">BI", 1, l1)  # 构造消息长度信息，前导1表示编码图像
            conn.sendall(lenb)  # 发送消息长度信息
            conn.sendall(imbyt)  # 发送编码后的图像字节流
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
            dest_addr = (controlIP, 12345)  # 目标IP地址和端口号
            # print(controlIP)
            # print(dest_addr)
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
        print(file_path)
        if not file_path:
            messagebox.showerror("错误", "请选择要发送的文件。")
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dest_addr = (controlIP, 54321)  # 目标IP地址和端口号
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
def start():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_addr = ('0.0.0.0', 12344)  # 监听所有地址的端口12345
    global controlIP
    sock.bind(listen_addr)
    print("监听消息...")
    while True:
        data, addr = sock.recvfrom(1024)  # 接收数据包，缓冲区大小为1024字节
        controlIP = addr[0]
        print(f"收到来自 {addr}消息: {data.decode('utf-8')}")
        if data.decode('utf-8') == '开始通信':
            threading.Thread(target=Chat).start()
    sock.close()
threading.Thread(target=start).start()  # 创建线程处理远程控制指令
while True:
    conn, addr = soc.accept()  # 接受客户端连接
    threading.Thread(target=handle, args=(conn,)).start()  # 创建线程处理屏幕捕获和图像传输
    threading.Thread(target=ctrl, args=(conn,)).start()  # 创建线程处理远程控制指令

