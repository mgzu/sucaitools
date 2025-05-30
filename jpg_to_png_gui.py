import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import threading
import tkinterdnd2

class JpgToPngFrame(ctk.CTkFrame):
    def __init__(self, master, lang_manager):
        super().__init__(master)
        self.lang_manager = lang_manager
        self.selected_folder = None
        self.is_processing = False
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # --- Folder Selection Frame ---
        self.folder_frame = ctk.CTkFrame(self)
        self.folder_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.folder_frame.grid_columnconfigure(1, weight=1)
        
        self.folder_label = ctk.CTkLabel(self.folder_frame, text=self.lang_manager.get_text('select_folder'))
        self.folder_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.folder_entry = ctk.CTkEntry(self.folder_frame, placeholder_text=self.lang_manager.get_text('select_folder_placeholder'))
        self.folder_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.browse_button = ctk.CTkButton(self.folder_frame, text=self.lang_manager.get_text('browse'), command=self.select_folder)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)
        
        # --- Options Frame ---
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.recursive_var = ctk.BooleanVar(value=True)
        self.recursive_checkbox = ctk.CTkCheckBox(self.options_frame, text=self.lang_manager.get_text('recursive_processing'), variable=self.recursive_var)
        self.recursive_checkbox.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.start_button = ctk.CTkButton(self.options_frame, text=self.lang_manager.get_text('start_conversion'), command=self.start_conversion)
        self.start_button.grid(row=0, column=1, padx=10, pady=5)
        
        # --- Progress and Log Frame ---
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)
        
        self.progress_label = ctk.CTkLabel(self.log_frame, text=self.lang_manager.get_text('status_idle'))
        self.progress_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.log_text = ctk.CTkTextbox(self.log_frame, height=200)
        self.log_text.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # --- Drag and Drop ---
        self.drop_target_register(tkinterdnd2.DND_FILES)
        self.dnd_bind('<<Drop>>', self.drop)
        
        self.update_ui_texts()
    
    def update_ui_texts(self):
        """更新界面文本"""
        self.folder_label.configure(text=self.lang_manager.get_text('select_folder'))
        self.folder_entry.configure(placeholder_text=self.lang_manager.get_text('select_folder_placeholder'))
        self.browse_button.configure(text=self.lang_manager.get_text('browse'))
        self.recursive_checkbox.configure(text=self.lang_manager.get_text('recursive_processing'))
        self.start_button.configure(text=self.lang_manager.get_text('start_conversion'))
        self.progress_label.configure(text=self.lang_manager.get_text('status_idle'))
    
    def select_folder(self):
        """选择文件夹"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.selected_folder = folder_path
            self.folder_entry.delete(0, 'end')
            self.folder_entry.insert(0, folder_path)
    
    def drop(self, event):
        """处理拖拽事件"""
        file_path = event.data
        if isinstance(file_path, str):
            if file_path.startswith('{') and file_path.endswith('}'):
                file_path = file_path[1:-1]
            
            if os.path.isdir(file_path):
                self.selected_folder = file_path
                self.folder_entry.delete(0, 'end')
                self.folder_entry.insert(0, file_path)
    
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.insert('end', message + '\n')
        self.log_text.see('end')
        self.update()
    
    def start_conversion(self):
        """开始转换"""
        if self.is_processing:
            messagebox.showwarning(self.lang_manager.get_text('warning_title'), 
                                 self.lang_manager.get_text('task_running'))
            return
        
        if not self.selected_folder or not os.path.exists(self.selected_folder):
            messagebox.showerror(self.lang_manager.get_text('error_title'), 
                               self.lang_manager.get_text('select_folder_error'))
            return
        
        # 确认操作
        if not messagebox.askyesno(self.lang_manager.get_text('confirm_title'), 
                                  self.lang_manager.get_text('confirm_jpg_to_png_operation').format(folder=self.selected_folder)):
            return
        
        # 清空日志
        self.log_text.delete('1.0', 'end')
        
        # 在新线程中执行转换
        self.is_processing = True
        self.start_button.configure(state='disabled')
        self.progress_label.configure(text=self.lang_manager.get_text('status_processing'))
        
        thread = threading.Thread(target=self.convert_images)
        thread.daemon = True
        thread.start()
    
    def convert_images(self):
        """转换图片"""
        try:
            total_converted = 0
            
            if self.recursive_var.get():
                # 递归处理
                for root, dirs, files in os.walk(self.selected_folder):
                    converted_count = self.process_folder(root, files)
                    total_converted += converted_count
            else:
                # 只处理当前文件夹
                files = os.listdir(self.selected_folder)
                total_converted = self.process_folder(self.selected_folder, files)
            
            # 完成处理
            self.after(0, lambda: self.progress_label.configure(text=self.lang_manager.get_text('status_complete').format(count=total_converted)))
            self.after(0, lambda: self.log_message(self.lang_manager.get_text('conversion_complete').format(total=total_converted)))
            
        except Exception as e:
            self.after(0, lambda: self.progress_label.configure(text=self.lang_manager.get_text('status_error')))
            self.after(0, lambda: self.log_message(self.lang_manager.get_text('unexpected_error').format(error=str(e))))
        
        finally:
            self.after(0, lambda: self.start_button.configure(state='normal'))
            self.is_processing = False
    
    def process_folder(self, folder_path, files):
        """处理单个文件夹中的图片"""
        converted_count = 0
        
        self.after(0, lambda: self.log_message(self.lang_manager.get_text('processing_folder').format(folder=folder_path)))
        
        for filename in files:
            if filename.lower().endswith(('.jpg', '.jpeg')):
                try:
                    input_path = os.path.join(folder_path, filename)
                    
                    # 生成输出文件名
                    name_without_ext = os.path.splitext(filename)[0]
                    output_filename = name_without_ext + '.png'
                    output_path = os.path.join(folder_path, output_filename)
                    
                    # 检查输出文件是否已存在
                    if os.path.exists(output_path):
                        self.after(0, lambda f=filename, o=output_filename: self.log_message(
                            self.lang_manager.get_text('skip_existing_file').format(input=f, output=o)))
                        continue
                    
                    # 转换图片
                    with Image.open(input_path) as img:
                        # 如果是RGBA模式，直接保存
                        # 如果是RGB模式，转换为RGBA以支持透明度
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')
                        
                        img.save(output_path, 'PNG')
                    
                    converted_count += 1
                    self.after(0, lambda f=filename, o=output_filename: self.log_message(
                        self.lang_manager.get_text('conversion_success').format(input=f, output=o)))
                    
                except Exception as e:
                    self.after(0, lambda f=filename, err=str(e): self.log_message(
                        self.lang_manager.get_text('conversion_error').format(file=f, error=err)))
        
        return converted_count