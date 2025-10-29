#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMP8110 — DS-Sim Client (First-Fit, fully stable)
修复 Out-of-bound 错误，确保 sid 合法
"""

import socket, argparse

def send_line(sock, text):
    sock.sendall((text.strip() + "\n").encode())

def recv_line(sock):
    data = b""
    while not data.endswith(b"\n"):
        chunk = sock.recv(1)
        if not chunk:
            break
        data += chunk
    return data.decode().strip()

def recv_data_block(sock, header):
    if not header.startswith("DATA"):
        return []
    n = int(header.split()[1])
    send_line(sock, "OK")
    records = [recv_line(sock).strip() for _ in range(n)]
    recv_line(sock)   # '.'
    send_line(sock, "OK")
    recv_line(sock)   # 'OK'
    return [r for r in records if r]

def choose_server(records):
    """Pick the first valid capable server safely."""
    for rec in records:
        f = rec.strip().split()
        if len(f) >= 2:
            stype = f[0].strip()
            try:
                sid = str(int(f[1]))  # ensure clean integer id
                return stype, sid
            except ValueError:
                continue
    return None, None

def run_client(host, port, user):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print(f"✅ Connected to ds-server at {host}:{port}")

    send_line(s, "HELO"); recv_line(s)
    send_line(s, f"AUTH {user}"); recv_line(s)
    send_line(s, "REDY")

    while True:
        msg = recv_line(s)
        if not msg:
            break

        if msg == "NONE":
            send_line(s, "QUIT")
            recv_line(s)
            break

        if msg.startswith("OK") or msg.startswith("JCPL"):
            send_line(s, "REDY")
            continue

        if msg.startswith("JOBN"):
            parts = msg.split()
            jid, cores, mem, disk = parts[2], parts[4], parts[5], parts[6]

            send_line(s, f"GETS Capable {cores} {mem} {disk}")
            header = recv_line(s)
            records = recv_data_block(s, header)

            stype, sid = choose_server(records)
            if stype is None:
                send_line(s, "REDY")
                continue

            send_line(s, f"SCHD {jid} {stype} {sid}")
            recv_line(s)  # expect OK
            send_line(s, "REDY")
            continue

        send_line(s, "REDY")

    s.close()
    print("✅ All jobs scheduled. Connection closed.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=50000)
    p.add_argument("--user", default="46725067")
    a = p.parse_args()
    run_client(a.host, a.port, a.user)

if __name__ == "__main__":
    main()





