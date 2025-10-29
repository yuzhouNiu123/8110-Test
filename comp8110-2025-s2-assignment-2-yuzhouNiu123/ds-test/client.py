#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMP8110 ds-sim Minimal Client — First-Fit baseline (final stable version)
✓ 修复 Out-of-bound 错误
✓ 自动忽略无效记录
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
        if buf and buf[-1] == "\n":
            break
    return "".join(buf).strip()

def recv_data_block(sock, header: str):
    if not header.startswith("DATA"):
        return []
    n = int(header.split()[1])
    send_line(sock, "OK")
    records = [recv_line(sock) for _ in range(n)]
    recv_line(sock)      # '.'
    send_line(sock, "OK")
    recv_line(sock)      # 'OK'
    return [r for r in records if r.strip()]

def choose_server(records):
    """First valid capable server."""
    for rec in records:
        f = rec.split()
        if len(f) < 2:
            continue
        try:
            stype = f[0]
            sid = int(f[1])
            return stype, sid
        except ValueError:
            continue
    return None, None

def run_client(host, port, student_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect((host, port))

    send_line(s, "HELO")
    recv_line(s)
    send_line(s, f"AUTH {student_id}")
    recv_line(s)
    send_line(s, "REDY")

    while True:
        msg = recv_line(s)
        if not msg:
            break

        if msg == "NONE":
            print("✅ All jobs done. Quitting.")
            send_line(s, "QUIT")
            recv_line(s)
            break

        if msg.startswith("JCPL") or msg == "OK":
            send_line(s, "REDY")
            continue

        if msg.startswith("JOBN"):
            parts = msg.split()
            jid   = int(parts[2])
            cores = int(parts[4])
            mem   = int(parts[5])
            disk  = int(parts[6])

            send_line(s, f"GETS Capable {cores} {mem} {disk}")
            header = recv_line(s)
            records = recv_data_block(s, header)
            stype, sid = choose_server(records)
            if stype is None:
                send_line(s, "REDY")
                continue

            # --- 安全检查：避免非法 server id ---
            if sid < 0:
                send_line(s, "REDY")
                continue

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





