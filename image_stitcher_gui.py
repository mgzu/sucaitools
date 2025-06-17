import customtkinter as ctk
from tkinter import filedialog
from language_manager import LanguageManager
import os
from PIL import Image # 需要安装 Pillow 库
from drag_drop_handler import handle_folder_drop
from tkinterdnd2 import DND_FILES  # 只导入DND_FILES常量，TkinterDnD已在主应用程序中初始化

class ImageStitcherFrame(ctk.CTkFrame):
    def __init__(self, master, lang_manager: LanguageManager):
        super().__init__(master)
        self.lang_manager = lang_manager
        self.selected_folder = None
        self.folder_path_var = ctk.StringVar()
        self.folder_path_var.trace_add("write", self.on_folder_entry_change)

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) # Row for image display area

        # --- Folder Selection ---
        self.folder_frame = ctk.CTkFrame(self)
        self.folder_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        # Configure grid layout for folder_frame
        self.folder_frame.grid_columnconfigure(0, weight=3) # Entry column
        self.folder_frame.grid_columnconfigure(1, weight=1) # Button column
        self.folder_frame.grid_rowconfigure(0, weight=0) # Label row
        self.folder_frame.grid_rowconfigure(1, weight=1) # Entry and Button row

        # --- Columns Setting ---
        self.columns_frame = ctk.CTkFrame(self)
        self.columns_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.columns_frame.grid_columnconfigure(0, weight=1)
        self.columns_frame.grid_columnconfigure(1, weight=1)
        
        self.columns_label = ctk.CTkLabel(self.columns_frame, text=self.lang_manager.get_text('stitcher_columns_label'))
        self.columns_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.columns_var = ctk.StringVar(value="3")
        self.columns_entry = ctk.CTkEntry(self.columns_frame, textvariable=self.columns_var, width=100)
        self.columns_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")


        self.folder_label = ctk.CTkLabel(self.folder_frame, text=self.lang_manager.get_text('stitcher_folder_label'))
        self.folder_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w") # Label spans two columns

        self.folder_entry = ctk.CTkEntry(self.folder_frame, 
                                         placeholder_text=self.lang_manager.get_text('stitcher_folder_placeholder'),
                                         textvariable=self.folder_path_var)
        self.folder_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew") # Entry in row 1, column 0

        # --- Drag and Drop ---
        try:
            # 注册拖放目标
            self.folder_entry.drop_target_register(DND_FILES)
            # 绑定拖放事件
            # Bind the drag and drop event to the handler, passing the entry widget
            self.folder_entry.dnd_bind('<<Drop>>', 
                                      lambda e: handle_folder_drop(e, self.folder_entry, self.lang_manager))
        except Exception as e:
            print(f"文件夹拖拽功能初始化失败: {e}")

        self.select_folder_button = ctk.CTkButton(self.folder_frame, text=self.lang_manager.get_text('stitcher_select_folder_button'), command=self.select_folder)
        self.select_folder_button.grid(row=1, column=1, padx=5, pady=5, sticky="e") # Button in row 1, column 1

        # --- Status Label ---
        self.status_label = ctk.CTkLabel(self, text="", wraplength=780)
        self.status_label.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        # --- Action Buttons ---
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)

        self.stitch_button = ctk.CTkButton(self.button_frame, text=self.lang_manager.get_text('stitcher_stitch_button'), command=self.stitch_images)
        self.stitch_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.save_button = ctk.CTkButton(self.button_frame, text=self.lang_manager.get_text('stitcher_save_button'), command=self.save_stitched_image, state="disabled")
        self.save_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.stitched_image = None # To hold the resulting image
        self.stitched_ctk_image = None # To hold the CTkImage for display

        # --- Image Display Area ---
        self.image_display_frame = ctk.CTkFrame(self)
        self.image_display_frame.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.image_display_frame.grid_columnconfigure(0, weight=1)
        self.image_display_frame.grid_rowconfigure(0, weight=1)

        self.image_display_label = ctk.CTkLabel(self.image_display_frame, text="")
        self.image_display_label.grid(row=0, column=0, sticky="nsew")
        self.image_display_label.bind("<Configure>", self.on_image_display_resize)


    def on_folder_entry_change(self, *args):
        """Handles changes to the folder_entry textvariable."""
        folder_path = self.folder_path_var.get()
        if folder_path and os.path.isdir(folder_path): # Add check if it's a valid directory
            self.selected_folder = folder_path
            self.folder_label.configure(text=f"{self.lang_manager.get_text('stitcher_folder_label')}: {self.selected_folder}")
            self.status_label.configure(text=self.lang_manager.get_text('stitcher_folder_selected').format(folder=os.path.basename(folder_path)))
            self.save_button.configure(state="disabled") # Disable save until stitched
            self.stitched_image = None # Reset stitched image
        else:
             # Handle case where entry is cleared or invalid path
             self.selected_folder = None
             self.folder_label.configure(text=self.lang_manager.get_text('stitcher_folder_label'))
             self.status_label.configure(text="")
             self.save_button.configure(state="disabled")
             self.stitched_image = None
             self.image_display_label.configure(image=None, text=self.lang_manager.get_text('stitcher_display_area')) # Clear displayed image

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_path_var.set(folder_path) # Update the StringVar

    def stitch_images(self):
        if not self.selected_folder or not os.path.isdir(self.selected_folder):
            self.status_label.configure(text=self.lang_manager.get_text('stitcher_no_folder_selected'))
            return

        image_files = [f for f in os.listdir(self.selected_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        if not image_files:
            self.status_label.configure(text=self.lang_manager.get_text('stitcher_no_images_found'))
            return

        images = []
        try:
            for file in image_files:
                img_path = os.path.join(self.selected_folder, file)
                images.append(Image.open(img_path))
        except Exception as e:
            self.status_label.configure(text=self.lang_manager.get_text('stitcher_error_loading_images').format(error=str(e)))
            return

        if not images:
            self.status_label.configure(text=self.lang_manager.get_text('stitcher_no_valid_images'))
            return

        # Assuming all images have the same size for simple grid stitching
        # In a real application, you might need more complex handling for different sizes
        first_img = images[0]
        img_width, img_height = first_img.size
        num_images = len(images)

        # Calculate grid dimensions
        # Get user-defined number of columns
        try:
            cols = int(self.columns_var.get())
            if cols <= 0:
                cols = 3  # Default to 3 if invalid input
        except ValueError:
            cols = 3  # Default to 3 if invalid input
            self.columns_var.set("3")  # Reset to default value
        
        rows = (num_images + cols - 1) // cols # Ceiling division to get the number of rows

        # Calculate stitched image dimensions
        stitched_width = img_width * cols
        stitched_height = img_height * rows

        self.stitched_image = Image.new('RGBA', (stitched_width, stitched_height))

        x_offset = 0
        y_offset = 0
        for i, img in enumerate(images):
            # Resize image if it's not the same size as the first one (basic handling)
            if img.size != (img_width, img_height):
                 img = img.resize((img_width, img_height))
                 
            self.stitched_image.paste(img, (x_offset, y_offset))
            x_offset += img_width
            if (i + 1) % cols == 0: # Use cols for wrapping to the next row
                x_offset = 0
                y_offset += img_height

        self.status_label.configure(text=self.lang_manager.get_text('stitcher_stitching_complete'))
        self.save_button.configure(state="normal")

        # Display the stitched image
        self.display_stitched_image()

    def display_stitched_image(self):
        if self.stitched_image:
            # Get the current size of the display label
            label_width = self.image_display_label.winfo_width()
            label_height = self.image_display_label.winfo_height()

            if label_width > 0 and label_height > 0:
                # Calculate the aspect ratio of the stitched image
                img_width, img_height = self.stitched_image.size
                aspect_ratio = img_width / img_height

                # Calculate the new size while maintaining aspect ratio and fitting within the label
                if label_width / label_height > aspect_ratio:
                    new_height = label_height
                    new_width = int(new_height * aspect_ratio)
                else:
                    new_width = label_width
                    new_height = int(new_width / aspect_ratio)

                # Resize the stitched image
                resized_image = self.stitched_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Convert to CTkImage and display
                self.stitched_ctk_image = ctk.CTkImage(light_image=resized_image,
                                                       dark_image=resized_image, size=(new_width, new_height))
                self.image_display_label.configure(image=self.stitched_ctk_image, text="")
            else:
                # If label size is not available yet, clear the image
                self.image_display_label.configure(image=None, text=self.lang_manager.get_text('stitcher_display_area')) # Add a placeholder text

    def on_image_display_resize(self, event):
        """Handles resizing of the image display label."""
        self.display_stitched_image() # Redraw the image when the label is resized

    def save_stitched_image(self):
        if self.stitched_image:
            save_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                     filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("BMP files", "*.bmp")])
            if save_path:
                try:
                    self.stitched_image.save(save_path)
                    self.status_label.configure(text=self.lang_manager.get_text('stitcher_save_success').format(path=os.path.basename(save_path)))
                except Exception as e:
                    self.status_label.configure(text=self.lang_manager.get_text('stitcher_error_saving').format(error=str(e)))
        else:
            self.status_label.configure(text=self.lang_manager.get_text('stitcher_no_image_to_save'))

    def update_ui_texts(self):
        """Updates all UI elements with current language texts."""
        self.folder_label.configure(text=self.lang_manager.get_text('stitcher_folder_label'))
        self.folder_entry.configure(placeholder_text=self.lang_manager.get_text('stitcher_folder_placeholder'))
        self.select_folder_button.configure(text=self.lang_manager.get_text('stitcher_select_folder_button'))
        self.columns_label.configure(text=self.lang_manager.get_text('stitcher_columns_label'))
        self.stitch_button.configure(text=self.lang_manager.get_text('stitcher_stitch_button'))
        self.save_button.configure(text=self.lang_manager.get_text('stitcher_save_button'))
        # Update status label if it contains a language string
        current_status_text = self.status_label.cget("text")
        if current_status_text:
             # Attempt to re-set status text based on current state if it was a language string
             if self.selected_folder:
                  self.status_label.configure(text=self.lang_manager.get_text('stitcher_folder_selected').format(folder=os.path.basename(self.selected_folder)))
             # Add other conditions here if status label can show other language strings
             else:
                  self.status_label.configure(text="") # Clear if no specific state to report

        # Update image display label text if no image is displayed
        if not self.stitched_ctk_image:
             self.image_display_label.configure(text=self.lang_manager.get_text('stitcher_display_area'))


if __name__ == "__main__":
    # Example usage (for testing the frame independently)
    class MockLanguageManager:
        def get_text(self, key):
            texts = {
                'stitcher_folder_label': 'Selected Folder',
                'stitcher_select_folder_button': 'Select Folder',
                'stitcher_columns_label': 'Columns per row:',
                'stitcher_stitch_button': 'Stitch Images',
                'stitcher_save_button': 'Save Stitched Image',
                'stitcher_no_folder_selected': 'Please select a folder first.',
                'stitcher_no_images_found': 'No image files found in the selected folder.',
                'stitcher_error_loading_images': 'Error loading images: {error}',
                'stitcher_no_valid_images': 'No valid images found in the selected folder.',
                'stitcher_stitching_complete': 'Image stitching complete.',
                'stitcher_save_success': 'Stitched image saved to: {path}',
                'stitcher_error_saving': 'Error saving image: {error}',
                'stitcher_no_image_to_save': 'No stitched image to save.',
                'stitcher_folder_selected': 'Folder selected: {folder}',
                'stitcher_display_area': 'Image stitching effect will be displayed here, scaled to fit the window size.' # Added placeholder text
            }
            return texts.get(key, f"_{key}_")

    root = ctk.CTk()
    root.geometry("800x600")
    lang_manager = MockLanguageManager()
    frame = ImageStitcherFrame(root, lang_manager)
    frame.pack(expand=True, fill="both", padx=10, pady=10)
    root.mainloop()
