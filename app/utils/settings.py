import os
import json

class Settings:
    def __init__(self):
        self.settings_file = os.path.expanduser("~/markdown_notes/.settings.json")
        self.settings = self.load_settings()
    
    def load_settings(self):
        """加载设置"""
        default_settings = {
            "notes_directory": os.path.expanduser("~/markdown_notes"),
            "font_family": "Microsoft YaHei",
            "font_size": 11,
            "theme": "default",
            "auto_save": True,
            "auto_save_interval": 60,  # 秒
            "editor_layout": "vertical"  # 默认上下布局
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as file:
                    loaded_settings = json.load(file)
                    # 合并默认设置和加载的设置
                    default_settings.update(loaded_settings)
            except Exception as e:
                print(f"加载设置失败: {str(e)}")
                
        return default_settings
    
    def save_settings(self):
        """保存设置"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            # 保存设置
            with open(self.settings_file, 'w', encoding='utf-8') as file:
                json.dump(self.settings, file, indent=4)
                
            return True
        except Exception as e:
            print(f"保存设置失败: {str(e)}")
            return False
    
    def get(self, key, default=None):
        """获取设置值"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """设置值"""
        self.settings[key] = value
        self.save_settings()