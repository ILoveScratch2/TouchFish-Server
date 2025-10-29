# TouchFish Server 模块文档

这是一个非官方的 TouchFish Python库服务端实现。

TouchFish: https://github.com/2044-space-elevator/TouchFish

该模块兼容现有的 TouchFish LTS 协议。

## 快速开始

可参考 `example_server.py` 文件中的示例代码。

### 基本示例

```python
from touchfish_server import TouchFishServer, ServerConfig

# 创建服务器配置
config = ServerConfig(
    host="0.0.0.0",
    port=8080,
    max_connections=100
)

# 创建服务器实例
server = TouchFishServer(config)

# 设置回调函数
def on_message(ip, username, message):
    print(f"{username}: {message}")
    server.broadcast(message)

server.on_message = on_message

# 启动服务器
server.start()

# 广播消息
server.broadcast("[系统提示] 服务器已启动")

# 停止服务器
# server.stop()
```

## API 参考

### ServerConfig

服务器配置类，用于设置服务器参数。

```python
ServerConfig(host="0.0.0.0", port=8080, max_connections=100, keepalive_idle=10800, keepalive_interval=30)
```

**参数：**

- `host` (str): 监听地址，默认 "0.0.0.0"（所有网卡）
- `port` (int): 监听端口，默认 8080
- `max_connections` (int): 最大连接数，默认 100
- `keepalive_idle` (int): TCP keepalive 空闲时间（秒），默认 10800
- `keepalive_interval` (int): TCP keepalive 探测间隔（秒），默认 30

**示例：**

```python
config = ServerConfig(
    host="127.0.0.1",
    port=9000,
    max_connections=50
)
```

### TouchFishServer

服务器核心类，处理所有 Socket 操作和连接管理。

```python
TouchFishServer(config)
```

**参数：**

- `config` (ServerConfig): 服务器配置对象

#### 属性

- **`connections`** (List[socket.socket]): 当前所有客户端连接的 socket 对象列表
- **`addresses`** (List[Tuple[str, int]]): 所有客户端的地址 (IP, 端口) 元组列表
- **`usernames`** (Dict[str, str]): IP 到用户名的映射字典
- **`online_status`** (Dict[str, bool]): IP 到在线状态的映射字典

#### 回调函数

- **`on_message`** (Optional[Callable[[str, str, str], None]]): 收到消息时的回调函数
  - 参数：
    - `ip` (str): 发送者 IP 地址
    - `username` (str): 发送者用户名
    - `message` (str): 消息内容

- **`on_connect`** (Optional[Callable[[str, int], None]]): 客户端连接时的回调函数
  - 参数：
    - `ip` (str): 客户端 IP 地址
    - `port` (int): 客户端端口

- **`on_disconnect`** (Optional[Callable[[str], None]]): 客户端断开时的回调函数
  - 参数：
    - `ip` (str): 客户端 IP 地址

- **`on_raw_data`** (Optional[Callable[[str, bytes], None]]): 收到原始数据时的回调函数（用于调试）
  - 参数：
    - `ip` (str): 发送者 IP 地址
    - `data` (bytes): 原始字节数据

#### 方法

##### `start()`

启动服务器，开始监听连接并接收消息。

该方法会创建并启动两个后台线程：
- 接受连接线程
- 接收消息线程

**示例：**

```python
server = TouchFishServer(config)
server.start()
```

##### `stop()`

停止服务器，关闭所有连接并清理资源。

**示例：**

```python
server.stop()
```

##### `broadcast(message, exclude_ip=None)`

向所有客户端广播消息。

**参数：**

- `message` (str): 要广播的消息（会自动添加 `\n` 结尾）
- `exclude_ip` (Optional[str]): 要排除的 IP 地址（可选）

**示例：**

```python
server.broadcast("欢迎新用户！")
server.broadcast("系统消息", exclude_ip="192.168.1.100")
```

##### `send_to_ip(ip, message)`

向指定 IP 发送消息。

**参数：**

- `ip` (str): 目标客户端 IP 地址
- `message` (str): 要发送的消息（会自动添加 `\n` 结尾）

**返回：**

- `bool`: 是否发送成功

**示例：**

```python
if server.send_to_ip("192.168.1.100", "私密消息"):
    print("发送成功")
```

##### `kick_client(ip, reason="")`

踢出指定客户端。

**参数：**

- `ip` (str): 要踢出的客户端 IP 地址
- `reason` (str): 踢出原因（可选，会发送给客户端）

**示例：**

```python
server.kick_client("192.168.1.100", "违反规则")
```

##### `get_client_list()`

获取所有客户端信息列表。

**返回：**

- `List[Dict[str, any]]`: 客户端信息字典列表，每个字典包含：
  - `ip` (str): IP 地址
  - `port` (int): 端口
  - `username` (str): 用户名
  - `online` (bool): 在线状态

**示例：**

```python
clients = server.get_client_list()
for client in clients:
    print(f"{client['username']} ({client['ip']}): {'在线' if client['online'] else '离线'}")
```

## 完整示例

### 带管理功能的服务器

```python
from touchfish_server import TouchFishServer, ServerConfig
import datetime

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 配置服务器
config = ServerConfig(host="0.0.0.0", port=8080)
server = TouchFishServer(config)

# 设置回调
def on_connect(ip, port):
    print(f"[{get_timestamp()}] 客户端连接: {ip}:{port}")
    server.send_to_ip(ip, f"[系统] 欢迎！在线: {len(server.connections)} 人")

def on_disconnect(ip):
    print(f"[{get_timestamp()}] 客户端断开: {ip}")

def on_message(ip, username, message):
    print(f"[{get_timestamp()}] {username}({ip}): {message.strip()}")
    server.broadcast(message)

server.on_connect = on_connect
server.on_disconnect = on_disconnect
server.on_message = on_message

# 启动服务器
server.start()
print(f"服务器启动: {config.host}:{config.port}")

# 管理命令循环
try:
    while True:
        cmd = input("> ").strip()
        
        if cmd == "list":
            for c in server.get_client_list():
                print(f"{c['ip']} - {c['username']} ({'在线' if c['online'] else '离线'})")
        
        elif cmd.startswith("kick "):
            ip = cmd[5:]
            server.kick_client(ip, "被管理员踢出")
        
        elif cmd.startswith("say "):
            server.broadcast(f"[管理员] {cmd[4:]}")
        
        elif cmd == "quit":
            server.broadcast("[系统] 服务器关闭")
            server.stop()
            break

except KeyboardInterrupt:
    server.stop()
```

## 协议说明

### 消息格式

**文本消息：**

```
用户名: 消息内容\n
```

**加入消息：**

```
用户 用户名 加入聊天室。\n
```

**文件传输消息（JSON 格式）：**

```json
{"type": "[FILE_START]", "name": "文件名", "size": 1234}\n
{"type": "[FILE_DATA]", "data": "base64编码数据"}\n
{"type": "[FILE_END]"}\n
```


## 故障排除

### 端口占用

如果启动时报错 "端口已被占用"：

```powershell
# Windows
netstat -ano | findstr :8080

# Linux/macOS  
lsof -i :8080
```

### 连接断开

检查防火墙设置和 keepalive 参数：

```python
config = ServerConfig(
    keepalive_idle=60,      # 减少空闲时间
    keepalive_interval=10   # 增加探测频率
)
```
