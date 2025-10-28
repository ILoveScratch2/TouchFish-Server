"""
TouchFish_Server

服务端模块，用于构建 TouchFish 服务器。
兼容现有 TouchFish LTS

作者：ILoveScratch2
版本：0.1.1
许可证：MPL-2.0
"""

__version__ = "0.1.1"
__author__ = "ILoveScratch2"
__all__ = ["TouchFishServer", "ServerConfig"]

import socket
import threading
import platform
import json
import time
from typing import Callable, Optional, Dict, List, Tuple


class ServerConfig:
    """
    服务器配置类
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        max_connections: int = 100,
        keepalive_idle: int = 180 * 60,
        keepalive_interval: int = 30
    ):
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.keepalive_idle = keepalive_idle
        self.keepalive_interval = keepalive_interval


class TouchFishServer:
    """
    TouchFish 服务器核心类
    """
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.server_socket: Optional[socket.socket] = None
        self.connections: List[socket.socket] = []
        self.addresses: List[Tuple[str, int]] = []
        self.usernames: Dict[str, str] = {}
        self.online_status: Dict[str, bool] = {}
        self.buffers: Dict[str, bytes] = {}
        self.running = False
        self.accept_thread: Optional[threading.Thread] = None
        self.receive_thread: Optional[threading.Thread] = None
        
        self.on_message: Optional[Callable[[str, str, str], None]] = None
        self.on_connect: Optional[Callable[[str, int], None]] = None
        self.on_disconnect: Optional[Callable[[str], None]] = None
        self.on_raw_data: Optional[Callable[[str, bytes], None]] = None

    def start(self):
        """
        启动服务器
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.config.host, self.config.port))
        self.server_socket.listen(self.config.max_connections)
        self.server_socket.setblocking(False)
        
        self.running = True
        
        self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.accept_thread.start()
        
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()

    def stop(self):
        """
        停止服务器
        """
        self.running = False
        
        for conn in self.connections:
            try:
                conn.close()
            except:
                pass
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.connections.clear()
        self.addresses.clear()
        self.usernames.clear()
        self.online_status.clear()
        self.buffers.clear()

    def broadcast(self, message: str, exclude_ip: Optional[str] = None):
        """
        向所有客户端广播消息   
        发送消息给所有已连接的客户端，可选择排除特定 IP。
        """
        if not message.endswith('\n'):
            message += '\n'
        
        message_bytes = message.encode('utf-8')
        
        new_connections = []
        new_addresses = []
        
        for i, conn in enumerate(self.connections):
            ip = self.addresses[i][0]
            
            if exclude_ip and ip == exclude_ip:
                new_connections.append(conn)
                new_addresses.append(self.addresses[i])
                continue
            
            try:
                conn.send(message_bytes)
                self.online_status[ip] = True
                new_connections.append(conn)
                new_addresses.append(self.addresses[i])
            except:
                self.online_status[ip] = False
                if self.on_disconnect:
                    self.on_disconnect(ip)

        self.connections = new_connections
        self.addresses = new_addresses

    def send_to_ip(self, ip: str, message: str) -> bool:
        """
        向指定 IP 发送消息
        发送消息给特定客户端。返回是否成功。
        """
        if not message.endswith('\n'):
            message += '\n'
        
        for i, addr in enumerate(self.addresses):
            if addr[0] == ip:
                try:
                    self.connections[i].send(message.encode('utf-8'))
                    self.online_status[ip] = True
                    return True
                except:
                    self.online_status[ip] = False
                    if self.on_disconnect:
                        self.on_disconnect(ip)
                    return False
        
        return False

    def kick_client(self, ip: str, reason: str = ""):
        """
        踢出客户端
        断开指定 IP 的连接，可选发送原因消息。
        """
        if reason:
            self.send_to_ip(ip, f"[系统提示] {reason}")
        
        new_connections = []
        new_addresses = []
        
        for i, addr in enumerate(self.addresses):
            if addr[0] == ip:
                try:
                    self.connections[i].close()
                except:
                    pass
                if self.on_disconnect:
                    self.on_disconnect(ip)
            else:
                new_connections.append(self.connections[i])
                new_addresses.append(addr)
        
        self.connections = new_connections
        self.addresses = new_addresses
        
        if ip in self.usernames:
            del self.usernames[ip]
        if ip in self.online_status:
            del self.online_status[ip]
        if ip in self.buffers:
            del self.buffers[ip]

    def get_client_list(self) -> List[Dict[str, any]]:
        """
        获取客户端列表
        返回所有已连接客户端的信息列表。
        """
        clients = []
        for addr in self.addresses:
            ip = addr[0]
            clients.append({
                'ip': ip,
                'port': addr[1],
                'username': self.usernames.get(ip, 'UNKNOWN'),
                'online': self.online_status.get(ip, False)
            })
        return clients

    def _accept_loop(self):
        """
        接受连接循环
        """
        while self.running:
            time.sleep(0.1)
            
            try:
                conn, addr = self.server_socket.accept()
            except:
                continue
            
            self._configure_socket(conn)
            conn.setblocking(False)
            
            self.connections.append(conn)
            self.addresses.append(addr)
            self.usernames[addr[0]] = "UNKNOWN"
            self.online_status[addr[0]] = True
            self.buffers[addr[0]] = b""
            
            if self.on_connect:
                self.on_connect(addr[0], addr[1])

    def _receive_loop(self):
        """
        接收消息循环
        """
        while self.running:
            time.sleep(0.1)
            
            for i, conn in enumerate(self.connections):
                try:
                    data = conn.recv(1024)
                    if not data:
                        continue
                    
                    ip = self.addresses[i][0]
                    self.online_status[ip] = True
                    
                    if self.on_raw_data:
                        self.on_raw_data(ip, data)
                    
                    if ip not in self.buffers:
                        self.buffers[ip] = b""
                    
                    self.buffers[ip] += data
                    
                    while b'\n' in self.buffers[ip]:
                        message_bytes, self.buffers[ip] = self.buffers[ip].split(b'\n', 1)
                        message = message_bytes.decode('utf-8')
                        
                        if '用户 ' in message and ' 加入聊天室' in message:
                            username = message.split('用户 ')[1].split(' 加入聊天室')[0]
                            self.usernames[ip] = username
                        elif ':' in message and not message.startswith('{'):
                            username = message.split(':', 1)[0].strip()
                            self.usernames[ip] = username
                        
                        if self.on_message:
                            self.on_message(ip, self.usernames.get(ip, 'UNKNOWN'), message)
                    
                except:
                    continue

    def _configure_socket(self, sock: socket.socket):
        """
        配置 socket 参数
        
        设置 TCP keepalive 和其他参数，跨平台兼容。
        """
        if platform.system() == "Windows":
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
            try:
                sock.ioctl(
                    socket.SIO_KEEPALIVE_VALS,
                    (1, self.config.keepalive_idle * 1000, self.config.keepalive_interval * 1000)
                )
            except:
                pass
        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, self.config.keepalive_idle)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, self.config.keepalive_interval)
