import os
import time
import json
import requests
from PyQt5.QtCore import QObject, pyqtSignal

from app.utils.sync_config import SyncConfig
from app.utils.file_operations import load_file, save_file

class SyncManager(QObject):
    """
    同步管理器
    处理与服务端的通信和同步逻辑
    """
    # 定义信号
    sync_started = pyqtSignal()
    sync_finished = pyqtSignal(bool, str)  # 成功/失败, 消息
    sync_progress = pyqtSignal(str)  # 进度消息
    
    def __init__(self):
        super().__init__()
        self.config = SyncConfig()
        
    def is_sync_enabled(self):
        """检查同步是否已启用"""
        return self.config.is_sync_enabled()
        
    def get_server_url(self):
        """获取服务器URL"""
        return self.config.get("server_url")
        
    def get_api_key(self):
        """获取API密钥"""
        return self.config.get("api_key")
        
    def set_api_key(self, api_key):
        """设置API密钥"""
        self.config.set("api_key", api_key)
        
    def enable_sync(self, enabled=True):
        """启用或禁用同步"""
        self.config.set("enabled", enabled)
        
    def get_headers(self):
        """获取HTTP请求头"""
        return {
            "Authorization": f"Bearer {self.get_api_key()}",
            "Content-Type": "application/json"
        }
        
    def _make_request(self, method, api_path, data=None, params=None):
        """
        发送HTTP请求，并处理常见错误
        
        Args:
            method: 请求方法 ('get', 'post', 'delete')
            api_path: API路径 (例如 '/api/v1/notes')
            data: 请求数据
            params: 查询参数
            
        Returns:
            (success, response_or_error_message)
        """
        # 使用基本URL，不再拼接API路径
        url = self.get_server_url()
        
        # 准备查询参数
        if params is None:
            params = {}
            
        # 将API路径添加为查询参数
        if api_path:
            # 去除前导斜杠
            api_path = api_path.lstrip('/')
            params['api_path'] = api_path
        
        try:
            # 设置请求选项
            request_options = {
                'headers': self.get_headers(),
                'timeout': 10,  # 10秒超时
                'verify': True,  # 验证SSL证书
                'proxies': None  # 不使用代理
            }
            
            if data:
                request_options['json'] = data
                
            if params:
                request_options['params'] = params
                
            # 发送请求
            if method.lower() == 'get':
                response = requests.get(url, **request_options)
            elif method.lower() == 'post':
                response = requests.post(url, **request_options)
            elif method.lower() == 'delete':
                response = requests.delete(url, **request_options)
            else:
                return False, f"不支持的请求方法: {method}"
                
            # 检查响应状态
            if response.status_code == 200:
                return True, response
            else:
                return False, f"服务器返回错误: HTTP {response.status_code}"
                
        except requests.exceptions.SSLError:
            return False, "SSL证书验证失败，请检查服务器证书是否有效"
        except requests.exceptions.ConnectionError as e:
            return False, f"连接服务器失败: {str(e)}"
        except requests.exceptions.Timeout:
            return False, "请求超时，服务器响应时间过长"
        except requests.exceptions.RequestException as e:
            return False, f"请求异常: {str(e)}"
        except Exception as e:
            return False, f"未知错误: {str(e)}"
        
    def upload_note(self, local_path, content=None):
        """
        上传笔记到服务器
        
        Args:
            local_path: 本地文件路径
            content: 文件内容，如果为None则从文件读取
            
        Returns:
            (success, message, cloud_path)
        """
        if not self.is_sync_enabled():
            return False, "同步未启用", None
            
        # 规范化路径，确保路径格式一致
        local_path = os.path.normpath(local_path)
            
        # 获取云端路径
        cloud_path = self.config.get_file_mapping(local_path)
        if not cloud_path:
            # 如果没有映射，使用相对路径作为云端路径
            base_dir = self.config.settings.get("notes_directory")
            base_dir = os.path.normpath(base_dir)
            
            if local_path.startswith(base_dir):
                cloud_path = os.path.relpath(local_path, base_dir)
                print(f"创建新映射: {local_path} -> {cloud_path}")
            else:
                cloud_path = os.path.basename(local_path)
                print(f"使用文件名作为云端路径: {local_path} -> {cloud_path}")
                
        # 如果未提供内容，则从文件读取
        if content is None:
            content = load_file(local_path)
            if content is None:
                return False, f"无法读取文件: {local_path}", None
                
        # 准备请求数据
        data = {
            "path": cloud_path,
            "content": content
        }
        
        # 发送请求
        success, response = self._make_request('post', '/api/v1/notes', data)
        
        if success:
            result = response.json()
            if result.get("success"):
                # 保存映射关系
                self.config.set_file_mapping(local_path, cloud_path)
                return True, "上传成功", cloud_path
            else:
                return False, f"上传失败: {result.get('error', '未知错误')}", None
        else:
            return False, response, None
            
    def download_note(self, cloud_path, local_path=None):
        """
        从服务器下载笔记
        
        Args:
            cloud_path: 云端文件路径
            local_path: 本地保存路径，如果为None则使用映射或默认路径
            
        Returns:
            (success, message, content)
        """
        if not self.is_sync_enabled():
            return False, "同步未启用", None
            
        # 如果未提供本地路径，尝试查找映射
        if local_path is None:
            # 查找映射表中是否有对应的本地路径
            for local, cloud in self.config.config.get("file_mapping", {}).items():
                if cloud == cloud_path:
                    local_path = local
                    break
                    
            # 如果仍未找到，使用默认路径
            if local_path is None:
                base_dir = self.config.settings.get("notes_directory")
                local_path = os.path.join(base_dir, cloud_path)
                
        # 发送请求
        success, response = self._make_request('get', f'/api/v1/notes/{cloud_path}')
        
        if success:
            result = response.json()
            content = result.get("content")
            
            if content is not None:
                # 保存映射关系
                self.config.set_file_mapping(local_path, cloud_path)
                return True, "下载成功", content
            else:
                return False, f"下载失败: {result.get('error', '未知错误')}", None
        else:
            return False, response, None
            
    def delete_note(self, cloud_path):
        """
        从服务器删除笔记或文件夹
        
        Args:
            cloud_path: 云端文件路径
            
        Returns:
            (success, message)
        """
        if not self.is_sync_enabled():
            return False, "同步未启用"
            
        # 发送请求
        success, response = self._make_request('delete', f'/api/v1/notes/{cloud_path}')
        
        if success:
            result = response.json()
            if result.get("success"):
                # 删除所有对应的映射
                for local, cloud in list(self.config.config.get("file_mapping", {}).items()):
                    if cloud == cloud_path or cloud.startswith(cloud_path + '/'):
                        self.config.remove_file_mapping(local)
                return True, "删除成功"
            else:
                return False, f"删除失败: {result.get('error', '未知错误')}"
        else:
            return False, response
            
    def list_remote_notes(self):
        """
        获取服务器上的笔记列表
        
        Returns:
            (success, message, notes)
        """
        if not self.is_sync_enabled():
            return False, "同步未启用", None
            
        # 发送请求
        success, response = self._make_request('get', '/api/v1/notes')
        
        if success:
            result = response.json()
            notes = result.get("notes", [])
            
            # 处理文件夹信息
            # 从文件路径中提取目录结构
            folders = set()
            for note in notes:
                path = note["path"]
                parts = path.split('/')
                # 添加所有父目录
                current_path = ""
                for part in parts[:-1]:  # 排除文件名
                    if not part:  # 跳过空部分
                        continue
                    current_path = current_path + "/" + part if current_path else part
                    folders.add(current_path)
            
            # 将文件夹添加到结果中
            for folder in folders:
                notes.append({
                    "path": folder,
                    "filename": os.path.basename(folder),
                    "last_modified": 0,
                    "size": 0,
                    "is_dir": True
                })
                
            return True, "获取成功", notes
        else:
            return False, response, None
            
    def search_remote_notes(self, keyword):
        """
        在服务器上搜索笔记
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            (success, message, results)
        """
        if not self.is_sync_enabled():
            return False, "同步未启用", None
            
        # 发送请求
        success, response = self._make_request('get', '/api/v1/search', params={'keyword': keyword})
        
        if success:
            result = response.json()
            results = result.get("results", [])
            return True, "搜索成功", results
        else:
            return False, response, None
            
    def test_connection(self):
        """
        测试与服务器的连接
        
        Returns:
            (success, message)
        """
        if not self.get_server_url():
            return False, "服务器地址未设置"
            
        try:
            # 构建简单的测试URL，使用查询参数而非路径
            api_url = self.get_server_url()
            
            # 添加认证头
            headers = self.get_headers()
            
            # 添加专用的测试参数
            params = {
                "test_connection": "1"
            }
            
            # 发送带有认证的GET请求
            response = requests.get(
                api_url,
                headers=headers,
                params=params,  # 使用查询参数
                timeout=5,
                verify=True,
                proxies=None
            )
            
            if response.status_code == 200:
                return True, "连接成功"
            else:
                return False, f"服务器返回错误: HTTP {response.status_code}"
                
        except requests.exceptions.SSLError:
            return False, "SSL证书验证失败，请检查服务器证书是否有效"
        except requests.exceptions.ConnectionError as e:
            return False, f"连接服务器失败: {str(e)}"
        except requests.exceptions.Timeout:
            return False, "请求超时，服务器响应时间过长"
        except requests.exceptions.RequestException as e:
            return False, f"请求异常: {str(e)}"
        except Exception as e:
            return False, f"未知错误: {str(e)}"
            
    def sync_notes(self):
        """
        同步笔记
        
        Returns:
            (success, message)
        """
        if not self.is_sync_enabled():
            return False, "同步未启用"
            
        self.sync_started.emit()
        self.sync_progress.emit("开始同步...")
        
        # 先测试连接
        success, message = self.test_connection()
        if not success:
            self.sync_finished.emit(False, f"无法连接到服务器: {message}")
            return False, f"无法连接到服务器: {message}"
        
        try:
            # 获取本地笔记列表
            base_dir = self.config.settings.get("notes_directory")
            local_notes = self._scan_local_notes(base_dir)
            
            # 构建同步请求数据
            sync_data = {
                "notes": []
            }
            
            for note in local_notes:
                local_path = note["path"]
                cloud_path = self.config.get_file_mapping(local_path)
                
                # 如果没有映射，使用相对路径
                if not cloud_path:
                    cloud_path = os.path.relpath(local_path, base_dir)
                    
                sync_data["notes"].append({
                    "path": cloud_path,
                    "last_modified": int(os.path.getmtime(local_path))
                })
                
            # 发送同步请求
            self.sync_progress.emit("正在与服务器通信...")
            success, response = self._make_request('post', '/api/v1/sync', sync_data)
            
            if not success:
                self.sync_finished.emit(False, f"同步失败: {response}")
                return False, f"同步失败: {response}"
                
            result = response.json()
            to_download = result.get("to_download", [])
            to_upload = result.get("to_upload", [])
            to_delete = result.get("to_delete", [])
            
            # 处理需要下载的笔记
            self.sync_progress.emit(f"需要下载 {len(to_download)} 个笔记...")
            for note in to_download:
                cloud_path = note["path"]
                success, message, content = self.download_note(cloud_path)
                
                if success and content:
                    # 查找或创建本地路径
                    local_path = None
                    for local, cloud in self.config.config.get("file_mapping", {}).items():
                        if cloud == cloud_path:
                            local_path = local
                            break
                            
                    if not local_path:
                        local_path = os.path.join(base_dir, cloud_path)
                        
                    # 保存到本地
                    save_file(content, local_path)
                    self.config.set_file_mapping(local_path, cloud_path)
                    
            # 处理需要上传的笔记
            self.sync_progress.emit(f"需要上传 {len(to_upload)} 个笔记...")
            for note in to_upload:
                cloud_path = note["path"]
                
                # 查找本地路径
                local_path = None
                for local, cloud in self.config.config.get("file_mapping", {}).items():
                    if cloud == cloud_path:
                        local_path = local
                        break
                        
                if not local_path:
                    local_path = os.path.join(base_dir, cloud_path)
                    
                if os.path.exists(local_path):
                    content = load_file(local_path)
                    if content:
                        self.upload_note(local_path, content)
                        
            # 更新最后同步时间
            self.config.update_last_sync_time()
            
            self.sync_progress.emit("同步完成")
            self.sync_finished.emit(True, f"同步完成: 下载 {len(to_download)} 个笔记, 上传 {len(to_upload)} 个笔记")
            return True, f"同步完成: 下载 {len(to_download)} 个笔记, 上传 {len(to_upload)} 个笔记"
            
        except Exception as e:
            error_msg = f"同步失败: {str(e)}"
            self.sync_finished.emit(False, error_msg)
            return False, error_msg
            
    def _scan_local_notes(self, base_dir):
        """扫描本地笔记文件"""
        notes = []
        
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.md') and not file.startswith('.'):
                    full_path = os.path.join(root, file)
                    notes.append({
                        "path": full_path,
                        "last_modified": int(os.path.getmtime(full_path))
                    })
                    
        return notes