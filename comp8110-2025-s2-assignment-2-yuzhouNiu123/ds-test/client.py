#!/usr/bin/env python3#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMP8110 — Minimal Handshake Client
只测试通信流程：HELO → AUTH → REDY → NONE → QUIT
不会调度任务，用于验证 ds-server 通信是否正常。
"""

import socket, argparse

def send_line(sock, s: str):
    if not s.endswith("\n"):
        s += "\n"
    sock.sendall(s.encode())

def recv_line(sock) -> str:
    buf = []
    while True:
        ch = sock.recv(1)
        if not ch:
            break
        buf.append(ch.decode(errors="ignore"))
        if ch == b"\n":
            break
    return "".join(buf).strip()

def run_client(host, port, student_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print(f"✅ Connected to ds-server at {host}:{port}")

    send_line(s, "HELO")
    print("→", recv_line(s))

    send_line(s, f"AUTH {student_id}")
    print("→", recv_line(s))

    send_line(s, "REDY")
    while True:
        msg = recv_line(s)
        print("←", msg)
        if msg == "NONE":
            send_line(s, "QUIT")
            print("→", recv_line(s))
            break
        else:
            send_line(s, "REDY")

    s.close()
    print("✅ Communication complete. Connection closed.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50000)
    parser.add_argument("--user", default="46725067")
    args = parser.parse_args()
    run_client(args.host, args.port, args.user)

if __name__ == "__main__":
    main()


