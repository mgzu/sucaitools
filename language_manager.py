import os
import json
import locale

CONFIG_FILE = 'config.json'

class LanguageManager:
    def __init__(self):
        self.current_language = None
        self.translations = {}
        # Correct the directory name
        self.languages_dir = os.path.join(os.path.dirname(__file__), 'languages') 
        self.supported_languages = {
            'en': 'English',
            'zh_CN': '中文',
            'ru': 'Русский',
            'ja': '日本語',
            'de': 'Deutsch',
            'pt': 'Português',
            'fr': 'Français'
        }
        self.default_language = 'en' # Default language

        # Load saved language or detect system language
        saved_lang = self.load_config()
        if saved_lang and self.load_language(saved_lang):
            pass # Language loaded from config
        else:
            # Try system language
            try:
                system_lang_code = locale.getdefaultlocale()[0].split('_')[0] # Get 'en' from 'en_US'
                if system_lang_code in self.supported_languages and self.load_language(system_lang_code):
                     pass # System language loaded
                else:
                    self.load_language(self.default_language) # Fallback to default
            except Exception:
                 self.load_language(self.default_language) # Fallback on error
    
    def load_language(self, lang_code):
        """加载指定的语言文件"""
        if lang_code not in self.supported_languages:
            lang_code = 'en'  # 默认使用英语
        
        try:
            # Use the corrected directory path
            file_path = os.path.join(self.languages_dir, f'{lang_code}.json') 
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            self.current_language = lang_code
            self.save_config(lang_code) # Save the newly loaded language
            return True
        except FileNotFoundError:
            print(f'Language file not found: {file_path}')
            # Attempt to load default language if the selected one fails
            if lang_code != self.default_language:
                print(f'Falling back to default language: {self.default_language}')
                return self.load_language(self.default_language)
            return False
        except Exception as e:
            print(f'Error loading language file {file_path}: {e}')
            return False
    
    def get_text(self, key):
        """获取翻译文本"""
        return self.translations.get(key, key)
    
    def get_current_language(self):
        """获取当前语言代码"""
        return self.current_language
    
    def get_supported_languages(self):
        """获取支持的语言列表"""
        return self.supported_languages

    def save_config(self, lang_code):
        """将当前语言代码保存到配置文件"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), CONFIG_FILE)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({'language': lang_code}, f, indent=4)
        except Exception as e:
            print(f"Error saving config file: {e}")

    def load_config(self):
        """从配置文件加载语言代码"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), CONFIG_FILE)
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('language')
        except Exception as e:
            print(f"Error loading config file: {e}")
        return None