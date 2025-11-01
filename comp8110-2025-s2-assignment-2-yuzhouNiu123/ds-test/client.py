#!/usr/bin/env python3
import socket

# 建立 socket 连接
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("localhost", 55067))  # 如果端口不同，请与 ds-server 的 -p 参数一致

def send(msg):
    sock.sendall((msg + '\n').encode())

def receive():
    return sock.recv(4096).decode().strip()

# 握手阶段
send("HELO")
receive()

send("AUTH yuzhouNiu")
receive()

# 请求所有服务器信息
send("GETS All")
response = receive()
parts = response.split()
nRecs = int(parts[1])   # 正确：第二个元素是服务器数量

# 接收服务器记录
send("OK")
records = []
for i in range(nRecs):
    record = receive().split()
    records.append(record)

receive()  # 接收最后一个 "."

# 选择拥有最多 core 的服务器
largest = max(records, key=lambda x: int(x[4]))  # 第 5 个字段是 core 数
server_type = largest[0]
server_id = largest[1]

# 任务调度循环
while True:
    send("REDY")
    response = receive()

    if response.startswith("JOBN"):
        parts = response.split()
        job_id = parts[2]
        send(f"SCHD {job_id} {server_type} {server_id}")
        receive()

    elif response == "NONE":
        break
    elif response.startswith("JCPL"):
        continue

# 结束通信
send("QUIT")
receive()
sock.close()

