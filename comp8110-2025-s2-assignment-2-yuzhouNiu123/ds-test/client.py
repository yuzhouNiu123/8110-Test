#!/usr/bin/env python3#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal DS-Sim Python client (newline-terminated).
Implements the standard protocol:
HELO -> AUTH <id> -> REDY -> (JOBN -> GETS Capable -> SCHD -> ... ) -> NONE -> QUIT

Strategy: First-Fit over GETS Capable result (pick the first capable server).
You can later replace the `choose_server(...)` function to upgrade the algorithm.
"""

import argparse
import os
import socket

# -------------------------
# Utilities
# -------------------------
def send_line(sock, s: str):
    """Send one line (must be newline-terminated)."""
    if not s.endswith("\n"):
        s = s + "\n"
    sock.sendall(s.encode())

def recv_line(sock) -> str:
    """Receive one line (newline-terminated)."""
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
    """
    After sending GETS ..., server replies: "DATA n ..." (variants exist).
    Protocol (common MQ DS-Sim variant):
      Server:  DATA n ...
      Client:  OK
      Server:  [n lines of server records]
      Client:  OK
      Server:  .
    Return the list of records (each is a line string).
    """
    if not header.startswith("DATA"):
        return []

    parts = header.split()
    # usually "DATA n" or "DATA n recs"
    n = int(parts[1])
    records = []

    # first OK to start receiving records
    send_line(sock, "OK")

    for _ in range(n):
        rec = recv_line(sock)
        records.append(rec)

    # tell server we’re ready for the '.' terminator
    send_line(sock, "OK")
    dot = recv_line(sock)  # should be "."
    return records

# -------------------------
# Scheduling policy (First-Fit)
# -------------------------
def choose_server(capable_records):
    """
    Very simple First-Fit: pick the first record from GETS Capable list.
    A record typically looks like:
      "<stype> <sid> <state> <curStart> <cores> <mem> <disk> <wJobs> <rJobs>"
    We'll parse at least stype and sid.
    """
    if not capable_records:
        return None, None
    first = capable_records[0].split()
    # Defensive checks
    if len(first) < 2:
        return None, None
    stype = first[0]
    sid = first[1]
    return stype, sid

# -------------------------
# Main client logic
# -------------------------
def run_client(host: str, port: int, student_id: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    # Handshake
    send_line(s, "HELO")
    recv_line(s)  # expect "OK"
    send_line(s, f"AUTH {student_id}")
    recv_line(s)  # expect "OK"
    send_line(s, "REDY")

    while True:
        msg = recv_line(s)
        if not msg:
            # connection closed unexpectedly
            break

        # Job completed, just ask for next
        if msg.startswith("JCPL") or msg.startswith("OK"):
            send_line(s, "REDY")
            continue

        # No more jobs
        if msg == "NONE":
            send_line(s, "QUIT")
            recv_line(s)  # expect "QUIT"
            break

        # New job arrives
        if msg.startswith("JOBN") or msg.startswith("JOBP"):
            # JOBN <time> <jid> <cores> <mem> <disk>
            parts = msg.split()
            # Robust parsing for both JOBN/JOBP
            # Format is consistent: time, jid, cores, mem, disk are the last 5 tokens
            # e.g., JOBN t j c m d
            # Some variants may add user/priority fields; handle from the end:
            jid   = int(parts[-5+1])  # second from these 5 -> jid
            cores = int(parts[-3])    # cores
            mem   = int(parts[-2])    # mem
            disk  = int(parts[-1])    # disk

            # Query capable servers
            send_line(s, f"GETS Capable {cores} {mem} {disk}")
            header = recv_line(s)  # "DATA n ..."
            capable = recv_data_block(s, header)

            # Choose a server (First-Fit)
            stype, sid = choose_server(capable)
            if stype is None:
                # Fallback: ask for all servers and still pick first (extremely rare)
                send_line(s, "GETS All")
                header2 = recv_line(s)
                allrec = recv_data_block(s, header2)
                stype, sid = choose_server(allrec)
                if stype is None:
                    # As a last resort, just REDY to avoid deadlock
                    send_line(s, "REDY")
                    continue

            # Schedule
            send_line(s, f"SCHD {jid} {stype} {sid}")
            recv_line(s)  # expect "OK"
            send_line(s, "REDY")
            continue

        # Any other messages: stay robust, keep REDY
        send_line(s, "REDY")

    s.close()

# -------------------------
# Entrypoint
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="DS-Sim Python client (First-Fit).")
    parser.add_argument("-s", "--server", default="127.0.0.1", help="ds-server host (default: 127.0.0.1)")
    parser.add_argument("-p", "--port", type=int,
                        default=int(os.environ.get("DS_SIM_PORT", "50000")),
                        help="ds-server port (default: 50000, or DS_SIM_PORT env)")
    parser.add_argument("-i", "--student_id", default=os.environ.get("MQ_STUDENT_ID", "46725067"),
                        help="student id for AUTH (default: 46725067 or MQ_STUDENT_ID env)")
    args = parser.parse_args()

    run_client(args.server, args.port, args.student_id)

if __name__ == "__main__":
    main()


