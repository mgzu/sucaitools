import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import tkinterdnd2
import threading

class ImageRotatorFrame(ctk.CTkFrame):
    def __init__(self, master, lang_manager):
        super().__init__(master)
        self.lang_manager = lang_manager
        self.current_image_path = None
        self.original_image = None
        self.image_tk = None
        self.is_processing = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- File Selection Frame ---
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.file_frame.grid_columnconfigure(0, weight=1)

        self.file_label = ctk.CTkLabel(self.file_frame, text=self.lang_manager.get_text('select_image_file'))
        self.file_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.select_button = ctk.CTkButton(self.file_frame, text=self.lang_manager.get_text('browse'), command=self.select_image)
        self.select_button.grid(row=0, column=1, padx=5, pady=5)

        self.file_path_label = ctk.CTkLabel(self.file_frame, text=self.lang_manager.get_text('no_image_selected'), text_color="gray")
        self.file_path_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        # --- Settings Frame ---
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.settings_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Rotation angle interval
        self.angle_label = ctk.CTkLabel(self.settings_frame, text=self.lang_manager.get_text('rotation_angle_interval'))
        self.angle_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.angle_entry = ctk.CTkEntry(self.settings_frame, placeholder_text="30")
        self.angle_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.angle_entry.insert(0, "30")

        # Start rotation button
        self.start_button = ctk.CTkButton(self.settings_frame, text=self.lang_manager.get_text('start_rotation'), command=self.start_rotation)
        self.start_button.grid(row=0, column=2, padx=5, pady=5)

        # Progress label
        self.progress_label = ctk.CTkLabel(self.settings_frame, text="")
        self.progress_label.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # --- Image Preview Frame ---
        self.preview_frame = ctk.CTkFrame(self)
        self.preview_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        self.preview_canvas = ctk.CTkCanvas(self.preview_frame, bg="#242424", highlightthickness=0)
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")

        # --- Log Frame ---
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.log_frame.grid_columnconfigure(0, weight=1)

        self.log_label = ctk.CTkLabel(self.log_frame, text=self.lang_manager.get_text('log'))
        self.log_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.log_text = ctk.CTkTextbox(self.log_frame, height=100)
        self.log_text.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        # --- Drag and Drop ---
        self.drop_target_register(tkinterdnd2.DND_FILES)
        self.dnd_bind('<<Drop>>', self.drop)

        self.update_ui_texts()

    def update_ui_texts(self):
        self.file_label.configure(text=self.lang_manager.get_text('select_image_file'))
        self.select_button.configure(text=self.lang_manager.get_text('browse'))
        self.angle_label.configure(text=self.lang_manager.get_text('rotation_angle_interval'))
        self.start_button.configure(text=self.lang_manager.get_text('start_rotation'))
        self.log_label.configure(text=self.lang_manager.get_text('log'))
        if not self.current_image_path:
            self.file_path_label.configure(text=self.lang_manager.get_text('no_image_selected'))

    def select_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[(self.lang_manager.get_text('image_files'), "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_path:
            self.load_image(file_path)

    def drop(self, event):
        file_path = event.data
        # Handle potential multiple files dropped (take the first one)
        if isinstance(file_path, str):
            # Remove curly braces if present (TkinterDND adds them for paths with spaces)
            if file_path.startswith('{') and file_path.endswith('}'):
                file_path = file_path[1:-1]
            self.load_image(file_path)
        elif isinstance(file_path, tuple) and file_path:
            # Remove curly braces if present (TkinterDND adds them for paths with spaces)
            first_file = file_path[0]
            if first_file.startswith('{') and first_file.endswith('}'):
                first_file = first_file[1:-1]
            self.load_image(first_file)

    def load_image(self, file_path):
        try:
            # Validate file extension
            valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
            if not file_path.lower().endswith(valid_extensions):
                messagebox.showerror(self.lang_manager.get_text('error_title'), 
                                   self.lang_manager.get_text('invalid_image_format'))
                return

            self.original_image = Image.open(file_path)
            self.current_image_path = file_path
            
            # Update file path label
            filename = os.path.basename(file_path)
            self.file_path_label.configure(text=filename, text_color="white")
            
            # Display preview
            self.display_image_preview()
            
            self.log_message(f"{self.lang_manager.get_text('image_loaded')}: {filename}")
            
        except Exception as e:
            messagebox.showerror(self.lang_manager.get_text('error_title'), 
                               f"{self.lang_manager.get_text('error_loading_image')}: {str(e)}")

    def display_image_preview(self):
        if self.original_image:
            # Calculate display size (max 300x300)
            display_size = self.calculate_display_size(self.original_image.size, (300, 300))
            
            # Resize image for display
            display_image = self.original_image.resize(display_size, Image.Resampling.LANCZOS)
            self.image_tk = ImageTk.PhotoImage(display_image)
            
            # Clear canvas and display image
            self.preview_canvas.delete("all")
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                x = canvas_width // 2
                y = canvas_height // 2
                self.preview_canvas.create_image(x, y, image=self.image_tk, anchor="center")

    def calculate_display_size(self, original_size, max_size):
        """Calculate the display size while maintaining aspect ratio"""
        width, height = original_size
        max_width, max_height = max_size
        
        # Calculate scaling factor
        scale = min(max_width / width, max_height / height)
        
        # Calculate new size
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        return (new_width, new_height)

    def start_rotation(self):
        if self.is_processing:
            messagebox.showwarning(self.lang_manager.get_text('warning_title'), 
                                 self.lang_manager.get_text('task_running'))
            return
            
        if not self.current_image_path or not self.original_image:
            messagebox.showerror(self.lang_manager.get_text('error_title'), 
                               self.lang_manager.get_text('no_image_selected'))
            return
            
        try:
            angle_interval = float(self.angle_entry.get())
            if angle_interval <= 0 or angle_interval >= 360:
                messagebox.showerror(self.lang_manager.get_text('error_title'), 
                                   self.lang_manager.get_text('invalid_angle_interval'))
                return
        except ValueError:
            messagebox.showerror(self.lang_manager.get_text('error_title'), 
                               self.lang_manager.get_text('invalid_angle_value'))
            return
            
        # Start rotation in a separate thread
        self.is_processing = True
        self.start_button.configure(state="disabled")
        self.progress_label.configure(text=self.lang_manager.get_text('processing'))
        
        thread = threading.Thread(target=self.rotate_images_thread, args=(angle_interval,))
        thread.daemon = True
        thread.start()

    def rotate_images_thread(self, angle_interval):
        try:
            # Get file info
            file_dir = os.path.dirname(self.current_image_path)
            file_name = os.path.basename(self.current_image_path)
            name_without_ext, ext = os.path.splitext(file_name)
            
            # Calculate number of rotations
            num_rotations = int(360 / angle_interval)
            
            self.log_message(f"{self.lang_manager.get_text('rotation_started')}: {angle_interval}° {self.lang_manager.get_text('interval')}")
            self.log_message(f"{self.lang_manager.get_text('total_images_to_generate')}: {num_rotations}")
            
            # Generate rotated images
            for i in range(1, num_rotations + 1):
                angle = angle_interval * i
                if angle >= 360:
                    break
                    
                # Rotate image
                rotated_image = self.original_image.rotate(-angle, expand=True, fillcolor=(0, 0, 0, 0))
                
                # Generate output filename
                output_filename = f"{name_without_ext}_{int(angle)}{ext}"
                output_path = os.path.join(file_dir, output_filename)
                
                # Save rotated image
                rotated_image.save(output_path)
                
                # Update progress
                progress_text = f"{self.lang_manager.get_text('processing')} {i}/{num_rotations}"
                self.after(0, lambda text=progress_text: self.progress_label.configure(text=text))
                
                # Log progress
                log_msg = f"{self.lang_manager.get_text('generated')}: {output_filename}"
                self.after(0, lambda msg=log_msg: self.log_message(msg))
            
            # Completion message
            completion_msg = f"{self.lang_manager.get_text('rotation_completed')}: {num_rotations} {self.lang_manager.get_text('images_generated')}"
            self.after(0, lambda msg=completion_msg: self.log_message(msg))
            self.after(0, lambda: self.progress_label.configure(text=self.lang_manager.get_text('completed')))
            
        except Exception as e:
            error_msg = f"{self.lang_manager.get_text('rotation_error')}: {str(e)}"
            self.after(0, lambda msg=error_msg: self.log_message(msg))
            self.after(0, lambda: messagebox.showerror(self.lang_manager.get_text('error_title'), error_msg))
        finally:
            self.after(0, self.rotation_finished)

    def rotation_finished(self):
        self.is_processing = False
        self.start_button.configure(state="normal")

    def log_message(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")