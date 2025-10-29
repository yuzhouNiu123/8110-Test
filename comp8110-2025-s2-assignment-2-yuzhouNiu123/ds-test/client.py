#!/usr/bin/env python3#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DS-Sim Python Client (debug version with CRLF line endings)
"""

import socket
import argparse
import os
import time

def send_line(sock, s: str):
    if not s.endswith("\n"):
        s = s + "\n"
    print(f"--> Sending: {repr(s)}")
    sock.sendall(s.encode())

def recv_line(sock) -> str:
    buf = []
    while True:
        ch = sock.recv(1)
        if not ch:
            break
        buf.append(ch.decode(errors="ignore"))
        if len(buf) >= 2 and buf[-2:] == ['\r', '\n']:
            break
    line = "".join(buf).strip()
    print(f"<-- Received: {repr(line)}")
    return line

def recv_data_block(sock, header: str):
    if not header.startswith("DATA"):
        return []
    n = int(header.split()[1])
    print(f"Expecting {n} data records...")
    send_line(sock, "OK")
    records = [recv_line(sock) for _ in range(n)]
    send_line(sock, "OK")
    recv_line(sock)  # read terminating '.'
    return records

def choose_server(records):
    if not records:
        return None, None
    parts = records[0].split()
    if len(parts) < 2:
        return None, None
    return parts[0], parts[1]

def run_client(host, port, user_id):
    print(f"Connecting to {host}:{port} ...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print("✅ Connected to server")

    # handshake
    send_line(s, "HELO")
    recv_line(s)
    send_line(s, f"AUTH {user_id}")
    recv_line(s)
    send_line(s, "REDY")

    while True:
        msg = recv_line(s)
        if not msg:
            print("Connection closed by server.")
            break

        if msg.startswith("JCPL") or msg == "OK":
            send_line(s, "REDY")
            continue

        if msg == "NONE":
            send_line(s, "QUIT")
            recv_line(s)
            break

        if msg.startswith("JOBN") or msg.startswith("JOBP"):
            parts = msg.split()
            jid   = int(parts[-5+1])
            cores = int(parts[-3])
            mem   = int(parts[-2])
            disk  = int(parts[-1])

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

    print("✅ Client finished, closing socket.")
    s.close()

def main():
    parser = argparse.ArgumentParser(description="DS-Sim debug client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50000)
    parser.add_argument("--user", default="46725067")
    args = parser.parse_args()
    run_client(args.host, args.port, args.user)

if __name__ == "__main__":
    main()



