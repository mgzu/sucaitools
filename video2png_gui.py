import tkinter
import tkinter.filedialog
import customtkinter as ctk
import cv2
import os
import threading
import math
import webbrowser
import tkinterdnd2 # Add import for tkinterdnd2

from tkinter import messagebox
from drag_drop_handler import handle_file_drop, handle_folder_drop # Add import for handlers

# LanguageManager will be passed in

class Video2PngFrame(ctk.CTkFrame):
    def __init__(self, master, lang_manager):
        super().__init__(master)
        self.lang_manager = lang_manager

        self.video_path = ""
        self.output_dir = ""
        self.is_processing = False
        self.original_width = 0
        self.original_height = 0
        self.github_url = "https://github.com/dependon/video2png" # Keep URL for link

        # --- GUI 组件 ---
        self.grid_columnconfigure(1, weight=1)

        # --- 行计数器 ---
        current_row = 0

        # 1. 视频文件选择
        self.label_video = ctk.CTkLabel(self, text=self.lang_manager.get_text('select_video_file'))
        self.label_video.grid(row=current_row, column=0, padx=10, pady=(10, 5), sticky="w")
        self.entry_video_path = ctk.CTkEntry(self, placeholder_text=self.lang_manager.get_text('placeholder_select_video'), width=350)
        self.entry_video_path.grid(row=current_row, column=1, padx=10, pady=(10, 5), sticky="ew")
        # 添加拖拽支持
        try:
            self.entry_video_path.drop_target_register(tkinterdnd2.DND_FILES)
            # Define allowed video extensions
            video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv'}
            self.entry_video_path.dnd_bind('<<Drop>>', lambda e: handle_file_drop(e, self.entry_video_path, self.lang_manager, video_extensions, self.update_video_path_and_resolution))
        except Exception as e:
            print(f"视频输入框拖拽功能初始化失败: {e}")
        self.button_browse_video = ctk.CTkButton(self, text=self.lang_manager.get_text('browse'), command=self.select_video_file)
        self.button_browse_video.grid(row=current_row, column=2, padx=10, pady=(10, 5))
        current_row += 1

        # 注册视频输入框为拖拽目标 (Requires tkinterdnd2 setup in main app)
        # self.entry_video_path.drop_target_register(tkinterdnd2.DND_FILES)
        # self.entry_video_path.dnd_bind('<<Drop>>', self.on_drop_video)

        # 1.5 显示原始分辨率
        self.label_original_res_info = ctk.CTkLabel(self, text=self.lang_manager.get_text('original_resolution_label'))
        self.label_original_res_info.grid(row=current_row, column=0, padx=10, pady=(0, 10), sticky="w")
        self.label_original_resolution = ctk.CTkLabel(self, text=self.lang_manager.get_text('no_video_selected'))
        self.label_original_resolution.grid(row=current_row, column=1, columnspan=2, padx=10, pady=(0, 10), sticky="w")
        current_row += 1

        # 2. 输出目录选择
        self.label_output = ctk.CTkLabel(self, text=self.lang_manager.get_text('select_output_dir_label'))
        self.label_output.grid(row=current_row, column=0, padx=10, pady=10, sticky="w")
        self.entry_output_dir = ctk.CTkEntry(self, placeholder_text=self.lang_manager.get_text('placeholder_select_output'), width=350)
        self.entry_output_dir.grid(row=current_row, column=1, padx=10, pady=10, sticky="ew")
        # 添加拖拽支持
        try:
            self.entry_output_dir.drop_target_register(tkinterdnd2.DND_FILES)
            self.entry_output_dir.dnd_bind('<<Drop>>', lambda e: handle_folder_drop(e, self.entry_output_dir, self.lang_manager, self.update_output_dir))
        except Exception as e:
            print(f"输出目录拖拽功能初始化失败: {e}")
        self.button_browse_output = ctk.CTkButton(self, text=self.lang_manager.get_text('browse'), command=self.select_output_dir)
        self.button_browse_output.grid(row=current_row, column=2, padx=10, pady=10)
        current_row += 1

        # 注册输出目录输入框为拖拽目标 (Requires tkinterdnd2 setup in main app)
        # self.entry_output_dir.drop_target_register(tkinterdnd2.DND_FILES)
        # self.entry_output_dir.dnd_bind('<<Drop>>', self.on_drop_output)

        # 3. 提取模式选择
        self.label_mode = ctk.CTkLabel(self, text=self.lang_manager.get_text('extraction_mode'))
        self.label_mode.grid(row=current_row, column=0, padx=10, pady=10, sticky="w")
        self.radio_var = tkinter.IntVar(value=0) # 0: All, 1: Interval
        self.radio_all = ctk.CTkRadioButton(self, text=self.lang_manager.get_text('extract_all_frames'), variable=self.radio_var, value=0, command=self.toggle_interval_entry)
        self.radio_all.grid(row=current_row, column=1, padx=(10,0), pady=10, sticky="w")
        current_row += 1
        self.radio_interval = ctk.CTkRadioButton(self, text=self.lang_manager.get_text('extract_interval_frames'), variable=self.radio_var, value=1, command=self.toggle_interval_entry)
        self.radio_interval.grid(row=current_row, column=1, padx=(10,0), pady=(0, 10), sticky="w")

        self.entry_interval = ctk.CTkEntry(self, width=60, placeholder_text="N")
        self.entry_interval.grid(row=current_row, column=1, padx=(200, 0), pady=(0, 10), sticky="w") # Adjust position
        self.entry_interval.configure(state=tkinter.DISABLED) # Default disabled
        current_row += 1

        # 4. 自定义分辨率设置
        self.custom_resolution_var = tkinter.IntVar(value=0) # 0: No, 1: Yes
        self.check_custom_res = ctk.CTkCheckBox(self, text=self.lang_manager.get_text('custom_output_resolution'), variable=self.custom_resolution_var,
                                                  onvalue=1, offvalue=0, command=self.toggle_custom_resolution_entries)
        self.check_custom_res.grid(row=current_row, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        current_row += 1

        self.label_custom_width = ctk.CTkLabel(self, text=self.lang_manager.get_text('width'))
        self.label_custom_width.grid(row=current_row, column=0, padx=(30, 5), pady=5, sticky="w") # Indent
        self.entry_custom_width = ctk.CTkEntry(self, width=80, placeholder_text=self.lang_manager.get_text('pixels'))
        self.entry_custom_width.grid(row=current_row, column=1, padx=(0, 5), pady=5, sticky="w")

        self.label_custom_height = ctk.CTkLabel(self, text=self.lang_manager.get_text('height'))
        self.label_custom_height.grid(row=current_row, column=1, padx=(90, 5), pady=5, sticky="w") # Adjust position
        self.entry_custom_height = ctk.CTkEntry(self, width=80, placeholder_text=self.lang_manager.get_text('pixels'))
        self.entry_custom_height.grid(row=current_row, column=1, padx=(135, 0), pady=5, sticky="w") # Adjust position

        # Initial disable custom resolution inputs
        self.entry_custom_width.configure(state=tkinter.DISABLED)
        self.label_custom_width.configure(text_color="gray") # Visual cue
        self.entry_custom_height.configure(state=tkinter.DISABLED)
        self.label_custom_height.configure(text_color="gray") # Visual cue
        current_row += 1

        # 5. 图片格式 (Simplified for now)
        self.image_format = ".png"
        # Add format selection later if needed

        # 6. 开始按钮
        self.button_start = ctk.CTkButton(self, text=self.lang_manager.get_text('start_extraction'), command=self.start_extraction_thread)
        self.button_start.grid(row=current_row, column=0, columnspan=3, padx=20, pady=20)
        current_row += 1

        # 7. 进度条
        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", mode="determinate")
        self.progress_bar.grid(row=current_row, column=0, columnspan=3, padx=20, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)
        current_row += 1

        # 8. 状态标签
        self.label_status = ctk.CTkLabel(self, text=self.lang_manager.get_text('status_initial'))
        self.label_status.grid(row=current_row, column=0, columnspan=3, padx=20, pady=(0, 10), sticky="w")
        current_row += 1

        # 9. 日志框
        self.log_textbox = ctk.CTkTextbox(self, height=120, state=tkinter.DISABLED) # Initial disabled
        self.log_textbox.grid(row=current_row, column=0, columnspan=3, padx=20, pady=(5, 5), sticky="nsew")
        self.grid_rowconfigure(current_row, weight=1) # Allow log box to expand
        current_row += 1

        # 10. 清空日志按钮
        self.button_clear_log = ctk.CTkButton(self, text=self.lang_manager.get_text('clear_log'), width=100, command=self.clear_log)
        self.button_clear_log.grid(row=current_row, column=2, padx=20, pady=(0, 5), sticky="e") # Align right
        current_row += 1

        # 11. GitHub 链接
        self.label_github = ctk.CTkLabel(
            self,
            text=self.github_url,
            text_color="#0078D7", # Bright blue
            cursor="hand2"
        )
        self.label_github.grid(
            row=current_row,
            column=0,
            columnspan=3,
            padx=20,
            pady=(15, 10),
            sticky="s"
        )
        self.label_github.bind("<Button-1>", self.open_github_link)

    def update_ui_texts(self):
        """Updates all UI element texts based on the current language."""
        self.label_video.configure(text=self.lang_manager.get_text('select_video_file'))
        self.entry_video_path.configure(placeholder_text=self.lang_manager.get_text('placeholder_select_video'))
        self.button_browse_video.configure(text=self.lang_manager.get_text('browse'))
        self.label_original_res_info.configure(text=self.lang_manager.get_text('original_resolution_label'))
        # Keep original resolution text as is, or update if needed based on state
        # self.label_original_resolution.configure(text=...)
        self.label_output.configure(text=self.lang_manager.get_text('select_output_dir_label'))
        self.entry_output_dir.configure(placeholder_text=self.lang_manager.get_text('placeholder_select_output'))
        self.button_browse_output.configure(text=self.lang_manager.get_text('browse'))
        self.label_mode.configure(text=self.lang_manager.get_text('extraction_mode'))
        self.radio_all.configure(text=self.lang_manager.get_text('extract_all_frames'))
        self.radio_interval.configure(text=self.lang_manager.get_text('extract_interval_frames'))
        self.check_custom_res.configure(text=self.lang_manager.get_text('custom_output_resolution'))
        self.label_custom_width.configure(text=self.lang_manager.get_text('width'))
        self.entry_custom_width.configure(placeholder_text=self.lang_manager.get_text('pixels'))
        self.label_custom_height.configure(text=self.lang_manager.get_text('height'))
        self.entry_custom_height.configure(placeholder_text=self.lang_manager.get_text('pixels'))
        self.button_start.configure(text=self.lang_manager.get_text('start_extraction') if not self.is_processing else self.lang_manager.get_text('processing'))
        # Update status label based on current state, not just initial text
        # self.label_status.configure(text=...)
        self.button_clear_log.configure(text=self.lang_manager.get_text('clear_log'))

    def log(self, message):
        """Appends a message to the log text box."""
        def _update_log():
            self.log_textbox.configure(state=tkinter.NORMAL)
            self.log_textbox.insert(tkinter.END, message + "\n")
            self.log_textbox.see(tkinter.END)
            self.log_textbox.configure(state=tkinter.DISABLED)
        self.after(0, _update_log) # Schedule update in main thread

    def clear_log(self):
        self.log_textbox.configure(state=tkinter.NORMAL)
        self.log_textbox.delete('1.0', tkinter.END)
        self.log_textbox.configure(state=tkinter.DISABLED)

    def update_status(self, message):
        """Updates the status label."""
        self.label_status.configure(text=message)

    def update_progress(self, value):
        """Updates the progress bar."""
        self.progress_bar.set(value)

    def update_original_resolution_label(self, text):
        """Updates the label showing the original video resolution."""
        self.label_original_resolution.configure(text=text)

    def select_video_file(self):
        if self.is_processing:
            messagebox.showwarning(self.lang_manager.get_text('warning_title'), self.lang_manager.get_text('task_running'))
            return
        file_path = tkinter.filedialog.askopenfilename(
            title=self.lang_manager.get_text('select_video_file_title'),
            filetypes=[(self.lang_manager.get_text('video_files'), "*.mp4 *.avi *.mov *.mkv *.wmv"), (self.lang_manager.get_text('all_files'), "*.*")]
        )
        if file_path:
            self.update_video_path_and_resolution(file_path)

    def update_video_path_and_resolution(self, file_path):
        """Updates the video path entry and fetches resolution."""
        self.video_path = file_path
        self.entry_video_path.delete(0, tkinter.END)
        self.entry_video_path.insert(0, self.video_path)
        self.update_status(f"{self.lang_manager.get_text('status_selected_video')}: {os.path.basename(self.video_path)}")
        self.get_video_resolution(file_path) # Get and display resolution
        self.check_start_button_state()

    def select_output_dir(self):
        if self.is_processing:
            messagebox.showwarning(self.lang_manager.get_text('warning_title'), self.lang_manager.get_text('task_running'))
            return
        dir_path = tkinter.filedialog.askdirectory(title=self.lang_manager.get_text('select_output_dir_title'))
        if dir_path:
            self.update_output_dir(dir_path)

    def update_output_dir(self, dir_path):
        """Updates the output directory entry."""
        self.output_dir = dir_path
        self.entry_output_dir.delete(0, tkinter.END)
        self.entry_output_dir.insert(0, self.output_dir)
        self.update_status(f"{self.lang_manager.get_text('status_selected_output')}: {self.output_dir}")
        self.check_start_button_state()

    def toggle_interval_entry(self):
        if self.radio_var.get() == 1: # Interval selected
            self.entry_interval.configure(state=tkinter.NORMAL)
        else:
            self.entry_interval.configure(state=tkinter.DISABLED)

    def toggle_custom_resolution_entries(self):
        if self.custom_resolution_var.get() == 1: # Custom resolution checked
            self.entry_custom_width.configure(state=tkinter.NORMAL)
            self.label_custom_width.configure(text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"]) # Use theme color
            self.entry_custom_height.configure(state=tkinter.NORMAL)
            self.label_custom_height.configure(text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        else:
            self.entry_custom_width.configure(state=tkinter.DISABLED)
            self.label_custom_width.configure(text_color="gray")
            self.entry_custom_height.configure(state=tkinter.DISABLED)
            self.label_custom_height.configure(text_color="gray")

    def start_extraction_thread(self):
        if self.is_processing:
            messagebox.showwarning(self.lang_manager.get_text('warning_title'), self.lang_manager.get_text('task_running'))
            return

        self.video_path = self.entry_video_path.get()
        self.output_dir = self.entry_output_dir.get()

        if not self.video_path or not os.path.isfile(self.video_path):
            messagebox.showerror(self.lang_manager.get_text('error_title'), self.lang_manager.get_text('error_invalid_video_path'))
            return
        if not self.output_dir or not os.path.isdir(self.output_dir):
            messagebox.showerror(self.lang_manager.get_text('error_title'), self.lang_manager.get_text('error_invalid_output_path'))
            return

        extract_mode = self.radio_var.get()
        interval = 0
        if extract_mode == 1: # Interval
            try:
                interval = int(self.entry_interval.get())
                if interval <= 0:
                    raise ValueError("Interval must be positive")
            except ValueError:
                messagebox.showerror(self.lang_manager.get_text('error_title'), self.lang_manager.get_text('error_invalid_interval'))
                return

        custom_res = self.custom_resolution_var.get() == 1
        target_width, target_height = 0, 0
        if custom_res:
            try:
                target_width = int(self.entry_custom_width.get())
                target_height = int(self.entry_custom_height.get())
                if target_width <= 0 or target_height <= 0:
                    raise ValueError("Dimensions must be positive")
            except ValueError:
                messagebox.showerror(self.lang_manager.get_text('error_title'), self.lang_manager.get_text('error_invalid_resolution'))
                return

        # Disable UI elements
        self.button_start.configure(state=tkinter.DISABLED, text=self.lang_manager.get_text('processing'))
        self.button_browse_video.configure(state=tkinter.DISABLED)
        self.button_browse_output.configure(state=tkinter.DISABLED)
        self.is_processing = True
        self.clear_log()
        self.log(self.lang_manager.get_text('log_start_extraction'))
        self.update_status(self.lang_manager.get_text('status_processing'))
        self.update_progress(0)

        # Start thread
        thread = threading.Thread(target=self.extract_frames,
                                  args=(self.video_path, self.output_dir, extract_mode, interval, custom_res, target_width, target_height))
        thread.daemon = True
        thread.start()

    def extract_frames(self, video_path, output_dir, mode, interval, custom_res, target_width, target_height):
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.log(self.lang_manager.get_text('error_cant_open_video'))
                self.after(0, self.on_extraction_complete, False)
                return

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.log(self.lang_manager.get_text('log_total_frames').format(count=total_frames))

            frame_count = 0
            extracted_count = 0
            base_filename = os.path.splitext(os.path.basename(video_path))[0]

            while True:
                ret, frame = cap.read()
                if not ret:
                    break # End of video

                frame_count += 1

                process_this_frame = False
                if mode == 0: # All frames
                    process_this_frame = True
                elif mode == 1: # Interval
                    if frame_count % interval == 0:
                        process_this_frame = True

                if process_this_frame:
                    # Resize if needed
                    if custom_res and target_width > 0 and target_height > 0:
                        try:
                            frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
                        except Exception as resize_e:
                            self.log(self.lang_manager.get_text('error_resizing_frame').format(frame_num=frame_count, error=resize_e))
                            continue # Skip this frame

                    # Save frame
                    output_filename = f"{base_filename}_frame_{extracted_count + 1:06d}{self.image_format}"
                    output_path = os.path.join(output_dir, output_filename)
                    try:
                        # Ensure directory exists (though checked before, good practice)
                        os.makedirs(output_dir, exist_ok=True)
                        # Use imencode to handle potential path issues with non-ASCII characters
                        is_success, buffer = cv2.imencode(self.image_format, frame)
                        if is_success:
                            with open(output_path, 'wb') as f:
                                f.write(buffer)
                            extracted_count += 1
                        else:
                             self.log(self.lang_manager.get_text('error_encoding_frame').format(frame_num=frame_count))

                    except Exception as e:
                        self.log(self.lang_manager.get_text('error_saving_frame').format(frame_num=frame_count, error=e))

                # Update progress bar (in main thread)
                progress = frame_count / total_frames if total_frames > 0 else 0
                self.after(0, self.update_progress, progress)

            self.log(self.lang_manager.get_text('log_extraction_finished').format(count=extracted_count))
            self.after(0, self.on_extraction_complete, True, extracted_count)

        except Exception as e:
            self.log(self.lang_manager.get_text('error_unexpected').format(error=e))
            self.after(0, self.on_extraction_complete, False)
        finally:
            if cap:
                cap.release()

    def on_extraction_complete(self, success, extracted_count=0):
        """Called when the extraction thread finishes."""
        if success:
            messagebox.showinfo(self.lang_manager.get_text('info_title'), self.lang_manager.get_text('info_extraction_complete').format(count=extracted_count))
            self.update_status(self.lang_manager.get_text('status_complete').format(count=extracted_count))
        else:
            messagebox.showerror(self.lang_manager.get_text('error_title'), self.lang_manager.get_text('error_extraction_failed'))
            self.update_status(self.lang_manager.get_text('status_failed'))

        # Re-enable UI elements
        self.button_start.configure(state=tkinter.NORMAL, text=self.lang_manager.get_text('start_extraction'))
        self.button_browse_video.configure(state=tkinter.NORMAL)
        self.button_browse_output.configure(state=tkinter.NORMAL)
        self.is_processing = False
        self.update_progress(0)

    def open_github_link(self, event):
        webbrowser.open_new(self.github_url)

    # --- Drag and Drop Handlers (Placeholder - require main app setup) ---
    def on_drop_video(self, event):
        # This needs to be adapted if used, potentially calling select_video_file logic
        # Requires parsing event.data
        filepath = event.data.strip('{}') # Basic parsing, might need refinement
        if os.path.isfile(filepath):
             self.video_path = filepath
             self.entry_video_path.delete(0, tkinter.END)
             self.entry_video_path.insert(0, self.video_path)
             self.update_status(self.lang_manager.get_text('status_video_selected').format(filename=os.path.basename(self.video_path)))
             self.get_video_resolution(filepath)
        else:
            self.log(self.lang_manager.get_text('log_drop_invalid_video'))

    def on_drop_output(self, event):
        # Similar adaptation needed
        dirpath = event.data.strip('{}')
        if os.path.isdir(dirpath):
            self.output_dir = dirpath
            self.entry_output_dir.delete(0, tkinter.END)
            self.entry_output_dir.insert(0, self.output_dir)
            self.update_status(self.lang_manager.get_text('status_output_selected').format(dirname=os.path.basename(self.output_dir)))
        else:
            self.log(self.lang_manager.get_text('log_drop_invalid_output'))

# Removed standalone execution block
# if __name__ == "__main__":
#     # Need LanguageManager instance if running standalone for testing
#     # from language_manager import LanguageManager
#     # lang_manager = LanguageManager()
#     # root = ctk.CTk() # Use CTk for main window if testing
#     # app = Video2PngFrame(root, lang_manager)
#     # app.pack(expand=True, fill="both")
#     # root.mainloop()
#     pass # No standalone execution intended