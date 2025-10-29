#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMP8110 — Minimal Stable Client
通信+调度，完全符合 ds-sim 协议顺序
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

    # --- handshake ---
    send_line(s, "HELO"); recv_line(s)
    send_line(s, f"AUTH {student_id}"); recv_line(s)
    send_line(s, "REDY")

    while True:
        msg = recv_line(s)
        if not msg:
            break
        print("←", msg)

        # no more jobs
        if msg == "NONE":
            send_line(s, "QUIT")
            print("→", recv_line(s))
            break

        # server OK or JCPL
        if msg.startswith("OK") or msg.startswith("JCPL"):
            send_line(s, "REDY")
            continue

        # new job
        if msg.startswith("JOBN"):
            parts = msg.split()
            jid = parts[2]
            # send schedule command
            send_line(s, f"SCHD {jid} small 0")
            ack = recv_line(s)  # 读取OK回复
            print("→", ack)
            # send REDY for next job
            send_line(s, "REDY")
            continue

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


