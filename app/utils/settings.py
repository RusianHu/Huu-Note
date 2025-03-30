from app.utils.config_manager import ConfigManager

class Settings:
    """
    应用设置类
    现在使用统一的配置管理器来处理设置
    """
    def __init__(self):
        # 使用统一的配置管理器
        self.config_manager = ConfigManager()
    
    def get(self, key, default=None):
        """获取设置值"""
        return self.config_manager.get_app_setting(key, default)
    
    def set(self, key, value):
        """设置值"""
        self.config_manager.set_app_setting(key, value)