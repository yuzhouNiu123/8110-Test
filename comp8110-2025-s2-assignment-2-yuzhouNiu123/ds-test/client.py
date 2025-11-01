#!/usr/bin/env python3
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("localhost", 55067))

def send(msg):
    sock.sendall((msg + '\n').encode())

def receive():
    return sock.recv(4096).decode().strip()

send("HELO")
receive()

send("AUTH yuzhouNiu")
receive()

send("GETS All")
response = receive()
parts = response.split()
nRecs = int(parts,[object Object],)

send("OK")
records = []
for i in range(nRecs):
    records.append(receive().split())
receive()

largest = max(records, key=lambda x: int(x,[object Object],))
server_type = largest,[object Object],
server_id = largest,[object Object],

while True:
    send("REDY")
    response = receive()
    
    if response.startswith("JOBN"):
        job_id = response.split(),[object Object],
        send("SCHD " + job_id + " " + server_type + " " + server_id)
        receive()
    elif response == "NONE":
        break
    elif response.startswith("JCPL"):
        continue

send("QUIT")
receive()
sock.close()
