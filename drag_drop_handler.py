import os
import tkinter.messagebox
from tkinter import ttk

def handle_file_drop(event, target_entry, lang_manager, allowed_extensions=('.mp4', '.avi', '.mov', '.mkv', '.jpg', '.png')):
    """处理文件拖放事件"""
    try:
        path = event.data.strip('{}')
        if os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in allowed_extensions:
                target_entry.delete(0, 'end')
                target_entry.insert(0, path)
            else:
                tkinter.messagebox.showerror(
                    lang_manager.get_text('error_title'),
                    lang_manager.get_text('invalid_file_type').format(ext=ext)
                )
    except Exception as e:
        tkinter.messagebox.showerror(
            lang_manager.get_text('error_title'),
            lang_manager.get_text('file_drop_error').format(error=str(e))
        )

def handle_folder_drop(event, target_entry, lang_manager):
    """处理文件夹拖放事件"""
    try:
        path = event.data.strip('{}')
        if os.path.isdir(path):
            target_entry.delete(0, 'end')
            target_entry.insert(0, path)
        else:
            tkinter.messagebox.showerror(
                lang_manager.get_text('error_title'),
                lang_manager.get_text('invalid_folder_path')
            )
    except Exception as e:
        tkinter.messagebox.showerror(
            lang_manager.get_text('error_title'),
            lang_manager.get_text('folder_drop_error').format(error=str(e))
        )