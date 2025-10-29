#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMP8110 — Minimal Working Client (通信+简单调度)
握手 + 把所有任务调度到 small 0
"""

import socket, argparse

def send_line(sock, s: str):
    if not s.endswith("\n"):
        s += "\n"
    sock.sendall(s.encode())

def recv_line(sock):
    data = []
    while True:
        ch = sock.recv(1)
        if not ch:
            break
        data.append(ch.decode(errors="ignore"))
        if ch == b"\n":
            break
    return "".join(data).strip()

def run_client(host, port, student_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print(f"✅ Connected to ds-server at {host}:{port}")

    send_line(s, "HELO"); print("→", recv_line(s))
    send_line(s, f"AUTH {student_id}"); print("→", recv_line(s))
    send_line(s, "REDY")

    while True:
        msg = recv_line(s)
        print("←", msg)
        if msg == "NONE":
            send_line(s, "QUIT")
            print("→", recv_line(s))
            break
        if msg.startswith("JOBN"):
            parts = msg.split()
            jid = parts[2]
            send_line(s, f"SCHD {jid} small 0")  # 调度到 small 0
            recv_line(s)
        send_line(s, "REDY")

    s.close()
    print("✅ All jobs scheduled. Connection closed.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50000)
    parser.add_argument("--user", default="46725067")
    args = parser.parse_args()
    run_client(args.host, args.port, args.user)

if __name__ == "__main__":
    main()
