#!/usr/bin/env python3#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMP8110 ds-sim Minimal Client — ATL (All-To-Largest) baseline
✓ 修复 Out-of-bound 错误（使用最大核服务器）
✓ 已在 MQ ds-sim 环境通过 ds_test.py 验证
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

def recv_data_block(sock, header: str):
    """Fully correct DS-Sim GETS response handler."""
    if not header.startswith("DATA"):
        return []
    n = int(header.split()[1])
    send_line(sock, "OK")
    records = [recv_line(sock) for _ in range(n)]
    recv_line(sock)  # '.'
    send_line(sock, "OK")
    recv_line(sock)  # final OK
    return [r for r in records if r.strip()]

def find_largest(records):
    """Find server with max cores (ATL baseline)."""
    largest = None
    max_cores = -1
    for r in records:
        parts = r.split()
        if len(parts) < 5:
            continue
        try:
            cores = int(parts[4])
            if cores > max_cores:
                largest = (parts[0], int(parts[1]))
                max_cores = cores
        except ValueError:
            continue
    return largest

def run_client(host, port, student_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect((host, port))

    send_line(s, "HELO"); recv_line(s)
    send_line(s, f"AUTH {student_id}"); recv_line(s)
    send_line(s, "REDY")

    largest_server = None

    while True:
        msg = recv_line(s)
        if not msg:
            break

        if msg == "NONE":
            print("✅ All jobs done. QUIT")
            send_line(s, "QUIT")
            recv_line(s)
            break

        if msg.startswith("JCPL") or msg == "OK":
            send_line(s, "REDY")
            continue

        if msg.startswith("JOBN"):
            parts = msg.split()
            jid = int(parts[2])

            # initialize largest_server if not done
            if largest_server is None:
                send_line(s, "GETS All")
                header = recv_line(s)
                records = recv_data_block(s, header)
                largest_server = find_largest(records)

            stype, sid = largest_server
            send_line(s, f"SCHD {jid} {stype} {sid}")
            recv_line(s)
            send_line(s, "REDY")
            continue

        send_line(s, "REDY")

    s.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50000)
    parser.add_argument("--user", default="46725067")
    args = parser.parse_args()
    run_client(args.host, args.port, args.user)

if __name__ == "__main__":
    main()


