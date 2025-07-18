import tkinter as tk
from tkinter import messagebox
import serial
import time

class SimpleCarTest:
    def __init__(self, root):
        self.root = root
        self.root.title("小车简单测试")
        self.root.geometry("400x300")
        
        # 串口连接
        self.ser = None
        self.com_port = "COM3"
        
        # 动作定义
        self.actions = [
            ('亮灯', '5'),
            ('前进', '2'),
            ('左转', '3'),
            ('右转', '4'),
            ('后退', '1'),
            ('鸣笛', '6'),
            ('前进单步', '7')  # 新增前进单步
        ]
        
        # 记录的动作序列
        self.recorded_sequence = []
        self.is_recording = False
        
        self.setup_ui()
    
    def setup_ui(self):
        # 串口连接区域
        conn_frame = tk.Frame(self.root)
        conn_frame.pack(pady=10)
        
        tk.Label(conn_frame, text="串口:").pack(side=tk.LEFT)
        self.com_entry = tk.Entry(conn_frame, width=8)
        self.com_entry.insert(0, self.com_port)
        self.com_entry.pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = tk.Button(conn_frame, text="连接", command=self.connect_serial)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        # 动作按钮区域
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        tk.Label(btn_frame, text="点击测试动作:", font=("Arial", 12, "bold")).pack()
        
        # 按钮网格子容器（解决布局冲突）
        grid_frame = tk.Frame(btn_frame)
        grid_frame.pack()

        for i, (name, code) in enumerate(self.actions):
            row = i // 3
            col = i % 3
            btn = tk.Button(grid_frame, text=name, width=8, height=2,
                            command=lambda n=name, c=code: self.test_action(n, c))
            btn.grid(row=row, column=col, padx=5, pady=5)
        
        # 记录控制
        record_frame = tk.Frame(self.root)
        record_frame.pack(pady=10)
        
        self.record_btn = tk.Button(record_frame, text="开始记录", command=self.toggle_record, bg="green", fg="white")
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(record_frame, text="清空", command=self.clear_sequence)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 显示区域
        display_frame = tk.Frame(self.root)
        display_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        tk.Label(display_frame, text="记录序列:").pack()
        
        self.text_area = tk.Text(display_frame, height=8, width=40)
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # 复制按钮
        copy_btn = tk.Button(display_frame, text="复制序列", command=self.copy_sequence)
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        # 执行序列按钮
        execute_btn = tk.Button(display_frame, text="执行序列", command=self.execute_sequence)
        execute_btn.pack(side=tk.LEFT, padx=5)
    
    def connect_serial(self):
        try:
            self.com_port = self.com_entry.get()
            if self.ser:
                self.ser.close()
            
            self.ser = serial.Serial(self.com_port, 9600, timeout=1)
            self.connect_btn.config(text="已连接", bg="green", fg="white")
            messagebox.showinfo("成功", f"已连接到 {self.com_port}")
        except Exception as e:
            messagebox.showerror("错误", f"连接失败: {str(e)}")
    
    def test_action(self, name, code):
        if not self.ser:
            messagebox.showwarning("警告", "请先连接串口")
            return
        
        try:
            # 使用与ssvep_car.py相同的控制逻辑
            if code == '2':  # 前进
                self.ser.write(b'2')
                time.sleep(0.3)
                self.ser.write(b'2')
                print(f"执行: {name} ({code}) - 发送两次命令")
            elif code == '7':  # 前进单步
                self.ser.write(b'2')
                print(f"执行: {name} ({code}) - 单步前进")
            else:
                self.ser.write(code.encode())
                print(f"执行: {name} ({code})")
            
            if self.is_recording:
                self.recorded_sequence.append(int(code))
                self.update_display()
        except Exception as e:
            messagebox.showerror("错误", f"执行失败: {str(e)}")
    
    def toggle_record(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.record_btn.config(text="停止记录", bg="red", fg="white")
        else:
            self.record_btn.config(text="开始记录", bg="green", fg="white")
    
    def clear_sequence(self):
        self.recorded_sequence = []
        self.update_display()
    
    def update_display(self):
        self.text_area.delete(1.0, tk.END)
        
        if not self.recorded_sequence:
            self.text_area.insert(tk.END, "暂无记录")
            return
        
        # 显示序列
        self.text_area.insert(tk.END, f"序列长度: {len(self.recorded_sequence)}\n\n")
        
        for i, code in enumerate(self.recorded_sequence):
            name = [n for n, c in self.actions if c == str(code)]
            name = name[0] if name else f"未知({code})"
            self.text_area.insert(tk.END, f"{i+1:2d}. {name}\n")
        
        # 显示Python数组
        self.text_area.insert(tk.END, f"\nPython数组:\n{self.recorded_sequence}")
    
    def copy_sequence(self):
        if self.recorded_sequence:
            sequence_str = str(self.recorded_sequence)
            self.root.clipboard_clear()
            self.root.clipboard_append(sequence_str)
            messagebox.showinfo("成功", "序列已复制到剪贴板")
        else:
            messagebox.showwarning("警告", "没有可复制的序列")
    
    def execute_sequence(self):
        """执行记录的序列"""
        if not self.ser:
            messagebox.showwarning("警告", "请先连接串口")
            return
        
        if not self.recorded_sequence:
            messagebox.showwarning("警告", "没有可执行的序列")
            return
        
        # 在新线程中执行序列，避免界面卡死
        import threading
        
        def run_sequence():
            try:
                for i, code in enumerate(self.recorded_sequence):
                    name = [n for n, c in self.actions if c == str(code)]
                    name = name[0] if name else f"未知({code})"
                    
                    print(f"执行序列第{i+1}步: {name} (代码: {code})")
                    
                    # 使用与ssvep_car.py相同的控制逻辑
                    if code == 2:  # 前进
                        self.ser.write(b'2')
                        time.sleep(0.3)
                        self.ser.write(b'2')
                    elif code == 7:  # 前进单步
                        self.ser.write(b'2')
                    else:
                        self.ser.write(str(code).encode())
                    
                    # 每个动作之间延时2秒
                    time.sleep(2)
                
                print("序列执行完成")
                messagebox.showinfo("完成", "序列执行完成")
            except Exception as e:
                messagebox.showerror("错误", f"执行序列失败: {str(e)}")
        
        # 启动执行线程
        thread = threading.Thread(target=run_sequence)
        thread.daemon = True
        thread.start()

def main():
    root = tk.Tk()
    app = SimpleCarTest(root)
    root.mainloop()

if __name__ == "__main__":
    main()
