import socket
import threading
import sys
import os
from cryptography.fernet import Fernet

# Завантаження ключа
try:
    with open("secret.key", "rb") as k_file:
        cipher = Fernet(k_file.read())
except:
    print("Error: Run setup.py first!")
    sys.exit()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(('127.0.0.1', 5555))
except:
    print("Server is offline.")
    sys.exit()

def receive():
    while True:
        try:
            data = client.recv(1024)
            if not data: break
            message = cipher.decrypt(data).decode()
            print(message)
            if "Too many attempts" in message:
                os._exit(0)
        except:
            break
    print("\nDisconnected.")
    os._exit(0)

threading.Thread(target=receive, daemon=True).start()

try:
    while True:
        msg = input("")
        if msg:
            client.send(cipher.encrypt(msg.encode()))
except:
    os._exit(0)