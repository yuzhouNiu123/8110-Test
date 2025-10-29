#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMP8110 — Minimal Confirmed Handshake Client
完全验证通信; 只接收一次 JOBN 就退出
"""

import socket, argparse

def send_line(sock, text):
    sock.sendall((text + "\n").encode())

def recv_line(sock):
    data = b""
    while not data.endswith(b"\n"):
        chunk = sock.recv(1)
        if not chunk:
            break
        data += chunk
    return data.decode().strip()

def run_client(host, port, user):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print(f"Connected to {host}:{port}")

    send_line(s, "HELO"); print("→", recv_line(s))
    send_line(s, f"AUTH {user}"); print("→", recv_line(s))
    send_line(s, "REDY")

    while True:
        msg = recv_line(s)
        print("←", msg)
        if msg.startswith("JOBN"):
            jid = msg.split()[2]
            send_line(s, f"SCHD {jid} small 0")
            print("→", recv_line(s))   # expect OK
            send_line(s, "QUIT")
            print("→", recv_line(s))
            break
        if msg == "NONE":
            send_line(s, "QUIT")
            print("→", recv_line(s))
            break

    s.close()
    print("Done.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=50000)
    p.add_argument("--user", default="46725067")
    a = p.parse_args()
    run_client(a.host, a.port, a.user)

if __name__ == "__main__":
