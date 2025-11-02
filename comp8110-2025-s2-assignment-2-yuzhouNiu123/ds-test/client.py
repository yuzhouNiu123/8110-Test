import socket

# ===== 基本设置 =====
BUF_SIZE = 8192
PORT = 55067
USER = "yuzhouNiu"
VERBOSE = True

# ======== 通信工具函数 ========
def send_line(sock, msg: str):
    """发送带换行的消息"""
    if VERBOSE:
        print("Sent:", msg)
    sock.sendall(bytes(f"{msg}\n", encoding="utf-8"))

def recv_line(sock) -> str:
    """接收单行消息"""
    data = b""
    sock.settimeout(5.0)
    while True:
        try:
            ch = sock.recv(1)
            if not ch:
                break
            data += ch
            if ch == b"\n":
                break
        except socket.timeout:
            break
    line = data.decode(errors="ignore").strip()
    if VERBOSE and line:
        print("Received:", line)
    return line

def recv_data_block(sock, n_lines: int):
    """接收 DATA 块（n_lines 行 + '.' 结束）"""
    lines = []
    buffer = b""
    sock.settimeout(5.0)
    while len(lines) < n_lines:
        chunk = sock.recv(BUF_SIZE)
        if not chunk:
            break
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            line = line.decode(errors="ignore").strip()
            if line == ".":
                return lines
            lines.append(line)
            if len(lines) >= n_lines:
                break
    return lines

# ======== 建立连接 ========
sock = socket.socket()
sock.settimeout(5)
sock.connect(("localhost", PORT))

send_line(sock, "HELO")
recv_line(sock)
send_line(sock, f"AUTH {USER}")
recv_line(sock)

# ======== 获取服务器信息 ========
send_line(sock, "GETS All")
resp = recv_line(sock)

if not resp.startswith("DATA"):
    print("Unexpected:", resp)
    sock.close()
    exit()

try:
    nRecs = int(resp.split()[1])
except Exception:
    print("Parse error:", resp)
    sock.close()
    exit()

send_line(sock, "OK")
server_lines = recv_data_block(sock, nRecs)
send_line(sock, "OK")
recv_line(sock)

# 解析服务器
servers = []
for line in server_lines:
    parts = line.strip().split()
    if len(parts) >= 8:
        servers.append(parts)

if not servers:
    print("No servers found, exiting.")
    sock.close()
    exit()

# ======== 服务器排序（核心数） ========
servers.sort(key=lambda s: int(s[4]))
stype_small, sid_small = servers[0][0], servers[0][1]
stype_large, sid_large = servers[-1][0], servers[-1][1]

# ======== 调度循环 ========
while True:
    send_line(sock, "REDY")
    msg = recv_line(sock)

    if msg == "NONE":
        break

    if msg.startswith("JOBN"):
        parts = msg.split()
        job_id = parts[1]
        cores = int(parts[4])
        mem = int(parts[5])
        disk = int(parts[6])

        #  混合优化策略（Hybrid Small+Large Fit）
        # 小任务 → 最小服务器；中大任务 → 搜索最适合的
        if cores <= 4:
            target = servers[0]
        else:
            # 从小到大找能容纳任务的第一个服务器
            target = next((s for s in servers if int(s[4]) >= cores and int(s[5]) >= mem and int(s[6]) >= disk), servers[-1])

        send_line(sock, f"SCHD {job_id} {target[0]} {target[1]}")
        reply = recv_line(sock)
        if reply.startswith("ERR"):
            print(f"⚠️ Job {job_id} 调度失败，继续下一条。")
        continue

    if msg.startswith(("JCPL", "RESF", "RESR", "OK")):
        continue

    if msg.startswith("ERR"):
        print("Warning:", msg)
        break

# ======== 退出 ========
send_line(sock, "QUIT")
recv_line(sock)
sock.close()
print("✅ Client finished successfully.")


