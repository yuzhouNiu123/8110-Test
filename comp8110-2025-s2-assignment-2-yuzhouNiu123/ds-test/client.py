#!/usr/bin/env python3
# COMP8110 Assignment 2 - Basic client for ds-server
# Author: Yuzhou Niu
# Date: 2025-10-30

import socket
import sys
import getpass

HOST = "127.0.0.1"   # 服务器在本地
PORT = 54678         # 要和 ds-server 保持一致

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

# === Handshake sequence ===
s.sendall(b"HELO\n")
print("Sent: HELO")
data = s.recv(1024)
print("Received:", data.decode().strip())

s.sendall(b"AUTH 46725067\n")  # 用你的 student ID
print("Sent: AUTH 46725067")
data = s.recv(1024)
print("Received:", data.decode().strip())

s.sendall(b"REDY\n")
print("Sent: REDY")
data = s.recv(1024)
print("Received:", data.decode().strip())

s.close()

def main():
    try:
        # 建立 TCP 连接
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))

        def recv():
            return s.recv(1024).decode()

        def send(msg):
            s.sendall(msg.encode())

        # ---- 1️⃣ 握手阶段 ----
        data = recv()
        send("HELO\n")
        data = recv()
        username = getpass.getuser()
        send(f"AUTH {username}\n")
        data = recv()

        # ---- 2️⃣ 请求第一个任务 ----
        send("REDY\n")
        data = recv()

        # ---- 3️⃣ 主循环：处理任务直到收到 NONE ----
        while "NONE" not in data:
            if data.startswith("JOBN"):
                # 解析任务行，例如 "JOBN 0 23 100 1 500 1000"
                parts = data.strip().split()
                job_id = parts[2]

                # 请求服务器列表
                send("GETS All\n")
                data = recv()
                send("OK\n")

                # 读取服务器信息
                servers = []
                while True:
                    line = recv()
                    if line.strip() == "OK":
                        break
                    servers.append(line.strip())

                # 简单策略：选第一个服务器的第一个核心
                if servers:
                    first_server = servers[0].split()[0]
                    send(f"SCHD {job_id} {first_server} 0\n")
                    data = recv()
                else:
                    send("REDY\n")
                    data = recv()
                    continue

            # 请求下一个任务
            send("REDY\n")
            data = recv()

        # ---- 4️⃣ 任务结束 ----
        send("QUIT\n")
        s.close()
        print("✅ Client finished successfully.")

    except Exception as e:
        print("Error:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

