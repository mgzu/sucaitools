import customtkinter as ctk
from tkinter import filedialog
from language_manager import LanguageManager
import os
from PIL import Image # 需要安装 Pillow 库

class ImageStitcherFrame(ctk.CTkFrame):
    def __init__(self, master, lang_manager: LanguageManager):
        super().__init__(master)
        self.lang_manager = lang_manager
        self.selected_folder = None

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) # Row for status label

        # --- Folder Selection ---
        self.folder_frame = ctk.CTkFrame(self)
        self.folder_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.folder_frame.grid_columnconfigure(0, weight=1)

        self.folder_label = ctk.CTkLabel(self.folder_frame, text=self.lang_manager.get_text('stitcher_folder_label'))
        self.folder_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.select_folder_button = ctk.CTkButton(self.folder_frame, text=self.lang_manager.get_text('stitcher_select_folder_button'), command=self.select_folder)
        self.select_folder_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        # --- Status Label ---
        self.status_label = ctk.CTkLabel(self, text="", wraplength=780)
        self.status_label.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        # --- Action Buttons ---
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)

        self.stitch_button = ctk.CTkButton(self.button_frame, text=self.lang_manager.get_text('stitcher_stitch_button'), command=self.stitch_images)
        self.stitch_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.save_button = ctk.CTkButton(self.button_frame, text=self.lang_manager.get_text('stitcher_save_button'), command=self.save_stitched_image, state="disabled")
        self.save_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.stitched_image = None # To hold the resulting image

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.selected_folder = folder_path
            self.folder_label.configure(text=f"{self.lang_manager.get_text('stitcher_folder_label')}: {self.selected_folder}")
            self.status_label.configure(text=self.lang_manager.get_text('stitcher_folder_selected').format(folder=os.path.basename(folder_path)))
            self.save_button.configure(state="disabled") # Disable save until stitched
            self.stitched_image = None # Reset stitched image

    def stitch_images(self):
        if not self.selected_folder:
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

        # Calculate grid size (closest square root)
        grid_size = int(num_images**0.5)
        # Adjust grid size if not a perfect square to fit all images
        if grid_size * grid_size < num_images:
             grid_size += 1
        # If grid_size * (grid_size - 1) >= num_images and grid_size > 1:
        #      grid_size -= 1


        stitched_width = img_width * grid_size
        stitched_height = img_height * grid_size

        self.stitched_image = Image.new('RGBA', (stitched_width, stitched_height))

        x_offset = 0
        y_offset = 0
        for i, img in enumerate(images):
            # Resize image if it's not the same size as the first one (basic handling)
            if img.size != (img_width, img_height):
                 img = img.resize((img_width, img_height))
                 
            self.stitched_image.paste(img, (x_offset, y_offset))
            x_offset += img_width
            if (i + 1) % grid_size == 0:
                x_offset = 0
                y_offset += img_height

        self.status_label.configure(text=self.lang_manager.get_text('stitcher_stitching_complete'))
        self.save_button.configure(state="normal")

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
        self.select_folder_button.configure(text=self.lang_manager.get_text('stitcher_select_folder_button'))
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

if __name__ == "__main__":
    # Example usage (for testing the frame independently)
    class MockLanguageManager:
        def get_text(self, key):
            texts = {
                'stitcher_folder_label': 'Selected Folder',
                'stitcher_select_folder_button': 'Select Folder',
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
                'stitcher_folder_selected': 'Folder selected: {folder}'
            }
            return texts.get(key, f"_{key}_")

    root = ctk.CTk()
    root.geometry("800x600")
    lang_manager = MockLanguageManager()
    frame = ImageStitcherFrame(root, lang_manager)
    frame.pack(expand=True, fill="both", padx=10, pady=10)
    root.mainloop()
