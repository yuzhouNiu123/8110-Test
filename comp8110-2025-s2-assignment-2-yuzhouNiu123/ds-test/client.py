#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMP8110 ds-sim Minimal Client — Fully Fixed First-Fit baseline
✓ 修复 Out-of-bound 问题（完整遵守 GETS 协议序列）
✓ 已验证可通过 ds_test.py (config12-short-med.xml)
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
    parts = header.split()
    n = int(parts[1])

    send_line(sock, "OK")            # 1. tell server we’re ready
    records = [recv_line(sock) for _ in range(n)]  # 2. read n lines
    recv_line(sock)                  # 3. read '.'
    send_line(sock, "OK")            # 4. acknowledge '.'
    recv_line(sock)                  # 5. expect final 'OK' from server
    return [r for r in records if r.strip()]

def choose_server(records):
    """Pick the first valid record."""
    for r in records:
        parts = r.split()
        if len(parts) < 2:
            continue
        try:
            stype = parts[0]
            sid = int(parts[1])
            return stype, sid
        except ValueError:
            continue
    return None, None

def run_client(host, port, student_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect((host, port))

    send_line(s, "HELO"); recv_line(s)
    send_line(s, f"AUTH {student_id}"); recv_line(s)
    send_line(s, "REDY")

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






