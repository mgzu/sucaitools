import os
import tkinter as tk
import customtkinter as ctk # Import customtkinter
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
from tkinterdnd2 import DND_FILES  # 只导入DND_FILES常量，TkinterDnD已在主应用程序中初始化
from drag_drop_handler import handle_folder_drop # Add import for handlers
# LanguageManager will be passed in, no need to import if passed
# from language_manager import LanguageManager

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

# --- 核心重命名逻辑 ---
def rename_images_in_folder(folder_path, log_callback, lang_manager): # Add lang_manager
    try:
        folder_name = os.path.basename(folder_path)
        if not folder_name:
             log_callback(lang_manager.get_text('skip_root').format(folder_path=folder_path)) # Use passed lang_manager
             return 0

        count = 1
        renamed_count = 0
        log_callback(lang_manager.get_text('start_processing').format(folder_path=folder_path))

        items = sorted(os.listdir(folder_path))

        for filename in items:
            original_full_path = os.path.join(folder_path, filename)

            if os.path.isfile(original_full_path):
                _, ext = os.path.splitext(filename)
                if ext.lower() in SUPPORTED_EXTENSIONS:
                    new_filename = f"{folder_name}_{count}{ext}"
                    new_full_path = os.path.join(folder_path, new_filename)

                    if original_full_path == new_full_path:
                        log_callback(lang_manager.get_text('skip_same_name').format(filename=filename))
                        count += 1
                        continue
                    elif os.path.exists(new_full_path):
                         log_callback(lang_manager.get_text('warning_existing_file').format(filename=filename, new_filename=new_filename))
                         continue

                    try:
                        os.rename(original_full_path, new_full_path)
                        log_callback(lang_manager.get_text('success').format(filename=filename, new_filename=new_filename))
                        renamed_count += 1
                        count += 1
                    except OSError as e:
                        log_callback(lang_manager.get_text('error_rename').format(filename=filename, error=str(e)))

        log_callback(lang_manager.get_text('folder_processed').format(folder_path=folder_path, renamed_count=renamed_count))
        return renamed_count

    except Exception as e:
        log_callback(lang_manager.get_text('unexpected_error').format(error=str(e))) # Use passed lang_manager
        return 0

def rename_images_recursively(root_dir, log_callback, lang_manager): # Add lang_manager
    total_renamed = 0
    if not os.path.isdir(root_dir):
        log_callback(lang_manager.get_text('invalid_folder_error')) # Use passed lang_manager
        return 0

    log_callback(lang_manager.get_text('recursive_start').format(root_dir=root_dir)) # Use passed lang_manager

    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        # Pass lang_manager to the inner function
        renamed_in_folder = rename_images_in_folder(dirpath, log_callback, lang_manager)
        total_renamed += renamed_in_folder

    log_callback(lang_manager.get_text('recursive_complete').format(total_renamed=total_renamed)) # Use passed lang_manager
    return total_renamed

# --- GUI 部分 (Refactored for embedding) ---
class RenamerFrame(ctk.CTkFrame): # Inherit from CTkFrame
    def __init__(self, master, lang_manager):
        super().__init__(master)
        self.lang_manager = lang_manager # Use passed language manager
        # No need to update window title here, main app handles it
        # self.update_window_title() 

        # Configure grid layout for the frame itself
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1) # Adjust row index for log area

        self.selected_folder = tk.StringVar()
        self.is_running = False

        # Language selector is now in the main app
        # self.create_language_selector()

        # 文件夹选择部分 (Use self as master)
        # Use CTk widgets for consistency
        ctk.CTkLabel(self, text=self.lang_manager.get_text('select_folder')).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.folder_entry = ctk.CTkEntry(self, textvariable=self.selected_folder, width=350) # Adjusted width
        self.folder_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.browse_button = ctk.CTkButton(self, text=self.lang_manager.get_text('browse'), command=self.browse_folder)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)

        # --- Drag and Drop ---
        try:
            # 注册拖放目标
            self.folder_entry.drop_target_register(DND_FILES)
            # 绑定拖放事件
            self.folder_entry.dnd_bind('<<Drop>>', 
                                      lambda e: handle_folder_drop(e, self.folder_entry, self.lang_manager))
        except Exception as e:
            print(f"文件夹拖拽功能初始化失败: {e}")

        # 开始按钮 (Use self as master)
        self.rename_button = ctk.CTkButton(self, text=self.lang_manager.get_text('start_rename'), command=self.start_renaming_thread)
        self.rename_button.grid(row=1, column=0, columnspan=3, padx=5, pady=10)

        # 日志区域 (Use self as master)
        ctk.CTkLabel(self, text=self.lang_manager.get_text('log')).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        # Use CTkTextbox for log area
        self.log_area = ctk.CTkTextbox(self, wrap=tk.WORD, height=200) # Adjusted height
        self.log_area.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.log_area.configure(state='disabled')

        # Grid configuration moved to __init__

    # Removed create_language_selector method

    # Removed on_language_change method (handled by main app)

    def update_ui_texts(self):
        # No window title to update here
        # self.update_window_title()
        self.browse_button.configure(text=self.lang_manager.get_text('browse'))
        self.rename_button.configure(text=self.lang_manager.get_text('start_rename') if not self.is_running else self.lang_manager.get_text('processing'))

        # Update label texts using CTk widgets and adjusted grid rows
        # Find labels more robustly if possible, or by grid position
        # Assuming grid layout remains consistent for now
        select_folder_label = self.grid_slaves(row=0, column=0)[0]
        log_label = self.grid_slaves(row=2, column=0)[0]
        if isinstance(select_folder_label, ctk.CTkLabel):
            select_folder_label.configure(text=self.lang_manager.get_text('select_folder'))
        if isinstance(log_label, ctk.CTkLabel):
            log_label.configure(text=self.lang_manager.get_text('log'))

    # Removed update_window_title method

    def log(self, message):
        # Use CTkTextbox methods
        def _update_log():
            self.log_area.configure(state='normal')
            self.log_area.insert(tk.END, message + "\n")
            self.log_area.see(tk.END)
            self.log_area.configure(state='disabled')
        # Use self.after for scheduling within the frame
        self.after(0, _update_log)

    def browse_folder(self):
        if self.is_running:
            messagebox.showwarning(self.lang_manager.get_text('title'), self.lang_manager.get_text('task_running'))
            return
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder.set(folder)

    def update_folder_path(self, path):
        """Update the folder path."""
        self.selected_folder.set(path)

    def start_renaming_thread(self):
        if self.is_running:
            messagebox.showwarning(self.lang_manager.get_text('title'), self.lang_manager.get_text('task_running'))
            return

        root_dir = self.selected_folder.get()
        if not root_dir:
            messagebox.showerror(self.lang_manager.get_text('title'), self.lang_manager.get_text('select_folder_error'))
            return
        if not os.path.isdir(root_dir):
            messagebox.showerror(self.lang_manager.get_text('title'), self.lang_manager.get_text('invalid_folder_error'))
            return

        if not messagebox.askyesno(self.lang_manager.get_text('title'),
                                  self.lang_manager.get_text('confirm_operation').format(folder=os.path.basename(root_dir))):
            return

        self.log_area.configure(state='normal')
        self.log_area.delete('1.0', tk.END)
        self.log_area.configure(state='disabled')
        self.rename_button.configure(state='disabled', text=self.lang_manager.get_text('processing'))
        self.browse_button.configure(state='disabled')
        self.is_running = True

        self.rename_thread = threading.Thread(target=self.run_rename_task, args=(root_dir,))
        self.rename_thread.daemon = True
        self.rename_thread.start()

    def run_rename_task(self, root_dir):
        try:
            # Pass self.lang_manager to the recursive function
            rename_images_recursively(root_dir, self.log, self.lang_manager)
        except Exception as e:
            self.log(self.lang_manager.get_text('unexpected_error').format(error=str(e)))
        finally:
            self.master.after(0, self.on_rename_complete)

    def on_rename_complete(self):
        messagebox.showinfo(self.lang_manager.get_text('title'), self.lang_manager.get_text('completed'))
        self.rename_button.configure(state='normal', text=self.lang_manager.get_text('start_rename'))
        self.browse_button.configure(state='normal')
        self.is_running = False

# Removed standalone execution block
# if __name__ == "__main__":
#     lang_manager = LanguageManager()
#     root = tk.Tk()
#     app = RenamerApp(root)
#     root.mainloop()
