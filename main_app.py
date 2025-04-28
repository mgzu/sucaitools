import customtkinter as ctk
from tkinter import ttk
from language_manager import LanguageManager
from rename_images_gui import RenamerFrame # Import the refactored frame
from image_resizer_gui import ImageResizerFrame # Import the image resizer frame
from video2png_gui import Video2PngFrame # Import the video to png frame
import webbrowser
# Import other tool modules here later

import tkinterdnd2

class MainApplication(ctk.CTk):
    def __init__(self):
        super().__init__()
        # 初始化TkinterDnD，但不使用多重继承
        self.TkdndVersion = tkinterdnd2.TkinterDnD._require(self)
        
        self.lang_manager = LanguageManager()

        self.configure(bg="#242424")      # 设置主窗口背景为深灰色
 
        self.title(self.lang_manager.get_text('main_title')) # Assuming 'main_title' key exists
        self.geometry("800x600")

        # --- Language Selector --- (Moved to main app)
        self.create_language_selector()

        # --- Tab View --- 
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(expand=True, fill="both", padx=10, pady=(0, 10))

        # Add tabs for each tool
        self.renamer_tab_name = self.lang_manager.get_text('tab_rename_images')
        self.resizer_tab_name = self.lang_manager.get_text('tab_resize_images')
        self.video2png_tab_name = self.lang_manager.get_text('tab_video_to_png') # Get initial name

        self.tab_view.add(self.renamer_tab_name)
        self.tab_view.add(self.resizer_tab_name)
        self.tab_view.add(self.video2png_tab_name)
        # self.tab_view.add("Tool 4")

        # --- Embed Tool GUIs --- 
        # Get the actual tab frames using the translated names
        self.renamer_tab_frame = self.tab_view.tab(self.renamer_tab_name)
        self.resizer_tab_frame = self.tab_view.tab(self.resizer_tab_name)
        self.video2png_tab_frame = self.tab_view.tab(self.video2png_tab_name)

        # Instantiate and pack the RenamerFrame into its tab
        self.renamer_app = RenamerFrame(self.renamer_tab_frame, self.lang_manager)
        self.renamer_app.pack(expand=True, fill="both")

        # Instantiate and pack the ImageResizerFrame into its tab
        self.resizer_app = ImageResizerFrame(self.resizer_tab_frame, self.lang_manager)
        self.resizer_app.pack(expand=True, fill="both")

        # Instantiate and pack the Video2PngFrame into its tab
        self.video2png_app = Video2PngFrame(self.video2png_tab_frame, self.lang_manager)
        self.video2png_app.pack(expand=True, fill="both")

        # GitHub 仓库地址
        self.github_label = ctk.CTkLabel(self, text="GitHub: https://github.com/dependon/sucaitools", cursor="hand2", text_color="#78e46f")
        self.github_label.pack(side="bottom", pady=5)
        self.github_label.bind("<Button-1>", lambda event: webbrowser.open_new("https://github.com/dependon/sucaitools"))

        # Add other tool frames here

    def create_language_selector(self):
        languages = self.lang_manager.get_supported_languages()
        current_lang = self.lang_manager.get_current_language()
        current_lang_name = languages.get(current_lang, 'English') # Default to English name if not found

        # Use CTk components if desired, or standard ttk for consistency with existing code
        # For now, using ttk to match rename_images_gui
        lang_frame = ctk.CTkFrame(self) # Use CTkFrame for consistency with main window
        lang_frame.pack(side="top", fill="x", padx=10, pady=(10, 0))

        lang_label = ctk.CTkLabel(lang_frame, text=self.lang_manager.get_text('language') + ":")
        lang_label.pack(side="left", padx=(0, 5))

        self.lang_var = ctk.StringVar(value=current_lang_name)
        self.lang_name_to_code = {v: k for k, v in languages.items()}

        # Using CTkComboBox
        self.lang_combobox = ctk.CTkComboBox(lang_frame, 
                                             variable=self.lang_var, 
                                             values=list(languages.values()), 
                                             state='readonly', 
                                             command=self.on_language_change)
        self.lang_combobox.pack(side="left")

    def on_language_change(self, choice):
        selected_lang_name = self.lang_var.get()
        selected_lang_code = self.lang_name_to_code.get(selected_lang_name)
        if selected_lang_code and self.lang_manager.load_language(selected_lang_code):
            self.restart_application()
        else:
            print(f"Could not switch language to: {selected_lang_name}") # Add logging

    def restart_application(self):
        """更新应用程序的语言设置"""
        try:
            # 在打包环境下，直接更新UI文本而不是重启应用程序
            self.update_ui_texts()
        except Exception as e:
            print(f"更新界面文本时出错：{str(e)}")
            # 如果更新失败，尝试重新加载默认语言
            self.lang_manager.load_language('en')
            self.update_ui_texts()

    def update_ui_texts(self):
        # Update main window title
        self.title(self.lang_manager.get_text('main_title'))

        # Update language selector label
        try:
            lang_frame = self.winfo_children()[0]
            lang_label = lang_frame.winfo_children()[0]
            if isinstance(lang_label, ctk.CTkLabel):
                lang_label.configure(text=self.lang_manager.get_text('language') + ":")
        except (IndexError, AttributeError) as e:
            print(f"Error finding language label: {e}")

        # Get new tab names
        new_renamer_name = self.lang_manager.get_text('tab_rename_images')
        new_resizer_name = self.lang_manager.get_text('tab_resize_images')
        new_video2png_name = self.lang_manager.get_text('tab_video_to_png')

        # Store current tab for later
        current_tab = self.tab_view.get()

        # First unpack all tool frames
        if hasattr(self, 'renamer_app'):
            self.renamer_app.pack_forget()
            self.renamer_app.destroy()
            del self.renamer_app
        if hasattr(self, 'resizer_app'):
            self.resizer_app.pack_forget()
            self.resizer_app.destroy()
            del self.resizer_app
        if hasattr(self, 'video2png_app'):
            self.video2png_app.pack_forget()
            self.video2png_app.destroy()
            del self.video2png_app

        # Remove all existing tabs
        for tab in self.tab_view._tab_dict.copy():
            self.tab_view._tab_dict[tab].grid_remove()
            self.tab_view._tab_dict.pop(tab)

        # Clear segmented button values
        self.tab_view._segmented_button.configure(values=[])

        # Add tabs with new names
        self.tab_view.add(new_renamer_name)
        self.tab_view.add(new_resizer_name)
        self.tab_view.add(new_video2png_name)

        # Update stored names
        self.renamer_tab_name = new_renamer_name
        self.resizer_tab_name = new_resizer_name
        self.video2png_tab_name = new_video2png_name

        # Get new tab frames and ensure they are ready
        self.renamer_tab_frame = self.tab_view.tab(new_renamer_name)
        self.resizer_tab_frame = self.tab_view.tab(new_resizer_name)
        self.video2png_tab_frame = self.tab_view.tab(new_video2png_name)

        # Update the UI before repacking
        self.update()

        # Re-pack the tool frames into their new tabs
        # 重新实例化并pack
        self.renamer_app = RenamerFrame(self.renamer_tab_frame, self.lang_manager)
        self.renamer_app.pack(expand=True, fill="both")
        self.renamer_app.update_ui_texts()

        self.resizer_app = ImageResizerFrame(self.resizer_tab_frame, self.lang_manager)
        self.resizer_app.pack(expand=True, fill="both")
        self.resizer_app.update_ui_texts()

        self.video2png_app = Video2PngFrame(self.video2png_tab_frame, self.lang_manager)
        self.video2png_app.pack(expand=True, fill="both")
        self.video2png_app.update_ui_texts()

        # Try to set the previously selected tab
        try:
            if current_tab == self.renamer_tab_name:
                self.tab_view.set(new_renamer_name)
            elif current_tab == self.resizer_tab_name:
                self.tab_view.set(new_resizer_name)
            elif current_tab == self.video2png_tab_name:
                self.tab_view.set(new_video2png_name)
        except Exception as e:
            print(f"Error setting current tab: {e}")
            # Default to first tab if there's an error
            self.tab_view.set(new_renamer_name)

    def destroy(self):
        """重写destroy方法，确保正确清理资源"""
        try:
            # 先清理所有子组件
            for widget in self.winfo_children():
                if hasattr(widget, 'destroy'):
                    try:
                        widget.destroy()
                    except Exception as e:
                        print(f"清理子组件时出错: {str(e)}")
            
            # 手动清理可能导致问题的命令和回调
            try:
                for command in list(self.tk.call('after', 'info')):
                    self.after_cancel(command)
            except Exception as e:
                print(f"清理after命令时出错: {str(e)}")
                
            # 最后调用父类的destroy方法
            super().destroy()
        except Exception as e:
            print(f"销毁窗口时出错: {str(e)}")

if __name__ == "__main__":
    app = MainApplication()
    app.protocol("WM_DELETE_WINDOW", app.destroy)
    app.mainloop()
