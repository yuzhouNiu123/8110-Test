#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMP8110 — DS-Sim Client (All-To-Largest, DS_SIM_PORT auto-detect)
✓ 自动读取 DS_SIM_PORT
✓ 能通过 ds_test.py 评测
"""

import socket, os, time

def send(sock, msg): sock.sendall((msg + "\n").encode())
def recv(sock):
    data = b""
    while not data.endswith(b"\n"):
        chunk = sock.recv(1)
        if not chunk: break
        data += chunk
    return data.decode().strip()

def recv_data(sock, header):
    if not header.startswith("DATA"): return []
    n = int(header.split()[1])
    send(sock, "OK")
    recs = [recv(sock) for _ in range(n)]
    recv(sock)  # '.'
    send(sock, "OK")
    recv(sock)
    return recs

def find_largest(servers):
    largest = None
    max_cores = -1
    for s in servers:
        p = s.split()
        if len(p) >= 5:
            try:
                cores = int(p[4])
                if cores > max_cores:
                    max_cores = cores
                    largest = (p[0], str(int(p[1])))
            except: pass
    return largest

def run_client():
    host = "127.0.0.1"
    port = int(os.getenv("DS_SIM_PORT", "50000"))  # 🔹 自动读取测试脚本传入端口
    user = os.getenv("MQ_STUDENT_ID", "46725067")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)

    # 等待 ds-server 启动
    for _ in range(15):
        try:
            s.connect((host, port))
            break
        except Exception:
            time.sleep(0.3)
    else:
        raise RuntimeError(f"❌ Failed to connect to {host}:{port}")

    send(s, "HELO"); recv(s)
    send(s, f"AUTH {user}"); recv(s)
    send(s, "REDY")

    largest = None
    while True:
        msg = recv(s)
        if not msg: break

        if msg == "NONE":
            send(s, "QUIT"); recv(s)
            break
        if msg.startswith("OK") or msg.startswith("JCPL"):
            send(s, "REDY"); continue
        if msg.startswith("JOBN"):
            p = msg.split()
            jid, cores, mem, disk = p[2], p[4], p[5], p[6]
            if largest is None:
                send(s, "GETS All")
                header = recv(s)
                servers = recv_data(s, header)
                largest = find_largest(servers)
                if largest is None:
                    send(s, "REDY"); continue
            stype, sid = largest
            send(s, f"SCHD {jid} {stype} {sid}")
            recv(s)
            send(s, "REDY")
        else:
            send(s, "REDY")

    s.close()

if __name__ == "__main__":
    run_client()
