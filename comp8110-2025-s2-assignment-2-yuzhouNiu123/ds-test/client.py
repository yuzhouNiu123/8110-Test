#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Macquarie DS-Sim Python Client (First-Fit)
Compatible with MQ teaching version ds-server (no HELO step).
"""

import socket
import argparse
import os

# ------------------------- Utility functions -------------------------
def send_line(sock, s: str):
    """Send one line with newline termination."""
    if not s.endswith("\n"):
        s = s + "\n"
    print(f"--> Sending: {repr(s)}")
    sock.sendall(s.encode())

def recv_line(sock) -> str:
    """Receive a single line (newline terminated)."""
    buf = []
    while True:
        ch = sock.recv(1)
        if not ch:
            break
        buf.append(ch.decode(errors="ignore"))
        if buf[-1] == "\n":
            break
    line = "".join(buf).strip()
    if line:
        print(f"<-- Received: {repr(line)}")
    return line

def recv_data_block(sock, header: str):
    """Handle DATA ... blocks returned by GETS Capable."""
    if not header.startswith("DATA"):
        return []
    n = int(header.split()[1])
    print(f"Expecting {n} server records...")
    send_line(sock, "OK")
    records = [recv_line(sock) for _ in range(n)]
    send_line(sock, "OK")
    recv_line(sock)  # terminating '.'
    return records

def choose_server(records):
    """Simple First-Fit: pick the first capable server."""
    if not records:
        return None, None
    parts = records[0].split()
    if len(parts) < 2:
        return None, None
    return parts[0], parts[1]

# ------------------------- Core client logic -------------------------
def run_client(host, port, user_id):
    print(f"Connecting to {host}:{port} ...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print("✅ Connected to ds-server")

    # === MQ Teaching Server Handshake (AUTH only) ===
    send_line(s, f"AUTH {user_id}")
    reply = recv_line(s)
    print(f"AUTH response: {reply}")

    send_line(s, "REDY")
    print("Sent REDY, waiting for first JOB...")

    while True:
        msg = recv_line(s)
        if not msg:
            print("⚠️  Server closed connection.")
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

    print("✅ Client finished all jobs. Closing socket.")
    s.close()

# ------------------------- Entrypoint -------------------------
def main():
    parser = argparse.ArgumentParser(description="MQ DS-Sim Python client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50000)
    parser.add_argument("--user", default="46725067")
    args = parser.parse_args()
    run_client(args.host, args.port, args.user)

if __name__ == "__main__":
    main()





