<?php
/**
 * HuuNoteServer.php
 * 
 * Huu Note 笔记同步服务端
 * 提供笔记的上传、下载、删除、搜索、同步、重命名等功能
 */

// 设置时区
date_default_timezone_set('Asia/Shanghai');

// 允许跨域请求
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, DELETE, PUT, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
header('Content-Type: application/json; charset=UTF-8');

// 如果是OPTIONS请求，直接返回200
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// 引入API密钥文件
require_once('api_keys.php');

/**
 * 主服务类
 */
class HuuNoteServer {
    // 定义存储路径
    private $baseStoragePath = 'notes_storage';
    
    // API版本
    private $apiVersion = 'v1';
    
    /**
     * 构造函数
     */
    public function __construct() {
        // 确保存储目录存在
        if (!file_exists($this->baseStoragePath)) {
            mkdir($this->baseStoragePath, 0755, true);
        }
    }
    
    /**
     * 路由请求到对应的处理方法
     */
    public function handleRequest() {
        // 获取请求方法和路径
        $method = $_SERVER['REQUEST_METHOD'];
        
        // 检查是否是测试连接请求
        if (isset($_GET['test_connection'])) {
            // 直接验证API密钥
            if ($this->authenticateRequest()) {
                $this->sendResponse(['success' => true, 'message' => '连接成功']);
            } else {
                $this->sendResponse(['error' => '未授权访问'], 401);
            }
            return;
        }
        
        // 使用URL参数获取API路径
        if (isset($_GET['api_path'])) {
            $pathParts = explode('/', trim($_GET['api_path'], '/'));
        } else {
            // 原有解析方式作为备选
            $requestUri = isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : '';
            $path = parse_url($requestUri, PHP_URL_PATH);
            $pathParts = explode('/', trim($path, '/'));
        }
        
        // 检查是否是API请求
        if (count($pathParts) < 2 || $pathParts[0] != 'api') {
            $this->sendResponse(['error' => '无效的API请求'], 400);
            return;
        }
        
        // 验证API版本
        if ($pathParts[1] != $this->apiVersion) {
            $this->sendResponse(['error' => '不支持的API版本'], 400);
            return;
        }
        
        // 验证API密钥
        if (!$this->authenticateRequest()) {
            $this->sendResponse(['error' => '未授权访问'], 401);
            return;
        }
        
        // 路由到对应方法
        $endpoint = isset($pathParts[2]) ? $pathParts[2] : '';
        
        switch ($endpoint) {
            case 'notes':
                if ($method === 'GET' && isset($pathParts[3])) {
                    $this->downloadNote($pathParts[3]);
                } elseif ($method === 'GET') {
                    $this->listNotes();
                } elseif ($method === 'POST') {
                    $this->uploadNote();
                } elseif ($method === 'DELETE' && isset($pathParts[3])) {
                    $this->deleteNote($pathParts[3]);
                } else {
                    $this->sendResponse(['error' => '无效的请求'], 400);
                }
                break;
                
            case 'sync':
                $this->syncNotes();
                break;
                
            case 'search':
                $this->searchNotes();
                break;
                
            // 添加重命名端点
            case 'rename':
                if ($method === 'PUT') {
                    $this->renameItem();
                } else {
                    $this->sendResponse(['error' => '无效的请求方法，重命名功能需要使用PUT'], 405);
                }
                break;
                
            default:
                $this->sendResponse(['error' => '未找到请求的资源'], 404);
        }
    }
    
    /**
     * 验证请求的API密钥
     * @return bool 验证是否通过
     */
    private function authenticateRequest() {
        global $API_KEYS;
        
        // 从请求头中获取API密钥
        $headers = getallheaders();
        $apiKey = isset($headers['Authorization']) ? str_replace('Bearer ', '', $headers['Authorization']) : '';
        
        // 验证API密钥
        return in_array($apiKey, $API_KEYS);
    }
    
    /**
     * 获取指定用户的存储目录
     * @param string $apiKey API密钥
     * @return string 存储目录路径
     */
    private function getUserStoragePath($apiKey) {
        // 使用API密钥的MD5值作为用户目录名，避免直接暴露密钥
        $userDir = md5($apiKey);
        $path = $this->baseStoragePath . '/' . $userDir;
        
        // 确保目录存在
        if (!file_exists($path)) {
            mkdir($path, 0755, true);
        }
        
        return $path;
    }
    
    /**
     * 列出所有笔记
     */
    private function listNotes() {
        $apiKey = $this->getApiKeyFromRequest();
        $userPath = $this->getUserStoragePath($apiKey);
        
        $notes = [];
        $this->scanDirectory($userPath, '', $notes);
        
        $this->sendResponse(['notes' => $notes]);
    }
    
    /**
     * 递归扫描目录获取笔记列表
     * @param string $baseDir 基础目录
     * @param string $subDir 子目录
     * @param array &$results 结果数组
     */
    private function scanDirectory($baseDir, $subDir, &$results) {
        $currentDir = $baseDir;
        if ($subDir !== '') {
            $currentDir .= '/' . $subDir;
        }
        
        if (!file_exists($currentDir)) {
            return;
        }
        
        $files = scandir($currentDir);
        foreach ($files as $file) {
            if ($file === '.' || $file === '..') {
                continue;
            }
            
            $path = $currentDir . '/' . $file;
            $relativePath = $subDir !== '' ? $subDir . '/' . $file : $file;
            
            if (is_dir($path)) {
                $this->scanDirectory($baseDir, $relativePath, $results);
            } elseif (pathinfo($file, PATHINFO_EXTENSION) === 'md') {
                $results[] = [
                    'path' => $relativePath,
                    'filename' => $file,
                    'last_modified' => filemtime($path),
                    'size' => filesize($path)
                ];
            }
        }
    }
    
    /**
     * 上传笔记
     */
    private function uploadNote() {
        $apiKey = $this->getApiKeyFromRequest();
        $userPath = $this->getUserStoragePath($apiKey);
        
        // 获取请求内容
        $requestData = json_decode(file_get_contents('php://input'), true);
        
        if (!isset($requestData['path']) || !isset($requestData['content'])) {
            $this->sendResponse(['error' => '缺少必要参数'], 400);
            return;
        }
        
        $notePath = $requestData['path'];
        $content = $requestData['content'];
        
        // 安全检查：确保路径不包含 ..
        if (strpos($notePath, '..') !== false) {
            $this->sendResponse(['error' => '无效的笔记路径'], 400);
            return;
        }
        
        // 确保文件扩展名为 .md
        if (pathinfo($notePath, PATHINFO_EXTENSION) !== 'md') {
            $notePath .= '.md';
        }
        
        // 构建完整路径
        $fullPath = $userPath . '/' . $notePath;
        
        // 确保目录存在
        $directory = dirname($fullPath);
        if (!file_exists($directory)) {
            mkdir($directory, 0755, true);
        }
        
        // 写入文件
        if (file_put_contents($fullPath, $content) !== false) {
            $this->sendResponse([
                'success' => true,
                'path' => $notePath,
                'last_modified' => filemtime($fullPath)
            ]);
        } else {
            $this->sendResponse(['error' => '保存笔记失败'], 500);
        }
    }
    
    /**
     * 下载笔记
     * @param string $notePath 笔记路径
     */
    private function downloadNote($notePath) {
        $apiKey = $this->getApiKeyFromRequest();
        $userPath = $this->getUserStoragePath($apiKey);
        
        // 安全检查：确保路径不包含 ..
        if (strpos($notePath, '..') !== false) {
            $this->sendResponse(['error' => '无效的笔记路径'], 400);
            return;
        }
        
        // 构建完整路径
        $fullPath = $userPath . '/' . $notePath;
        
        if (!file_exists($fullPath)) {
            $this->sendResponse(['error' => '笔记不存在'], 404);
            return;
        }
        
        // 读取文件内容
        $content = file_get_contents($fullPath);
        if ($content !== false) {
            $this->sendResponse([
                'path' => $notePath,
                'content' => $content,
                'last_modified' => filemtime($fullPath)
            ]);
        } else {
            $this->sendResponse(['error' => '读取笔记失败'], 500);
        }
    }
    
    /**
     * 删除笔记或文件夹
     * @param string $notePath 笔记路径
     */
    private function deleteNote($notePath) {
        $apiKey = $this->getApiKeyFromRequest();
        $userPath = $this->getUserStoragePath($apiKey);
        
        // 安全检查：确保路径不包含 ..
        if (strpos($notePath, '..') !== false) {
            $this->sendResponse(['error' => '无效的笔记路径'], 400);
            return;
        }
        
        // 构建完整路径
        $fullPath = $userPath . '/' . $notePath;
        
        if (!file_exists($fullPath)) {
            $this->sendResponse(['error' => '笔记或文件夹不存在'], 404);
            return;
        }
        
        // 判断是文件还是目录
        if (is_dir($fullPath)) {
            // 删除目录及其内容
            if ($this->deleteDirectory($fullPath)) {
                $this->sendResponse(['success' => true, 'path' => $notePath, 'is_dir' => true]);
            } else {
                $this->sendResponse(['error' => '删除文件夹失败'], 500);
            }
        } else {
            // 删除文件
            if (unlink($fullPath)) {
                $this->sendResponse(['success' => true, 'path' => $notePath, 'is_dir' => false]);
            } else {
                $this->sendResponse(['error' => '删除笔记失败'], 500);
            }
        }
    }
    
    /**
     * 递归删除目录及其内容
     * @param string $dir 目录路径
     * @return bool 是否成功删除
     */
    private function deleteDirectory($dir) {
        if (!file_exists($dir)) {
            return true;
        }
        
        if (!is_dir($dir)) {
            return unlink($dir);
        }
        
        // 遍历目录内容
        foreach (scandir($dir) as $item) {
            if ($item == '.' || $item == '..') {
                continue;
            }
            
            if (!$this->deleteDirectory($dir . DIRECTORY_SEPARATOR . $item)) {
                return false;
            }
        }
        
        return rmdir($dir);
    }
    
    /**
     * 重命名笔记或文件夹
     * 支持重命名单个笔记文件或整个文件夹
     */
    private function renameItem() {
        $apiKey = $this->getApiKeyFromRequest();
        $userPath = $this->getUserStoragePath($apiKey);
        
        // 获取请求内容
        $requestData = json_decode(file_get_contents('php://input'), true);
        
        if (!isset($requestData['old_path']) || !isset($requestData['new_path'])) {
            $this->sendResponse(['error' => '缺少必要参数，需要提供old_path和new_path'], 400);
            return;
        }
        
        $oldPath = $requestData['old_path'];
        $newPath = $requestData['new_path'];
        
        // 安全检查：确保路径不包含 ..
        if (strpos($oldPath, '..') !== false || strpos($newPath, '..') !== false) {
            $this->sendResponse(['error' => '无效的路径'], 400);
            return;
        }
        
        // 构建完整路径
        $oldFullPath = $userPath . '/' . $oldPath;
        $newFullPath = $userPath . '/' . $newPath;
        
        // 检查源是否存在
        if (!file_exists($oldFullPath)) {
            $this->sendResponse(['error' => '源文件或文件夹不存在'], 404);
            return;
        }
        
        // 检查目标是否已存在
        if (file_exists($newFullPath)) {
            $this->sendResponse(['error' => '目标路径已存在，不能覆盖'], 409);
            return;
        }
        
        // 确保新文件的目录存在
        $newDirectory = dirname($newFullPath);
        if (!file_exists($newDirectory)) {
            if (!mkdir($newDirectory, 0755, true)) {
                $this->sendResponse(['error' => '无法创建目标目录'], 500);
                return;
            }
        }
        
        // 执行重命名
        if (rename($oldFullPath, $newFullPath)) {
            $isDir = is_dir($newFullPath);
            $this->sendResponse([
                'success' => true,
                'old_path' => $oldPath,
                'new_path' => $newPath,
                'is_dir' => $isDir,
                'last_modified' => filemtime($newFullPath)
            ]);
        } else {
            $this->sendResponse(['error' => '重命名失败'], 500);
        }
    }
    
    /**
     * 同步笔记
     * 客户端发送本地的笔记列表，服务器比较后返回需要更新的笔记列表
     */
    private function syncNotes() {
        $apiKey = $this->getApiKeyFromRequest();
        $userPath = $this->getUserStoragePath($apiKey);
        
        // 获取请求内容
        $requestData = json_decode(file_get_contents('php://input'), true);
        
        if (!isset($requestData['notes'])) {
            $this->sendResponse(['error' => '缺少必要参数'], 400);
            return;
        }
        
        $clientNotes = $requestData['notes'];
        $clientNotesMap = [];
        
        // 创建客户端笔记的映射，方便查找
        foreach ($clientNotes as $note) {
            $clientNotesMap[$note['path']] = $note;
        }
        
        // 获取服务器上的笔记
        $serverNotes = [];
        $this->scanDirectory($userPath, '', $serverNotes);
        
        // 比较差异
        $toDownload = []; // 客户端需要下载的笔记
        $toUpload = []; // 客户端需要上传的笔记
        $toDelete = []; // 客户端需要删除的笔记
        
        // 检查服务器上有但客户端可能没有或需要更新的笔记
        foreach ($serverNotes as $serverNote) {
            if (!isset($clientNotesMap[$serverNote['path']])) {
                // 服务器上有，客户端没有的笔记
                $toDownload[] = $serverNote;
            } else {
                // 比较修改时间，取最新的
                $clientNote = $clientNotesMap[$serverNote['path']];
                if ($serverNote['last_modified'] > $clientNote['last_modified']) {
                    $toDownload[] = $serverNote;
                }
            }
        }
        
        // 检查客户端有但服务器可能没有或需要更新的笔记
        foreach ($clientNotes as $clientNote) {
            $found = false;
            foreach ($serverNotes as $serverNote) {
                if ($serverNote['path'] === $clientNote['path']) {
                    $found = true;
                    if ($clientNote['last_modified'] > $serverNote['last_modified']) {
                        $toUpload[] = $clientNote;
                    }
                    break;
                }
            }
            if (!$found) {
                $toUpload[] = $clientNote;
            }
        }
        
        $this->sendResponse([
            'to_download' => $toDownload,
            'to_upload' => $toUpload,
            'to_delete' => $toDelete
        ]);
    }
    
    /**
     * 搜索笔记
     */
    private function searchNotes() {
        $apiKey = $this->getApiKeyFromRequest();
        $userPath = $this->getUserStoragePath($apiKey);
        
        // 获取搜索关键词
        $keyword = isset($_GET['keyword']) ? $_GET['keyword'] : '';
        
        if (empty($keyword)) {
            $this->sendResponse(['error' => '缺少搜索关键词'], 400);
            return;
        }
        
        // 获取所有笔记
        $notes = [];
        $this->scanDirectory($userPath, '', $notes);
        
        // 搜索结果
        $results = [];
        
        foreach ($notes as $note) {
            $fullPath = $userPath . '/' . $note['path'];
            $content = file_get_contents($fullPath);
            
            if (stripos($content, $keyword) !== false) {
                // 找到关键词，获取上下文
                $context = $this->getSearchContext($content, $keyword);
                $results[] = [
                    'path' => $note['path'],
                    'filename' => $note['filename'],
                    'context' => $context,
                    'matches' => substr_count(strtolower($content), strtolower($keyword))
                ];
            }
        }
        
        $this->sendResponse(['results' => $results]);
    }
    
    /**
     * 获取搜索关键词的上下文
     * @param string $content 文件内容
     * @param string $keyword 搜索关键词
     * @param int $contextLength 上下文长度
     * @return string 上下文
     */
    private function getSearchContext($content, $keyword, $contextLength = 60) {
        $pos = stripos($content, $keyword);
        if ($pos === false) {
            return '';
        }
        
        $start = max(0, $pos - $contextLength);
        $end = min(strlen($content), $pos + strlen($keyword) + $contextLength);
        
        $context = substr($content, $start, $end - $start);
        
        if ($start > 0) {
            $context = '...' . $context;
        }
        
        if ($end < strlen($content)) {
            $context = $context . '...';
        }
        
        return $context;
    }
    
    /**
     * 从请求中获取API密钥
     * @return string API密钥
     */
    private function getApiKeyFromRequest() {
        $headers = getallheaders();
        return isset($headers['Authorization']) ? str_replace('Bearer ', '', $headers['Authorization']) : '';
    }
    
    /**
     * 发送JSON响应
     * @param mixed $data 响应数据
     * @param int $statusCode HTTP状态码
     */
    private function sendResponse($data, $statusCode = 200) {
        http_response_code($statusCode);
        echo json_encode($data, JSON_UNESCAPED_UNICODE);
        exit;
    }
}

// 创建实例并处理请求
$server = new HuuNoteServer();
$server->handleRequest();