import customtkinter as ctk
from tkinter import filedialog, colorchooser, simpledialog, messagebox
from PIL import Image, ImageTk
import os
import tkinterdnd2
import numpy as np

class ImageProcessorFrame(ctk.CTkFrame):
    def __init__(self, master, lang_manager):
        super().__init__(master)
        self.lang_manager = lang_manager
        self.current_image_path = None
        self.original_image = None
        self.processed_image = None
        self.image_tk = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- File Selection Frame ---
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.file_frame.grid_columnconfigure(0, weight=1)

        self.file_label = ctk.CTkLabel(self.file_frame, text=self.lang_manager.get_text('select_image_file'))
        self.file_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.select_button = ctk.CTkButton(self.file_frame, text=self.lang_manager.get_text('browse'), command=self.select_image)
        self.select_button.grid(row=0, column=1, padx=5, pady=5)

        # --- Image Display Area ---
        self.image_display_frame = ctk.CTkFrame(self)
        self.image_display_frame.grid(row=1, column=0, padx=10, pady=0, sticky="nsew")
        self.image_display_frame.grid_columnconfigure(0, weight=1)
        self.image_display_frame.grid_rowconfigure(0, weight=1)

        self.image_canvas = ctk.CTkCanvas(self.image_display_frame, bg="#242424", highlightthickness=0)
        self.image_canvas.grid(row=0, column=0, sticky="nsew")

        # --- Controls Frame ---
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.controls_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1) # Adjusted columns after removing crop

        self.flip_horizontal_button = ctk.CTkButton(self.controls_frame, text=self.lang_manager.get_text('flip_horizontal'), command=self.flip_horizontal)
        self.flip_horizontal_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.flip_vertical_button = ctk.CTkButton(self.controls_frame, text=self.lang_manager.get_text('flip_vertical'), command=self.flip_vertical)
        self.flip_vertical_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.color_to_transparent_button = ctk.CTkButton(self.controls_frame, text=self.lang_manager.get_text('color_to_transparent'), command=self.color_to_transparent)
        self.color_to_transparent_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.rotate_left_button = ctk.CTkButton(self.controls_frame, text=self.lang_manager.get_text('rotate_left'), command=lambda: self.rotate_image(90))
        self.rotate_left_button.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        self.rotate_right_button = ctk.CTkButton(self.controls_frame, text=self.lang_manager.get_text('rotate_right'), command=lambda: self.rotate_image(-90))
        self.rotate_right_button.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

        self.resize_button = ctk.CTkButton(self.controls_frame, text=self.lang_manager.get_text('resize_image'), command=self.resize_image)
        self.resize_button.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        self.save_button = ctk.CTkButton(self.controls_frame, text=self.lang_manager.get_text('save_image'), command=self.save_image)
        self.save_button.grid(row=0, column=6, padx=5, pady=5, sticky="ew") # Moved save button to the last column

        # --- Drag and Drop ---
        self.drop_target_register(tkinterdnd2.DND_FILES)
        self.dnd_bind('<<Drop>>', self.drop)

        self.update_ui_texts() # Initial text update

    def update_ui_texts(self):
        self.file_label.configure(text=self.lang_manager.get_text('select_image_file'))
        self.select_button.configure(text=self.lang_manager.get_text('browse'))
        self.flip_horizontal_button.configure(text=self.lang_manager.get_text('flip_horizontal'))
        self.flip_vertical_button.configure(text=self.lang_manager.get_text('flip_vertical'))
        self.color_to_transparent_button.configure(text=self.lang_manager.get_text('color_to_transparent'))
        self.rotate_left_button.configure(text=self.lang_manager.get_text('rotate_left'))
        self.rotate_right_button.configure(text=self.lang_manager.get_text('rotate_right'))
        self.resize_button.configure(text=self.lang_manager.get_text('resize_image'))
        self.save_button.configure(text=self.lang_manager.get_text('save_image'))

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
            self.original_image = Image.open(file_path)
            self.processed_image = self.original_image.copy()
            self.current_image_path = file_path
            self.display_image()
        except Exception as e:
            print(f"Error loading image: {e}")
            # Optionally show an error message to the user

    def display_image(self):
        if self.processed_image:
            # Resize image to fit canvas while maintaining aspect ratio
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()

            if canvas_width == 1 or canvas_height == 1: # Handle initial size before widget is fully rendered
                 self.after(10, self.display_image) # Retry after a short delay
                 return

            img_width, img_height = self.processed_image.size
            aspect_ratio = img_width / img_height

            if img_width > canvas_width or img_height > canvas_height:
                if (canvas_width / aspect_ratio) <= canvas_height:
                    new_width = canvas_width
                    new_height = int(canvas_width / aspect_ratio)
                else:
                    new_height = canvas_height
                    new_width = int(canvas_height * aspect_ratio)
                display_img = self.processed_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                display_img = self.processed_image.copy()

            self.image_tk = ImageTk.PhotoImage(display_img)

            # Clear previous image and draw the new one
            self.image_canvas.delete("all")
            x_center = canvas_width / 2
            y_center = canvas_height / 2
            self.image_canvas.create_image(x_center, y_center, image=self.image_tk, anchor="center")

            # Bind resize event to update image display
            self.image_canvas.bind('<Configure>', self.on_canvas_resize)

    def on_canvas_resize(self, event):
        self.display_image() # Redraw image on canvas resize

    def flip_horizontal(self):
        if self.processed_image:
            self.processed_image = self.processed_image.transpose(Image.FLIP_LEFT_RIGHT)
            self.display_image()

    def flip_vertical(self):
        if self.processed_image:
            self.processed_image = self.processed_image.transpose(Image.FLIP_TOP_BOTTOM)
            self.display_image()

    def color_to_transparent(self):
        if self.processed_image:
            # Ask user to pick a color
            color_code = colorchooser.askcolor(title=self.lang_manager.get_text('select_color_for_transparency'))
            if color_code and color_code[0]: # color_code is ((R, G, B), '#hex')
                rgb_color = color_code[0] # (R, G, B) tuple

                # Convert image to RGBA if not already
                if self.processed_image.mode != 'RGBA':
                    self.processed_image = self.processed_image.convert('RGBA')

                data = np.array(self.processed_image)   # "data" is a height x width x 4 array
                red, green, blue, alpha = data.T # Transpose and split channels

                # Replace the chosen color with transparency
                # Use a tolerance for color matching
                tolerance = 10 # You can adjust this tolerance
                mask = (abs(red - rgb_color[0]) < tolerance) & \
                       (abs(green - rgb_color[1]) < tolerance) & \
                       (abs(blue - rgb_color[2]) < tolerance)

                data[..., :][mask.T] = (0, 0, 0, 0) # Set matching pixels to transparent (R, G, B, A)

                self.processed_image = Image.fromarray(data)
                self.display_image()

    def rotate_image(self, degrees):
        if self.processed_image:
            # Expand to avoid cropping
            self.processed_image = self.processed_image.rotate(degrees, expand=True)
            self.display_image()

    def resize_image(self):
        if self.processed_image:
            current_width, current_height = self.processed_image.size
            default_text = f"{current_width},{current_height}"

            # Prompt user for new dimensions (width,height)
            new_dimensions_str = simpledialog.askstring(
                self.lang_manager.get_text('resize_title'),
                self.lang_manager.get_text('enter_new_dimensions'),
                parent=self,
                initialvalue=default_text
            )

            if new_dimensions_str is None: # User cancelled
                return

            try:
                width_str, height_str = new_dimensions_str.split(',')
                new_width = int(width_str.strip())
                new_height = int(height_str.strip())

                # Ensure dimensions are valid
                if new_width <= 0 or new_height <= 0:
                    messagebox.showerror(self.lang_manager.get_text('error_title'), self.lang_manager.get_text('error_invalid_dimensions'))
                    return

                # Apply resize
                self.processed_image = self.processed_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.display_image()

            except ValueError:
                messagebox.showerror(self.lang_manager.get_text('error_title'), self.lang_manager.get_text('error_invalid_dimensions_format'))
            except Exception as e:
                print(f"Error during resizing: {e}")
                messagebox.showerror(self.lang_manager.get_text('error_title'), f"{self.lang_manager.get_text('error_during_resize')}: {e}")


    def save_image(self):
        if self.processed_image and self.current_image_path:
            original_dir = os.path.dirname(self.current_image_path)
            original_name, original_ext = os.path.splitext(os.path.basename(self.current_image_path))

            # Suggest a new filename (e.g., original_name_processed.png)
            suggested_name = f"{original_name}_processed{original_ext}"
            suggested_path = os.path.join(original_dir, suggested_name)

            file_path = filedialog.asksaveasfilename(
                initialdir=original_dir,
                initialfile=suggested_name,
                defaultextension=original_ext,
                filetypes=[(self.lang_manager.get_text('image_files'), "*.png *.jpg *.jpeg *.bmp *.gif")]
            )
            if file_path:
                try:
                    # Ensure the image is in a format suitable for saving (e.g., convert RGBA to RGB if saving as JPG)
                    if self.processed_image.mode == 'RGBA' and (file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg')):
                        # Create a white background image
                        background = Image.new('RGB', self.processed_image.size, (255, 255, 255))
                        # Paste the RGBA image onto the background
                        background.paste(self.processed_image, mask=self.processed_image.split()[3]) # 3 is the alpha channel
                        img_to_save = background
                    else:
                        img_to_save = self.processed_image

                    img_to_save.save(file_path)
                    print(f"Image saved successfully to {file_path}")
                    # Optionally show a success message
                except Exception as e:
                    print(f"Error saving image: {e}")
                    # Optionally show an error message

# Example usage (for testing the frame independently)
if __name__ == "__main__":
    class MockLanguageManager:
        def get_text(self, key):
            texts = {
                'select_image_file': '选择图片文件',
                'browse': '浏览',
                'mirror_image': '镜像翻转', # This key is no longer used in the main class but kept for the mock
                'flip_horizontal': '水平翻转',
                'flip_vertical': '垂直翻转',
                'color_to_transparent': '颜色转透明',
                'rotate_left': '左旋转 90°',
                'rotate_right': '右旋转 90°',
                'save_image': '保存图片',
                'image_files': '图片文件',
                'mirror_direction_title': '镜像方向', # This key is no longer used in the main class but kept for the mock
                'mirror_direction_prompt': '输入镜像方向 (水平/垂直):', # This key is no longer used in the main class but kept for the mock
                'horizontal': '水平', # This key is no longer used in the main class but kept for the mock
                'vertical': '垂直', # This key is no longer used in the main class but kept for the mock
                'select_color_for_transparency': '选择透明色',
                'resize_image': '缩放图片',
                'resize_title': '缩放',
                'enter_new_dimensions': '输入新尺寸 (宽,高):',
                'error_title': '错误',
                'error_invalid_dimensions': '无效的尺寸。宽度和高度必须是正整数。',
                'error_invalid_dimensions_format': '无效的格式。请输入“宽度,高度”，例如“800,600”。',
                'error_during_resize': '缩放过程中出错'
            }
            return texts.get(key, key)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.geometry("700x500")
    root.title("Image Processor Test")

    lang_manager = MockLanguageManager()

    frame = ImageProcessorFrame(root, lang_manager)
    frame.pack(expand=True, fill="both", padx=10, pady=10)

    root.mainloop()
