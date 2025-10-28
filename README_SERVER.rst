TouchFish Server 模块文档
========================

.. module:: touchfish_server
   :synopsis: TouchFish 服务端 Socket 封装模块

概述
----

``touchfish_server`` 是 TouchFish 项目的服务端核心模块，提供了完整的聊天服务器实现。
该模块兼容现有的 TouchFish LTS 协议（基于 ``\n`` 分隔的文本消息和 JSON 文件传输）。

主要特性
--------

* 完整的 TCP Socket 服务器封装
* 多客户端连接管理
* 消息广播和单播
* 自动用户名识别
* 在线状态跟踪
* 客户端踢出功能
* 基于回调的事件处理
* 跨平台 TCP keepalive 支持


快速开始
--------

基本示例
~~~~~~~~

.. code-block:: python

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


API 参考
--------

ServerConfig
~~~~~~~~~~~~

服务器配置类，用于设置服务器参数。

.. class:: ServerConfig(host="0.0.0.0", port=8080, max_connections=100, keepalive_idle=10800, keepalive_interval=30)

   :param str host: 监听地址，默认 "0.0.0.0"（所有网卡）
   :param int port: 监听端口，默认 8080
   :param int max_connections: 最大连接数，默认 100
   :param int keepalive_idle: TCP keepalive 空闲时间（秒），默认 10800
   :param int keepalive_interval: TCP keepalive 探测间隔（秒），默认 30

   **示例**::

       config = ServerConfig(
           host="127.0.0.1",
           port=9000,
           max_connections=50
       )


TouchFishServer
~~~~~~~~~~~~~~~

服务器核心类，处理所有 Socket 操作和连接管理。

.. class:: TouchFishServer(config)

   :param ServerConfig config: 服务器配置对象

   **属性**

   .. attribute:: connections

      当前所有客户端连接的 socket 对象列表
      
      :type: List[socket.socket]

   .. attribute:: addresses

      所有客户端的地址 (IP, 端口) 元组列表
      
      :type: List[Tuple[str, int]]

   .. attribute:: usernames

      IP 到用户名的映射字典
      
      :type: Dict[str, str]

   .. attribute:: online_status

      IP 到在线状态的映射字典
      
      :type: Dict[str, bool]

   **回调函数**

   .. attribute:: on_message

      收到消息时的回调函数
      
      :type: Optional[Callable[[str, str, str], None]]
      :param str ip: 发送者 IP 地址
      :param str username: 发送者用户名
      :param str message: 消息内容

   .. attribute:: on_connect

      客户端连接时的回调函数
      
      :type: Optional[Callable[[str, int], None]]
      :param str ip: 客户端 IP 地址
      :param int port: 客户端端口

   .. attribute:: on_disconnect

      客户端断开时的回调函数
      
      :type: Optional[Callable[[str], None]]
      :param str ip: 客户端 IP 地址

   .. attribute:: on_raw_data

      收到原始数据时的回调函数（用于调试）
      
      :type: Optional[Callable[[str, bytes], None]]
      :param str ip: 发送者 IP 地址
      :param bytes data: 原始字节数据

   **方法**

   .. method:: start()

      启动服务器，开始监听连接并接收消息。
      
      该方法会创建并启动两个后台线程：
      
      * 接受连接线程
      * 接收消息线程

      **示例**::

          server = TouchFishServer(config)
          server.start()

   .. method:: stop()

      停止服务器，关闭所有连接并清理资源。

      **示例**::

          server.stop()

   .. method:: broadcast(message, exclude_ip=None)

      向所有客户端广播消息。

      :param str message: 要广播的消息（会自动添加 ``\n`` 结尾）
      :param Optional[str] exclude_ip: 要排除的 IP 地址（可选）

      **示例**::

          server.broadcast("欢迎新用户！")
          server.broadcast("系统消息", exclude_ip="192.168.1.100")

   .. method:: send_to_ip(ip, message)

      向指定 IP 发送消息。

      :param str ip: 目标客户端 IP 地址
      :param str message: 要发送的消息（会自动添加 ``\n`` 结尾）
      :return: 是否发送成功
      :rtype: bool

      **示例**::

          if server.send_to_ip("192.168.1.100", "私密消息"):
              print("发送成功")

   .. method:: kick_client(ip, reason="")

      踢出指定客户端。

      :param str ip: 要踢出的客户端 IP 地址
      :param str reason: 踢出原因（可选，会发送给客户端）

      **示例**::

          server.kick_client("192.168.1.100", "违反规则")

   .. method:: get_client_list()

      获取所有客户端信息列表。

      :return: 客户端信息字典列表，每个字典包含：
      
               * ``ip`` (str): IP 地址
               * ``port`` (int): 端口
               * ``username`` (str): 用户名
               * ``online`` (bool): 在线状态
               
      :rtype: List[Dict[str, any]]

      **示例**::

          clients = server.get_client_list()
          for client in clients:
              print(f"{client['username']} ({client['ip']}): {'在线' if client['online'] else '离线'}")


完整示例
--------

带管理功能的服务器
~~~~~~~~~~~~~~~~~~

.. code-block:: python

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


协议说明
--------

消息格式
~~~~~~~~

**文本消息**::

    用户名: 消息内容\n

**加入消息**::

    用户 用户名 加入聊天室。\n

**文件传输消息**（JSON 格式）::

    {"type": "[FILE_START]", "name": "文件名", "size": 1234}\n
    {"type": "[FILE_DATA]", "data": "base64编码数据"}\n
    {"type": "[FILE_END]"}\n


注意事项
--------

* 所有消息必须以 ``\n`` 结尾
* 服务器会自动为每个客户端维护接收缓冲区，正确处理跨包消息
* 用户名从客户端发送的第一条消息中自动提取
* 建议在生产环境中添加错误处理和日志记录
* 默认的 keepalive 参数适合长连接场景，可根据需要调整


故障排除
--------

端口占用
~~~~~~~~

如果启动时报错 "端口已被占用"::

    # Windows
    netstat -ano | findstr :8080
    
    # Linux/macOS  
    lsof -i :8080

连接断开
~~~~~~~~

检查防火墙设置和 keepalive 参数::

    config = ServerConfig(
        keepalive_idle=60,      # 减少空闲时间
        keepalive_interval=10   # 增加探测频率
    )


版本信息
--------

:版本: 0.1.1
:作者: ILoveScratch2
:许可证: MPL-2.0
:兼容性: Python 3.6+, Windows/Linux/macOS


更新日志
--------

v0.1.1 (2025-10-28)
~~~~~~~~~~~~~~~~~~~

* 添加缓冲区管理，修复大消息分包问题
* 修复用户名提取逻辑
* 改进在线状态跟踪

v0.1.0 (2025-10-28)
~~~~~~~~~~~~~~~~~~~

* 初始版本
* 基础服务器功能
* 消息广播和单播
* 客户端管理
