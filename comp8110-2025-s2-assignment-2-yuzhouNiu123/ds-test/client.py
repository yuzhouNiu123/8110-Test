#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMP8110 — DS-Sim Client (First-Fit baseline)
Handshake + Job scheduling via GETS Capable + SCHD
"""

import socket, argparse

# -------------------------
# Utility functions
# -------------------------
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

def recv_data_block(sock, header):
    """Handle 'DATA n' response from server."""
    if not header.startswith("DATA"):
        return []
    n = int(header.split()[1])
    send_line(sock, "OK")               # tell server ready
    records = [recv_line(sock) for _ in range(n)]  # read n lines
    recv_line(sock)                     # read '.'
    send_line(sock, "OK")               # confirm
    recv_line(sock)                     # expect 'OK'
    return [r.strip() for r in records if r.strip()]

# -------------------------
# Scheduling (First-Fit)
# -------------------------
def choose_server(records):
    """Pick the first capable server."""
    for rec in records:
        parts = rec.split()
        if len(parts) >= 2:
            return parts[0], parts[1]  # type, id
    return None, None

# -------------------------
# Main client logic
# -------------------------
def run_client(host, port, user):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print(f"✅ Connected to ds-server at {host}:{port}")

    # --- Handshake ---
    send_line(s, "HELO"); recv_line(s)
    send_line(s, f"AUTH {user}"); recv_line(s)
    send_line(s, "REDY")

    while True:
        msg = recv_line(s)
        if not msg:
            break

        # No more jobs
        if msg == "NONE":
            send_line(s, "QUIT")
            recv_line(s)
            break

        # Job completed / server OK
        if msg.startswith("OK") or msg.startswith("JCPL"):
            send_line(s, "REDY")
            continue

        # New job
        if msg.startswith("JOBN"):
            parts = msg.split()
            jid = parts[2]
            cores = parts[4]
            mem = parts[5]
            disk = parts[6]

            # Ask for capable servers
            send_line(s, f"GETS Capable {cores} {mem} {disk}")
            header = recv_line(s)
            records = recv_data_block(s, header)

            # Pick first capable server
            stype, sid = choose_server(records)
            if stype is None:
                send_line(s, "REDY")
                continue

            # Schedule
            send_line(s, f"SCHD {jid} {stype} {sid}")
            recv_line(s)  # expect OK
            send_line(s, "REDY")
            continue

        # fallback
        send_line(s, "REDY")

    s.close()
    print("✅ All jobs scheduled. Connection closed.")

# -------------------------
# Entrypoint
# -------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=50000)
    p.add_argument("--user", default="46725067")
    a = p.parse_args()
    run_client(a.host, a.port, a.user)

if __name__ == "__main__":
    main()



