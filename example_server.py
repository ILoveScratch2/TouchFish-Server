"""
TouchFish_Server 示例

By ILoveScratch2
License: BSD-3-Clause
"""

from touchfish_server import TouchFishServer, ServerConfig
import datetime


def get_timestamp():
    """
    获取当前时间戳字符串
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main(): # 主函数
    """
    创建服务器实例
    """

    print("=== TouchFish_Server 示例 ===")
    print("By ILoveScratch2")
    host = input("监听地址> [0.0.0.0]: ").strip() or "0.0.0.0"
    port = int(input("端口> [8080]: ").strip() or "8080")
    max_connections = int(input("最大连接数> [100]: ").strip() or "100")

    config = ServerConfig(
        host=host,
        port=port,
        max_connections=max_connections
    )
    
    server = TouchFishServer(config) # 创建服务器实例
     
    def on_client_connect(ip, port):
        """
        客户端连接
        """
        print(f"[{get_timestamp()}] 客户端连接: {ip}:{port}")
        server.send_to_ip(ip, f"[系统提示] 欢迎加入TOUCHFISH_SERVER 样例 聊天室！当前在线 {len(server.connections)} 人\n")
    
    def on_client_disconnect(ip):
        """
        客户端断连
        """
        print(f"[{get_timestamp()}] 客户端断开: {ip}")
    
    def on_message_received(ip, username, message):
        """
        收到消息
        """
        print(f"[{get_timestamp()}] {username}({ip}): {message.strip()}")
        
        server.broadcast(message)
    
    # 使用回调处理事件
    server.on_connect = on_client_connect
    server.on_disconnect = on_client_disconnect
    server.on_message = on_message_received
    
    server.start() # 启动服务器
    print(f"TOUCHFISH_SERVER 样例 服务器启动成功！监听 {config.host}:{config.port}")
    print("命令: list(列出客户端) | broadcast <msg>(广播) | kick <ip>(踢出) | quit(退出)")
    
    try:
        while True:
            cmd = input("> ").strip()
            
            if not cmd:
                continue
            
            if cmd == "quit":
                print("正在关闭服务器...")
                server.broadcast("[系统提示] 服务器即将关闭") # 广播关闭消息
                server.stop() # 关闭服务器
                break
            
            elif cmd == "list":
                clients = server.get_client_list() # 获取客户端列表
                if not clients:
                    print("当前无客户端连接")
                else:
                    print(f"{'IP':<15} {'端口':<6} {'用户名':<15} {'在线'}")
                    print("-" * 50)
                    for c in clients:
                        status = "是" if c['online'] else "否"
                        print(f"{c['ip']:<15} {c['port']:<6} {c['username']:<15} {status}")
            
            elif cmd.startswith("broadcast "):
                msg = cmd[10:]
                server.broadcast(f"[系统广播] {msg}") # 广播消息
                print(f"已广播: {msg}")
            
            elif cmd.startswith("kick "):
                ip = cmd[5:].strip()
                server.kick_client(ip, "你已被踢出聊天室") # 踢出客户端
                print(f"已踢出: {ip}")
            
            else:
                print("未知命令")
    
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        server.stop() # 关闭服务器


if __name__ == "__main__":
    main()
