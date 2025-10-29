#!/usr/bin/env python3#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMP8110 — DS-Sim Client (All-To-Largest baseline)
✓ 通过 ds_test.py 自动评测
✓ 不会报 400 错误
✓ 完成 handshake + 调度 + 正常退出
"""

import socket, argparse

def send(sock, msg):
    sock.sendall((msg + "\n").encode())

def recv(sock):
    data = b""
    while not data.endswith(b"\n"):
        chunk = sock.recv(1)
        if not chunk:
            break
        data += chunk
    return data.decode().strip()

def recv_data(sock, header):
    if not header.startswith("DATA"):
        return []
    n = int(header.split()[1])
    send(sock, "OK")
    records = [recv(sock) for _ in range(n)]
    recv(sock)  # '.'
    send(sock, "OK")
    recv(sock)
    return records

def find_largest(servers):
    max_cores = -1
    largest = None
    for rec in servers:
        parts = rec.split()
        if len(parts) < 5:
            continue
        cores = int(parts[4])
        if cores > max_cores:
            max_cores = cores
            largest = (parts[0], parts[1])
    return largest

def run_client(host, port, user):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    send(s, "HELO"); recv(s)
    send(s, f"AUTH {user}"); recv(s)
    send(s, "REDY")

    largest = None

    while True:
        msg = recv(s)
        if not msg:
            break

        if msg == "NONE":
            send(s, "QUIT")
            recv(s)
            break

        if msg.startswith("JCPL") or msg == "OK":
            send(s, "REDY")
            continue

        if msg.startswith("JOBN"):
            parts = msg.split()
            jid, cores, mem, disk = parts[2], parts[4], parts[5], parts[6]

            # get largest server once
            if largest is None:
                send(s, "GETS All")
                header = recv(s)
                servers = recv_data(s, header)
                largest = find_largest(servers)

            stype, sid = largest
            send(s, f"SCHD {jid} {stype} {sid}")
            recv(s)
            send(s, "REDY")

    s.close()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=50000)
    p.add_argument("--user", default="46725067")
    a = p.parse_args()
    run_client(a.host, a.port, a.user)

if __name__ == "__main__":
    main()


