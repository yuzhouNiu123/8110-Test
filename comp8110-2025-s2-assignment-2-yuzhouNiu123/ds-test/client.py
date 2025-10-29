#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMP8110 ds-sim Minimal Client — First-Fit baseline (fixed version)
✓ 修复了 “400: Out of bound!” 错误（sid 强制转为 int）
✓ 完整握手流程验证通过 (HELO → AUTH → REDY → JOBN/SCHD → NONE → QUIT)
"""

import socket
import argparse

# -------------------------
# Utilities
# -------------------------
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
    """Receive records after GETS Capable."""
    if not header.startswith("DATA"):
        return []
    parts = header.split()
    n = int(parts[1])
    send_line(sock, "OK")
    records = [recv_line(sock) for _ in range(n)]
    recv_line(sock)      # should be '.'
    send_line(sock, "OK")  # confirm end of block
    recv_line(sock)      # expect 'OK'
    return records

# -------------------------
# Server selection  (safe First-Fit)
# -------------------------
def choose_server(records):
    """Pick the first capable server safely."""
    if not records:
        return None, None
    fields = records[0].split()
    if len(fields) < 2:
        return None, None
    stype = fields[0]
    sid = int(fields[1])       # ✅ 强制转换整数，避免 Out-of-bound
    return stype, sid

# -------------------------
# Main logic
# -------------------------
def run_client(host, port, student_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect((host, port))

    # --- Handshake ---
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
            print("✅ No more jobs. Quitting.")
            send_line(s, "QUIT")
            recv_line(s)
            break

        if msg.startswith("JCPL") or msg == "OK":
            send_line(s, "REDY")
            continue

        if msg.startswith("JOBN"):
            parts = msg.split()
            # JOBN submitTime jobID estRuntime cores memory disk
            jid   = int(parts[2])
            cores = int(parts[4])
            mem   = int(parts[5])
            disk  = int(parts[6])

            # --- Query Capable servers ---
            send_line(s, f"GETS Capable {cores} {mem} {disk}")
            header = recv_line(s)
            records = recv_data_block(s, header)

            stype, sid = choose_server(records)
            if stype is None:
                # fallback if no capable server returned
                send_line(s, "GETS All")
                header = recv_line(s)
                records = recv_data_block(s, header)
                stype, sid = choose_server(records)
                if stype is None:
                    send_line(s, "REDY")
                    continue

            # --- Schedule job ---
            send_line(s, f"SCHD {jid} {stype} {sid}")
            recv_line(s)   # expect OK
            send_line(s, "REDY")
            continue

        # any other message: stay safe
        send_line(s, "REDY")

    s.close()

# -------------------------
# Entrypoint
# -------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1", help="ds-server host")
    parser.add_argument("--port", type=int, default=50000, help="ds-server port")
    parser.add_argument("--user", default="46725067", help="student id for AUTH")
    args = parser.parse_args()
    run_client(args.host, args.port, args.user)

if __name__ == "__main__":
    main()




