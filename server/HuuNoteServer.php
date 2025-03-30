<?php
/**
 * HuuNoteServer.php
 * 
 * Huu Note 笔记同步服务端
 * 提供笔记的上传、下载、删除、搜索、同步等功能
 */

// 设置时区
date_default_timezone_set('Asia/Shanghai');

// 允许跨域请求
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS');
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
        $requestUri = isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : '';
        
        // 提取API路径
        $path = parse_url($requestUri, PHP_URL_PATH);
        $pathParts = explode('/', trim($path, '/'));
        
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
     * 删除笔记
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
            $this->sendResponse(['error' => '笔记不存在'], 404);
            return;
        }
        
        // 删除文件
        if (unlink($fullPath)) {
            $this->sendResponse(['success' => true, 'path' => $notePath]);
        } else {
            $this->sendResponse(['error' => '删除笔记失败'], 500);
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